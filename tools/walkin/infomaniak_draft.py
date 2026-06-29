#!/usr/bin/env python3
"""
infomaniak_draft.py — push walk-in follow-up mails straight into the Infomaniak mailbox
as openable DRAFTS (open -> send), so the operator no longer copy-pastes out of Notion.

Mechanism: IMAP APPEND into the Drafts folder with the \\Draft flag. ONLY imaplib is used,
never smtplib — by construction this tool cannot send anything, it only deposits a draft the
operator opens and sends manually from Infomaniak webmail.

  --payload P    JSON file (or "-" for stdin) of the mails to draft (schema below).
  --dry-run      Build + print each MIME message, no network.
  --list-folders Login, print the folder tree + the auto-detected Drafts folder + separator.
  --selftest     Offline checks of MIME build / folder-path logic (no creds, no network).
  --dedup        Skip a company whose draft (same X-Walkin-Company header) is already present.
  --no-verify    Skip the post-append Message-ID search check.

Payload schema:
  {"from": "joaquin@automatisierbar.ch",
   "drafts": [
     {"company": "Novideas AG", "to": "x@y.ch", "subject": "...", "body": "...",
      "confident": true},
     {"company": "Pro Infirmis", "to": "", "subject": "...", "body": "...",
      "confident": false, "note": "Adresse prüfen"}   // confident:false / empty to -> An: leer
   ]}

Auth (.env): INFOMANIAK_IMAP_USER, INFOMANIAK_IMAP_PASSWORD (Infomaniak application password).
Missing creds -> exit 2 with a clear message; the calling skill then falls back to Notion-only.
Defaults (host/port/subfolder/identity) live in walkin_config.json; env vars override.
"""
import os, sys, json, argparse, re, time, imaplib
from email.message import EmailMessage
from email.utils import make_msgid, formatdate
from email.header import decode_header, make_header
import email.policy

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_ENV_CANDIDATES = [os.path.join(_SCRIPT_DIR, ".env"),
                   os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), ".env")]
ENV_PATH = next((p for p in _ENV_CANDIDATES if os.path.exists(p)), _ENV_CANDIDATES[0])
CFG_PATH = os.path.join(_SCRIPT_DIR, "walkin_config.json")

DEFAULT_CFG = {
    "imap_host": "mail.infomaniak.com",
    "imap_port": 993,
    "drafts_subfolder": "Walk-in",
    "drafts_parent": "Drafts",      # fallback only, if special-use detection fails
    "from": "joaquin@automatisierbar.ch",
    "sender": "Joaquin Gamonal",
    "phone": "+41 76 477 11 07",
    "booking": "https://calendar.app.google/mWy2heiDmRFcgFKA7",
}


def env(k, d=None):
    try:
        for ln in open(ENV_PATH):
            if ln.strip().startswith(k + "="):
                return ln.strip().split("=", 1)[1].strip()
    except FileNotFoundError:
        pass
    return os.environ.get(k, d)


def load_config():
    cfg = dict(DEFAULT_CFG)
    try:
        with open(CFG_PATH) as f:
            cfg.update(json.load(f))
    except FileNotFoundError:
        pass
    return cfg


# ---- pure helpers (offline-testable) ----------------------------------------

def build_message(draft, from_addr, msgid=None):
    """Build a plain-text UTF-8 EmailMessage. Empty/absent `to` => no To header (An: leer)."""
    msg = EmailMessage()
    msg["From"] = from_addr
    to = (draft.get("to") or "").strip()
    if to:
        msg["To"] = to
    msg["Subject"] = draft.get("subject", "")
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = msgid or make_msgid(domain="automatisierbar.ch")
    company = (draft.get("company") or "").strip()
    if company:
        msg["X-Walkin-Company"] = company
    msg.set_content(draft.get("body", ""), subtype="plain", charset="utf-8")
    return msg


def message_bytes(msg):
    """Serialize with CRLF line endings (RFC 5322 / IMAP-APPEND-conformant)."""
    return msg.as_bytes(policy=email.policy.SMTP)


_LIST_RE = re.compile(r'^\((?P<flags>[^)]*)\)\s+(?P<sep>"[^"]*"|NIL)\s+(?P<name>.+?)\s*$')


def _parse_list_line(line):
    """Parse one IMAP LIST response line -> {flags, sep, name} (name kept in on-wire form)."""
    s = line.decode("utf-8", "surrogateescape") if isinstance(line, (bytes, bytearray)) else line
    m = _LIST_RE.match(s)
    if not m:
        return None
    flags = m.group("flags").split()
    sep = m.group("sep")
    sep = "/" if sep == "NIL" else (sep.strip('"') or "/")
    name = m.group("name").strip()
    if len(name) >= 2 and name[0] == '"' and name[-1] == '"':
        name = name[1:-1]
    return {"flags": flags, "sep": sep, "name": name}


