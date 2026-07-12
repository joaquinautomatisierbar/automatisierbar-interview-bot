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
    """The hub (dashboard + Lernen + Unterlagen). The questionnaire moved to
    /vrv/fragebogen — its API endpoints are unchanged, so open tabs and the
    localStorage queue survive the move."""
    return send_from_directory(current_app.static_folder, "vrv-hub.html")


@bp.route("/vrv/fragebogen", methods=["GET"])
def vrv_fragebogen_page():
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
# Hub: docs (manifest-exact serving) + dashboard
# ---------------------------------------------------------------------------

@bp.route("/api/vrv/docs", methods=["GET"])
def vrv_docs_manifest():
    guard = _require_internal()
    if guard:
        return guard
    from vrv import docs
    return jsonify({"sections": docs.manifest()})


@bp.route("/api/vrv/docs/<path:relpath>", methods=["GET"])
def vrv_docs_file(relpath):
    guard = _require_internal()
    if guard:
        return guard
    from flask import send_file
    from vrv import docs
    resolved = docs.resolve(relpath)
    if resolved is None:
        return jsonify({"ok": False, "error": "Unbekanntes Dokument"}), 404
    path, item = resolved
    if not path.is_file():
        return jsonify({"ok": False, "error": "Datei fehlt auf dem Server"}), 404
    if item["kind"] == "md":
        resp = Response(
            path.read_text(encoding="utf-8", errors="replace"),
            mimetype="text/markdown",
        )
        if item.get("material"):
            resp.headers["X-Content-Type-Options"] = "nosniff"
        return resp
    resp = send_file(
        path,
        mimetype=docs.MIME_BY_KIND[item["kind"]],
        as_attachment=item["kind"] in docs.ATTACHMENT_KINDS,
        download_name=path.name,
        conditional=True,
    )
    if item.get("material"):
        # Uploaded (not committed) files: never sniff, and HTML decks run in a
        # CSP sandbox → opaque origin → the SameSite=Lax session cookie is not
        # sent on requests they make: no authenticated cockpit calls from
        # uploaded content. Self-contained decks work unchanged.
        resp.headers["X-Content-Type-Options"] = "nosniff"
        if item["kind"] == "html":
            resp.headers["Content-Security-Policy"] = "sandbox allow-scripts allow-modals"
    return resp


@bp.route("/api/vrv/dashboard", methods=["GET"])
def vrv_dashboard():
    guard = _require_internal()
    if guard:
        return guard
    from vrv import docs
    return jsonify(docs.dashboard_payload())


# ---------------------------------------------------------------------------
# Hub: homework submissions (Abgaben). Files live in VRV_DATA_DIR/uploads,
# lookups go by uuid id only — the on-disk name never leaves the server.
# ---------------------------------------------------------------------------

@bp.route("/api/vrv/uploads", methods=["POST"])
def vrv_upload_create():
    guard = _require_internal()
    if guard:
        return guard
    from vrv import uploads
    f = request.files.get("file")
    if f is None or not (f.filename or "").strip():
        return jsonify({"ok": False, "error": "Datei fehlt (Feld 'file')"}), 400
    error = uploads.validate_meta(
        (request.form.get("modul") or "").strip(),
        (request.form.get("who") or "").strip(),
        request.form.get("comment") or "",
    )
    if error:
        return jsonify({"ok": False, "error": error}), 400
    content = f.read(uploads.MAX_UPLOAD_BYTES + 1)
    if not content:
        return jsonify({"ok": False, "error": "Datei ist leer"}), 400
    if len(content) > uploads.MAX_UPLOAD_BYTES:
        return jsonify({"ok": False, "error": "Datei zu gross (max. 15 MB)"}), 413
    try:
        entry = uploads.save_upload(
            (request.form.get("modul") or "").strip(),
            (request.form.get("who") or "").strip(),
            request.form.get("comment") or "",
            content,
            f.mimetype,
            f.filename,
        )
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 415
    return jsonify({"ok": True, "upload": uploads.public_entry(entry)}), 201


@bp.route("/api/vrv/uploads", methods=["GET"])
def vrv_upload_list():
    guard = _require_internal()
    if guard:
        return guard
    from vrv import uploads
    modul = (request.args.get("modul") or "").strip() or None
    return jsonify({"uploads": [uploads.public_entry(e) for e in uploads.list_uploads(modul)]})


@bp.route("/api/vrv/uploads/<uid>/file", methods=["GET"])
def vrv_upload_file(uid):
    guard = _require_internal()
    if guard:
        return guard
    from flask import send_file
    from vrv import uploads
    entry = uploads.get_upload(uid)
    if entry is None:
        return jsonify({"ok": False, "error": "Unbekannte Abgabe"}), 404
    path = uploads.abs_path_for(entry)
    if not os.path.isfile(path):
        return jsonify({"ok": False, "error": "Datei fehlt auf dem Server"}), 404
    resp = send_file(
        path,
        mimetype=uploads.serve_mimetype(entry),
        as_attachment=False,
        download_name=entry.get("orig_name") or entry["stored"],
        conditional=True,
    )
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp


