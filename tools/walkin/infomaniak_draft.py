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
import os, sys, json, argparse, re, time, imaplib, tempfile
import html as _htmlmod
from email.message import EmailMessage
from email.utils import make_msgid, formatdate
from email.header import decode_header, make_header
import email.policy

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_ENV_CANDIDATES = [os.path.join(_SCRIPT_DIR, ".env"),
                   os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), ".env")]
ENV_PATH = next((p for p in _ENV_CANDIDATES if os.path.exists(p)), _ENV_CANDIDATES[0])
CFG_PATH = os.path.join(_SCRIPT_DIR, "walkin_config.json")

# Signature injection (Infomaniak doesn't auto-add the webmail signature to IMAP drafts).
sys.path.insert(0, _SCRIPT_DIR)
from infomaniak_signature import get_signature

# Legacy booking links to rewrite when migrating existing drafts.
OLD_BOOKINGS = ["https://calendar.app.google/mWy2heiDmRFcgFKA7"]

DEFAULT_CFG = {
    "imap_host": "mail.infomaniak.com",
    "imap_port": 993,
    "drafts_subfolder": "Walk-in",
    "drafts_parent": "Drafts",      # fallback only, if special-use detection fails
    "from": "joaquin@automatisierbar.ch",
    "sender": "Joaquin Gamonal",
    "phone": "+41 76 477 11 07",
    "cc": "tej@automatisierbar.ch",
    "booking": "https://cockpit.automatisierbar.ch/book",
    "mail_hosting_id": 985192,
    "mailbox_name": "joaquin",
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

def _body_to_html(body):
    """Render the plain-text mail body as a simple HTML block: escape, linkify http(s) URLs,
    newlines -> <br />. Font matches the Infomaniak signature so body + signature read as one."""
    esc = _htmlmod.escape(body)
    esc = re.sub(r"(https?://[^\s<]+)",
                 r'<a href="\1" style="color:rgb(21,201,122);text-decoration:none">\1</a>', esc)
    esc = esc.replace("\n", "<br />\n")
    return ('<div style="font-family:Helvetica,Arial,sans-serif;font-size:14px;'
            'line-height:1.55;color:rgb(12,20,16);white-space:normal">'
            + esc + "</div><br />\n")


def build_message(draft, from_addr, signature=None, msgid=None, cc=None,
                  in_reply_to=None, references=None):
    """Build a UTF-8 EmailMessage. Empty/absent `to` => no To header (An: leer).

    `cc` (or a per-draft `cc`) adds a Cc header — walk-in drafts always Cc the team (tej@).
    With a `signature` dict ({html, text}) the message is multipart/alternative: a plain-text
    part (body + text signature) and an HTML part (body + the operator's real HTML signature),
    so IMAP-appended drafts carry the standard Infomaniak signature. Without one it stays
    single-part plain text (graceful fallback).

    `in_reply_to` / `references` (or per-draft keys of the same name) set the RFC 5322 threading
    headers so a reply draft slots into the original conversation in the mail client. Both default
    to None (no headers) — walk-in drafts are new threads and never pass them."""
    msg = EmailMessage()
    msg["From"] = from_addr
    to = (draft.get("to") or "").strip()
    if to:
        msg["To"] = to
    cc_val = (draft.get("cc") if draft.get("cc") is not None else cc) or ""
    cc_val = cc_val.strip()
    if cc_val:
        msg["Cc"] = cc_val
    msg["Subject"] = draft.get("subject", "")
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = msgid or make_msgid(domain="automatisierbar.ch")
    irt = (draft.get("in_reply_to") if draft.get("in_reply_to") is not None else in_reply_to) or ""
    irt = irt.strip()
    if irt:
        msg["In-Reply-To"] = irt
    refs = (draft.get("references") if draft.get("references") is not None else references) or ""
    refs = refs.strip()
    if refs:
        msg["References"] = refs
    company = (draft.get("company") or "").strip()
    if company:
        msg["X-Walkin-Company"] = company
    body = draft.get("body", "")
    sig_html = (signature or {}).get("html") if signature else None
    sig_text = (signature or {}).get("text") if signature else None
    if sig_html or sig_text:
        msg.set_content(body + "\n\n" + (sig_text or ""), subtype="plain", charset="utf-8")
        msg.add_alternative(_body_to_html(body) + (sig_html or ""),
                            subtype="html", charset="utf-8")
    else:
        msg.set_content(body, subtype="plain", charset="utf-8")
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
    sig = get_signature(cfg)
    print(f"[dry ] Signatur: {'gefunden (' + sig['source'] + ')' if sig else 'KEINE (Fallback Klartext)'}")
    for d in drafts:
        msg = build_message(d, from_addr, signature=sig, cc=cfg.get("cc"))
        print("=" * 64)
        print(message_bytes(msg).decode("utf-8", "replace"))
    print("=" * 64)
    print(f"[dry ] {len(drafts)} Draft(s) gebaut, nichts gesendet.")
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
    sig = get_signature(cfg)
    print(f"[info] Signatur: {'gefunden (' + sig['source'] + ')' if sig else 'KEINE (Fallback Klartext)'}")
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
                msg = build_message(d, from_addr, signature=sig, cc=cfg.get("cc"))
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


# ---- migration (rewrite existing walk-in drafts) ----------------------------

def _decode_body_text(msg):
    """Best plain-text body from a parsed message (single-part or multipart/alternative)."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_content()
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                return part.get_content()
        return ""
    return msg.get_content()


def migrate_body(text, new_booking):
    """Rewrite an existing draft body: swap legacy booking links for the current one, and drop
    the hand-written identity lines under the closing salutation (the appended signature now
    carries name/company/phone). Keeps the 'Freundliche Grüsse …' salutation line itself."""
    for old in OLD_BOOKINGS:
        text = text.replace(old, new_booking)
    text = re.sub(r"(Freundliche Gr[üu]sse[^\n]*)\n.*\Z", r"\1", text, flags=re.S)
    return text.rstrip()


def _already_migrated(raw, m, cc=None):
    """True if a draft is already in the new format: multipart/alternative, no legacy booking
    link, the appended signature present (`Co-Founder` marker), and the team Cc present (when a
    `cc` is configured). Lets --migrate re-run as a clean no-op instead of churning done drafts."""
    text = raw.decode("utf-8", "replace") if isinstance(raw, (bytes, bytearray)) else raw
    cc_ok = (not cc) or (cc.lower() in (str(m.get("Cc") or "")).lower())
    return (m.is_multipart()
            and "Co-Founder" in text
            and not any(o in text for o in OLD_BOOKINGS)
            and cc_ok)


def cmd_migrate(cfg, args):
    """Rewrite every existing walk-in draft (X-Walkin-Company header) in the Drafts folder so
    it carries the current booking link + the real signature. --dry-run previews only.
    Apply path: append the rebuilt draft, back up the original, then delete + expunge it
    (append-before-delete, so a failure never loses a draft)."""
    from_addr = cfg["from"]
    new_booking = cfg.get("booking", DEFAULT_CFG["booking"])
    cc = cfg.get("cc")
    sig = get_signature(cfg)
    print(f"[migrate] Signatur: {'gefunden (' + sig['source'] + ')' if sig else 'KEINE (Fallback Klartext)'}"
          + (f" · Cc: {cc}" if cc else ""))
    if not sig and not args.dry_run:
        print("[FAIL] keine Signatur verfügbar (kein Token, kein Cache) — Abbruch, "
              "damit keine Drafts ohne Signatur entstehen.")
        return 2
    imap = _connect(cfg, args)
    if not imap:
        return 2
    try:
        target = _resolve_target(imap, cfg, args)
        imap.select(_q(target), readonly=bool(args.dry_run))
        typ, data = imap.uid("SEARCH", None, "ALL")
        uids = data[0].split() if typ == "OK" and data and data[0] else []
        # Fetch ALL raw messages first, so later appends don't disturb what we still need.
        walkin = []
        for uid in uids:
            t, d = imap.uid("FETCH", uid, "(BODY.PEEK[])")
            if t != "OK" or not d or not d[0]:
                continue
            raw = d[0][1]
            m = email.message_from_bytes(raw, policy=email.policy.default)
            if m.get("X-Walkin-Company"):
                walkin.append((uid, raw, m))
        print(f"[migrate] {len(walkin)} Walk-in-Draft(s) in {target} "
              f"(von {len(uids)} Drafts gesamt; Rest unangetastet)")
        if not walkin:
            return 0

        backup_dir = args.backup_dir or tempfile.gettempdir()
        if not args.dry_run:
            os.makedirs(backup_dir, exist_ok=True)
        changed = fails = skipped = 0
        for uid, raw, m in walkin:
            company = str(m.get("X-Walkin-Company") or "(?)")
            to = str(m.get("To") or "")
            subject = str(m.get("Subject") or "")
            to_tag = to or "(leer)"
            if _already_migrated(raw, m, cc):
                skipped += 1
                print(f"  [SKIP] {company}  An={to_tag}  (bereits migriert)")
                continue
            old_text = _decode_body_text(m)
            new_text = migrate_body(old_text, new_booking)
            book_fix = any(o in old_text for o in OLD_BOOKINGS)
            sign_fix = new_text != old_text.rstrip()
            cc_fix = bool(cc) and cc.lower() not in (str(m.get("Cc") or "")).lower()
            tags = ", ".join([t for t, on in (("Booking", book_fix), ("Signatur", sign_fix),
                                              ("Cc", cc_fix)) if on]) or "keine Änderung"
            if args.dry_run:
                print(f"  [DRY] {company}  An={to_tag}  -> {tags}")
                if book_fix:
                    print(f"          Booking: {OLD_BOOKINGS[0]} -> {new_booking}")
                continue
            try:
                # 1) back up the original FIRST — a backup failure must never leave a
                #    half-migrated duplicate (append succeeded, original not deleted).
                safe = re.sub(r"[^A-Za-z0-9]+", "_", company).strip("_") or "draft"
                bpath = os.path.join(backup_dir, f"walkin_migrate_{safe}_{uid.decode()}.eml")
                with open(bpath, "wb") as f:
                    f.write(raw)
                # 2) append the rebuilt draft, then 3) delete the original (append-before-delete).
                draft = {"company": company, "to": to, "subject": subject, "body": new_text}
                newmsg = build_message(draft, from_addr, signature=sig, cc=cc)
                t2, adata = imap.append(_q(target), "(\\Draft)",
                                        imaplib.Time2Internaldate(time.time()), message_bytes(newmsg))
                if t2 != "OK":
                    raise RuntimeError(f"APPEND -> {t2} {adata}")
                imap.uid("STORE", uid, "+FLAGS", "(\\Deleted)")
                changed += 1
                print(f"  [OK ] {company}  An={to_tag}  -> {tags}  (Backup {bpath})")
            except Exception as e:
                fails += 1
                print(f"  [FAIL] {company}: {e}")

        if args.dry_run:
            todo = len(walkin) - skipped
            print(f"[migrate] DRY-RUN: {todo} Draft(s) würden neu erstellt, "
                  f"{skipped} bereits migriert, nichts geändert.")
            return 0
        if changed:
            imap.expunge()
        print(f"[migrate] {changed} neu erstellt"
              + (f", {skipped} übersprungen (bereits migriert)" if skipped else "")
              + (f", {fails} fehlgeschlagen" if fails else "")
              + (", Originale entfernt." if changed else "."))
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

    # Signature path => multipart/alternative with plain + html, signature appended
    SIG = {"html": "<div>Joaquin Gamonal</div>", "text": "Joaquin Gamonal\nautomatisierbar.ch"}
    d3 = {"company": "X AG", "to": "a@b.ch", "subject": "S",
          "body": "Hallo,\n\n👉 https://cockpit.automatisierbar.ch/book\n\nFreundliche Grüsse aus Baden,"}
    m3 = build_message(d3, "joaquin@automatisierbar.ch", signature=SIG, msgid="<t3@automatisierbar.ch>")
    check("Signatur => multipart/alternative", m3.get_content_type() == "multipart/alternative")
    types = [p.get_content_type() for p in m3.iter_parts()]
    check("multipart hat text/plain", "text/plain" in types)
    check("multipart hat text/html", "text/html" in types)
    plain = next(p for p in m3.iter_parts() if p.get_content_type() == "text/plain").get_content()
    htmlp = next(p for p in m3.iter_parts() if p.get_content_type() == "text/html").get_content()
    check("Plain enthält Signatur-Text", "automatisierbar.ch" in plain and "Joaquin Gamonal" in plain)
    check("HTML enthält Signatur", "Joaquin Gamonal" in htmlp)
    check("HTML verlinkt neuen Booking-Link",
          'href="https://cockpit.automatisierbar.ch/book"' in htmlp)
    check("neuer Booking-Link im Body", "cockpit.automatisierbar.ch/book" in plain)
    check("Emoji bleibt in beiden Teilen", "👉" in plain and "👉" in htmlp)
    check("kein Gedankenstrich im HTML", "—" not in htmlp and "–" not in htmlp)
    check("multipart CRLF", b"\r\n" in message_bytes(m3))

    # Cc header (team copy on every walk-in draft)
    m_cc = build_message(d1, "joaquin@automatisierbar.ch", cc="tej@automatisierbar.ch",
                         msgid="<t4@automatisierbar.ch>")
    check("Cc gesetzt", m_cc["Cc"] == "tej@automatisierbar.ch")
    m_nocc = build_message(d1, "joaquin@automatisierbar.ch", msgid="<t5@automatisierbar.ch>")
    check("kein Cc ohne Angabe", m_nocc["Cc"] is None)
    d_ovr = {"company": "Y AG", "to": "a@b.ch", "subject": "s", "body": "x", "cc": "override@x.ch"}
    m_ovr = build_message(d_ovr, "joaquin@automatisierbar.ch", cc="tej@automatisierbar.ch")
    check("per-draft Cc override", m_ovr["Cc"] == "override@x.ch")

    # Threading headers (reply drafts slot into the original conversation)
    m_thr = build_message(d1, "joaquin@automatisierbar.ch", msgid="<r1@automatisierbar.ch>",
                          in_reply_to="<orig@example.ch>",
                          references="<a@example.ch> <orig@example.ch>")
    check("In-Reply-To gesetzt", m_thr["In-Reply-To"] == "<orig@example.ch>")
    check("References gesetzt", m_thr["References"] == "<a@example.ch> <orig@example.ch>")
    check("In-Reply-To serialisiert", b"In-Reply-To: <orig@example.ch>" in message_bytes(m_thr))
    m_nothr = build_message(d1, "joaquin@automatisierbar.ch", msgid="<r2@automatisierbar.ch>")
    check("kein In-Reply-To ohne Angabe", m_nothr["In-Reply-To"] is None)
    check("kein References ohne Angabe", m_nothr["References"] is None)
    d_irt = {"company": "Z AG", "to": "a@b.ch", "subject": "s", "body": "x",
             "in_reply_to": "<perdraft@example.ch>"}
    m_irt = build_message(d_irt, "joaquin@automatisierbar.ch")
    check("per-draft In-Reply-To", m_irt["In-Reply-To"] == "<perdraft@example.ch>")

    # _body_to_html: linkify + <br />
    h = _body_to_html("Zeile1\nhttps://cockpit.automatisierbar.ch/book")
    check("_body_to_html <br />", "<br />" in h)
    check("_body_to_html linkify", 'href="https://cockpit.automatisierbar.ch/book"' in h)

    # migrate_body: swap legacy link, strip identity lines, keep salutation
    sample = ("Guten Tag,\n\n👉 " + OLD_BOOKINGS[0] +
              "\n\nFreundliche Grüsse aus Baden,\nJoaquin Gamonal\nAutomatisierbar\n+41 76 477 11 07")
    mb = migrate_body(sample, "https://cockpit.automatisierbar.ch/book")
    check("migrate: alter Link weg", OLD_BOOKINGS[0] not in mb)
    check("migrate: neuer Link da", "https://cockpit.automatisierbar.ch/book" in mb)
    check("migrate: Salutation bleibt", mb.rstrip().endswith("Freundliche Grüsse aus Baden,"))
    check("migrate: Identitätszeilen weg", "Joaquin Gamonal" not in mb and "477 11 07" not in mb)

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
    ap.add_argument("--dry-run", action="store_true", help="Build + print MIME / preview migration, no writes")
    ap.add_argument("--list-folders", action="store_true", help="Login + show folders/detection")
    ap.add_argument("--selftest", action="store_true", help="Offline format/logic checks")
    ap.add_argument("--migrate", action="store_true",
                    help="Rewrite existing walk-in drafts (booking link + signature). Honors --dry-run.")
    ap.add_argument("--backup-dir", help="Where --migrate backs up original drafts (default: temp dir)")
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

    if args.migrate:
        sys.exit(cmd_migrate(cfg, args))

    if not args.payload:
        ap.error("either --payload, --list-folders, --migrate, or --selftest is required")

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
