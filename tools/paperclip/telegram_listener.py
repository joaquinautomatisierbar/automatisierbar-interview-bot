#!/usr/bin/env python3
"""
Telegram ↔ paperclip bidirectional bridge.

INBOUND (Telegram → paperclip):
  Polls the Automatisierbar Operations bot for incoming messages, identifies the
  sender by chat_id, posts the message as a comment on that user's recurring
  Team Chat issue, then triggers the CEO agent heartbeat to wake + respond.

OUTBOUND (paperclip → Telegram):
  Background thread polls each Team Chat issue's comments every ~5s. New
  agent-authored comments (filtered to skip the listener's own user-echoes)
  are forwarded to the user's Telegram chat via the Bot API.

Why bidirectional in the listener? Skills inside paperclip's claude_local
adapter don't auto-fire from prose mentions — having the agent bash-call
Telegram is fragile (env-var dependency, error handling per agent). The
listener owns transport in BOTH directions; agents only deal with paperclip
comments.

Run:
  python3 tools/paperclip/telegram_listener.py

Or via launchd (see tools/paperclip/launchd/com.automatisierbar.telegram-listener.plist).
"""
from __future__ import annotations

import json
import logging
import os
import re
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# ────────────────────────────────────────────────────────────────────────────
# Config

BOT_TOKEN = os.environ.get("TEAM_TELEGRAM_BOT_TOKEN", "").strip()
PAPERCLIP_API = os.environ.get("PAPERCLIP_API", "http://localhost:3100")
CEO_AGENT_ID = os.environ.get("CEO_AGENT_ID", "9e3d3cb5-6ff5-45e3-b31a-b794be21edc1")
POLL_INTERVAL_S = float(os.environ.get("POLL_INTERVAL_S", "2"))
LONG_POLL_TIMEOUT_S = int(os.environ.get("LONG_POLL_TIMEOUT_S", "25"))
PROJECT_ROOT = Path(__file__).resolve().parents[2]

STATE_DIR = Path.home() / ".paperclip" / "team-chat"
FILES_DIR = STATE_DIR / "files"
STATE_DIR.mkdir(parents=True, exist_ok=True)
FILES_DIR.mkdir(parents=True, exist_ok=True)
OFFSET_FILE = STATE_DIR / "telegram_offset.txt"
FORWARDED_STATE_FILE = STATE_DIR / "forwarded_state.json"
MAPPING_FILE = Path(__file__).resolve().parent / "team_chat_mapping.json"

OUTBOUND_POLL_INTERVAL_S = float(os.environ.get("OUTBOUND_POLL_INTERVAL_S", "5"))
MAX_TELEGRAM_TEXT_LEN = 3800  # Telegram's hard limit is 4096; leave headroom for our formatting

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [listener] %(message)s",
)
log = logging.getLogger("team-chat-listener")


def load_mapping() -> dict:
    """chat_id (str) → { name, chat_id, issue_id, identifier }"""
    if not MAPPING_FILE.exists():
        log.error("missing mapping file: %s", MAPPING_FILE)
        sys.exit(1)
    return json.loads(MAPPING_FILE.read_text())


def get_offset() -> int:
    try:
        return int(OFFSET_FILE.read_text().strip())
    except (FileNotFoundError, ValueError):
        return 0


def save_offset(offset: int) -> None:
    OFFSET_FILE.write_text(str(offset))


def telegram_get(method: str, **params) -> dict:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=LONG_POLL_TIMEOUT_S + 10) as r:
        return json.loads(r.read().decode("utf-8"))


def telegram_send(chat_id: int | str, text: str) -> dict:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def telegram_download_file(file_id: str, save_as: Path) -> Path:
    """Resolve a Telegram file_id to a public URL via getFile, then download it locally.
    Saves to save_as. Returns the saved path."""
    info = telegram_get("getFile", file_id=file_id)
    if not info.get("ok"):
        raise RuntimeError(f"getFile failed: {info}")
    file_path = info["result"]["file_path"]
    url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    save_as.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=30) as r, open(save_as, "wb") as f:
        f.write(r.read())
    return save_as