@bp.route("/api/vrv/uploads/<uid>", methods=["DELETE"])
def vrv_upload_delete(uid):
    guard = _require_internal()
    if guard:
        return guard
    from vrv import uploads
    if not uploads.delete_upload(uid):
        return jsonify({"ok": False, "error": "Unbekannte Abgabe"}), 404
    current_app.logger.info("vrv upload %s deleted", uid)
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Hub: self-service session materials (deck/handout per module). One slot per
# (modul, role); upload replaces. Served through /api/vrv/docs/<path> via the
# manifest merge in docs.py (uploaded HTML gets a CSP sandbox there).
# ---------------------------------------------------------------------------

@bp.route("/api/vrv/materials", methods=["POST"])
def vrv_material_create():
    guard = _require_internal()
    if guard:
        return guard
    from vrv import materials
    f = request.files.get("file")
    if f is None or not (f.filename or "").strip():
        return jsonify({"ok": False, "error": "Datei fehlt (Feld 'file')"}), 400
    modul = (request.form.get("modul") or "").strip()
    role = (request.form.get("role") or "").strip()
    who = (request.form.get("who") or "").strip()
    error = materials.validate_meta(modul, role, who)
    if error:
        return jsonify({"ok": False, "error": error}), 400
    content = f.read(materials.MAX_MATERIAL_BYTES + 1)
    if not content:
        return jsonify({"ok": False, "error": "Datei ist leer"}), 400
    if len(content) > materials.MAX_MATERIAL_BYTES:
        return jsonify({"ok": False, "error": "Datei zu gross (max. 15 MB)"}), 413
    try:
        entry = materials.save_material(modul, role, who, content, f.mimetype, f.filename)
    except materials.StaticSlotError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 409
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 415
    current_app.logger.info("vrv material %s/%s uploaded by %s", modul, role, who)
    return jsonify({"ok": True, "material": materials.public_entry(entry)}), 201


@bp.route("/api/vrv/materials", methods=["GET"])
def vrv_material_list():
    guard = _require_internal()
    if guard:
        return guard
    from vrv import materials
    modul = (request.args.get("modul") or "").strip() or None
    payload = {"materials": [materials.public_entry(e) for e in materials.list_materials(modul)]}
    if modul:
        payload["static_slots"] = materials.static_slots(modul)
    return jsonify(payload)


@bp.route("/api/vrv/materials/<uid>", methods=["DELETE"])
def vrv_material_delete(uid):
    guard = _require_internal()
    if guard:
        return guard
    from vrv import materials
    if not materials.delete_material(uid):
        return jsonify({"ok": False, "error": "Unbekanntes Material"}), 404
    current_app.logger.info("vrv material %s deleted", uid)
    return jsonify({"ok": True})


@bp.app_errorhandler(413)
def vrv_payload_too_large(e):
    """JSON 413 for the vrv API only (uploads > global MAX_CONTENT_LENGTH die
    in Werkzeug before our route runs); every other tool keeps the default."""
    if request.path.startswith("/api/vrv/"):
        return jsonify({"ok": False, "error": "Datei zu gross (max. 15 MB)"}), 413
    return e


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
# Client pre-send page (v2) — magic-token link, strictly isolated from the
# internal surface. Env check comes FIRST so unsetting VRV_CLIENT_TOKEN after
# the tender revokes access even for live 365-day session cookies.
# ---------------------------------------------------------------------------

def _client_token():
    return (os.environ.get("VRV_CLIENT_TOKEN") or "").strip()


def _client_authed():
    return bool(_client_token()) and session.get("vrv_client") is True


@bp.route("/vrv/kunde", methods=["GET"])
def vrv_client_page():
    token = _client_token()
    given = (request.args.get("k") or "").strip()
    if token and given:
        if given == token:
            session["vrv_client"] = True
            session.permanent = True
        # redirect-clean either way: the token must not linger in the URL bar
        from flask import redirect
        return redirect("/vrv/kunde")
    return send_from_directory(current_app.static_folder, "vrv-kunde.html")


def _require_client():
    if not _client_authed():
        return jsonify({"ok": False, "error": "Link ungültig oder abgelaufen"}), 401
    return None


_CLIENT_FIELDS = ("id", "text", "type", "options", "value")


@bp.route("/api/vrv/client/questions", methods=["GET"])
def vrv_client_questions():
    guard = _require_client()
    if guard:
        return guard
    from vrv import catalog, store
    answers = store.load_state().get("answers", {})
    out = []
    for q in catalog.client_visible_questions():
        item = {
            "id": q["id"],
            "text": q.get("client_text") or q["text"],
            "type": q["type"],
            "value": (answers.get(q["id"]) or {}).get("client_value", ""),
        }
        if q["type"] == "choice":
            item["options"] = q.get("options", [])
        # hard whitelist: never let internal fields leak through refactors
        assert set(item.keys()) <= set(_CLIENT_FIELDS)
        out.append(item)
    return jsonify({"questions": out})


@bp.route("/api/vrv/client/answer/<qid>", methods=["PATCH"])
def vrv_client_answer(qid):
    guard = _require_client()
    if guard:
        return guard
    from vrv import catalog, store
    q = catalog.question_by_id(qid)
    if q is None or not q.get("client_visible"):
        return jsonify({"ok": False, "error": "Nicht verfügbar"}), 403
    body = request.get_json(silent=True) or {}
    try:
        store.upsert_client_answer(qid, (body.get("value") or "").strip())
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Health (public, no data)
# ---------------------------------------------------------------------------

@bp.route("/api/vrv/health", methods=["GET"])
def vrv_health():
    from vrv import store
    ok = store.health()
    return jsonify({"ok": ok, "store_writable": ok}), (200 if ok else 503)
