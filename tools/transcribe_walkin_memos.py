#!/usr/bin/env python3
"""transcribe_walkin_memos.py — daily Walk-in voice-memo transcription (Gemini).

Mirrors the Cold-Call audio→transcript pipeline (workflows/audio_to_transcript.md):
gemini-2.5-flash, inline base64 audio, x-goog-api-key. Runs once a day from a VPS
cron, transcribes up to WALKIN_TRANSCRIBE_MAX_PER_DAY pending memos (Gemini free
tier), writes each transcript as a row in the "Walk-in Knowledge Base" Notion DB,
and flips the memo's sidecar to "transcribed" — idempotent: a transcribed memo is
never re-sent.

The sidecar JSON (next to each audio file in WALKIN_MEMO_DIR) is the source of
truth for pending-vs-done; see walkin_capture.py for its schema.

Env:
  GEMINI_API_KEY                 (required — no key ⇒ no-op with a logged warning)
  WALKIN_KB_DB_ID                (required — the Knowledge Base DB; see setup-kb-db)
  WALKIN_MEMO_DIR                (default /srv/cockpit/voice_memos)
  WALKIN_TRANSCRIBE_MAX_PER_DAY  (default 10)
  WALKIN_MAX_AUDIO_MB            (default 20 — Gemini inline limit)
  NOTION_API_KEY                 (to write the KB row)
  OPERATOR_TELEGRAM_BOT_TOKEN / OPERATOR_TELEGRAM_CHAT_ID  (optional daily summary)

Usage:
  python3 tools/transcribe_walkin_memos.py            # cron mode (cap = MAX_PER_DAY)
  python3 tools/transcribe_walkin_memos.py --max 1    # supervised first run
  python3 tools/transcribe_walkin_memos.py --dry-run  # transcribe + print, no writes
"""

import argparse
import base64
import os
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import walkin_capture as wc  # noqa: E402

GEMINI_URL = ("https://generativelanguage.googleapis.com/v1beta/models/"
              "gemini-2.5-flash:generateContent")

TRANSCRIBE_PROMPT = (
    "Dies ist ein Sprachmemo eines Verkäufers von Automatisierbar, aufgenommen "
    "direkt nach einem Walk-in-Besuch bei einem Unternehmen. Transkribiere die "
    "Aufnahme wörtlich auf Hochdeutsch. Wenn Schweizerdeutsch gesprochen wird, ins "
    "Hochdeutsche übertragen, aber Firmennamen und Fachbegriffe exakt lassen. Keine "
    "Zeitstempel, keine Kommentare, keine Zusammenfassung — nur das wörtliche Transkript."
)

KB_MEMBERS = ("Tej", "Joaquin", "Nico", "Patrik")

# Container ext → the audio mime Gemini expects on the inline part.
_EXT_GEMINI_MIME = {
    ".m4a": "audio/mp4", ".mp4": "audio/mp4",
    ".webm": "audio/webm",
    ".ogg": "audio/ogg", ".opus": "audio/ogg",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".aac": "audio/aac",
    ".flac": "audio/flac",
}


def _gemini_mime(audio_filename: str, sidecar_mime: str) -> str:
    _, ext = os.path.splitext(audio_filename)
    return _EXT_GEMINI_MIME.get(ext.lower(), sidecar_mime or "audio/mp4")


def _max_audio_bytes() -> int:
    try:
        mb = int(os.environ.get("WALKIN_MAX_AUDIO_MB", "20"))
    except (TypeError, ValueError):
        mb = 20
    return mb * 1024 * 1024