def pick_drafts_folder(list_lines):
    """Return (parent_name, separator). Prefer the \\Drafts special-use folder, then common
    names, then any 'draft'/'entwurf' match. parent_name is None if nothing plausible found."""
    parsed = [p for p in (_parse_list_line(l) for l in (list_lines or [])) if p]
    sep_default = parsed[0]["sep"] if parsed else "/"
    # 1) RFC 6154 special-use flag
    for p in parsed:
        if any(f.lower() == "\\drafts" for f in p["flags"]):
            return p["name"], p["sep"]
    # 2) exact common names
    by_name = {p["name"]: p for p in parsed}
    for nm in ("Drafts", "INBOX.Drafts", "INBOX/Drafts", "Entwürfe", "Entwurf"):
        if nm in by_name:
            return nm, by_name[nm]["sep"]
    # 3) fuzzy
    for p in parsed:
        low = p["name"].lower()
        if "draft" in low or "entwurf" in low or "entwürf" in low:
            return p["name"], p["sep"]
    return None, sep_default


def build_target(parent, sep, subfolder):
    """Concatenate in on-wire form. Keeping the server's raw parent name + ASCII parts means
    a modified-UTF-7 parent (e.g. Entwürfe) stays valid without us re-encoding it."""
    if not subfolder:
        return parent
    return parent + sep + subfolder


def _q(mbox):
    return '"' + mbox.replace('"', '\\"') + '"'


# ---- IMAP operations --------------------------------------------------------

def _folder_names(imap):
    typ, lines = imap.list()
    names = set()
    for l in (lines or []):
        p = _parse_list_line(l)
        if p:
            names.add(p["name"])
    return names


def ensure_folder(imap, target):
    if target not in _folder_names(imap):
        imap.create(_q(target))
        try:
            imap.subscribe(_q(target))
        except Exception:
            pass


_APPENDUID_RE = re.compile(rb"APPENDUID\s+(\d+)\s+(\d+)")


def _appenduid(append_data):
    """Pull the assigned UID out of the server's APPEND response (RFC 4315 UIDPLUS).
    Race-free confirmation — unlike a post-append header search, which can miss a
    message Dovecot hasn't indexed yet."""
    for part in (append_data or []):
        if isinstance(part, (bytes, bytearray)):
            m = _APPENDUID_RE.search(part)
            if m:
                return m.group(2).decode()
        elif isinstance(part, str):
            m = _APPENDUID_RE.search(part.encode())
            if m:
                return m.group(2).decode()
    return None


def _existing_companies(imap, target):
    """Set of X-Walkin-Company values already in the folder. Fetches + decodes headers in Python
    rather than a server-side HEADER SEARCH, which imaplib can't encode for non-ASCII criteria
    (e.g. 'Helvetia Zürich') and which Dovecot won't match on an empty string."""
    out = set()
    try:
        imap.select(_q(target))
        typ, data = imap.search(None, "ALL")
        if typ != "OK" or not data or not data[0]:
            return out
        for num in data[0].split():
            t, d = imap.fetch(num, "(BODY.PEEK[HEADER.FIELDS (X-WALKIN-COMPANY)])")
            if t != "OK" or not d or not d[0]:
                continue
            raw = d[0][1]
            if isinstance(raw, (bytes, bytearray)):
                raw = raw.decode("utf-8", "replace")
            m = re.search(r"X-Walkin-Company:\s*(.+)", raw)
            if m:
                out.add(str(make_header(decode_header(m.group(1).strip()))))
    except Exception:
        pass
    return out


def _connect(cfg, args):
    user = args.user or env("INFOMANIAK_IMAP_USER") or cfg.get("from")
    pw = env("INFOMANIAK_IMAP_PASSWORD")
    if not user or not pw:
        print("[FAIL] Infomaniak-Creds fehlen (INFOMANIAK_IMAP_USER / INFOMANIAK_IMAP_PASSWORD in .env)")
        return None
    host = args.host or env("INFOMANIAK_IMAP_HOST") or cfg["imap_host"]
    port = int(args.port or env("INFOMANIAK_IMAP_PORT") or cfg["imap_port"])
    try:
        imap = imaplib.IMAP4_SSL(host, port)
        imap.login(user, pw)
        return imap
    except Exception as e:
        print(f"[FAIL] IMAP-Login fehlgeschlagen ({host}:{port}): {e}")
        return None


