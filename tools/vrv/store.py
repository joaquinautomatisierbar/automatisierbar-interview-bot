"""JSON-on-disk store for the vRv discovery tool.

One tender = one state file (data/vrv/state.json). Concurrency-safe for the
real deployment shape (2 gunicorn workers, up to 4 team members editing):
every read-modify-write holds an exclusive fcntl lock on a sidecar lockfile,
and writes are atomic (tmp file + os.replace). VRV_DATA_DIR is read at call
time (never at import) so tests and the VPS env can point it anywhere.

Storage rationale (vs. Notion) in tender-vrv/MASTERPLAN.md, WS1 Detail-Spec.
"""
import fcntl
import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone

from vrv import catalog

MAX_VALUE_CHARS = 4000
MAX_NOTE_CHARS = 2000

VALID_STATUS = ("open", "answered", "skipped", "unclear")
VALID_SOURCE = ("prep", "meeting", "client")
SYNTHESIS_KINDS = ("brief", "spec")


def _data_dir():
    base = os.environ.get("VRV_DATA_DIR")
    if not base:
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        base = os.path.join(repo_root, "data", "vrv")
    os.makedirs(base, exist_ok=True)
    return base


def _state_path():
    return os.path.join(_data_dir(), "state.json")


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _default_state():
    return {
        "version": 1,
        "answers": {},
        "custom_questions": [],
        "followup_suggestions": {},
        "extra_notes": "",
        "synthesis": {
            kind: {"status": "idle", "markdown": "", "error": "", "generated_at": None}
            for kind in SYNTHESIS_KINDS
        },
    }


def _read_state_unlocked():
    path = _state_path()
    if not os.path.exists(path):
        return _default_state()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            state = json.load(fh)
    except (json.JSONDecodeError, OSError):
        # Corrupt state must never brick the tool mid-meeting; keep the broken
        # file aside for forensics and start from the default shape.
        try:
            os.replace(path, path + ".corrupt")
        except OSError:
            pass
        return _default_state()
    base = _default_state()
    base.update(state)
    for kind in SYNTHESIS_KINDS:
        base["synthesis"].setdefault(kind, _default_state()["synthesis"][kind])
    return base


def _write_state_unlocked(state):
    path = _state_path()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=1)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


@contextmanager
def _locked():
    lock_path = os.path.join(_data_dir(), "state.lock")
    with open(lock_path, "w") as lock_fh:
        fcntl.flock(lock_fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_fh, fcntl.LOCK_UN)


def load_state():
    with _locked():
        return _read_state_unlocked()


def _mutate(fn):
    """Run fn(state) under the exclusive lock and persist the result."""
    with _locked():
        state = _read_state_unlocked()
        result = fn(state)
        _write_state_unlocked(state)
        return result


def upsert_answer(qid, *, value=None, note=None, status=None, source=None, updated_by=None):
    """Team-side upsert. Unknown qid raises KeyError, oversize raises ValueError."""
    question = catalog.question_by_id(qid)
    if value is not None and len(value) > MAX_VALUE_CHARS:
        raise ValueError(f"value exceeds {MAX_VALUE_CHARS} chars")
    if note is not None and len(note) > MAX_NOTE_CHARS:
        raise ValueError(f"note exceeds {MAX_NOTE_CHARS} chars")
    if status is not None and status not in VALID_STATUS:
        raise ValueError(f"invalid status {status!r}")
    if source is not None and source not in VALID_SOURCE:
        raise ValueError(f"invalid source {source!r}")

    def fn(state):
        if question is None:
            known_custom = {q["id"] for q in state.get("custom_questions", [])}
            if qid not in known_custom:
                raise KeyError(qid)
        row = state["answers"].setdefault(qid, {
            "value": "", "note": "", "status": "open", "source": "prep",
            "updated_at": None, "updated_by": "",
            "client_value": "", "client_submitted_at": None,
        })
        if value is not None:
            row["value"] = value
            if status is None and value.strip() and row["status"] == "open":
                row["status"] = "answered"
        if note is not None:
            row["note"] = note
        if status is not None:
            row["status"] = status
        if source is not None:
            row["source"] = source
        if updated_by is not None:
            row["updated_by"] = updated_by
        row["updated_at"] = _now()
        return dict(row)

    return _mutate(fn)


def upsert_client_answer(qid, value):
    """Client pre-send upsert: only client_visible catalog questions, only client_value."""
    question = catalog.question_by_id(qid)
    if question is None or not question.get("client_visible"):
        raise KeyError(qid)
    if value is not None and len(value) > MAX_VALUE_CHARS:
        raise ValueError(f"value exceeds {MAX_VALUE_CHARS} chars")

    def fn(state):
        row = state["answers"].setdefault(qid, {
            "value": "", "note": "", "status": "open", "source": "prep",
            "updated_at": None, "updated_by": "",
            "client_value": "", "client_submitted_at": None,
        })
        row["client_value"] = value or ""
        row["client_submitted_at"] = _now()
        return dict(row)

    return _mutate(fn)


def add_custom_question(chapter, text, *, origin="manual", priority="nice"):
    if catalog.chapter_by_id(chapter) is None:
        raise KeyError(chapter)
    if not (text or "").strip():
        raise ValueError("empty question text")
    if priority not in ("must", "nice"):
        raise ValueError(f"invalid priority {priority!r}")
    if origin not in ("manual", "ai"):
        raise ValueError(f"invalid origin {origin!r}")

    def fn(state):
        seq = len(state["custom_questions"]) + 1
        q = {"id": f"{chapter.lower()}_f{seq}", "chapter": chapter,
             "text": text.strip(), "origin": origin, "priority": priority,
             "created_at": _now()}
        state["custom_questions"].append(q)
        return q

    return _mutate(fn)


def set_followups(chapter, suggestions):
    def fn(state):
        state["followup_suggestions"][chapter] = suggestions
        return suggestions

    return _mutate(fn)


def set_synthesis(kind, *, status=None, markdown=None, error=None, stamp=False):
    if kind not in SYNTHESIS_KINDS:
        raise KeyError(kind)

    def fn(state):
        row = state["synthesis"][kind]
        if status is not None:
            row["status"] = status
        if markdown is not None:
            row["markdown"] = markdown
        if error is not None:
            row["error"] = error
        if stamp:
            row["generated_at"] = _now()
        return dict(row)

    return _mutate(fn)


def set_extra_notes(text):
    if text is not None and len(text) > MAX_VALUE_CHARS:
        raise ValueError(f"extra_notes exceeds {MAX_VALUE_CHARS} chars")

    def fn(state):
        state["extra_notes"] = text or ""
        return state["extra_notes"]

    return _mutate(fn)


def health():
    """Writable-store probe for /api/vrv/health; never exposes data."""
    try:
        probe = os.path.join(_data_dir(), ".health")
        with open(probe, "w") as fh:
            fh.write("ok")
        os.remove(probe)
        return True
    except OSError:
        return False
