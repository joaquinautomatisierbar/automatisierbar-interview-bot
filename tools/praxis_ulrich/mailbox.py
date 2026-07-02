"""mailbox.py — IMAP access for the Befund-Automat.

Two layers:

  * pure functions (offline-testable on .eml fixtures):
      extract_pdf_attachments(raw) -> [(filename, bytes, index)]
      parse_message_meta(raw)      -> {message_id, from_email, subject}
  * MailboxClient — thin imaplib wrapper with an injectable connection factory
      (tests pass a FakeIMAP), UID-based discovery, BODY.PEEK fetch (never sets
      \\Seen), and the red flag via UID STORE +FLAGS (\\Flagged).

UID-based polling because Outlook + HIN Client run in parallel on the same
mailbox and mark messages \\Seen before we ever see them — SEARCH UNSEEN would
silently miss everything. We track last_uid per UIDVALIDITY (state.py) and add
a SINCE rescan window on startup as a safety net; the dedup keys in state.py
make the rescan idempotent.

The client NEVER deletes, moves, or marks messages read. The only write it
ever performs on the mailbox is +FLAGS (\\Flagged) after a successful filing.
"""

from __future__ import annotations

import email
import email.policy
import imaplib
import re
from datetime import datetime, timedelta
from email.header import decode_header, make_header
from email.utils import parseaddr

# IMAP SEARCH date format is locale-independent English by spec.
_IMAP_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

_INTERNALDATE_RE = re.compile(rb'INTERNALDATE "([^"]+)"')
_MONTH_NUM = {m: i + 1 for i, m in enumerate(_IMAP_MONTHS)}


def imap_since(days: int, today: datetime | None = None) -> str:
    d = (today or datetime.now()) - timedelta(days=days)
    return f"{d.day:02d}-{_IMAP_MONTHS[d.month - 1]}-{d.year}"


# ---------------------------------------------------------------------------
# Pure message parsing
# ---------------------------------------------------------------------------


def _dh(raw) -> str:
    """Decode a possibly MIME-encoded header to plain text (pattern:
    tools/inbox_reply_drafter.py)."""
    if raw is None:
        return ""
    try:
        return str(make_header(decode_header(str(raw))))
    except Exception:
        return str(raw)


def parse_message_meta(raw: bytes) -> dict:
    m = email.message_from_bytes(raw, policy=email.policy.default)
    _, from_email = parseaddr(str(m.get("From", "")))
    return {
        "message_id": (str(m.get("Message-ID", "")) or "").strip(),
        "from_email": (from_email or "").lower().strip(),
        "subject": _dh(m.get("Subject", "")).strip(),
    }


def extract_pdf_attachments(raw: bytes) -> list[tuple[str, bytes, int]]:
    """All PDF attachments of a raw RFC 5322 message as (filename, bytes, index).

    A part counts as PDF if its content type is application/pdf OR its declared
    filename ends in .pdf (some hospital gateways send application/octet-stream).
    Inline non-PDF parts, images, signatures etc. are ignored. Never raises —
    an unparseable message yields [].
    """
    out: list[tuple[str, bytes, int]] = []
    try:
        m = email.message_from_bytes(raw, policy=email.policy.default)
        idx = 0
        for part in m.walk():
            if part.is_multipart():
                continue
            fname = _dh(part.get_filename() or "").strip()
            ctype = (part.get_content_type() or "").lower()
            is_pdf = ctype == "application/pdf" or fname.lower().endswith(".pdf")
            if not is_pdf:
                continue
            try:
                payload = part.get_payload(decode=True)
            except Exception:
                payload = None
            if not payload:
                continue
            if not fname:
                fname = f"anhang-{idx + 1}.pdf"
            out.append((fname, payload, idx))
            idx += 1
    except Exception:
        return []
    return out


# ---------------------------------------------------------------------------
# IMAP client
# ---------------------------------------------------------------------------


class MailboxError(Exception):
    pass