def paperclip_post_comment(issue_id: str, body: str) -> dict:
    url = f"{PAPERCLIP_API}/api/issues/{issue_id}/comments"
    data = json.dumps({"body": body}).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def trigger_ceo_heartbeat() -> None:
    """Fire and forget — CEO will wake, read the new comment, respond."""
    try:
        subprocess.Popen(
            [
                "npx",
                "paperclipai",
                "heartbeat",
                "run",
                "--agent-id",
                CEO_AGENT_ID,
                "--source",
                "on_demand",
                "--trigger",
                "callback",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=PROJECT_ROOT,
            start_new_session=True,
        )
    except FileNotFoundError:
        log.warning("npx not on PATH — install Node or add it; can't trigger CEO")


def _extract_attachments(msg: dict, user: dict, update_id: int) -> tuple[list[str], list[str]]:
    """Download any photos/documents/voice/audio from the message into local cache.
    Returns (saved_local_paths, attachment_descriptions_for_comment).
    """
    saved: list[str] = []
    descs: list[str] = []
    user_dir = FILES_DIR / user["chat_id"]
    user_dir.mkdir(parents=True, exist_ok=True)

    # Photos arrive as an array of sizes; pick the largest.
    photos = msg.get("photo") or []
    if photos:
        biggest = max(photos, key=lambda p: p.get("file_size") or 0)
        ext = ".jpg"
        path = user_dir / f"{update_id}_photo{ext}"
        try:
            telegram_download_file(biggest["file_id"], path)
            saved.append(str(path))
            descs.append(f"📷 Photo ({biggest.get('width','?')}x{biggest.get('height','?')}, "
                         f"{biggest.get('file_size','?')} bytes) saved at `{path}`")
        except Exception as e:
            descs.append(f"📷 Photo (download failed: {e})")

    # Documents (PDFs, Excel, etc.)
    doc = msg.get("document")
    if doc:
        fname = doc.get("file_name") or f"doc_{update_id}"
        # Sanitize filename to avoid weird path issues
        safe = "".join(c for c in fname if c.isalnum() or c in "._-")
        if not safe:
            safe = f"doc_{update_id}"
        path = user_dir / f"{update_id}_{safe}"
        try:
            telegram_download_file(doc["file_id"], path)
            saved.append(str(path))
            descs.append(f"📄 Document `{fname}` ({doc.get('mime_type','?')}, "
                         f"{doc.get('file_size','?')} bytes) saved at `{path}`")
        except Exception as e:
            descs.append(f"📄 Document `{fname}` (download failed: {e})")

    # Voice messages (OGG)
    voice = msg.get("voice")
    if voice:
        path = user_dir / f"{update_id}_voice.ogg"
        try:
            telegram_download_file(voice["file_id"], path)
            saved.append(str(path))
            descs.append(f"🎤 Voice message ({voice.get('duration','?')}s, "
                         f"{voice.get('file_size','?')} bytes) saved at `{path}`. "
                         "CEO: transcribe if relevant (use Gemini 2.5 Flash via existing n8n workflow C pattern).")
        except Exception as e:
            descs.append(f"🎤 Voice message (download failed: {e})")

    # Audio files
    audio = msg.get("audio")
    if audio:
        fname = audio.get("file_name") or f"audio_{update_id}"
        safe = "".join(c for c in fname if c.isalnum() or c in "._-")
        path = user_dir / f"{update_id}_{safe}"
        try:
            telegram_download_file(audio["file_id"], path)
            saved.append(str(path))
            descs.append(f"🎵 Audio `{fname}` saved at `{path}`")
        except Exception as e:
            descs.append(f"🎵 Audio (download failed: {e})")

    # Videos
    video = msg.get("video")
    if video:
        path = user_dir / f"{update_id}_video.mp4"
        try:
            telegram_download_file(video["file_id"], path)
            saved.append(str(path))
            descs.append(f"🎬 Video ({video.get('duration','?')}s) saved at `{path}`")
        except Exception as e:
            descs.append(f"🎬 Video (download failed: {e})")

    return saved, descs


def handle_message(msg: dict, mapping: dict) -> None:
    chat = msg.get("chat", {})
    chat_id = str(chat.get("id"))
    update_id_seed = msg.get("message_id") or int(time.time() * 1000)
    text = (msg.get("text") or msg.get("caption") or "").strip()

    user = mapping.get(chat_id)
    if not user:
        log.warning("unknown chat_id %s — sender %s. Sending polite rejection.",
                    chat_id, chat.get("username") or chat.get("first_name") or "?")
        telegram_send(
            chat_id,
            "👋 This bot is for the Automatisierbar core team only. "
            f"Your chat_id is `{chat_id}` — share with Joaquin if you need access.",
        )
        return

    # Download attachments (photos / docs / voice / audio / video) into local cache.
    # CEO will read them via the Read tool / file_extract tooling on demand.
    saved_paths, attachment_descs = _extract_attachments(msg, user, update_id_seed)

    if not text and not saved_paths:
        log.info("empty message in chat %s — ignoring", chat_id)
        return

    log.info("← %s (%s): text=%r attachments=%d",
             user["name"], chat_id, text[:80], len(saved_paths))

    # Slash commands (handled by listener directly, no CEO wake)
    if text.startswith("/") and not saved_paths:
        handle_slash(chat_id, user, text)
        return

    # Build the comment body
    parts: list[str] = []
    parts.append(f"**[{user['name']} via Telegram, chat_id `{chat_id}`]**")
    if text:
        parts.append("")
        parts.append(text)
    if attachment_descs:
        parts.append("")
        parts.append("**Attachments:**")
        for d in attachment_descs:
            parts.append(f"- {d}")
        parts.append("")
        parts.append("*CEO: use the Read tool on local file paths above to inspect images / PDFs / text. "
                     "For Excel/CSV, prefer `tools/file_extract.py:extract_text` from this repo "
                     "(handles pandas head/tail/sample/outliers patterns). For voice/audio, use Gemini "
                     "Flash transcription via n8n Workflow C pattern.*")
    comment_body = "\n".join(parts)

    try:
        paperclip_post_comment(user["issue_id"], comment_body)
        log.info("→ paperclip comment posted on %s", user["identifier"])
    except Exception as e:
        log.exception("failed to post paperclip comment")
        telegram_send(chat_id, "⚠️ Failed to forward your message to paperclip. Joaquin has been pinged.")
        return

    trigger_ceo_heartbeat()
    log.info("→ CEO heartbeat triggered")


def handle_slash(chat_id: str, user: dict, text: str) -> None:
    cmd = text.split(maxsplit=1)
    name = cmd[0].lstrip("/").lower()
    arg = cmd[1] if len(cmd) > 1 else ""

    if name in ("help", "start"):
        reply = (
            f"👋 Hi {user['name']}, you're talking to *Automatisierbar Operations*.\n\n"
            "Just write me what you need — I'll route it to the right person on the team.\n\n"
            "*Slash commands (fast lookups, no AI):*\n"
            "/status — what builds are active right now\n"
            "/builds — all build-pipeline issues\n"
            "/myissues — issues assigned to you\n"
            "/help — this message\n\n"
            "Anything else: just type a question or instruction. The CEO will answer."
        )
        telegram_send(chat_id, reply)
        return

    if name == "status":
        reply = fetch_status_summary()
        telegram_send(chat_id, reply)
        return

    if name == "builds":
        reply = fetch_builds_summary()
        telegram_send(chat_id, reply)
        return

    if name == "myissues":
        reply = fetch_my_issues(user["name"])
        telegram_send(chat_id, reply)
        return

    telegram_send(chat_id, f"Unknown command `{cmd[0]}`. Try /help.")


def fetch_status_summary() -> str:
    try:
        with urllib.request.urlopen(
            f"{PAPERCLIP_API}/api/companies/e43fbb5f-4239-48f6-b0ed-627e2c77f742/issues",
            timeout=10,
        ) as r:
            issues = json.load(r)
        active = [i for i in issues if i["status"] in ("in_progress", "in_review")]
        if not active:
            return "🟢 No active issues — system is idle."
        lines = ["*Active issues:*"]
        for i in active[:10]:
            lines.append(f"• `{i['identifier']}` ({i['status']}) — {i['title'][:60]}")
        if len(active) > 10:
            lines.append(f"_… and {len(active) - 10} more_")
        return "\n".join(lines)
    except Exception as e:
        return f"⚠️ Status fetch failed: {e}"


def fetch_builds_summary() -> str:
    try:
        with urllib.request.urlopen(
            f"{PAPERCLIP_API}/api/companies/e43fbb5f-4239-48f6-b0ed-627e2c77f742/issues",
            timeout=10,
        ) as r:
            issues = json.load(r)
        builds = [
            i
            for i in issues
            if "[smoke]" in (i.get("title") or "").lower()
            or (i.get("title") or "").startswith("Build:")
            or (i.get("description") or "").startswith("# Build-Brief")
        ]
        if not builds:
            return "📭 No build-pipeline issues yet."
        lines = ["*Build pipeline issues (latest 10):*"]
        for i in sorted(builds, key=lambda x: x["createdAt"], reverse=True)[:10]:
            lines.append(f"• `{i['identifier']}` ({i['status']}) — {i['title'][:60]}")
        return "\n".join(lines)
    except Exception as e:
        return f"⚠️ Builds fetch failed: {e}"


def fetch_my_issues(user_name: str) -> str:
    # Currently, paperclip Issues are agent-assigned not user-assigned.
    # So "my issues" maps to the Team Chat issue + any issue where the user is
    # mentioned in description/comments. For now, just return their Team Chat issue.
    mapping = load_mapping()
    me = next((u for u in mapping.values() if u["name"] == user_name), None)
    if not me:
        return "⚠️ Couldn't find you in the team-chat mapping."
    return (
        f"Your Team Chat surface: `{me['identifier']}`.\n\n"
        "All your messages here are stored in that paperclip issue's comments. "
        "I'll add per-user issue assignment when real-human assignment lands."
    )


# ────────────────────────────────────────────────────────────────────────────
# Outbound bridge — polls paperclip Team-Chat issue comments + forwards new
# agent (CEO) comments to the corresponding Telegram chat. Runs as a background
# thread alongside the inbound long-poll loop.
# ────────────────────────────────────────────────────────────────────────────


def load_forwarded_state() -> dict:
    try:
        return json.loads(FORWARDED_STATE_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_forwarded_state(state: dict) -> None:
    tmp = FORWARDED_STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True))
    tmp.replace(FORWARDED_STATE_FILE)


