#!/usr/bin/env python3
"""team_mailboxes.py — single source of truth mapping an Automatisierbar team member to
their Infomaniak mailbox (address, per-mailbox credential env names, signature mailbox).

Used by the walk-in draft worker (draft AS the entering person, in their box, with their
signature) and by the multi-mailbox inbox-reply-drafter. Keeps per-mailbox routing in ONE
place instead of scattering {prefix}_imap_* lookups across infomaniak_draft.py /
infomaniak_signature.py / inbox_reply_drafter.py.

Design notes:
  - Env var names are DISTINCT per mailbox on purpose. infomaniak_draft.env() /
    infomaniak_signature.env() read a literal .env file BEFORE os.environ, so a shared key
    cannot be safely overridden at runtime — each mailbox gets its own {PREFIX}_IMAP_USER /
    {PREFIX}_IMAP_PASSWORD, which also sidesteps that quirk entirely.
  - Joaquin + info fall back to the legacy INFOMANIAK_IMAP_* pair (joaquin locally, info@ on
    the VPS) so everything that already works keeps working with zero new creds.
  - Display name ("Nico") != mailbox localpart ("nicolas") — deliberate, do not "normalize".
"""
import os

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# repo-root .env (tools/ is one level under the repo root)
_ENV_PATH = os.path.abspath(os.path.join(_SCRIPT_DIR, os.pardir, ".env"))

DOMAIN = "automatisierbar.ch"

# person display name -> mailbox identity. `prefix` is the primary env namespace;
# `fallback_prefix` (optional) is tried second so joaquin/info reuse the legacy creds.
ROSTER = {
    "Joaquin": {"email": "joaquin@automatisierbar.ch", "prefix": "JOAQUIN",
                "mailbox_name": "joaquin", "fallback_prefix": "INFOMANIAK"},
    "Tej":     {"email": "tej@automatisierbar.ch",     "prefix": "TEJ",
                "mailbox_name": "tej"},
    "Nico":    {"email": "nicolas@automatisierbar.ch", "prefix": "NICO",
                "mailbox_name": "nicolas"},
    "Patrik":  {"email": "patrik@automatisierbar.ch",  "prefix": "PATRIK",
                "mailbox_name": "patrik"},
    "info":    {"email": "info@automatisierbar.ch",    "prefix": "INFO",
                "mailbox_name": "info", "fallback_prefix": "INFOMANIAK"},
}

# resolve by display name, localpart, or the email localpart (all lowercased)
_ALIASES = {}
for _name, _p in ROSTER.items():
    _ALIASES[_name.lower()] = _name
    _ALIASES[_p["mailbox_name"].lower()] = _name
    _ALIASES[_p["email"].split("@")[0].lower()] = _name


def env(key, default=None):
    """Read the repo-root .env (literal, first match) then os.environ — same precedence as
    the walk-in tools, so local .env and VPS-exported env both work."""
    try:
        with open(_ENV_PATH) as fh:
            for ln in fh:
                s = ln.strip()
                if s.startswith(key + "="):
                    return s.split("=", 1)[1].strip()
    except FileNotFoundError:
        pass
    return os.environ.get(key, default)


def resolve(person):
    """person: a display name ('Nico'), localpart ('nicolas'), email localpart, or 'info'.
    Returns the roster profile dict (with 'person' = the canonical display name).
    Raises KeyError for an unknown person."""
    key = _ALIASES.get((person or "").strip().lower())
    if not key:
        raise KeyError(f"unknown mailbox: {person!r}")
    return dict(ROSTER[key], person=key)


def address(person):
    return resolve(person)["email"]


def _cred_prefixes(profile):
    prefixes = [profile["prefix"]]
    if profile.get("fallback_prefix"):
        prefixes.append(profile["fallback_prefix"])
    return prefixes


def imap_user(person):
    """The IMAP login user for this mailbox: {PREFIX}_IMAP_USER if set, else the address."""
    p = resolve(person)
    for pre in _cred_prefixes(p):
        v = env(f"{pre}_IMAP_USER")
        if v:
            return v
    return p["email"]


def imap_password_env(person):
    """The env var NAME holding this mailbox's IMAP app-password (first prefix that's set,
    else the primary). Passed to infomaniak_draft via --password-env so the tool reads the
    right secret without a shared-key runtime override."""
    p = resolve(person)
    for pre in _cred_prefixes(p):
        name = f"{pre}_IMAP_PASSWORD"
        if env(name):
            return name
    return f"{p['prefix']}_IMAP_PASSWORD"


def imap_user_env(person):
    """The env var NAME holding this mailbox's IMAP user (first prefix that's set, else primary)."""
    p = resolve(person)
    for pre in _cred_prefixes(p):
        name = f"{pre}_IMAP_USER"
        if env(name):
            return name
    return f"{p['prefix']}_IMAP_USER"


def imap_password(person):
    return env(imap_password_env(person))


def has_creds(person):
    """True when this mailbox has a usable IMAP app-password configured."""
    try:
        return bool(imap_password(person))
    except KeyError:
        return False


def mail_token_env(person):
    """Prefer a per-mailbox {PREFIX}_MAIL_TOKEN, else the hosting-scoped INFOMANIAK_MAIL_TOKEN.
    Lets one hosting token cover every signature while allowing per-mailbox tokens if scope
    turns out to be narrower."""
    p = resolve(person)
    name = f"{p['prefix']}_MAIL_TOKEN"
    return name if env(name) else "INFOMANIAK_MAIL_TOKEN"


def draft_cfg(person, base_cfg):
    """A copy of base_cfg (from infomaniak_draft.load_config()) rebound to `person`:
    from / sender / mailbox_name / mail_token_env swapped so the draft is authored AS them
    with THEIR signature. Cc is intentionally left to the caller (chosen per entry)."""
    p = resolve(person)
    cfg = dict(base_cfg or {})
    cfg["from"] = p["email"]
    cfg["sender"] = p["person"]
    cfg["mailbox_name"] = p["mailbox_name"]
    cfg["mail_token_env"] = mail_token_env(person)
    return cfg


def all_mailboxes():
    """Canonical roster display names, in a stable order."""
    return list(ROSTER.keys())


if __name__ == "__main__":
    import sys
    who = sys.argv[1] if len(sys.argv) > 1 else None
    if who:
        p = resolve(who)
        print(f"{p['person']:8} -> {p['email']:32} "
              f"imap_user_env={imap_user_env(who):22} "
              f"pw_env={imap_password_env(who):22} "
              f"mailbox={p['mailbox_name']:9} creds={'yes' if has_creds(who) else 'NO'}")
    else:
        for name in all_mailboxes():
            has = "yes" if has_creds(name) else "NO"
            print(f"{name:8} {address(name):32} creds={has}")