class MailboxClient:
    """Minimal IMAP session bound to one folder.

    conn_factory(host, port) -> imaplib.IMAP4_SSL-compatible object; tests
    inject a FakeIMAP here. Use as context manager or call close() yourself.
    """

    def __init__(self, host: str, port: int, user: str, password: str,
                 folder: str = "INBOX", conn_factory=None):
        self._factory = conn_factory or (lambda h, p: imaplib.IMAP4_SSL(h, p))
        self.host, self.port, self.user, self.folder = host, port, user, folder
        self._password = password
        self.conn = None
        self.uidvalidity: int = 0

    # -- lifecycle ---------------------------------------------------------

    def connect(self) -> "MailboxClient":
        conn = self._factory(self.host, self.port)
        typ, _ = conn.login(self.user, self._password)
        if typ != "OK":
            raise MailboxError("IMAP-Login fehlgeschlagen")
        typ, _ = conn.select(self.folder)
        if typ != "OK":
            raise MailboxError(f"Ordner nicht wählbar: {self.folder}")
        self.conn = conn
        self.uidvalidity = self._read_uidvalidity()
        return self

    def _read_uidvalidity(self) -> int:
        try:
            typ, data = self.conn.response("UIDVALIDITY")
            if data and data[0]:
                return int(data[0])
        except Exception:
            pass
        # Fallback via STATUS — some servers don't expose the untagged reply.
        try:
            typ, data = self.conn.status(self.folder, "(UIDVALIDITY)")
            m = re.search(rb"UIDVALIDITY (\d+)", data[0] or b"")
            if m:
                return int(m.group(1))
        except Exception:
            pass
        return 0

    def close(self) -> None:
        if self.conn is not None:
            try:
                self.conn.logout()
            except Exception:
                pass
            self.conn = None

    def __enter__(self):
        return self.connect()

    def __exit__(self, *exc):
        self.close()

    # -- discovery ---------------------------------------------------------

    def new_uids(self, last_uid: int, rescan_days: int = 0) -> list[int]:
        """UIDs above last_uid, plus (optionally) everything SINCE the rescan
        window. Sorted ascending, deduped. RFC quirk: 'UID N:*' matches the
        last message even when its UID < N, so we filter in code."""
        uids: set[int] = set()

        typ, data = self.conn.uid("search", None, "UID", f"{last_uid + 1}:*")
        if typ == "OK" and data and data[0]:
            uids.update(int(u) for u in data[0].split())

        if rescan_days > 0:
            typ, data = self.conn.uid("search", None, "SINCE", imap_since(rescan_days))
            if typ == "OK" and data and data[0]:
                uids.update(int(u) for u in data[0].split())

        return sorted(u for u in uids if u > last_uid or rescan_days > 0)

    # -- fetch -------------------------------------------------------------

    def fetch_raw(self, uid: int) -> tuple[bytes, datetime | None]:
        """(raw message bytes, INTERNALDATE or None). BODY.PEEK — leaves \\Seen
        untouched for Outlook."""
        typ, data = self.conn.uid("fetch", str(uid), "(INTERNALDATE BODY.PEEK[])")
        if typ != "OK" or not data:
            raise MailboxError(f"FETCH fehlgeschlagen für UID {uid}")
        raw, internal = b"", None
        for item in data:
            if isinstance(item, tuple) and len(item) >= 2:
                raw = item[1] or b""
                internal = _parse_internaldate(item[0] or b"")
        if not raw:
            raise MailboxError(f"leere FETCH-Antwort für UID {uid}")
        return raw, internal

    # -- the one mailbox write ----------------------------------------------

    def flag_red(self, uid: int) -> bool:
        """Set \\Flagged (shows as red follow-up flag in Outlook). True on OK."""
        try:
            typ, _ = self.conn.uid("STORE", str(uid), "+FLAGS", "(\\Flagged)")
            return typ == "OK"
        except Exception:
            return False


def _parse_internaldate(meta: bytes) -> datetime | None:
    """Parse INTERNALDATE out of a FETCH metadata line, locale-independent."""
    m = _INTERNALDATE_RE.search(meta)
    if not m:
        return None
    # e.g. 02-Jul-2026 09:32:00 +0200
    try:
        s = m.group(1).decode()
        dm = re.match(r"\s*(\d{1,2})-([A-Za-z]{3})-(\d{4}) (\d{2}):(\d{2}):(\d{2})", s)
        if not dm:
            return None
        day, mon, year, hh, mm, ss = dm.groups()
        return datetime(int(year), _MONTH_NUM[mon.title()], int(day),
                        int(hh), int(mm), int(ss))
    except Exception:
        return None