def paperclip_get_comments(issue_id: str) -> list:
    url = f"{PAPERCLIP_API}/api/issues/{issue_id}/comments"
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def _is_listener_user_echo(body: str) -> bool:
    """Filter out the listener's own posts (user-message comments).
    Those start with `**[<name> via Telegram` per build_comment_body()."""
    stripped = (body or "").lstrip()
    return stripped.startswith("**[") and "via Telegram" in stripped[:200]


def _clean_for_telegram(body: str) -> str:
    """Strip paperclip-internal markup that doesn't render well in Telegram,
    enforce length cap. Keep Markdown formatting intact (Telegram supports it)."""
    text = (body or "").strip()
    # Drop trailing internal references like "Reassigning to [Agent](/AUT/agents/x)"
    # (CEO Team Chat shouldn't produce these, but defensive)
    text = re.sub(r"\n+Reassigning to \[[^\]]+\]\([^)]+\)\.?\s*$", "", text)
    # Truncate if absurdly long — agent should self-limit but defensive
    if len(text) > MAX_TELEGRAM_TEXT_LEN:
        text = text[: MAX_TELEGRAM_TEXT_LEN - 60] + "\n\n_…(gekürzt — voller Text in paperclip)_"
    return text


def outbound_tick(mapping: dict, state: dict) -> None:
    """One sweep through the 4 Team-Chat issues. For each, find agent-authored
    comments newer than what we've last forwarded, and send them to Telegram."""
    state_changed = False
    for chat_id, user in mapping.items():
        issue_id = user["issue_id"]
        last_forwarded_at = (state.get(chat_id) or {}).get("last_forwarded_at") or ""
        try:
            comments = paperclip_get_comments(issue_id)
        except Exception as e:
            log.warning("outbound: failed to fetch comments on %s: %s", user["identifier"], e)
            continue
        # Sort ascending by createdAt so we forward in chronological order
        comments_sorted = sorted(comments, key=lambda c: c.get("createdAt") or "")
        for c in comments_sorted:
            created_at = c.get("createdAt") or ""
            if created_at <= last_forwarded_at:
                continue
            author_type = c.get("authorType")
            if author_type != "agent":
                continue  # only forward agent-authored comments
            body = c.get("body") or ""
            if _is_listener_user_echo(body):
                continue  # skip the listener's own posts (user messages)
            if not body.strip():
                continue
            cleaned = _clean_for_telegram(body)
            try:
                telegram_send(chat_id, cleaned)
                log.info(
                    "outbound → %s (%s): forwarded comment %s (%d chars)",
                    user["name"], chat_id, (c.get("id") or "?")[:8], len(cleaned),
                )
            except urllib.error.HTTPError as e:
                err_body = ""
                try: err_body = e.read().decode("utf-8")[:200]
                except: pass
                log.warning("outbound: Telegram send failed for %s (HTTP %s): %s",
                            user["name"], e.code, err_body)
                # On 4xx, advance the cursor anyway to avoid retry-spam.
                # On 5xx, leave cursor so next tick retries.
                if e.code < 500:
                    pass  # advance below
                else:
                    continue
            except Exception as e:
                log.warning("outbound: Telegram send failed for %s: %s", user["name"], e)
                continue
            # Advance the cursor
            state[chat_id] = {"last_forwarded_at": created_at, "last_comment_id": c.get("id")}
            state_changed = True
    if state_changed:
        save_forwarded_state(state)


