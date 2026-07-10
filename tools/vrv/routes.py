"""Flask Blueprint for the vRv discovery tool (/vrv + /api/vrv/*).

Patterns copied from tools/ausgaben/routes.py: self-contained Blueprint,
fail-closed password auth in an own session namespace (vrv_auth), lazy
in-route imports so a broken submodule can never block app boot, and a
public health probe that exposes no data.

Synthesis runs in a daemon thread with all state on disk (vrv.store), because
the app runs with 2 gunicorn workers: process memory is not shared.
"""
import os
import threading

from flask import Blueprint, Response, current_app, jsonify, request, send_from_directory, session

bp = Blueprint("vrv", __name__)


# ---------------------------------------------------------------------------
# Auth (fail-closed)
# ---------------------------------------------------------------------------

def _configured_password():
    return (os.environ.get("VRV_PASSWORD") or "").strip()


def _api_key_ok():
    configured = (os.environ.get("VRV_API_KEY") or "").strip()
    given = (request.headers.get("X-VRV-Key") or "").strip()
    return bool(configured) and given == configured


def _internal_authed():
    return session.get("vrv_auth") is True or _api_key_ok()


def _require_internal():
    if not _internal_authed():
        return jsonify({"ok": False, "error": "Nicht angemeldet"}), 401
    return None


# ---------------------------------------------------------------------------
# Page + session
# ---------------------------------------------------------------------------

@bp.route("/vrv", methods=["GET"])
def vrv_page():
    return send_from_directory(current_app.static_folder, "vrv.html")


@bp.route("/api/vrv/login", methods=["POST"])
def vrv_login():
    pw = _configured_password()
    if not pw:
        current_app.logger.warning("VRV_PASSWORD not set — login refused (fail-closed)")
        return jsonify({"ok": False, "error": "Login nicht konfiguriert"}), 503
    given = ((request.get_json(silent=True) or {}).get("password") or "").strip()
    if given and given == pw:
        session["vrv_auth"] = True
        session.permanent = True
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Falsches Passwort"}), 401


@bp.route("/api/vrv/logout", methods=["POST"])
def vrv_logout():
    session.pop("vrv_auth", None)
    return jsonify({"ok": True})


@bp.route("/api/vrv/whoami", methods=["GET"])
def vrv_whoami():
    return jsonify({"authed": _internal_authed()})


# ---------------------------------------------------------------------------
# Catalog + state
# ---------------------------------------------------------------------------

@bp.route("/api/vrv/catalog", methods=["GET"])
def vrv_catalog():
    guard = _require_internal()
    if guard:
        return guard
    from vrv import catalog, store
    state = store.load_state()
    return jsonify({
        "chapters": catalog.CHAPTERS,
        "questions": catalog.QUESTIONS,
        "custom_questions": state.get("custom_questions", []),
    })


@bp.route("/api/vrv/state", methods=["GET"])
def vrv_state():
    guard = _require_internal()
    if guard:
        return guard
    from vrv import catalog, store
    state = store.load_state()
    synthesis_status = {
        kind: {k: v for k, v in row.items() if k != "markdown"} | {
            "has_markdown": bool(row.get("markdown"))}
        for kind, row in state.get("synthesis", {}).items()
    }
    return jsonify({
        "answers": state.get("answers", {}),
        "progress": catalog.progress(state.get("answers", {})),
        "followup_suggestions": state.get("followup_suggestions", {}),
        "extra_notes": state.get("extra_notes", ""),
        "synthesis": synthesis_status,
    })


@bp.route("/api/vrv/answer/<qid>", methods=["PATCH"])
def vrv_answer(qid):
    guard = _require_internal()
    if guard:
        return guard
    from vrv import store
    body = request.get_json(silent=True) or {}
    try:
        row = store.upsert_answer(
            qid,
            value=body.get("value"),
            note=body.get("note"),
            status=body.get("status"),
            source=body.get("source"),
            updated_by=body.get("updated_by"),
        )
    except KeyError:
        return jsonify({"ok": False, "error": f"Unbekannte Frage {qid}"}), 404
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify({"ok": True, "answer": row})


