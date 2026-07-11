"""Homework submissions for the vRv hub (Abgaben, /api/vrv/uploads).

Pattern copied from store.py (own flock sidecar + atomic tmp/fsync/replace) and
tools/ausgaben/capture.py (server-generated basenames, never the client
filename in a path). Files + index live under VRV_DATA_DIR/uploads (gitignored,
survives deploys; on the VPS the dir is created at call time by gunicorn's
paperclip user — never pre-create it as root).

Security invariants:
- The served mimetype derives ONLY from the stored file's extension
  (serve_mimetype), never from the client-supplied mime, and md/txt are forced
  to text/plain: an upload can therefore never become stored XSS.
- public_entry() strips the on-disk filename; lookups go by uuid id.
"""
import fcntl
import json
import os
import re
import tempfile
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

FOUNDERS = ("Joaquin", "Nico", "Tej", "Patrik")
MAX_UPLOAD_BYTES = 15 * 1024 * 1024
MAX_COMMENT_CHARS = 500

_MODUL_RE = re.compile(r"^modul-[1-9][0-9]?$")
_SAFE_RE = re.compile(r"[^A-Za-z0-9_-]")

# Serving mimetypes by stored extension. md/txt are deliberately text/plain
# (inline in every browser, immune to html sniffing).
_EXT_MIME = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".heic": "image/heic",
    ".md": "text/plain; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
}
# Upload-time mime → extension (mime wins over the filename; iOS sends
# application/octet-stream for HEIC from the Files app, hence the ext fallback).
_MIME_EXT = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/heic": ".heic",
    "image/heif": ".heic",
    "text/markdown": ".md",
    "text/plain": ".txt",
}


def _data_dir():
    base = os.environ.get("VRV_DATA_DIR")
    if not base:
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        base = os.path.join(repo_root, "data", "vrv")
    os.makedirs(base, exist_ok=True)
    return base


def uploads_dir():
    path = os.path.join(_data_dir(), "uploads")
    os.makedirs(path, exist_ok=True)
    return path


def _index_path():
    return os.path.join(_data_dir(), "uploads.json")


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _default_index():
    return {"version": 1, "uploads": []}


def _read_index_unlocked():
    path = _index_path()
    if not os.path.exists(path):
        return _default_index()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            index = json.load(fh)
    except (json.JSONDecodeError, OSError):
        try:
            os.replace(path, path + ".corrupt")
        except OSError:
            pass
        return _default_index()
    base = _default_index()
    base.update(index)
    if not isinstance(base.get("uploads"), list):
        base["uploads"] = []
    return base


def _write_index_unlocked(index):
    path = _index_path()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False, indent=1)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


@contextmanager
def _locked():
    lock_path = os.path.join(_data_dir(), "uploads.lock")
    with open(lock_path, "w") as lock_fh:
        fcntl.flock(lock_fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_fh, fcntl.LOCK_UN)


def _mutate(fn):
    with _locked():
        index = _read_index_unlocked()
        result = fn(index)
        _write_index_unlocked(index)
        return result


def _safe(name):
    return _SAFE_RE.sub("", (name or "").strip())[:24] or "team"


def _display_name(filename):
    return re.sub(r"[\x00-\x1f\x7f]", "", filename or "").strip()[:140]


def ext_for_upload(mime, filename):
    """Extension for an incoming file: mime first, filename fallback. Empty
    string means: not allowed."""
    mime = (mime or "").split(";")[0].strip().lower()
    if mime in _MIME_EXT:
        return _MIME_EXT[mime]
    ext = os.path.splitext(filename or "")[1].lower()
    if ext in _EXT_MIME:
        return ".jpg" if ext == ".jpeg" else ext
    return ""


def validate_meta(modul, who, comment):
    if not _MODUL_RE.match(modul or ""):
        return "Ungültiges Modul"
    if who not in FOUNDERS:
        return "Unbekannter Name"
    if len(comment or "") > MAX_COMMENT_CHARS:
        return f"Kommentar zu lang (max. {MAX_COMMENT_CHARS} Zeichen)"
    return None


def save_upload(modul, who, comment, content, mime, orig_filename):
    """Store file + index entry. Raises ValueError on unsupported type."""
    ext = ext_for_upload(mime, orig_filename)
    if not ext:
        raise ValueError("Dateityp nicht unterstützt (erlaubt: PDF, PNG, JPG, HEIC, MD, TXT)")
    entry_id = uuid.uuid4().hex
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    stored = f"{stamp}__{_safe(who)}__{entry_id[:8]}{ext}"
    directory = uploads_dir()
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=ext)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(content)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, os.path.join(directory, stored))
    except OSError:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise
    entry = {
        "id": entry_id,
        "modul": modul,
        "who": who,
        "comment": (comment or "").strip(),
        "orig_name": _display_name(orig_filename) or stored,
        "stored": stored,
        "size": len(content),
        "mime": _EXT_MIME[ext].split(";")[0],
        "uploaded_at": _now(),
    }
    try:
        _mutate(lambda index: index["uploads"].append(entry))
    except Exception:
        # index write failed → don't leave an unlisted orphan behind
        try:
            os.remove(os.path.join(directory, stored))
        except OSError:
            pass
        raise
    return entry


def list_uploads(modul=None):
    with _locked():
        rows = _read_index_unlocked()["uploads"]
    if modul is not None:
        rows = [r for r in rows if r.get("modul") == modul]
    return sorted(rows, key=lambda r: r.get("uploaded_at", ""), reverse=True)


def get_upload(uid):
    with _locked():
        for row in _read_index_unlocked()["uploads"]:
            if row.get("id") == uid:
                return row
    return None


def delete_upload(uid):
    """Remove index entry first (under lock), then the file best-effort.
    A failed file removal leaves a harmless orphan, never a dangling entry."""
    holder = {}

    def _pop(index):
        for i, row in enumerate(index["uploads"]):
            if row.get("id") == uid:
                holder["entry"] = index["uploads"].pop(i)
                return True
        return False

    removed = _mutate(_pop)
    if removed and holder.get("entry", {}).get("stored"):
        try:
            os.remove(os.path.join(uploads_dir(), holder["entry"]["stored"]))
        except OSError:
            pass
    return removed


def abs_path_for(entry):
    return os.path.join(uploads_dir(), entry["stored"])


def serve_mimetype(entry):
    ext = os.path.splitext(entry.get("stored", ""))[1].lower()
    # bare type only: Flask appends charset to text/* itself
    return _EXT_MIME.get(ext, "application/octet-stream").split(";")[0]


def public_entry(entry):
    return {k: v for k, v in entry.items() if k != "stored"}
