"""Self-service session materials for the vRv hub (/api/vrv/materials).

Team members upload their own module deck (HTML), handout (MD) and handout-PDF
without server access. Each (modul, role) pair is ONE slot: a new upload
replaces the previous file. The manifest layer (docs.manifest) merges every
slot as a virtual entry `upskilling/modul-N-<deck.html|handout.md|handout.pdf>`
so the hub frontend groups, labels and buttons them exactly like the committed
modules — zero frontend special cases.

Pattern copied from uploads.py: files + index live under
VRV_DATA_DIR/materials (gitignored / outside the repo tree on the VPS, so they
survive deploys; the dir is created at call time by gunicorn's paperclip user
— never pre-create it as root). flock sidecar + atomic tmp/fsync/replace.

Security invariants:
- Slots whose virtual path exists in the hardcoded DOCS_MANIFEST are rejected
  (static wins): nobody can shadow the committed modul-2/modul-5 files.
- The served mimetype derives ONLY from the slot's role, never from the
  client-supplied mime.
- Uploaded HTML decks are served inline BUT with
  `Content-Security-Policy: sandbox allow-scripts allow-modals` (see routes):
  the document gets an opaque origin, so with our SameSite=Lax session cookie
  a malicious/broken deck cannot make authenticated cockpit requests.
  Self-contained decks (view transitions, frag engine) work unchanged.
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
MAX_MATERIAL_BYTES = 15 * 1024 * 1024

_MODUL_RE = re.compile(r"^modul-[1-9][0-9]?$")

# role → (virtual path suffix, manifest kind, serve mimetype, allowed upload
# mimes, allowed filename extensions). The suffixes are chosen so virtual
# paths satisfy the same convention as committed files
# (upskilling/modul-N-(deck|handout).(html|md|pdf)) and the hub's lernRole()
# picks the same buttons.
ROLES = {
    "deck": {
        "suffix": "deck.html",
        "kind": "html",
        "mime": "text/html",
        "upload_mimes": {"text/html"},
        "upload_exts": {".html", ".htm"},
        "label": "Präsentation",
    },
    "handout": {
        "suffix": "handout.md",
        "kind": "md",
        "mime": "text/markdown",
        "upload_mimes": {"text/markdown", "text/plain"},
        "upload_exts": {".md"},
        "label": "Handout",
    },
    "handout-pdf": {
        "suffix": "handout.pdf",
        "kind": "pdf",
        "mime": "application/pdf",
        "upload_mimes": {"application/pdf"},
        "upload_exts": {".pdf"},
        "label": "Handout (PDF)",
    },
}


def _data_dir():
    base = os.environ.get("VRV_DATA_DIR")
    if not base:
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        base = os.path.join(repo_root, "data", "vrv")
    os.makedirs(base, exist_ok=True)
    return base


def materials_dir():
    path = os.path.join(_data_dir(), "materials")
    os.makedirs(path, exist_ok=True)
    return path


def _index_path():
    return os.path.join(_data_dir(), "materials.json")


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _default_index():
    return {"version": 1, "materials": []}


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
    if not isinstance(base.get("materials"), list):
        base["materials"] = []
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
    lock_path = os.path.join(_data_dir(), "materials.lock")
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


def _display_name(filename):
    return re.sub(r"[\x00-\x1f\x7f]", "", filename or "").strip()[:140]


def virtual_path(modul, role):
    return f"upskilling/{modul}-{ROLES[role]['suffix']}"


def _is_static_slot(modul, role):
    """True when the committed manifest already owns this virtual path
    (modul-2/modul-5 deck + handouts). Static always wins."""
    from vrv import docs
    return virtual_path(modul, role) in docs._BY_PATH


def static_slots(modul):
    """Roles of this module that are owned by the committed manifest — the hub
    shows them as 'fix im Repo' and blocks the upload form."""
    return [role for role in ROLES if _is_static_slot(modul, role)]


def validate_meta(modul, role, who):
    if not _MODUL_RE.match(modul or ""):
        return "Ungültiges Modul"
    if role not in ROLES:
        return "Ungültige Rolle (erlaubt: deck, handout, handout-pdf)"
    if who not in FOUNDERS:
        return "Unbekannter Name"
    return None


def type_allowed(role, mime, filename):
    spec = ROLES[role]
    mime = (mime or "").split(";")[0].strip().lower()
    if mime in spec["upload_mimes"]:
        return True
    ext = os.path.splitext(filename or "")[1].lower()
    return ext in spec["upload_exts"]


class StaticSlotError(Exception):
    """The slot is owned by the committed manifest — upload refused."""


def save_material(modul, role, who, content, mime, orig_filename):
    """Store file + replace the (modul, role) slot. Raises ValueError on
    unsupported type, StaticSlotError when the committed manifest owns the
    slot."""
    if _is_static_slot(modul, role):
        raise StaticSlotError(
            f"{modul}/{ROLES[role]['label']} wird im Repo gepflegt und kann nicht überschrieben werden")
    if not type_allowed(role, mime, orig_filename):
        spec = ROLES[role]
        raise ValueError(
            f"Dateityp passt nicht zur Rolle {role} (erwartet: {', '.join(sorted(spec['upload_exts']))})")
    ext = os.path.splitext(ROLES[role]["suffix"])[1]
    entry_id = uuid.uuid4().hex
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    stored = f"{stamp}__{modul}-{role}__{entry_id[:8]}{ext}"
    directory = materials_dir()
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
        "role": role,
        "who": who,
        "orig_name": _display_name(orig_filename) or stored,
        "stored": stored,
        "size": len(content),
        "mime": ROLES[role]["mime"],
        "uploaded_at": _now(),
    }
    replaced = {}

    def _replace(index):
        keep = []
        for row in index["materials"]:
            if row.get("modul") == modul and row.get("role") == role:
                replaced["old"] = row
            else:
                keep.append(row)
        keep.append(entry)
        index["materials"] = keep

    try:
        _mutate(_replace)
    except Exception:
        # index write failed → don't leave an unlisted orphan behind
        try:
            os.remove(os.path.join(directory, stored))
        except OSError:
            pass
        raise
    old = replaced.get("old")
    if old and old.get("stored") and old["stored"] != stored:
        try:
            os.remove(os.path.join(directory, old["stored"]))
        except OSError:
            pass
    return entry


def list_materials(modul=None):
    with _locked():
        rows = _read_index_unlocked()["materials"]
    if modul is not None:
        rows = [r for r in rows if r.get("modul") == modul]
    return sorted(rows, key=lambda r: (r.get("modul", ""), r.get("role", "")))


def get_material(uid):
    with _locked():
        for row in _read_index_unlocked()["materials"]:
            if row.get("id") == uid:
                return row
    return None


def by_virtual_path(relpath):
    """Exact index lookup by virtual manifest path — same traversal safety as
    docs._BY_PATH (user input is only ever compared, never joined)."""
    for row in list_materials():
        if virtual_path(row["modul"], row["role"]) == relpath:
            return row
    return None


def delete_material(uid):
    """Remove index entry first (under lock), then the file best-effort."""
    holder = {}

    def _pop(index):
        for i, row in enumerate(index["materials"]):
            if row.get("id") == uid:
                holder["entry"] = index["materials"].pop(i)
                return True
        return False

    removed = _mutate(_pop)
    if removed and holder.get("entry", {}).get("stored"):
        try:
            os.remove(os.path.join(materials_dir(), holder["entry"]["stored"]))
        except OSError:
            pass
    return removed


def abs_path_for(entry):
    return os.path.join(materials_dir(), entry["stored"])


def _fmt_date(iso):
    try:
        return datetime.fromisoformat(iso).strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        return ""


def manifest_items():
    """Virtual manifest entries for docs.manifest(): one per slot, shaped like
    _i() items plus material metadata for the hub's Material page."""
    items = []
    for row in list_materials():
        role = row.get("role")
        if role not in ROLES:
            continue
        modul_no = row["modul"].split("-", 1)[1]
        title = f"Modul {modul_no} · {ROLES[role]['label']}"
        if role == "deck":
            title = f"Modul {modul_no} · Präsentation"
        when = _fmt_date(row.get("uploaded_at", ""))
        desc = f"Hochgeladen von {row.get('who', '?')}" + (f" · {when}" if when else "")
        items.append({
            "path": virtual_path(row["modul"], role),
            "title": title,
            "desc": desc,
            "kind": ROLES[role]["kind"],
            "material": True,
            "material_id": row["id"],
            "who": row.get("who"),
            "uploaded_at": row.get("uploaded_at"),
        })
    return items


def public_entry(entry):
    out = {k: v for k, v in entry.items() if k != "stored"}
    out["path"] = virtual_path(entry["modul"], entry["role"])
    return out
