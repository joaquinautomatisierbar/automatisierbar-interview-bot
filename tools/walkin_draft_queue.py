#!/usr/bin/env python3
"""walkin_draft_queue.py — file-backed job queue for the walk-in auto-draft pipeline.

`POST /api/walkin/lead` enqueues one job per captured lead; `walkin_draft_worker.py` (a cron,
optionally kicked inline) claims and processes them. Mirrors the voice-memo sidecar pattern in
walkin_capture.py (atomic JSON writes) and adds a POSIX advisory lock so the cron and an inline
kick can't double-process the same job — and a crashed holder never strands one (the OS releases
the lock on process exit; a stale-`processing` reclaim window backs it up).

One JSON file per lead. `status`: pending -> processing -> drafted | skipped | failed.
"""
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

try:
    import fcntl  # POSIX only (macOS/Linux) — the VPS + dev Macs are both POSIX
    _HAVE_FCNTL = True
except ImportError:  # pragma: no cover - Windows fallback (unused in prod)
    _HAVE_FCNTL = False

MAX_ATTEMPTS = 3
STALE_PROCESSING_SEC = 600  # a 'processing' job older than this is reclaimable
_TERMINAL = ("drafted", "skipped", "failed")
_TZ = "Europe/Zurich"


def queue_dir() -> str:
    d = os.environ.get("WALKIN_DRAFT_QUEUE_DIR") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp", "walkin_drafts")
    os.makedirs(d, exist_ok=True)
    return d


def _now_local() -> datetime:
    try:
        return datetime.now(ZoneInfo(_TZ))
    except Exception:
        return datetime.now(timezone.utc)


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return (s or "lead")[:40]


def _atomic_write(path: str, data: dict) -> None:
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def job_path(job_id: str) -> str:
    return os.path.join(queue_dir(), f"{job_id}.json")


def enqueue_job(payload: dict) -> dict:
    """Write one pending job. `payload` carries the lead fields + routing (entering_person, cc,
    next_action, lead_page_id, walkin_date, and the raw form fields). Returns the job dict."""
    now = _now_local()
    stamp = now.strftime("%Y%m%d-%H%M%S")
    # a short uniquifier without Math.random-style deps: microseconds are plenty at this volume
    uniq = f"{now.microsecond:06d}"
    company = (payload.get("company") or (payload.get("fields") or {}).get("company") or "")
    job_id = f"{stamp}__{_slug(company)}__{uniq}"
    job = {
        "job_id": job_id,
        "created_at": now.isoformat(),
        "status": "pending",
        "attempts": 0,
        "claimed_at": None,
        "error": None,
        "drafted_at": None,
        "resolved_email": None,
        "resolved_email_confident": None,
        "sector": None,
        "skip_reason": None,
    }
    job.update(payload)  # caller-provided keys win, then we re-assert the invariants
    job["job_id"] = job_id
    job["status"] = "pending"
    job["attempts"] = 0
    _atomic_write(job_path(job_id), job)
    return job


def _read(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def list_jobs() -> list:
    out = []
    for name in os.listdir(queue_dir()):
        if not name.endswith(".json"):
            continue
        try:
            out.append(_read(os.path.join(queue_dir(), name)))
        except Exception:
            continue
    return out


def _is_stale_processing(job: dict) -> bool:
    if job.get("status") != "processing":
        return False
    claimed = job.get("claimed_at")
    if not claimed:
        return True
    try:
        age = (_now_local() - datetime.fromisoformat(claimed)).total_seconds()
    except Exception:
        return True
    return age > STALE_PROCESSING_SEC


def pending_jobs() -> list:
    """Claimable jobs (pending, or stale-processing) under the attempt cap, oldest first."""
    jobs = [j for j in list_jobs()
            if j.get("attempts", 0) < MAX_ATTEMPTS
            and (j.get("status") == "pending" or _is_stale_processing(j))]
    jobs.sort(key=lambda j: j.get("created_at") or "")
    return jobs


def update_job(job_id: str, **changes) -> dict:
    """Read-modify-write a job atomically. The worker holds the flock while calling this, so
    concurrent writers to the same job can't interleave."""
    path = job_path(job_id)
    job = _read(path)
    job.update(changes)
    _atomic_write(path, job)
    return job


def claim(job_id: str):
    """Take an exclusive, non-blocking advisory lock on the job's lock file. Returns an open fd
    on success (the CALLER must close() it to release — even on error), or None if another
    process already holds it. The OS auto-releases on process exit, so a crashed holder never
    permanently strands the job."""
    lock = job_path(job_id) + ".lock"
    fd = os.open(lock, os.O_CREAT | os.O_RDWR, 0o644)
    if not _HAVE_FCNTL:
        return fd
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except (BlockingIOError, OSError):
        os.close(fd)
        return None


def release(fd) -> None:
    if fd is None:
        return
    try:
        if _HAVE_FCNTL:
            fcntl.flock(fd, fcntl.LOCK_UN)
    except Exception:
        pass
    try:
        os.close(fd)
    except Exception:
        pass


def job_stats() -> dict:
    stats = {"total": 0, "pending": 0, "processing": 0, "drafted": 0, "skipped": 0, "failed": 0}
    for j in list_jobs():
        stats["total"] += 1
        stats[j.get("status", "pending")] = stats.get(j.get("status", "pending"), 0) + 1
    return stats