def transcribe_audio(content: bytes, mime: str, api_key: str) -> str:
    """Call Gemini once (with one retry on 429/5xx). Returns the transcript text.
    Raises RuntimeError on a non-retryable error or an empty/blocked response."""
    body = {
        "contents": [{"parts": [
            {"text": TRANSCRIBE_PROMPT},
            {"inline_data": {"mime_type": mime,
                             "data": base64.b64encode(content).decode("ascii")}},
        ]}],
        # Disable 2.5 "thinking" — transcription needs none, and thinking tokens
        # would otherwise eat the output budget and can truncate the transcript.
        "generation_config": {
            "temperature": 0.0,
            "maxOutputTokens": 16384,
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    last = None
    for attempt in range(2):
        try:
            r = requests.post(GEMINI_URL, headers=headers, json=body, timeout=180)
            if r.status_code == 429 or r.status_code >= 500:
                last = RuntimeError(f"Gemini {r.status_code}: {r.text[:200]}")
                if attempt == 0:
                    time.sleep(5)
                    continue
                raise last
            r.raise_for_status()
            data = r.json()
            cands = data.get("candidates") or []
            if not cands:
                raise RuntimeError(f"no candidates (blocked? {data.get('promptFeedback')})")
            parts = (cands[0].get("content") or {}).get("parts") or []
            text = "".join(p.get("text", "") for p in parts).strip()
            if not text:
                raise RuntimeError(f"empty transcript (finishReason={cands[0].get('finishReason')})")
            return text
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            last = e
            if attempt == 0:
                time.sleep(5)
                continue
            raise
    raise last or RuntimeError("transcription failed")


def _notify(text: str) -> None:
    tok = os.environ.get("OPERATOR_TELEGRAM_BOT_TOKEN", "")
    chat = os.environ.get("OPERATOR_TELEGRAM_CHAT_ID", "")
    if not (tok and chat):
        return
    try:
        requests.post(f"https://api.telegram.org/bot{tok}/sendMessage",
                      json={"chat_id": chat, "text": text, "disable_web_page_preview": True},
                      timeout=10)
    except Exception:
        pass


def run(max_override=None, dry_run=False) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    kb_db = os.environ.get("WALKIN_KB_DB_ID", "").strip()
    memo_dir = wc.memo_dir()

    if not api_key:
        print("[walkin-transcribe] GEMINI_API_KEY not set — skipping (no-op).")
        return {"skipped": "no_api_key"}
    if not kb_db and not dry_run:
        print("[walkin-transcribe] WALKIN_KB_DB_ID not set — skipping (no-op).")
        return {"skipped": "no_kb_db"}

    import notion_session as ns
    if not dry_run and not ns.available():
        print("[walkin-transcribe] NOTION_API_KEY not set — skipping (no-op).")
        return {"skipped": "no_notion"}

    pending = wc.pending_memos()
    done_today = wc.transcribed_today_count()
    cap = wc.max_per_day() if max_override is None else int(max_override)
    budget = max(0, cap - done_today)
    todo = pending[:budget]

    ok = failed = 0
    max_bytes = _max_audio_bytes()
    for s in todo:
        audio = s.get("audio", "")
        path = os.path.join(memo_dir, audio)
        try:
            with open(path, "rb") as f:
                content = f.read()
        except Exception as e:
            wc.update_sidecar(audio, status="error", error=f"read_failed: {e}",
                              attempts=int(s.get("attempts", 0)) + 1)
            failed += 1
            continue

        if len(content) > max_bytes:
            wc.update_sidecar(audio, status="error", error="too_large_for_inline",
                              attempts=int(s.get("attempts", 0)) + 1)
            failed += 1
            print(f"[walkin-transcribe] {audio}: too large ({len(content)//1024//1024}MB > inline)")
            continue

        mime = _gemini_mime(audio, s.get("mime", ""))
        try:
            transcript = transcribe_audio(content, mime, api_key)
        except Exception as e:
            wc.update_sidecar(audio, error=str(e)[:400],
                              attempts=int(s.get("attempts", 0)) + 1)  # stays pending, retried
            failed += 1
            print(f"[walkin-transcribe] {audio}: FAILED — {e}")
            continue

        if dry_run:
            print(f"[walkin-transcribe] DRY-RUN {audio} ({len(transcript)} chars):\n{transcript[:500]}\n---")
            ok += 1
            continue

        recorder = s.get("recorder", "")
        fields = {
            "Name": f"{recorder or 'Memo'} — {(s.get('recorded_at') or '')[:10]} — {audio}",
            "Transcript": transcript,
            "Recorded At": s.get("recorded_at") or None,
            "Duration (s)": s.get("duration_sec"),
            "Audio Filename": audio,
            "Status": "transcribed",
        }
        if recorder in KB_MEMBERS:
            fields["Recorded By"] = recorder
        try:
            page_id = ns.create_walkin_kb_row(kb_db, fields)
        except Exception as e:
            wc.update_sidecar(audio, error=f"notion_write: {e}"[:400],
                              attempts=int(s.get("attempts", 0)) + 1)
            failed += 1
            print(f"[walkin-transcribe] {audio}: Notion write FAILED — {e}")
            continue

        from datetime import datetime
        wc.update_sidecar(audio, status="transcribed", kb_page_id=page_id,
                          transcribed_at=datetime.now(wc.TZ).isoformat(timespec="seconds"),
                          error=None)
        ok += 1
        print(f"[walkin-transcribe] {audio}: ok → {page_id}")
        time.sleep(0.4)  # gentle on Notion (~3 req/s)

    summary = (f"[walkin-transcribe] pending={len(pending)} cap={cap} done_today={done_today} "
               f"budget={budget} ok={ok} failed={failed} dry_run={dry_run}")
    print(summary)
    if not dry_run and (ok or failed):
        _notify(f"🎙️ Walk-in Memos: {ok} transkribiert, {failed} fehlgeschlagen "
                f"({len(pending) - ok} offen)")
    return {"pending": len(pending), "ok": ok, "failed": failed, "budget": budget}


def main():
    ap = argparse.ArgumentParser(description="Daily Walk-in voice-memo transcription (Gemini).")
    ap.add_argument("--max", type=int, default=None, help="Override the per-day cap for this run.")
    ap.add_argument("--dry-run", action="store_true", help="Transcribe + print, no Notion/sidecar writes.")
    args = ap.parse_args()
    run(max_override=args.max, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
