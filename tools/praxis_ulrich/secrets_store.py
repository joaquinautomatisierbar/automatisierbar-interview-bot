"""secrets_store.py — secrets via Windows Credential Locker (keyring), env fallback.

Medical context: the HIN Mail Token and the LLM API key never live in
config.json or any plaintext file on the practice machine. Storage order:

    get:  env var  >  keyring (service "BefundAutomat")  >  None
    set:  keyring only (the installer/doctor writes them once, interactively)

Env-first on get keeps the dev harness and offline tests trivially injectable
(BEFUND_IMAP_PASSWORD=... python3 ...). keyring is imported lazily so importing
this module works on machines without it (CI, macOS dev without backend).

Known secrets:
    imap_password   — HIN Mail Token (prod) or Infomaniak app password (test)
    llm_api_key     — key for the active LLM provider
"""

from __future__ import annotations

import os

_SERVICE = "BefundAutomat"

# secret name -> env var checked first
_ENV_MAP = {
    "imap_password": "BEFUND_IMAP_PASSWORD",
    "llm_api_key": "BEFUND_LLM_API_KEY",
}
# dev convenience: fall back to the repo-wide key for the anthropic provider
_ENV_FALLBACKS = {
    "llm_api_key": ["ANTHROPIC_API_KEY"],
}


def get_secret(name: str) -> str | None:
    """Return the secret or None. Never raises."""
    env_key = _ENV_MAP.get(name)
    if env_key and os.environ.get(env_key):
        return os.environ[env_key]
    for fb in _ENV_FALLBACKS.get(name, []):
        if os.environ.get(fb):
            return os.environ[fb]
    try:
        import keyring
        val = keyring.get_password(_SERVICE, name)
        return val or None
    except Exception:
        return None


def set_secret(name: str, value: str) -> bool:
    """Store in the OS credential store. Returns False if no backend available."""
    try:
        import keyring
        keyring.set_password(_SERVICE, name, value)
        return True
    except Exception as e:
        print(f"[befund-secrets] keyring nicht verfügbar: {e!r}", flush=True)
        return False


def delete_secret(name: str) -> bool:
    try:
        import keyring
        keyring.delete_password(_SERVICE, name)
        return True
    except Exception:
        return False
