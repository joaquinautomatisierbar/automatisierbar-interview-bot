#!/usr/bin/env python3
"""infomaniak_signature.py — fetch the operator's real Infomaniak mail signature.

The walk-in draft tool embeds this so IMAP-appended drafts carry the operator's standard
signature (Infomaniak only auto-inserts the webmail signature on a fresh compose, never on
an IMAP-appended draft — so we have to put it in ourselves).

Source of truth: the Infomaniak mail-hosting API
    GET https://api.infomaniak.com/1/mail_hostings/{hosting_id}/mailboxes/{name}/signatures
authenticated with the same INFOMANIAK_MAIL_TOKEN bearer cockpit_email.py uses.

get_signature(cfg) is graceful by design:
  1. try the live API (always current — if the operator edits their webmail signature,
     drafts follow on the next run) and refresh the committed cache on success,
  2. on any failure (no token / no network / API error) fall back to the committed cache
     files signature.html + signature.txt next to this script,
  3. if both fail, return None and the caller builds a plain-text-only draft (no hard fail).

CLI:
  --show      print the resolved signature (live if possible, else cache) + its source
  --refresh   force a live fetch and rewrite the cache files
"""
import os
import re
import sys
import json
import html as _html

import requests

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_ENV_CANDIDATES = [os.path.join(_SCRIPT_DIR, ".env"),
                   os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), ".env")]
ENV_PATH = next((p for p in _ENV_CANDIDATES if os.path.exists(p)), _ENV_CANDIDATES[0])
CFG_PATH = os.path.join(_SCRIPT_DIR, "walkin_config.json")
CACHE_HTML = os.path.join(_SCRIPT_DIR, "signature.html")
CACHE_TEXT = os.path.join(_SCRIPT_DIR, "signature.txt")

API_BASE = "https://api.infomaniak.com"


def env(k, d=None):
    try:
        for ln in open(ENV_PATH):
            if ln.strip().startswith(k + "="):
                return ln.strip().split("=", 1)[1].strip()
    except FileNotFoundError:
        pass
    return os.environ.get(k, d)


def load_config():
    cfg = {"mail_hosting_id": None, "mailbox_name": None}
    try:
        with open(CFG_PATH) as f:
            cfg.update(json.load(f))
    except FileNotFoundError:
        pass
    return cfg


def html_to_text(html):
    """Flatten the signature HTML to plain text: <br>/</div>/</p> -> newline, strip tags,
    unescape entities (incl. &#43;->+ and &#64;->@), drop blank lines."""
    t = re.sub(r"(?i)<br\s*/?>", "\n", html)
    t = re.sub(r"(?i)</(div|p)>", "\n", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = _html.unescape(t)
    lines = [ln.strip() for ln in t.splitlines()]
    return "\n".join(ln for ln in lines if ln)


def _tls_verify():
    # Real environments verify normally; an explicit opt-out exists only for a sandbox
    # that intercepts TLS (self-signed cert in the chain). Defaults to secure.
    return env("INFOMANIAK_TLS_INSECURE", "0") not in ("1", "true", "yes")


def fetch_default_signature(token, hosting_id, mailbox_name, timeout=20):
    """Fetch the is_default signature for a mailbox. Returns {html, text, name} or raises."""
    if not token or not hosting_id or not mailbox_name:
        raise ValueError("token / hosting_id / mailbox_name required")
    url = f"{API_BASE}/1/mail_hostings/{hosting_id}/mailboxes/{mailbox_name}/signatures"
    r = requests.get(url, headers={"Authorization": f"Bearer {token}",
                                   "Accept": "application/json"},
                     timeout=timeout, verify=_tls_verify())
    r.raise_for_status()
    data = r.json().get("data", {})
    sigs = data.get("signatures", []) if isinstance(data, dict) else (data or [])
    if not sigs:
        raise LookupError(f"no signatures for {mailbox_name}")
    chosen = next((s for s in sigs if s.get("is_default")), sigs[0])
    html = (chosen.get("content") or "").strip()
    return {"html": html, "text": html_to_text(html), "name": chosen.get("name") or ""}


def _write_cache(sig):
    try:
        with open(CACHE_HTML, "w") as f:
            f.write(sig["html"])
        with open(CACHE_TEXT, "w") as f:
            f.write(sig["text"].rstrip("\n") + "\n")
    except OSError:
        pass


def _read_cache():
    try:
        with open(CACHE_HTML) as f:
            html = f.read().strip()
        with open(CACHE_TEXT) as f:
            text = f.read().strip()
        if html or text:
            return {"html": html, "text": text or html_to_text(html), "name": "cache"}
    except FileNotFoundError:
        pass
    return None


def get_signature(cfg=None, *, refresh=True):
    """Resolve the signature dict {html, text, name, source}. Never raises.
    Live API first (refresh cache on success), else committed cache, else None."""
    cfg = cfg or load_config()
    token = env("INFOMANIAK_MAIL_TOKEN")
    if refresh and token:
        try:
            sig = fetch_default_signature(token, cfg.get("mail_hosting_id"),
                                          cfg.get("mailbox_name"))
            _write_cache(sig)
            sig["source"] = "api"
            return sig
        except Exception as e:
            print(f"[signature] live fetch failed ({e}); using cache", file=sys.stderr)
    cached = _read_cache()
    if cached:
        cached["source"] = "cache"
        return cached
    return None


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Inspect / refresh the Infomaniak signature.")
    ap.add_argument("--show", action="store_true", help="Print the resolved signature + source")
    ap.add_argument("--refresh", action="store_true", help="Force live fetch + rewrite cache")
    args = ap.parse_args()
    cfg = load_config()

    if args.refresh:
        token = env("INFOMANIAK_MAIL_TOKEN")
        sig = fetch_default_signature(token, cfg.get("mail_hosting_id"), cfg.get("mailbox_name"))
        _write_cache(sig)
        print(f"[refresh] cached signature '{sig['name']}' "
              f"({len(sig['html'])} chars html) -> {CACHE_HTML}")
        print("---- text ----")
        print(sig["text"])
        return 0

    # default + --show
    sig = get_signature(cfg)
    if not sig:
        print("[show] no signature available (no token, no cache)")
        return 1
    print(f"[show] source={sig['source']} name={sig.get('name')!r} "
          f"html={len(sig['html'])} chars")
    print("---- text ----")
    print(sig["text"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
