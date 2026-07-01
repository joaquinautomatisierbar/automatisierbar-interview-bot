"""backup.py — nightly safety net for KnowSpesen data (VPS cron).

The SQLite DB + the receipt images live ONLY on the VPS, so a lost/corrupted disk
loses every submitted expense. This makes a verified, rotated snapshot:

  1. sqlite3 online .backup() of knowspesen.db -> a consistent copy even while the
     app is writing (NOT a raw cp, which can capture a half-written page).
  2. tar.gz the DB snapshot + the whole receipts dir ->
     /srv/knowspesen/backups/knowspesen-<ts>.tar.gz
  3. verify the archive (the sqlite snapshot opens + integrity_check, tar lists).
  4. rotate: keep the newest KEEP archives.
  5. optional off-box push (SPESEN_BACKUP_REMOTE) so a full VPS loss is survivable.
  6. record last_backup_at / last_backup_ok in app_meta (surfaced by /api/spesen/health
     and the dashboard), Telegram-alert the operator on failure.

Usage:  python3 tools/spesen/backup.py            (run a backup)
        python3 tools/spesen/backup.py --dry-run  (plan only, no writes/push)

Env:
  SPESEN_DB_PATH, SPESEN_RECEIPT_DIR   what to back up (same as the app)
  SPESEN_BACKUP_DIR                    local archive dir (default /srv/knowspesen/backups)
  SPESEN_BACKUP_KEEP                   how many local archives to keep (default 14)
  SPESEN_BACKUP_REMOTE                 optional off-box target; see _push_offbox()
  OPERATOR_TELEGRAM_BOT_TOKEN / _CHAT_ID   failure alert
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo

try:
    from . import db
except ImportError:  # pragma: no cover - direct-script run
    import db

TZ = ZoneInfo("Europe/Zurich")


def backup_dir() -> str:
    return os.environ.get("SPESEN_BACKUP_DIR", "/srv/knowspesen/backups")


def keep_count() -> int:
    try:
        return max(1, int(os.environ.get("SPESEN_BACKUP_KEEP", "14")))
    except (TypeError, ValueError):
        return 14


def _receipt_dir() -> str:
    return os.environ.get("SPESEN_RECEIPT_DIR", "/srv/knowspesen/receipts")


def _snapshot_db(dst_path: str) -> None:
    """Consistent online snapshot of the live DB (safe during writes)."""
    src = sqlite3.connect(db.db_path())
    try:
        dst = sqlite3.connect(dst_path)
        try:
            src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()


def _verify_snapshot(path: str) -> bool:
    conn = sqlite3.connect(path)
    try:
        row = conn.execute("PRAGMA integrity_check").fetchone()
        # touch a core table so a structurally-fine-but-empty file still fails loudly
        conn.execute("SELECT COUNT(*) FROM knowbodies").fetchone()
        return bool(row) and row[0] == "ok"
    except Exception:
        return False
    finally:
        conn.close()


def _post_telegram(text: str) -> None:
    token = os.environ.get("OPERATOR_TELEGRAM_BOT_TOKEN", "")
    chat = os.environ.get("OPERATOR_TELEGRAM_CHAT_ID") or os.environ.get("COCKPIT_TEAM_CHAT_ID", "")
    if not token or not chat:
        print("[backup] no Telegram creds, skipping alert")
        return
    try:
        import requests
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat, "text": text}, timeout=15)
    except Exception as e:
        print(f"[backup] Telegram error: {e!r}")


def _push_offbox(archive_path: str, dry_run: bool) -> str:
    """Push the archive off the VPS. Destination configured via SPESEN_BACKUP_REMOTE:
      - "rclone:remote:path"   -> rclone copy (Drive/S3/etc.; rclone must be configured)
      - "rsync:user@host:/path" -> rsync over ssh (key auth)
    Returns a short status string. No-op (returns 'skip') if unset — the local snapshot
    still protects against accidental delete/corruption; off-box is the halt-gated add."""
    remote = (os.environ.get("SPESEN_BACKUP_REMOTE") or "").strip()
    if not remote:
        return "skip (kein SPESEN_BACKUP_REMOTE)"
    if dry_run:
        return f"würde pushen -> {remote}"
    try:
        if remote.startswith("rclone:"):
            target = remote[len("rclone:"):]
            subprocess.run(["rclone", "copy", archive_path, target], check=True, timeout=600)
        elif remote.startswith("rsync:"):
            target = remote[len("rsync:"):]
            subprocess.run(["rsync", "-az", archive_path, target], check=True, timeout=600)
        else:
            return f"unbekanntes Ziel-Schema: {remote.split(':',1)[0]}"
        return f"gepusht -> {remote}"
    except Exception as e:
        return f"push FEHLER: {type(e).__name__}: {e}"


def _rotate(bdir: str, keep: int) -> int:
    archives = sorted(
        (os.path.join(bdir, f) for f in os.listdir(bdir)
         if f.startswith("knowspesen-") and f.endswith(".tar.gz")),
        key=os.path.getmtime, reverse=True)
    removed = 0
    for old in archives[keep:]:
        try:
            os.remove(old)
            removed += 1
        except OSError:
            pass
    return removed


def run(dry_run: bool = False) -> dict:
    now = datetime.now(TZ)
    stamp = now.strftime("%Y%m%d-%H%M%S")
    bdir = backup_dir()
    rdir = _receipt_dir()
    archive = os.path.join(bdir, f"knowspesen-{stamp}.tar.gz")

    result = {"ok": False, "archive": archive, "when": now.isoformat(timespec="seconds")}
    try:
        if dry_run:
            print(f"[backup] (dry-run) würde erstellen: {archive}")
            print(f"[backup] (dry-run) DB={db.db_path()}  receipts={rdir}")
            print(f"[backup] (dry-run) off-box: {_push_offbox(archive, dry_run=True)}")
            result["ok"] = True
            return result

        os.makedirs(bdir, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="ksbk_") as tmp:
            snap = os.path.join(tmp, "knowspesen.db")
            _snapshot_db(snap)
            if not _verify_snapshot(snap):
                raise RuntimeError("DB-Snapshot integrity_check fehlgeschlagen")
            with tarfile.open(archive, "w:gz") as tf:
                tf.add(snap, arcname="knowspesen.db")
                if os.path.isdir(rdir):
                    tf.add(rdir, arcname="receipts")

        # verify the finished archive is readable + contains the DB
        with tarfile.open(archive, "r:gz") as tf:
            names = tf.getnames()
        if "knowspesen.db" not in names:
            raise RuntimeError("Archiv unvollständig (knowspesen.db fehlt)")

        size_mb = round(os.path.getsize(archive) / (1024 * 1024), 2)
        removed = _rotate(bdir, keep_count())
        push = _push_offbox(archive, dry_run=False)

        db.meta_set("last_backup_at", now.isoformat(timespec="seconds"))
        db.meta_set("last_backup_ok", "1")
        db.meta_set("last_backup_size_mb", str(size_mb))
        result.update({"ok": True, "size_mb": size_mb, "rotated": removed,
                       "receipts_included": len([n for n in names if n.startswith("receipts/")]),
                       "offbox": push})
        print(f"[backup] OK {archive} ({size_mb} MB), rotiert={removed}, off-box: {push}")
        if push.startswith("push FEHLER"):
            _post_telegram(f"🟠 KnowSpesen Backup: lokal OK, aber off-box {push}")
        return result
    except Exception as e:
        try:
            db.meta_set("last_backup_ok", "0")
            db.meta_set("last_backup_error", f"{type(e).__name__}: {e}")
        except Exception:
            pass
        print(f"[backup] FEHLER: {e!r}")
        _post_telegram(f"🔴 KnowSpesen Backup FEHLGESCHLAGEN: {type(e).__name__}: {e}")
        result["error"] = str(e)
        return result


if __name__ == "__main__":
    r = run(dry_run=("--dry-run" in sys.argv))
    sys.exit(0 if r.get("ok") else 1)