def _resolve_target(imap, cfg, args):
    typ, lines = imap.list()
    parent, sep = pick_drafts_folder(lines)
    if not parent:
        parent = env("INFOMANIAK_DRAFTS_PARENT") or cfg.get("drafts_parent", "Drafts")
    subfolder = args.folder or env("INFOMANIAK_WALKIN_SUBFOLDER") or cfg["drafts_subfolder"]
    return build_target(parent, sep, subfolder)


# ---- commands ---------------------------------------------------------------

def cmd_dry_run(payload, cfg):
    from_addr = payload.get("from") or cfg["from"]
    drafts = payload.get("drafts", [])
    if not drafts:
        print("[noop] keine Drafts im Payload")
        return 0
    for d in drafts:
        msg = build_message(d, from_addr)
        print("=" * 64)
        print(message_bytes(msg).decode("utf-8", "replace"))
    print("=" * 64)
    print(f"[dry ] {len(drafts)} Draft(s) gebaut, nichts gesendet, kein Netzzugriff.")
    return 0


def cmd_list_folders(cfg, args):
    imap = _connect(cfg, args)
    if not imap:
        return 2
    try:
        typ, lines = imap.list()
        print("--- Ordner ---")
        for l in (lines or []):
            p = _parse_list_line(l)
            if p:
                flag = " ".join(p["flags"])
                print(f"  {p['name']}   (sep={p['sep']!r}  flags={flag})")
        parent, sep = pick_drafts_folder(lines)
        target = build_target(parent or cfg.get("drafts_parent", "Drafts"), sep,
                              args.folder or cfg["drafts_subfolder"])
        print(f"--- erkannt: Drafts-Parent={parent!r}  sep={sep!r}  ->  Ziel={target!r} ---")
        return 0
    finally:
        try:
            imap.logout()
        except Exception:
            pass


def cmd_push(payload, cfg, args):
    drafts = payload.get("drafts", [])
    if not drafts:
        print("[noop] keine Drafts im Payload")
        return 0
    from_addr = payload.get("from") or cfg["from"]
    imap = _connect(cfg, args)
    if not imap:
        return 2
    try:
        target = _resolve_target(imap, cfg, args)
        ensure_folder(imap, target)
        print(f"[info] Ziel-Ordner: {target}")
        existing = _existing_companies(imap, target) if args.dedup else set()
        fails = 0
        for d in drafts:
            company = (d.get("company") or "(?)").strip()
            try:
                if args.dedup and company in existing:
                    print(f"[skip] {company} (Duplikat schon im Ordner)")
                    continue
                msg = build_message(d, from_addr)
                raw = message_bytes(msg)
                typ, adata = imap.append(_q(target), "(\\Draft)",
                                         imaplib.Time2Internaldate(time.time()), raw)
                if typ != "OK":
                    raise RuntimeError(f"APPEND -> {typ} {adata}")
                empty = not (d.get("to") or "").strip()
                tag = " (An: leer)" if empty else ""
                ver = ""
                if not args.no_verify:
                    uid = _appenduid(adata)
                    ver = f" [uid {uid}]" if uid else " [ok, keine UID]"
                print(f"[OK  ] {company} -> {target}{tag}{ver}")
            except Exception as e:
                fails += 1
                print(f"[FAIL] {company}: {e}")
        print(f"[done] {len(drafts) - fails}/{len(drafts)} als Draft abgelegt"
              + (f", {fails} fehlgeschlagen" if fails else ""))
        return 1 if fails else 0
    finally:
        try:
            imap.logout()
        except Exception:
            pass


# ---- selftest (offline) -----------------------------------------------------

