"""Per-mailbox dedup ledger for the mail-sync CRM logger.

One JSON file per mailbox under .tmp/ maps every processed message-id -> ISO timestamp so a
message is classified + pushed at most once (classification-cost dedup). The Hub additionally
enforces a unique externalMessageId, so even a lost ledger can't create duplicate LeadMail rows
(storage dedup) — this file just avoids re-paying for classification each run. Old ids are
pruned past the retention window to keep the file small.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone

RETENTION_DAYS = 45  # comfortably longer than any lookback window


def _base_dir(base_dir: str = None) -> str:
    if base_dir:
        return base_dir
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(repo_root, ".tmp")


def state_path(mailbox: str, base_dir: str = None) -> str:
    return os.path.join(_base_dir(base_dir), f"mail-sync-state.{mailbox or 'default'}.json")


def load_state(mailbox: str, base_dir: str = None) -> dict:
    try:
        with open(state_path(mailbox, base_dir)) as f:
            st = json.load(f)
        st.setdefault("processed", {})
        st.setdefault("last_run", "")
        return st
    except (FileNotFoundError, json.JSONDecodeError):
        return {"processed": {}, "last_run": ""}


def save_state(state: dict, mailbox: str, base_dir: str = None) -> None:
    path = state_path(mailbox, base_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)).isoformat()
    state["processed"] = {k: v for k, v in state.get("processed", {}).items() if (v or "") >= cutoff}
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, path)


def is_seen(state: dict, mid: str) -> bool:
    return bool(mid) and mid in (state or {}).get("processed", {})


def mark_seen(state: dict, mid: str) -> None:
    if mid:
        state.setdefault("processed", {})[mid] = datetime.now(timezone.utc).isoformat(timespec="seconds")
