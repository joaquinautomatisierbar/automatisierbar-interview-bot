"""mail_sync/vendor_noise.py — drop vendor/support/transactional mail before it costs a Claude call.

Mirror of the Hub's `apps/api/src/services/leadmail/vendor-noise.ts`. The HUB is authoritative (it
filters at ingest, so every mailbox is covered even if this worker is stale); this copy exists purely
so we don't pay to classify mail the Hub is going to discard anyway.

Same narrow rule as the Hub: fire only when the counterparty's DOMAIN is denylisted AND the local-part
is transactional. A support-ish local-part alone is NOT enough — plenty of real Swiss SMEs write from
`info@`, and losing a lead's mail is far worse than one wasted classification.

Extend without editing code via LEADMAIL_VENDOR_DOMAINS (comma/whitespace separated); the value is
MERGED with the baseline, never replaces it.
"""
from __future__ import annotations

import os

# Keep in step with DEFAULT_VENDOR_DOMAINS in the Hub's vendor-noise.ts.
DEFAULT_VENDOR_DOMAINS = (
    # AI / dev platforms
    "anthropic.com", "openai.com", "github.com", "gitlab.com", "vercel.com",
    "render.com", "netlify.com", "cloudflare.com", "atlassian.com", "sentry.io",
    # hosting / infra / domains
    "hostinger.com", "infomaniak.com", "infomaniak.ch", "hetzner.com",
    "digitalocean.com", "namecheap.com", "godaddy.com",
    # SaaS we use
    "notion.so", "stripe.com", "slack.com", "zoom.us", "canva.com", "figma.com",
    "brevo.com", "sendinblue.com", "vapi.ai", "n8n.io",
    # big-platform account/billing noise
    "google.com", "googlemail.com", "accounts.google.com", "microsoft.com",
    "microsoftonline.com", "apple.com", "linkedin.com", "meta.com",
    "facebookmail.com", "x.com", "twitter.com", "paypal.com", "amazon.com",
    "amazonaws.com",
)

TRANSACTIONAL_LOCAL_PARTS = frozenset({
    "support", "help", "helpdesk", "billing", "invoice", "invoices", "receipts",
    "accounts", "accounting", "noreply", "no-reply", "no_reply", "donotreply",
    "do-not-reply", "notifications", "notification", "notify", "alerts", "alert",
    "news", "newsletter", "updates", "security", "team", "hello", "mail", "mailer",
    "service", "services", "info", "admin", "system",
})

_NOREPLY_PREFIXES = ("no-reply", "noreply", "donotreply", "do-not-reply",
                     "mailer-daemon", "bounce")


def parse_vendor_domains(raw: str | None):
    """Comma/whitespace separated env value -> lowercased, de-@'d, deduped list."""
    out, seen = [], set()
    for part in (raw or "").replace(",", " ").split():
        d = part.strip().lower().lstrip("@")
        if d and d not in seen:
            seen.add(d)
            out.append(d)
    return out


def vendor_domains(env=None):
    """The effective denylist: baseline MERGED with LEADMAIL_VENDOR_DOMAINS."""
    env = env if env is not None else os.environ
    extra = parse_vendor_domains(env.get("LEADMAIL_VENDOR_DOMAINS"))
    return list(DEFAULT_VENDOR_DOMAINS) + [d for d in extra if d not in DEFAULT_VENDOR_DOMAINS]


def _domain_matches(domain: str, denylist) -> bool:
    return any(domain == d or domain.endswith("." + d) for d in denylist)


def is_vendor_noise(email: str | None, denylist=None) -> bool:
    """True for vendor/support/billing mail. `email` is the COUNTERPARTY address."""
    denylist = denylist if denylist is not None else DEFAULT_VENDOR_DOMAINS
    addr = (email or "").strip().lower()
    local, _, domain = addr.partition("@")
    if not local or not domain:
        return False
    if not _domain_matches(domain, denylist):
        return False
    local = local.split("+")[0]          # strip plus-addressing
    if local in TRANSACTIONAL_LOCAL_PARTS:
        return True
    return local.startswith(_NOREPLY_PREFIXES)


def counterparty_of(p: dict, direction: str) -> str:
    """The external party's address for a parsed message: sender in, recipient out."""
    return (p.get("from_email") if direction == "incoming" else p.get("to_email")) or ""