def cmd_selftest():
    PASS, FAIL = [], []

    def check(name, cond):
        (PASS if cond else FAIL).append(name)
        print(("  ok  " if cond else "FAIL  ") + name)

    # MIME build: confident draft with To
    d1 = {"company": "Novideas AG", "to": "x@y.ch", "subject": "Betreff ä",
          "body": "Guten Tag Herr Meyer,\n\nGrüsse 👉 https://x", "confident": True}
    m1 = build_message(d1, "joaquin@automatisierbar.ch", msgid="<t1@automatisierbar.ch>")
    b1 = message_bytes(m1)
    check("From gesetzt", m1["From"] == "joaquin@automatisierbar.ch")
    check("To gesetzt", m1["To"] == "x@y.ch")
    check("Subject gesetzt", m1["Subject"] == "Betreff ä")
    check("X-Walkin-Company gesetzt", m1["X-Walkin-Company"] == "Novideas AG")
    check("Message-ID gesetzt", m1["Message-ID"] == "<t1@automatisierbar.ch>")
    check("CRLF-Zeilenenden", b"\r\n" in b1 and b"\n" not in b1.replace(b"\r\n", b""))
    check("Umlaut bleibt erhalten", "Grüsse" in m1.get_content())
    check("Emoji bleibt erhalten", "👉" in m1.get_content())
    check("kein Gedankenstrich im Body", "—" not in m1.get_content() and "–" not in m1.get_content())

    # Empty-To draft (best-guess address)
    d2 = {"company": "Pro Infirmis", "to": "", "subject": "B", "body": "x", "confident": False}
    m2 = build_message(d2, "joaquin@automatisierbar.ch", msgid="<t2@automatisierbar.ch>")
    check("Empty-To => kein To-Header", m2["To"] is None)

    # Folder detection: special-use, separator "/"
    lines_slash = [b'(\\HasNoChildren) "/" "INBOX"',
                   b'(\\HasNoChildren \\Drafts) "/" "Drafts"',
                   b'(\\HasNoChildren \\Sent) "/" "Sent"']
    p, sep = pick_drafts_folder(lines_slash)
    check("special-use \\Drafts erkannt", p == "Drafts" and sep == "/")
    check("Ziel-Pfad (/) korrekt", build_target(p, sep, "Walk-in") == "Drafts/Walk-in")

    # Folder detection: separator ".", INBOX namespace
    lines_dot = [b'(\\HasNoChildren) "." INBOX',
                 b'(\\HasNoChildren \\Drafts) "." INBOX.Drafts']
    p2, sep2 = pick_drafts_folder(lines_dot)
    check("special-use mit sep '.'", p2 == "INBOX.Drafts" and sep2 == ".")
    check("Ziel-Pfad (.) korrekt", build_target(p2, sep2, "Walk-in") == "INBOX.Drafts.Walk-in")

    # Folder detection: no special-use, fall back to name "Drafts"
    lines_noflag = [b'(\\HasNoChildren) "/" "INBOX"',
                    b'(\\HasNoChildren) "/" "Drafts"']
    p3, sep3 = pick_drafts_folder(lines_noflag)
    check("Fallback auf Namen 'Drafts'", p3 == "Drafts")

    # Folder detection: localized "Entwürfe" via special-use
    lines_de = [b'(\\HasNoChildren) "/" "INBOX"',
                b'(\\HasNoChildren \\Drafts) "/" "Entw\xc3\xbcrfe"']
    p4, sep4 = pick_drafts_folder(lines_de)
    check("lokalisierter Drafts-Name via special-use", p4 is not None and "Entw" in p4)

    # Quoting
    check("Mailbox-Quoting", _q("Drafts/Walk-in") == '"Drafts/Walk-in"')

    print()
    if FAIL:
        print(f"❌ {len(FAIL)} FEHLGESCHLAGEN: {FAIL}")
        return 1
    print(f"✅ alle {len(PASS)} infomaniak_draft Selftests bestanden")
    return 0


def load_payload(path):
    if path == "-":
        return json.load(sys.stdin)
    with open(path) as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser(description="Push walk-in mails as Infomaniak IMAP drafts.")
    ap.add_argument("--payload", help='JSON payload file, or "-" for stdin')
    ap.add_argument("--dry-run", action="store_true", help="Build + print MIME, no network")
    ap.add_argument("--list-folders", action="store_true", help="Login + show folders/detection")
    ap.add_argument("--selftest", action="store_true", help="Offline format/logic checks")
    ap.add_argument("--dedup", action="store_true", help="Skip companies already drafted")
    ap.add_argument("--no-verify", action="store_true", help="Skip post-append verification")
    ap.add_argument("--host", help="Override IMAP host")
    ap.add_argument("--port", help="Override IMAP port")
    ap.add_argument("--user", help="Override IMAP user")
    ap.add_argument("--folder", help="Subfolder under Drafts; empty/unset = main Drafts folder")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(cmd_selftest())

    cfg = load_config()

    if args.list_folders:
        sys.exit(cmd_list_folders(cfg, args))

    if not args.payload:
        ap.error("either --payload, --list-folders, or --selftest is required")

    try:
        payload = load_payload(args.payload)
    except (OSError, json.JSONDecodeError) as e:
        print(f"[FAIL] Payload nicht lesbar: {e}")
        sys.exit(2)

    if args.dry_run:
        sys.exit(cmd_dry_run(payload, cfg))
    sys.exit(cmd_push(payload, cfg, args))


if __name__ == "__main__":
    main()
