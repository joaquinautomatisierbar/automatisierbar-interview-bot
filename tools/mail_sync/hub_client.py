"""POST a LeadMail to the Automatisierbar Hub REST surface (/api/v1/leadmails).

Auth is the X-API-Key header (a Hub API key with the leadmail:write scope). The transport is
injectable for testing; the default uses requests. Retries on transport errors, 5xx, and 429
with exponential backoff; a 2xx returns ok, a 4xx (other than 429) is terminal (no retry storm
on a bad payload / bad key). The Hub dedups on externalMessageId, so a retried POST is safe.
"""
from __future__ import annotations

import time


class Result:
    def __init__(self, ok, status=None, body=None, error=None):
        self.ok = ok
        self.status = status
        self.body = body
        self.error = error

    def __repr__(self):
        return f"Result(ok={self.ok}, status={self.status}, error={self.error!r})"


def _requests_transport(url, headers, body):
    import requests  # lazy — keeps the module importable offline
    r = requests.post(url, headers=headers, json=body, timeout=20)
    try:
        parsed = r.json()
    except Exception:
        parsed = {"raw": (r.text or "")[:500]}
    return type("Resp", (), {"status": r.status_code, "body": parsed})()


def post_leadmail(payload, *, base_url, api_key, transport=None, max_attempts=3,
                  sleep=time.sleep, backoff=1.5) -> Result:
    transport = transport or _requests_transport
    url = base_url.rstrip("/") + "/api/v1/leadmails"
    headers = {"X-API-Key": api_key or "", "Content-Type": "application/json"}
    last_err = None
    for attempt in range(1, max_attempts + 1):
        try:
            resp = transport(url, headers, payload)
            status = getattr(resp, "status", None)
            rbody = getattr(resp, "body", None)
            if status is not None and 200 <= status < 300:
                return Result(ok=True, status=status, body=rbody)
            # 4xx (except 429) is terminal — retrying won't help.
            if status is not None and status < 500 and status != 429:
                return Result(ok=False, status=status, body=rbody, error=f"http {status}")
            last_err = f"http {status}"
        except Exception as e:  # noqa: BLE001
            last_err = str(e)
        if attempt < max_attempts:
            sleep(backoff ** attempt)
    return Result(ok=False, error=last_err)
