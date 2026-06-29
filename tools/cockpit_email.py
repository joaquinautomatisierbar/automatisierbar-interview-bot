"""cockpit_email.py — branded booking-confirmation email + calendar invite (.ics).

Sends a clean confirmation email with an attached iCalendar invite (METHOD:REQUEST)
so the prospect can add the appointment to any calendar (Google/Apple/Outlook) just
like a Google booking. Sends via Infomaniak SMTP using the SAME credentials the
walk-in IMAP tool uses (INFOMANIAK_IMAP_USER / INFOMANIAK_IMAP_PASSWORD — one
Infomaniak application password works for both IMAP and SMTP).

Graceful: if no SMTP credentials are configured, send_confirmation() returns False
and logs — the booking still succeeds, the email is simply skipped.
"""

import os
import smtplib
import uuid
from datetime import datetime, timezone
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from urllib.parse import quote

import requests


def _smtp_cfg() -> dict:
    user = os.environ.get("INFOMANIAK_SMTP_USER") or os.environ.get("INFOMANIAK_IMAP_USER", "")
    pw = os.environ.get("INFOMANIAK_SMTP_PASSWORD") or os.environ.get("INFOMANIAK_IMAP_PASSWORD", "")
    return {
        "host": os.environ.get("INFOMANIAK_SMTP_HOST", "mail.infomaniak.com"),
        "port": int(os.environ.get("INFOMANIAK_SMTP_PORT", "465")),
        "user": user.strip(),
        "pw": pw,
        "from_name": os.environ.get("COCKPIT_FROM_NAME", "Automatisierbar"),
        # Visible sender / reply-to / organizer + footer contact. Public address.
        "from_email": (os.environ.get("COCKPIT_FROM_EMAIL", "info@automatisierbar.ch")).strip(),
    }


def smtp_configured() -> bool:
    c = _smtp_cfg()
    return bool(c["user"] and c["pw"])


# ---------------------------------------------------------------------------
# Infomaniak Mail API (token-based) — preferred path. Lets us send AS info@
# (which SMTP-as-joaquin@ can't, per Infomaniak "Sender mismatch"). One POST
# to /mail/{uuid}/draft with action=send delivers the mail.
# ---------------------------------------------------------------------------

INFOMANIAK_MAIL_API = "https://mail.infomaniak.com/api"
_mailbox_uuid_cache: dict = {}


def mail_api_token() -> str:
    return os.environ.get("INFOMANIAK_MAIL_TOKEN", "").strip()


def _mail_api_mailbox_uuid(token: str, from_email: str):
    """Resolve the mailbox UUID for `from_email` (cached). Returns None if not found."""
    key = from_email.lower()
    if key in _mailbox_uuid_cache:
        return _mailbox_uuid_cache[key]
    try:
        r = requests.get(
            f"{INFOMANIAK_MAIL_API}/mailbox?with=aliases,permissions,accountId,count_users",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            timeout=20)
        r.raise_for_status()
        for m in r.json().get("data", []):
            if (m.get("email") or "").lower() == key:
                uuid_ = m.get("mailbox_uuid") or m.get("uuid")
                _mailbox_uuid_cache[key] = uuid_
                return uuid_
    except Exception as e:
        print(f"[cockpit_email] mailbox uuid lookup failed: {e}")
    return None


def _send_via_mail_api(*, token, from_email, from_name, to_email, to_name, subject, html) -> bool:
    """Send one HTML email via the Infomaniak Mail API. Returns True on success."""
    uuid_ = _mail_api_mailbox_uuid(token, from_email)
    if not uuid_:
        print(f"[cockpit_email] mail-api: no mailbox uuid for {from_email}")
        return False
    body = {
        "from": {"id": None, "name": from_name, "email": from_email},
        "to": [{"name": to_name or "", "email": to_email}],
        "subject": subject,
        "body": html,
        "mime_type": "text/html",
        "action": "send",
    }
    try:
        r = requests.post(
            f"{INFOMANIAK_MAIL_API}/mail/{uuid_}/draft",
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json", "Accept": "application/json"},
            json=body, timeout=30)
        if r.status_code >= 300:
            print(f"[cockpit_email] mail-api send failed: {r.status_code} {r.text[:200]}")
            return False
        if r.json().get("result") != "success":
            print(f"[cockpit_email] mail-api not success: {r.text[:200]}")
            return False
        return True
    except Exception as e:
        print(f"[cockpit_email] mail-api send error: {e}")
        return False


