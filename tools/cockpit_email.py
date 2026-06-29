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


def _confirmation_html(*, name, when_label, address, slot_minutes, organizer_email) -> str:
    """Clean, email-client-safe (light, inline-styled) confirmation."""
    return f"""\
<!DOCTYPE html><html><body style="margin:0;padding:0;background:#f4f6f5;font-family:Arial,Helvetica,sans-serif;color:#16201c">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f5;padding:24px 0">
<tr><td align="center">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:520px;background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid #e6eae8">
  <tr><td style="background:#0A0F0D;padding:22px 26px">
    <span style="display:inline-block;width:26px;height:26px;background:#15C97A;border-radius:7px;vertical-align:middle"></span>
    <span style="color:#ECF3EF;font-size:17px;font-weight:bold;vertical-align:middle;margin-left:10px">Automatisierbar</span>
  </td></tr>
  <tr><td style="padding:28px 26px 8px">
    <h1 style="margin:0 0 6px;font-size:21px;color:#0A8F54">Ihr Termin ist bestätigt</h1>
    <p style="margin:0;font-size:15px;color:#46524c">Guten Tag {name}, danke für Ihre Buchung. Wir freuen uns auf das Gespräch.</p>
  </td></tr>
  <tr><td style="padding:18px 26px 4px">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f8f6;border:1px solid #e6eae8;border-radius:10px">
      <tr><td style="padding:14px 16px;font-size:14px;color:#46524c">
        <strong style="color:#16201c">📅 {when_label} Uhr</strong><br>
        <span style="color:#6b7872">Prozessermittlung · {slot_minutes} Minuten · vor Ort bei Ihnen</span><br>
        <span style="color:#6b7872">📍 {address}</span>
      </td></tr>
    </table>
  </td></tr>
  <tr><td style="padding:16px 26px 6px;font-size:14px;color:#46524c">
    Die <strong>Kalendereinladung</strong> ist dieser E-Mail angehängt, einfach öffnen, um den Termin
    in Ihren Kalender zu übernehmen. Wir kommen zum vereinbarten Zeitpunkt zu Ihnen.
  </td></tr>
  <tr><td style="padding:8px 26px 28px;font-size:13px;color:#8a948f">
    Müssen Sie den Termin verschieben? Antworten Sie einfach auf diese E-Mail
    ({organizer_email}).
  </td></tr>
  <tr><td style="background:#0A0F0D;padding:14px 26px;font-size:12px;color:#5A655F">
    Automatisierbar · Prozesse automatisieren, die Ihre Zeit fressen.
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
    c = _smtp_cfg()
    if not (c["user"] and c["pw"]):
        return False
    organizer_email = c["from_email"]      # visible/reply address (info@…)
    ics = build_ics(
        start_dt=start_dt, end_dt=end_dt, summary=summary, description=description,
        location=address, organizer_email=organizer_email, organizer_name=c["from_name"],
        attendee_email=to_email, attendee_name=to_name)

    msg = MIMEMultipart("mixed")
    msg["Subject"] = f"Bestätigung: Prozessermittlung am {when_label} Uhr"
    msg["From"] = f'{c["from_name"]} <{organizer_email}>'
    msg["To"] = f"{to_name} <{to_email}>" if to_name else to_email
    msg["Reply-To"] = organizer_email

    alt = MIMEMultipart("alternative")
    kw = dict(name=to_name, when_label=when_label, address=address,
              slot_minutes=slot_minutes, organizer_email=organizer_email)
    alt.attach(MIMEText(_confirmation_text(**kw), "plain", "utf-8"))
    alt.attach(MIMEText(_confirmation_html(**kw), "html", "utf-8"))
    msg.attach(alt)

    # Inline calendar part — drives the "add to calendar" widget in Gmail/Apple Mail.
    ical = MIMEText(ics, "calendar", "utf-8")
    ical.replace_header("Content-Type", 'text/calendar; charset=UTF-8; method=REQUEST')
    msg.attach(ical)

    # Also a downloadable .ics attachment as a fallback.
    att = MIMEBase("application", "ics")
    att.set_payload(ics.encode("utf-8"))
    encoders.encode_base64(att)
    att.add_header("Content-Disposition", 'attachment; filename="termin.ics"')
    msg.attach(att)

    try:
        with smtplib.SMTP_SSL(c["host"], c["port"], timeout=20) as s:
            s.login(c["user"], c["pw"])
            # Envelope sender = authenticated account (deliverability); the visible
            # From/Reply-To header is the public info@ address.
            s.sendmail(c["user"], [to_email], msg.as_string())
        return True
    except Exception as e:
        print(f"[cockpit_email] send failed: {e}")
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