@bp.route("/api/vrv/questions", methods=["POST"])
def vrv_add_question():
    guard = _require_internal()
    if guard:
        return guard
    from vrv import store
    body = request.get_json(silent=True) or {}
    try:
        q = store.add_custom_question(
            (body.get("chapter") or "").strip().upper(),
            body.get("text") or "",
            origin=body.get("origin") or "manual",
            priority=body.get("priority") or "nice",
        )
    except KeyError:
        return jsonify({"ok": False, "error": "Unbekanntes Kapitel"}), 404
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify({"ok": True, "question": q}), 201


@bp.route("/api/vrv/notes", methods=["PATCH"])
def vrv_notes():
    guard = _require_internal()
    if guard:
        return guard
    from vrv import store
    body = request.get_json(silent=True) or {}
    try:
        text = store.set_extra_notes(body.get("text") or "")
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify({"ok": True, "extra_notes": text})


# ---------------------------------------------------------------------------
# AI: follow-up suggestions (sync) + synthesis (async on disk)
# ---------------------------------------------------------------------------

@bp.route("/api/vrv/followups/<chapter_id>", methods=["POST"])
def vrv_followups(chapter_id):
    guard = _require_internal()
    if guard:
        return guard
    from vrv import catalog, store, synthesis
    chapter_id = chapter_id.strip().upper()
    if catalog.chapter_by_id(chapter_id) is None:
        return jsonify({"ok": False, "error": "Unbekanntes Kapitel"}), 404
    suggestions = synthesis.suggest_followups(chapter_id, store.load_state())
    store.set_followups(chapter_id, suggestions)
    return jsonify({"ok": True, "suggestions": suggestions})


def _run_synthesis(kind):
    """Daemon-thread body: generate + persist. Must never touch Flask objects."""
    from vrv import store, synthesis
    try:
        fn = synthesis.generate_brief if kind == "brief" else synthesis.generate_spec
        markdown = fn(store.load_state())
        store.set_synthesis(kind, status="done", markdown=markdown, error="", stamp=True)
    except Exception as exc:  # noqa: BLE001 — status must reach the poller
        store.set_synthesis(kind, status="error", error=str(exc)[:500])


@bp.route("/api/vrv/synthesize/<kind>", methods=["POST"])
def vrv_synthesize(kind):
    guard = _require_internal()
    if guard:
        return guard
    from vrv import store
    if kind not in store.SYNTHESIS_KINDS:
        return jsonify({"ok": False, "error": "Unbekannter Export"}), 404
    store.set_synthesis(kind, status="pending", error="")
    thread = threading.Thread(target=_run_synthesis, args=(kind,), daemon=True)
    thread.start()
    return jsonify({"ok": True, "status": "pending"}), 202


@bp.route("/api/vrv/synthesis/<kind>", methods=["GET"])
def vrv_synthesis_status(kind):
    guard = _require_internal()
    if guard:
        return guard
    from vrv import store
    if kind not in store.SYNTHESIS_KINDS:
        return jsonify({"ok": False, "error": "Unbekannter Export"}), 404
    return jsonify(store.load_state()["synthesis"][kind])


_EXPORT_FILENAMES = {"brief": "Offerten-Brief.md", "spec": "Prototyp-Spec.md"}


@bp.route("/api/vrv/export/<kind>.md", methods=["GET"])
def vrv_export(kind):
    guard = _require_internal()
    if guard:
        return guard
    from vrv import store
    if kind not in store.SYNTHESIS_KINDS:
        return jsonify({"ok": False, "error": "Unbekannter Export"}), 404
    row = store.load_state()["synthesis"][kind]
    if row.get("status") != "done" or not row.get("markdown"):
        return jsonify({"ok": False, "error": "Noch nicht generiert"}), 409
    return Response(
        row["markdown"],
        mimetype="text/markdown",
        headers={"Content-Disposition":
                 f'attachment; filename="{_EXPORT_FILENAMES[kind]}"'},
    )


# ---------------------------------------------------------------------------
# Health (public, no data)
# ---------------------------------------------------------------------------

@bp.route("/api/vrv/health", methods=["GET"])
def vrv_health():
    from vrv import store
    ok = store.health()
    return jsonify({"ok": ok, "store_writable": ok}), (200 if ok else 503)