def _gcal_add_link(summary, start_dt, end_dt, location, details) -> str:
    """One-click 'add to Google Calendar' template link."""
    fmt = lambda d: d.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return ("https://calendar.google.com/calendar/render?action=TEMPLATE"
            f"&text={quote(str(summary))}&dates={fmt(start_dt)}/{fmt(end_dt)}"
            f"&location={quote(str(location))}&details={quote(str(details))}")


def _esc(s: str) -> str:
    """Escape a value for an iCalendar text field (RFC 5545)."""
    return (str(s or "")
            .replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\r\n", "\n").replace("\n", "\\n"))


def _utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def build_ics(*, start_dt, end_dt, summary, description, location,
              organizer_email, organizer_name, attendee_email, attendee_name,
              uid=None, now=None) -> str:
    """Return an iCalendar VEVENT (METHOD:REQUEST) string. Times are emitted in UTC."""
    uid = uid or (uuid.uuid4().hex + "@automatisierbar.ch")
    stamp = _utc(now or datetime.now(timezone.utc))
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Automatisierbar//Cockpit Booking//DE",
        "CALSCALE:GREGORIAN",
        "METHOD:REQUEST",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{stamp}",
        f"DTSTART:{_utc(start_dt)}",
        f"DTEND:{_utc(end_dt)}",
        f"SUMMARY:{_esc(summary)}",
        f"DESCRIPTION:{_esc(description)}",
        f"LOCATION:{_esc(location)}",
        f"ORGANIZER;CN={_esc(organizer_name)}:mailto:{organizer_email}",
        f"ATTENDEE;CN={_esc(attendee_name)};ROLE=REQ-PARTICIPANT;RSVP=TRUE:mailto:{attendee_email}",
        "STATUS:CONFIRMED",
        "SEQUENCE:0",
        "TRANSP:OPAQUE",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    return "\r\n".join(lines) + "\r\n"


def _confirmation_html(*, name, when_label, address, slot_minutes, organizer_email, add_to_cal="") -> str:
    """Branded confirmation in the booking-site's single dark theme (static/book.html):
    bg #0A0F0D, one accent green #15C97A, Inter + JetBrains Mono, a green-glow check that
    echoes the page's on-screen success state. Table-based + inline-styled for email clients.
    """
    logo_url = os.environ.get(
        "COCKPIT_LOGO_URL",
        "https://cockpit.automatisierbar.ch/static/automatisierbar-logo-email.png")
    _sans = ("'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,Helvetica,sans-serif")
    _mono = ("'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,'Courier New',monospace")
    if add_to_cal:
        cal_html = (
            f'<a href="{add_to_cal}" style="display:inline-block;background:#15C97A;'
            'background:linear-gradient(135deg,#5EE0A6,#15C97A);color:#04130c;'
            f"font-family:{_sans};font-weight:700;text-decoration:none;padding:13px 26px;"
            'border-radius:9px;font-size:14.5px">Zum Kalender hinzufügen</a>'
            '<div style="margin-top:14px;font-size:13.5px;color:#8A9892">'
            'Wir kommen zum vereinbarten Zeitpunkt zu Ihnen.</div>')
    else:
        cal_html = ('Die <strong style="color:#ECF3EF">Kalendereinladung</strong> ist dieser '
                    'E-Mail angehängt, einfach öffnen, um den Termin in Ihren Kalender zu '
                    'übernehmen. Wir kommen zum vereinbarten Zeitpunkt zu Ihnen.')
    return f"""\
<!DOCTYPE html><html lang="de"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark">
<meta name="supported-color-schemes" content="dark">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
</head>
<body style="margin:0;padding:0;background:#0A0F0D;background-image:radial-gradient(800px 420px at 50% -8%,rgba(21,201,122,.12),transparent 70%);font-family:{_sans};color:#ECF3EF">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="#0A0F0D" style="background:#0A0F0D;padding:30px 0">
<tr><td align="center" style="padding:0 16px">

  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:520px">
    <tr><td style="padding:2px 4px 18px">
      <table role="presentation" cellpadding="0" cellspacing="0"><tr>
        <td style="vertical-align:middle;padding-right:11px">
          <img src="{logo_url}" width="38" height="38" alt="Automatisierbar" style="display:block;border:0;border-radius:10px">
        </td>
        <td style="vertical-align:middle">
          <div style="font-size:15.5px;font-weight:700;color:#ECF3EF;letter-spacing:-.2px;line-height:1.25">Automatisierbar</div>
          <div style="font-size:11.5px;font-weight:500;color:#5A655F;letter-spacing:.3px">Automatisierung, die Zeit spart</div>
        </td>
      </tr></table>
    </td></tr>
  </table>

  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="#111815" style="max-width:520px;background:#111815;border:1px solid rgba(255,255,255,.08);border-radius:14px">
    <tr><td align="center" style="padding:34px 30px 0">
      <table role="presentation" cellpadding="0" cellspacing="0"><tr>
        <td width="62" height="62" align="center" valign="middle" bgcolor="#123425" style="width:62px;height:62px;background:rgba(21,201,122,.16);border-radius:50%;font-size:30px;line-height:62px;color:#5EE0A6;font-weight:700">&#10003;</td>
      </tr></table>
    </td></tr>
    <tr><td align="center" style="padding:20px 30px 0">
      <h1 style="margin:0;font-size:22px;font-weight:700;letter-spacing:-.4px;color:#ECF3EF">Ihr Termin ist bestätigt</h1>
    </td></tr>
    <tr><td align="center" style="padding:10px 30px 0">
      <p style="margin:0;font-size:14.5px;line-height:1.55;color:#8A9892">Guten Tag {name}, danke für Ihre Buchung. Wir freuen uns auf das Gespräch.</p>
    </td></tr>
    <tr><td style="padding:22px 30px 0">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="#18211D" style="background:#18211D;border:1px solid rgba(255,255,255,.08);border-radius:12px">
        <tr><td style="padding:16px 18px">
          <div style="font-family:{_mono};font-size:15px;font-weight:700;color:#5EE0A6;letter-spacing:.2px">{when_label} Uhr</div>
          <div style="margin-top:10px;font-size:13.5px;line-height:1.7;color:#8A9892">
            <span style="display:inline-block;width:7px;height:7px;border-radius:2px;background:#15C97A;vertical-align:middle;margin-right:10px"></span>Prozessermittlung · {slot_minutes} Minuten · vor Ort bei Ihnen<br>
            <span style="display:inline-block;width:7px;height:7px;border-radius:2px;background:#15C97A;vertical-align:middle;margin-right:10px"></span>{address}
          </div>
        </td></tr>
      </table>
    </td></tr>
    <tr><td align="center" style="padding:22px 30px 0;font-size:14px;line-height:1.55;color:#8A9892">
      {cal_html}
    </td></tr>
    <tr><td align="center" style="padding:18px 30px 0;font-size:12.5px;line-height:1.6;color:#5A655F">
      Müssen Sie den Termin verschieben? Antworten Sie einfach auf diese E-Mail
      (<a href="mailto:{organizer_email}" style="color:#5EE0A6;text-decoration:none">{organizer_email}</a>).
    </td></tr>
    <tr><td align="center" style="padding:24px 30px 26px">
      <div style="border-top:1px solid rgba(255,255,255,.07);padding-top:18px;font-size:11.5px;color:#5A655F;letter-spacing:.2px">Automatisierbar · Prozesse automatisieren, die Ihre Zeit fressen.</div>
    </td></tr>
  </table>

</td></tr></table></body></html>"""


def _confirmation_text(*, name, when_label, address, slot_minutes, organizer_email) -> str:
    return (f"Guten Tag {name}\n\n"
            f"Ihr Termin ist bestätigt:\n"
            f"  {when_label} Uhr\n"
            f"  Prozessermittlung · {slot_minutes} Minuten · vor Ort bei Ihnen\n"
            f"  Adresse: {address}\n\n"
            f"Die Kalendereinladung ist angehängt (termin.ics), einfach öffnen, um den Termin "
            f"in Ihren Kalender zu übernehmen.\n\n"
            f"Müssen Sie verschieben? Antworten Sie auf diese E-Mail ({organizer_email}).\n\n"
            f"Automatisierbar")


def send_confirmation(*, to_email, to_name, when_label, address, slot_minutes,
                      start_dt, end_dt, summary, description) -> bool:
    """Send the branded confirmation + .ics invite. Returns True on success, False if
    SMTP isn't configured or the send fails (caller logs/ignores — booking still ok)."""
    from_email = os.environ.get("COCKPIT_FROM_EMAIL", "info@automatisierbar.ch").strip()
    from_name = os.environ.get("COCKPIT_FROM_NAME", "Automatisierbar")
    subject = f"Bestätigung: Prozessermittlung am {when_label} Uhr"
    add_link = _gcal_add_link(summary, start_dt, end_dt, address, description)
    html = _confirmation_html(name=to_name, when_label=when_label, address=address,
                              slot_minutes=slot_minutes, organizer_email=from_email,
                              add_to_cal=add_link)

    # Preferred: Infomaniak Mail API (token) — sends AS info@.
    token = mail_api_token()
    if token:
        return _send_via_mail_api(token=token, from_email=from_email, from_name=from_name,
                                  to_email=to_email, to_name=to_name, subject=subject, html=html)

    # Fallback: SMTP (+ native .ics attachment). Sends as the authenticated account.
    c = _smtp_cfg()
    if not (c["user"] and c["pw"]):
        return False
    ics = build_ics(
        start_dt=start_dt, end_dt=end_dt, summary=summary, description=description,
        location=address, organizer_email=from_email, organizer_name=from_name,
        attendee_email=to_email, attendee_name=to_name)
    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = f'{from_name} <{from_email}>'
    msg["To"] = f"{to_name} <{to_email}>" if to_name else to_email
    msg["Reply-To"] = from_email
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(_confirmation_text(name=to_name, when_label=when_label, address=address,
               slot_minutes=slot_minutes, organizer_email=from_email), "plain", "utf-8"))
    alt.attach(MIMEText(html, "html", "utf-8"))
    msg.attach(alt)
    ical = MIMEText(ics, "calendar", "utf-8")
    ical.replace_header("Content-Type", 'text/calendar; charset=UTF-8; method=REQUEST')
    msg.attach(ical)
    att = MIMEBase("application", "ics")
    att.set_payload(ics.encode("utf-8"))
    encoders.encode_base64(att)
    att.add_header("Content-Disposition", 'attachment; filename="termin.ics"')
    msg.attach(att)
    try:
        with smtplib.SMTP_SSL(c["host"], c["port"], timeout=20) as s:
            s.login(c["user"], c["pw"])
            s.sendmail(c["user"], [to_email], msg.as_string())
        return True
    except Exception as e:
        print(f"[cockpit_email] smtp send failed: {e}")
        return False