def outbound_loop(mapping: dict) -> None:
    """Background thread entry point. Initializes state to NOW (so we don't
    re-forward historical comments on first startup), then polls every N seconds."""
    state = load_forwarded_state()
    # On first ever run, seed state to current time so we don't flood Telegram with
    # all historical CEO comments. After that, persisted state survives restarts.
    if not state:
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%S.999Z", time.gmtime())
        for chat_id in mapping:
            state[chat_id] = {"last_forwarded_at": now_iso, "last_comment_id": None}
        save_forwarded_state(state)
        log.info("outbound: seeded forwarded_state.json with current time for %d users", len(mapping))
    while _running:
        try:
            outbound_tick(mapping, state)
        except Exception:
            log.exception("outbound_tick failed (will retry)")
        time.sleep(OUTBOUND_POLL_INTERVAL_S)


_running = True


def _on_signal(signum, frame):
    global _running
    log.info("signal %s received, exiting", signum)
    _running = False


def main() -> int:
    if not BOT_TOKEN:
        log.error("TEAM_TELEGRAM_BOT_TOKEN not set in environment")
        return 1
    mapping = load_mapping()
    log.info("started — listening for %d known chat_ids (inbound + outbound bridge)", len(mapping))
    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)

    # Start outbound bridge thread (paperclip → Telegram)
    outbound_thread = threading.Thread(
        target=outbound_loop, args=(mapping,), name="outbound-bridge", daemon=True
    )
    outbound_thread.start()
    log.info("outbound bridge thread started (poll interval %.1fs)", OUTBOUND_POLL_INTERVAL_S)

    offset = get_offset()
    while _running:
        try:
            resp = telegram_get(
                "getUpdates",
                offset=offset,
                timeout=LONG_POLL_TIMEOUT_S,
                allowed_updates=json.dumps(["message"]),
            )
            if not resp.get("ok"):
                log.warning("telegram getUpdates not OK: %s", resp)
                time.sleep(5)
                continue
            updates = resp.get("result") or []
            for u in updates:
                offset = max(offset, u["update_id"] + 1)
                msg = u.get("message")
                if msg:
                    try:
                        handle_message(msg, mapping)
                    except Exception:
                        log.exception("handle_message failed")
            save_offset(offset)
        except urllib.error.URLError as e:
            log.warning("network error: %s — backing off", e)
            time.sleep(10)
        except Exception:
            log.exception("main loop error — backing off")
            time.sleep(5)
        else:
            if not updates:
                time.sleep(POLL_INTERVAL_S)
    log.info("listener exited cleanly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