if __name__ == "__main__":
    # Offline smoke: build an ICS + render the email, never sends.
    from datetime import timedelta
    from zoneinfo import ZoneInfo
    tz = ZoneInfo("Europe/Zurich")
    s = datetime(2026, 7, 1, 15, 0, tzinfo=tz)
    ics = build_ics(start_dt=s, end_dt=s + timedelta(minutes=60),
                    summary="Prozessermittlung — Muster AG",
                    description="Vor Ort, 60 Min.", location="Bahnhofstrasse 24, 5400 Baden",
                    organizer_email="info@automatisierbar.ch", organizer_name="Automatisierbar",
                    attendee_email="anna@musterag.ch", attendee_name="Anna Berger",
                    now=datetime(2026, 6, 29, 12, 0, tzinfo=timezone.utc))
    assert "BEGIN:VCALENDAR" in ics and "METHOD:REQUEST" in ics and "DTSTART:20260701T130000Z" in ics
    html = _confirmation_html(name="Anna Berger", when_label="01.07.2026 15:00",
                              address="Bahnhofstrasse 24, 5400 Baden", slot_minutes=60,
                              organizer_email="info@automatisierbar.ch")
    assert "Ihr Termin ist bestätigt" in html
    print("OK — ICS + email render; smtp_configured():", smtp_configured())
    print(ics)
