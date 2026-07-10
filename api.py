#!/usr/bin/env python3
"""Flask API for automatisierbar — PDF generation + adaptive survey.

Endpoints:
  GET  /health                       — health check
  POST /generate-pdf                 — generate branded PDF (Telegram bot)
  GET  /                             — serve survey web app
  GET  /api/leads/search?q=name      — search Interview Datenbank leads
  POST /api/session/start            — create session, return round 1 questions
  GET  /api/session/<id>             — get session state (for resume)
  POST /api/session/<id>/answers     — submit round answers
  GET  /api/session/<id>/pdf         — generate build-spec PDF, return binary
  GET  /api/session/<id>/prompt      — generate Claude Code prompt, return JSON

  POST /api/linkedin/comments        — generate 3 comment variants from text or image
  GET  /api/linkedin/leads-top20     — return top 20 leads ranked for LinkedIn engagement
  POST /api/linkedin/log             — log a comment/post/DM/connection to Notion
  POST /api/linkedin/setup-db        — one-time: create the LinkedIn Activity DB

Auth for /generate-pdf and all /api/linkedin/*: X-API-Key header (PDF_API_KEY env var)
"""

import os
import re
import sys

from flask import Flask, request, jsonify, send_file, send_from_directory, session, redirect

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tools"))

app = Flask(__name__, static_folder="static")

PDF_API_KEY = os.environ.get("PDF_API_KEY", "")

# Cockpit operator login (password gate → signed session cookie, no key in the URL).
COCKPIT_PASSWORD = os.environ.get("COCKPIT_PASSWORD", "Operations2026$")
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or ("ab-cockpit-secret-" + (PDF_API_KEY or "dev"))
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
# HTTPS-only cookie on Render (prod); plain http for local test_client.
app.config["SESSION_COOKIE_SECURE"] = bool(os.environ.get("RENDER"))

MAX_CONTEXT_CHARS = 8000  # Notion rich_text safe upper bound for State JSON
MAX_ANSWER_CHARS = 4000   # per-answer cap; 8 answers × 4000 = 32k headroom
MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024  # 5 MB hard cap per uploaded file
MAX_EXTRAS_CHARS = 8000   # sidebar notes pad cap
MAX_ADDITIONAL_AUTOMATIONS = 20  # "other automation ideas" captured mid-interview
MAX_PROCESS_STEPS = 30    # sane upper bound for the A→Z walkthrough


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default


# Walk-in voice memos can be larger than survey attachments. Cap at the Gemini
# inline limit (~20 MB); the upload route enforces this per-file too.
WALKIN_MAX_AUDIO_MB = _env_int("WALKIN_MAX_AUDIO_MB", 20)
WALKIN_MAX_AUDIO_BYTES = WALKIN_MAX_AUDIO_MB * 1024 * 1024
WALKIN_KB_DB_ID = os.environ.get("WALKIN_KB_DB_ID", "")

# --- Company Brief automation (Hub M9) --------------------------------------
# Generated HTML briefs are written here and served by this app at /b/<token>.html. Default
# base URL is the cockpit host so briefs are reachable immediately (no new DNS); flip
# BRIEF_BASE_URL to https://briefs.automatisierbar.ch once that subdomain proxies to :8082.
BRIEFS_DIR = os.environ.get(
    "BRIEFS_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), ".tmp", "briefs"))
BRIEF_BASE_URL = os.environ.get("BRIEF_BASE_URL", "https://cockpit.automatisierbar.ch").rstrip("/")
BRIEF_SHARED_SECRET = os.environ.get("BRIEF_SHARED_SECRET", "")
_BRIEF_TOKEN_RE = re.compile(r"^[0-9a-fA-F]{16,64}$")


def _brief_auth_ok() -> bool:
    """Fail-closed: the Hub's brief worker authenticates with the X-Brief-Secret header.
    If the secret isn't configured, refuse (never fall open)."""
    if not BRIEF_SHARED_SECRET:
        app.logger.warning("BRIEF_SHARED_SECRET not set — /api/brief/generate refused")
        return False
    return request.headers.get("X-Brief-Secret") == BRIEF_SHARED_SECRET

# Flask-level request body cap. Above the larger of the per-file caps to leave
# room for multipart overhead. Anything larger fails fast at the WSGI layer.
app.config["MAX_CONTENT_LENGTH"] = max(
    MAX_ATTACHMENT_BYTES + 64 * 1024,
    WALKIN_MAX_AUDIO_BYTES + 256 * 1024,
)

SESSION_ID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def _valid_session_id(sid: str) -> bool:
    return bool(sid and SESSION_ID_RE.match(sid))


def _validate_answer_list(answers):
    """Shared validation for a round's answers (submit + back-nav edit).
    Returns an error string if invalid, else None."""
    if not isinstance(answers, list) or len(answers) > 20:
        return "answers must be a list of ≤20 items"
    for a in answers:
        if not isinstance(a, dict):
            return "each answer must be an object"
        if len(str(a.get("answer", ""))) > MAX_ANSWER_CHARS:
            return f"answer too long (max {MAX_ANSWER_CHARS} chars)"
    if not answers:
        return "answers required"
    if not any(str(a.get("answer", "")).strip() for a in answers):
        return "at least one non-empty answer required"
    # Defense in depth — reject the literal "Andere…" placeholder. Frontend already
    # validates, but a third-party API client could post it directly.
    for a in answers:
        ans = str(a.get("answer", "")).strip()
        if ans in ("Andere…", "Andere...", "Andere"):
            return "Bitte deine Antwort eingeben — 'Andere…' braucht Freitext."
    return None


def _auth_ok() -> bool:
    """Fail-closed: if PDF_API_KEY isn't configured, deny all auth-required routes
    (was previously fail-open, exposing /generate-pdf and /api/linkedin/* to the
    public internet whenever the env var was unset)."""
    if not PDF_API_KEY:
        app.logger.warning("PDF_API_KEY not set — auth-required routes refused")
        return False
    return request.headers.get("X-API-Key") == PDF_API_KEY


def _cockpit_auth_ok() -> bool:
    """Cockpit/operator routes accept EITHER a valid password session cookie (the
    /api/cockpit/login flow) OR the X-API-Key header (scripts, n8n). Keeps the API
    key out of the browser URL while leaving programmatic access intact."""
    return bool(session.get("cockpit_auth")) or _auth_ok()


def _cockpit_home() -> bool:
    """True only on the cockpit VPS deployment (COCKPIT_HOME=1 in /etc/cockpit/env).
    There the bare root serves the public landing page and the interview bot lives at
    /interview. On Render this is unset, so the root keeps serving the interview bot.
    Read per-request so it stays unit-testable (monkeypatch the env var)."""
    return bool(os.environ.get("COCKPIT_HOME"))


# The interview bot now has a single canonical home: cockpit.automatisierbar.ch/interview
# (served from the feat/cockpit-booking branch on the VPS). Render is retained only for its
# OTHER routes (/generate-pdf, /api/linkedin/*, the voice cold-call cockpit). So on the Render
# deployment the two interview PAGE routes 302-redirect to cockpit — old/shared Render links
# keep working — while everything else on Render is untouched. 302 (not 301) keeps this
# revertible: browsers cache 301s aggressively.
COCKPIT_INTERVIEW_URL = os.environ.get(
    "COCKPIT_INTERVIEW_URL", "https://cockpit.automatisierbar.ch/interview"
)


def _redirect_to_cockpit_interview():
    """302 to the cockpit interview home, preserving ?s=<uuid> so resume links survive."""
    qs = request.query_string.decode()
    target = COCKPIT_INTERVIEW_URL + (("?" + qs) if qs else "")
    return redirect(target, code=302)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


# ---------------------------------------------------------------------------
# Existing: PDF generation for Telegram bot
# ---------------------------------------------------------------------------

@app.route("/generate-pdf", methods=["POST"])
def generate_pdf_route():
    if not _auth_ok():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No JSON body"}), 400

    try:
        from generate_pdf import generate
        path = generate(data)
        return send_file(
            path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=os.path.basename(path),
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.error("PDF generation failed: %s", e)
        return jsonify({"error": "PDF generation failed"}), 500


# ---------------------------------------------------------------------------
# Survey web app — serve frontend
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    # The walk-in PWA has its own host (walkin.automatisierbar.ch); send its bare
    # domain straight to the app instead of the cockpit landing page.
    host = request.host.split(":")[0]
    if host.startswith("walkin"):
        return redirect("/walkin")
    # KnowSpesen client app: knowspesen.automatisierbar.ch (also spesen.*) -> /spesen.
    if host.startswith("knowspesen") or host.startswith("spesen"):
        return redirect("/spesen")
    # Internal expense tracker: ausgaben.automatisierbar.ch -> /ausgaben (Blueprint).
    if host.startswith("ausgaben"):
        return redirect("/ausgaben")
    # Company briefs: briefs.automatisierbar.ch has no index — a brief is only reachable at
    # its unguessable /b/<token>.html URL (non-enumerable, holds confidential client info).
    if host.startswith("briefs"):
        return ("Not found", 404)
    # On the cockpit VPS deployment the bare domain is the public booking front door,
    # so it serves a small landing page; the interview bot moves to /interview (below).
    # On Render (COCKPIT_HOME unset) the root keeps serving the interview bot.
    if _cockpit_home():
        return send_from_directory("static", "cockpit-home.html")
    # Render (no COCKPIT_HOME): the interview lives on cockpit now — bounce there.
    if os.environ.get("RENDER"):
        return _redirect_to_cockpit_interview()
    return send_from_directory("static", "index.html")


@app.route("/interview")
def interview_page():
    # Stable URL for the interview bot. On the cockpit domain this is the canonical
    # home. On Render the interview has moved to cockpit, so redirect (preserving ?s=).
    if os.environ.get("RENDER") and not _cockpit_home():
        return _redirect_to_cockpit_interview()
    return send_from_directory("static", "index.html")


# ---------------------------------------------------------------------------
# Company Brief automation (Hub M9): serve generated briefs + generate on demand
# ---------------------------------------------------------------------------

@app.route("/b/<path:fname>", methods=["GET"])
def serve_brief(fname):
    """Serve a generated brief HTML by its unguessable token filename. No directory index;
    only exact <token>.html names resolve. Reached at cockpit.../b/<token>.html and (once
    the subdomain proxies here) briefs.automatisierbar.ch/b/<token>.html."""
    if not (fname.endswith(".html") and _BRIEF_TOKEN_RE.match(fname[:-5])):
        return ("Not found", 404)
    if not os.path.isfile(os.path.join(BRIEFS_DIR, fname)):
        return ("Brief nicht gefunden.", 404)
    return send_from_directory(BRIEFS_DIR, fname)


def _brief_file(name: str) -> str:
    return os.path.join(BRIEFS_DIR, name)


def _write_brief_file(name: str, content: str) -> None:
    os.makedirs(BRIEFS_DIR, exist_ok=True)
    with open(_brief_file(name), "w", encoding="utf-8") as fh:
        fh.write(content)


def _run_brief_generation(token: str, lead_page_id: str, brief_type):
    """Background worker body: generate the brief and persist its result as sidecar files
    (<token>.html + .meta.json on success, .skip on a normal skip, .error on failure). Runs in
    a daemon thread because generation takes minutes (web_search + a large completion)."""
    import json as _json
    import brief_generator as bg
    try:
        result = bg.generate(lead_page_id, brief_type)
        _write_brief_file(f"{token}.html", result["html"])
        _write_brief_file(f"{token}.meta.json", _json.dumps({
            "firma": result["firma"], "brief_type": result["brief_type"],
            "summary": result["summary"],
        }))
    except ValueError as e:
        # No brief for this stage / lead not found — a normal skip, not an error.
        _write_brief_file(f"{token}.skip", str(e)[:500])
    except Exception as e:  # noqa: BLE001
        app.logger.exception("brief generation failed")
        _write_brief_file(f"{token}.error", str(e)[:500])


@app.route("/api/brief/generate", methods=["POST"])
def brief_generate():
    """Kick off async company-brief generation. Called by the Hub's M9 brief worker
    (X-Brief-Secret). Body: {lead_page_id, brief_type?, appointment_id?}. Returns 202 with a
    token + the eventual brief_url + status_url immediately; the caller polls
    GET /api/brief/status/<token> until done (generation takes minutes). brief_type is
    auto-derived from the lead's pipeline stage when omitted."""
    if not _brief_auth_ok():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    lead_page_id = str(data.get("lead_page_id", "")).strip()
    brief_type = (str(data.get("brief_type", "")).strip() or None)
    if not lead_page_id:
        return jsonify({"error": "lead_page_id required"}), 400
    if brief_type and brief_type not in ("wf", "pilot", "general"):
        return jsonify({"error": "brief_type must be wf|pilot|general"}), 400

    import threading
    import uuid as _uuid
    token = _uuid.uuid4().hex
    try:
        os.makedirs(BRIEFS_DIR, exist_ok=True)
    except OSError as e:
        return jsonify({"error": f"briefs dir not writable: {e}"}), 500
    threading.Thread(target=_run_brief_generation, args=(token, lead_page_id, brief_type),
                     daemon=True).start()
    return jsonify({
        "ok": True,
        "token": token,
        "status": "pending",
        "brief_url": f"{BRIEF_BASE_URL}/b/{token}.html",
        "status_url": f"{BRIEF_BASE_URL}/api/brief/status/{token}",
    }), 202


@app.route("/api/brief/status/<token>", methods=["GET"])
def brief_status(token):
    """Poll a brief's generation status. done -> brief_url (+ firma/type/summary); skip/error ->
    reason; else pending. Same shared-secret auth as generate."""
    if not _brief_auth_ok():
        return jsonify({"error": "Unauthorized"}), 401
    if not _BRIEF_TOKEN_RE.match(token or ""):
        return jsonify({"error": "bad token"}), 400
    import json as _json
    if os.path.isfile(_brief_file(f"{token}.html")):
        meta = {}
        try:
            with open(_brief_file(f"{token}.meta.json"), encoding="utf-8") as fh:
                meta = _json.load(fh)
        except (OSError, ValueError):
            pass
        return jsonify({"status": "done", "brief_url": f"{BRIEF_BASE_URL}/b/{token}.html", **meta})
    for state in ("skip", "error"):
        p = _brief_file(f"{token}.{state}")
        if os.path.isfile(p):
            try:
                with open(p, encoding="utf-8") as fh:
                    reason = fh.read()[:500]
            except OSError:
                reason = ""
            return jsonify({"status": state, "reason": reason})
    return jsonify({"status": "pending"})


# ---------------------------------------------------------------------------
# Leads search
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------

@app.route("/api/leads/search", methods=["GET"])
def search_leads():
    q = (request.args.get("q") or "").strip()
    if len(q) < 2:
        return jsonify([])
    try:
        from notion_session import search_leads as _search
        results = _search(q)
        return jsonify(results)
    except Exception as e:
        app.logger.error("search_leads error: %s", e)
        return jsonify([])


# ---------------------------------------------------------------------------
# Feature B: operator overview of recently-conducted interviews.
# Lists ALL prospect data, so it's gated behind the cockpit operator login
# (cookie via /api/cockpit/login, or X-API-Key for scripts/n8n).
# ---------------------------------------------------------------------------

@app.route("/api/interviews", methods=["GET"])
def list_interviews_route():
    if not _cockpit_auth_ok():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        from notion_session import list_interviews, available as notion_available
        if not notion_available():
            return jsonify({"interviews": [], "truncated": False, "note": "notion not configured"})
        return jsonify(list_interviews(100))
    except Exception as e:
        app.logger.error("list_interviews error: %s", e)
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Survey API
# ---------------------------------------------------------------------------

@app.route("/api/session/start", methods=["POST"])
def start_session():
    data = request.get_json(silent=True) or {}
    context = (data.get("context") or "").strip()
    if not context:
        return jsonify({"error": "context required"}), 400
    if len(context) > MAX_CONTEXT_CHARS:
        return jsonify({"error": f"context too long (max {MAX_CONTEXT_CHARS} chars)"}), 400

    lead_page_id = (data.get("lead_page_id") or "").strip() or None

    # Interviewer = who conducted this interview. Drives per-role Telegram routing
    # downstream when the build pipeline ships. Allowed values: Joaquin / Nico / Tej / Patrik.
    # Default Joaquin (until the frontend exposes a selector).
    interviewer_raw = (data.get("interviewer") or "").strip() or "Joaquin"
    if interviewer_raw not in ("Joaquin", "Nico", "Tej", "Patrik"):
        interviewer_raw = "Joaquin"

    try:
        from claude_client import evaluate_context
        from notion_session import create_session, update_session, available as notion_available

        session_id = create_session(context, lead_page_id=lead_page_id)

        result = evaluate_context(context)
        questions = result.get("questions", [])

        if notion_available():
            update_session(session_id, {
                "current_questions": questions,
                "round": 1,
                "lead_page_id": lead_page_id,
                "interviewer": interviewer_raw,
            })

        return jsonify({
            "session_id": session_id,
            "round": 1,
            "status": result.get("status", "needs_process_selection"),
            "questions": questions,
        })

    except Exception as e:
        app.logger.error("start_session error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/session/<session_id>", methods=["GET"])
def get_session(session_id):
    if not _valid_session_id(session_id):
        return jsonify({"error": "invalid session id"}), 400
    try:
        from notion_session import get_session as _get, available as notion_available
        if not notion_available():
            return jsonify({"error": "session not found"}), 404

        state = _get(session_id)
        if not state:
            return jsonify({"error": "session not found"}), 404

        return jsonify(state)

    except Exception as e:
        app.logger.error("get_session error: %s", e)
        return jsonify({"error": str(e)}), 500


def _write_payoff_safely(lead_page_id, session_id, *, context, all_qa, roi,
                          process_map, process_map_notes, extra_context, attachments,
                          process_map_skipped=False, assumptions=None):
    """Spawn a background thread that generates the Claude Code prompt and appends
    the payoff (mermaid + table + code block) to the lead's Notion page.

    Threaded because the prompt generation is a 25–40s Sonnet call — it would blow
    past Render's gunicorn worker timeout if run inline. The user-facing /answers
    response returns immediately; the payoff lands on the Notion page ~30–60s later.
    Idempotent: write_payoff_to_page skips if the heading already exists, so a
    duplicate /answers complete (e.g. user double-submits) doesn't duplicate the page.
    """
    import threading

    def _worker():
        try:
            from claude_client import generate_claude_code_prompt, classify_process_map_automatability
            from notion_session import (
                write_payoff_to_page, get_lead_by_page_id, update_session,
                write_additional_automations_to_page, get_session as _get_state,
            )

            lead_info = None
            try:
                lead_info = get_lead_by_page_id(lead_page_id)
            except Exception as e:
                app.logger.warning("payoff: get_lead_by_page_id failed: %s", e)

            # Classify each step's automatability — drives mermaid colors + table reasoning.
            classification = []
            if process_map:
                try:
                    classification = classify_process_map_automatability(
                        process_map, context=context,
                    )
                    update_session(session_id, {"process_map_classification": classification})
                except Exception as e:
                    app.logger.warning("payoff: classification failed: %s", e)

            prompt_text = generate_claude_code_prompt(
                context, all_qa, roi or {}, lead_info,
                process_map=process_map,
                process_map_notes=process_map_notes,
                process_map_skipped=process_map_skipped,
                extra_context=extra_context,
                attachments=attachments,
                assumptions=assumptions or [],
            )
            # Cache the prompt in session state so /prompt returns instantly when
            # the user clicks "Claude Code Prompt" instead of re-running the 30 s LLM call.
            try:
                update_session(session_id, {"claude_code_prompt": prompt_text})
            except Exception as e:
                app.logger.warning("payoff: prompt cache write failed: %s", e)

            wrote = write_payoff_to_page(
                lead_page_id,
                process_map=process_map or [],
                process_map_notes=process_map_notes or "",
                claude_code_prompt=prompt_text or "",
                classification=classification,
            )
            app.logger.info("payoff written for session %s (lead %s): %s",
                            session_id, lead_page_id, wrote)

            # OTHER automation ideas captured mid-interview → actionable follow-up
            # section on the lead page (idempotent, separate from the build spec).
            try:
                fresh = _get_state(session_id) or {}
                write_additional_automations_to_page(
                    lead_page_id, fresh.get("additional_automations") or []
                )
            except Exception as e:
                app.logger.warning("payoff: additional_automations page write failed: %s", e)

            # Build-Pipeline dispatch is now MANUAL via POST /api/session/<id>/dispatch_build —
            # users hit a button on the completion screen to send the brief to the agent team.
            # No auto-fire from the payoff thread anymore. Confirmation-before-dispatch was an
            # explicit product decision (2026-05-15) so an operator can sanity-check the
            # generated prompt before burning agent compute.
        except Exception as e:
            app.logger.error("payoff write failed (non-fatal) for session %s: %s",
                             session_id, e)

    threading.Thread(target=_worker, name=f"payoff-{session_id[:8]}", daemon=True).start()


@app.route("/api/session/<session_id>/answers", methods=["POST"])
def submit_answers(session_id):
    if not _valid_session_id(session_id):
        return jsonify({"error": "invalid session id"}), 400
    data = request.get_json(silent=True) or {}
    round_num = data.get("round", 1)
    answers = data.get("answers", [])

    _answer_err = _validate_answer_list(answers)
    if _answer_err:
        return jsonify({"error": _answer_err}), 400

    try:
        from claude_client import evaluate_answers
        from notion_session import (
            get_session as _get, update_session,
            write_qa_to_page, write_roi_to_page,
            available as notion_available,
        )

        context = ""
        all_qa = []
        lead_page_id = None
        process_map = []
        process_map_notes = ""
        process_map_skipped = False
        extra_context = ""
        attachments = []
        # Question definitions shown for THIS round — stored alongside the answers so
        # the frontend can re-render a past round as an editable form (Feature C:
        # forward/back navigation with editing).
        round_questions = []

        if notion_available():
            state = _get(session_id)
            if state:
                context = state.get("context", "")
                all_qa = state.get("all_qa", [])
                lead_page_id = state.get("lead_page_id")
                process_map = state.get("process_map", []) or []
                process_map_notes = state.get("process_map_notes", "") or ""
                process_map_skipped = bool(state.get("process_map_skipped", False))
                extra_context = state.get("extra_context", "") or ""
                attachments = state.get("attachments", []) or []
                round_questions = state.get("current_questions", []) or []

        context = context or data.get("context", "")
        all_qa.append({"round": round_num, "qa": answers, "questions": round_questions})

        # Write this round's Q&A to the lead's Notion page
        if lead_page_id:
            write_qa_to_page(lead_page_id, round_num, answers)

        result = evaluate_answers(
            context, all_qa,
            process_map=process_map,
            process_map_notes=process_map_notes,
            process_map_skipped=process_map_skipped,
            extra_context=extra_context,
            attachments=attachments,
        )

        if result.get("status") == "complete":
            roi = result.get("roi", {})
            assumptions = result.get("assumptions", [])

            if notion_available():
                update_session(session_id, {
                    "status": "complete",
                    "all_qa": all_qa,
                    "current_questions": [],
                    "roi": roi,
                    "assumptions": assumptions,
                })

            # Write ROI to lead page + the end-of-interview payoff
            # (process map + mermaid + table + Claude Code prompt as a code block).
            if lead_page_id:
                write_roi_to_page(lead_page_id, roi, assumptions)
                _write_payoff_safely(
                    lead_page_id, session_id,
                    context=context, all_qa=all_qa, roi=roi,
                    process_map=process_map, process_map_notes=process_map_notes,
                    process_map_skipped=process_map_skipped,
                    extra_context=extra_context, attachments=attachments,
                    assumptions=assumptions or [],
                )

            return jsonify({
                "status": "complete",
                "assumptions": assumptions,
                "roi": roi,
            })

        elif result.get("status") == "ready_for_process_map":
            # LLM has identified the process + main tools; transition the user to the
            # process-map screen now. Q&A continues afterwards with the map in context.
            process_name = (result.get("process_name") or "").strip()
            tools_identified = result.get("tools_identified") or []
            if not isinstance(tools_identified, list):
                tools_identified = []
            if notion_available():
                update_session(session_id, {
                    "all_qa": all_qa,
                    "current_questions": [],
                    "round": round_num,
                    "process_name": process_name,
                    "tools_identified": tools_identified,
                })
            return jsonify({
                "status": "ready_for_process_map",
                "process_name": process_name,
                "tools_identified": tools_identified,
                "round": round_num,
                "assumptions": result.get("assumptions", []),
            })

        else:
            next_questions = result.get("questions", [])
            # Guard: if Claude returns needs_more but no questions, treat as complete
            # to avoid trapping the user in a no-op round.
            if not next_questions:
                fallback_roi = result.get("roi") or {}
                fallback_assumptions = result.get("assumptions", [])
                if notion_available():
                    update_session(session_id, {
                        "status": "complete",
                        "all_qa": all_qa,
                        "current_questions": [],
                        "roi": fallback_roi,
                        "assumptions": fallback_assumptions,
                    })
                if lead_page_id:
                    write_roi_to_page(lead_page_id, fallback_roi, fallback_assumptions)
                    _write_payoff_safely(
                        lead_page_id, session_id,
                        context=context, all_qa=all_qa, roi=fallback_roi,
                        process_map=process_map, process_map_notes=process_map_notes,
                        process_map_skipped=process_map_skipped,
                        extra_context=extra_context, attachments=attachments,
                        assumptions=fallback_assumptions or [],
                    )
                return jsonify({
                    "status": "complete",
                    "assumptions": fallback_assumptions,
                    "roi": fallback_roi,
                })
            next_round = round_num + 1
            if notion_available():
                update_session(session_id, {
                    "all_qa": all_qa,
                    "current_questions": next_questions,
                    "round": next_round,
                })
            return jsonify({
                "status": "needs_more",
                "round": next_round,
                "questions": next_questions,
                "assumptions": result.get("assumptions", []),
            })

    except Exception as e:
        app.logger.error("submit_answers error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/session/<session_id>/pdf", methods=["GET"])
def session_pdf(session_id):
    if not _valid_session_id(session_id):
        return jsonify({"error": "invalid session id"}), 400
    try:
        from claude_client import generate_spec_summary
        from notion_session import get_session as _get, available as notion_available
        from generate_pdf import generate

        context = request.args.get("context", "")
        all_qa = []
        process_map = []
        process_map_notes = ""
        process_map_skipped = False
        extra_context = ""
        attachments = []
        assumptions = []

        if notion_available():
            state = _get(session_id)
            if state:
                context = state.get("context", context)
                all_qa = state.get("all_qa", [])
                process_map = state.get("process_map", []) or []
                process_map_notes = state.get("process_map_notes", "") or ""
                process_map_skipped = bool(state.get("process_map_skipped", False))
                extra_context = state.get("extra_context", "") or ""
                attachments = state.get("attachments", []) or []
                assumptions = state.get("assumptions", []) or []

        spec_text = generate_spec_summary(
            context, all_qa,
            process_map=process_map,
            process_map_notes=process_map_notes,
            process_map_skipped=process_map_skipped,
            extra_context=extra_context,
            attachments=attachments,
            assumptions=assumptions,
        )

        questions = {}
        for round_data in all_qa:
            rn = round_data["round"]
            cat = f"Runde {rn}"
            questions[cat] = []
            for item in round_data.get("qa", []):
                q = item.get("question", "")
                a = item.get("answer", "nicht beantwortet")
                questions[cat].append(f"{q}\n→ {a}")

        if not questions:
            questions = {"Spezifikation": [spec_text[:500]]}

        import datetime
        pdf_data = {
            "type": "spec",
            "client_problem": context[:300] if context else "Automatisierungsprojekt",
            "questions": questions,
            "metadata": {"date": datetime.date.today().isoformat()},
        }

        path = generate(pdf_data)
        return send_file(
            path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"automatisierung_spezifikation_{session_id[:8]}.pdf",
        )

    except Exception as e:
        app.logger.error("session_pdf error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/session/<session_id>/prompt", methods=["GET"])
def session_prompt(session_id):
    if not _valid_session_id(session_id):
        return jsonify({"error": "invalid session id"}), 400
    try:
        from claude_client import generate_claude_code_prompt
        from notion_session import get_session as _get, update_session, available as notion_available

        context = ""
        all_qa = []
        roi = {}
        lead_page_id = None
        process_map = []
        process_map_notes = ""
        process_map_skipped = False
        extra_context = ""
        attachments = []
        assumptions = []
        cached_prompt = None

        if notion_available():
            state = _get(session_id)
            if state:
                context = state.get("context", "")
                all_qa = state.get("all_qa", [])
                roi = state.get("roi", {}) or {}
                lead_page_id = state.get("lead_page_id")
                process_map = state.get("process_map", []) or []
                process_map_notes = state.get("process_map_notes", "") or ""
                process_map_skipped = bool(state.get("process_map_skipped", False))
                extra_context = state.get("extra_context", "") or ""
                attachments = state.get("attachments", []) or []
                assumptions = state.get("assumptions", []) or []
                cached_prompt = state.get("claude_code_prompt")

        # Fast path: prompt was cached by the background payoff thread (post-completion)
        # or by a prior /prompt call. Avoids paying for a second 30 s Sonnet call.
        if cached_prompt:
            return jsonify({"prompt": cached_prompt, "cached": True})

        # If the session is already complete, the background payoff thread is most likely
        # still generating the prompt (races with the user clicking the toggle). Poll the
        # cache for up to 40 s before falling back to a fresh generation. Cheaper than 2×
        # the LLM call, still well under gunicorn's 120 s worker timeout.
        from notion_session import get_session as _get_state
        if state and state.get("status") == "complete":
            import time as _t
            for _ in range(20):  # 20 × 2 s = 40 s max
                _t.sleep(2)
                fresh = _get_state(session_id) or {}
                if fresh.get("claude_code_prompt"):
                    return jsonify({"prompt": fresh["claude_code_prompt"], "cached": True})

        lead_info = None
        if lead_page_id:
            try:
                from notion_session import get_lead_by_page_id
                lead_info = get_lead_by_page_id(lead_page_id)
            except Exception as e:
                app.logger.error("get_lead_by_page_id failed: %s", e)

        prompt_text = generate_claude_code_prompt(
            context, all_qa, roi, lead_info,
            process_map=process_map,
            process_map_notes=process_map_notes,
            process_map_skipped=process_map_skipped,
            extra_context=extra_context,
            attachments=attachments,
            assumptions=assumptions,
        )
        # Cache for subsequent calls (page reload, "copy prompt" button, second viewer).
        if notion_available():
            try:
                update_session(session_id, {"claude_code_prompt": prompt_text})
            except Exception as e:
                app.logger.warning("prompt cache write failed: %s", e)

        return jsonify({"prompt": prompt_text, "cached": False})

    except Exception as e:
        app.logger.error("session_prompt error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/session/<session_id>/dispatch_build", methods=["POST"])
def dispatch_build(session_id):
    """Manual confirmation endpoint — fires the n8n Interview-to-Builder Dispatcher
    webhook so paperclip's CTO picks up the brief and starts the autonomous build.

    Called from the ROI screen's "An Build-Team senden" button. Idempotent — if
    already dispatched, returns the existing dispatch metadata.
    """
    if not _valid_session_id(session_id):
        return jsonify({"error": "invalid session id"}), 400

    webhook_url = os.environ.get("BUILD_DISPATCHER_WEBHOOK_URL", "").strip()
    if not webhook_url:
        return jsonify({
            "error": "Build-Dispatcher noch nicht konfiguriert. Setze BUILD_DISPATCHER_WEBHOOK_URL in der Render-Umgebung.",
            "configured": False,
        }), 503

    try:
        from notion_session import get_session as _get_state, update_session
        state = _get_state(session_id) or {}
    except Exception as e:
        app.logger.error("dispatch_build: get_session failed: %s", e)
        return jsonify({"error": f"session lookup failed: {e}"}), 500

    if not state:
        return jsonify({"error": "session not found"}), 404

    # Idempotency: refuse to re-dispatch unless explicitly forced.
    already_dispatched_at = state.get("build_dispatched_at")
    if already_dispatched_at and not (request.get_json(silent=True) or {}).get("force"):
        return jsonify({
            "status": "already_dispatched",
            "dispatched_at": already_dispatched_at,
            "build_issue_identifier": state.get("build_issue_identifier"),
            "build_issue_id": state.get("build_issue_id"),
        })

    prompt_text = state.get("claude_code_prompt")
    if not prompt_text:
        return jsonify({"error": "Kein Build-Prompt verfügbar — Interview noch nicht abgeschlossen?"}), 409

    # Gather metadata for the webhook payload
    lead_page_id = state.get("lead_page_id")
    lead_info = None
    if lead_page_id:
        try:
            from notion_session import get_lead_by_page_id
            lead_info = get_lead_by_page_id(lead_page_id)
        except Exception as e:
            app.logger.warning("dispatch_build: lead lookup failed: %s", e)

    lead_name = (lead_info or {}).get("firma") or \
                (lead_info or {}).get("name") or \
                (state.get("context", "") or "")[:40] or \
                session_id[:8]
    interviewer = state.get("interviewer") or "Joaquin"

    payload = {
        "session_id": session_id,
        "lead_page_id": lead_page_id,
        "lead_name": lead_name,
        "claude_code_prompt": prompt_text,
        "process_map": state.get("process_map") or [],
        "interviewer": interviewer,
    }

    try:
        import requests as _requests
        resp = _requests.post(webhook_url, json=payload, timeout=15)
    except Exception as e:
        app.logger.error("dispatch_build: webhook POST failed: %s", e)
        return jsonify({"error": f"webhook POST failed: {e}"}), 502

    if resp.status_code >= 400:
        app.logger.warning(
            "dispatch_build: webhook returned %s — body=%s",
            resp.status_code, resp.text[:300],
        )
        return jsonify({
            "error": f"Build-Pipeline antwortete {resp.status_code}",
            "detail": resp.text[:300],
        }), 502

    # Parse response — n8n dispatcher returns the paperclip Issue payload (id, identifier, etc.)
    try:
        ack = resp.json() if resp.content else {}
    except Exception:
        ack = {"raw": resp.text[:500]}

    # Persist dispatch state in session
    from datetime import datetime, timezone
    dispatched_at = datetime.now(timezone.utc).isoformat()
    build_issue_id = ack.get("id")
    build_issue_identifier = ack.get("identifier")
    try:
        update_session(session_id, {
            "build_dispatched_at": dispatched_at,
            "build_issue_id": build_issue_id,
            "build_issue_identifier": build_issue_identifier,
            "build_interviewer": interviewer,
        })
    except Exception as e:
        app.logger.warning("dispatch_build: session update failed (non-fatal): %s", e)

    app.logger.info(
        "dispatch_build: session=%s lead=%s issue=%s",
        session_id, lead_name, build_issue_identifier or "?",
    )
    return jsonify({
        "status": "dispatched",
        "dispatched_at": dispatched_at,
        "build_issue_id": build_issue_id,
        "build_issue_identifier": build_issue_identifier,
        "lead_name": lead_name,
        "interviewer": interviewer,
    })


# ---------------------------------------------------------------------------
# Process map (guided A→Z walkthrough — captured between context and Q&A rounds)
# ---------------------------------------------------------------------------

PROCESS_STEP_KEYS = ("step", "who", "action", "tool", "data_in", "data_out", "automatable")
PROCESS_AUTOMATABLE_VALUES = {"yes", "partial", "no"}


def _validate_process_step(item) -> tuple[bool, str]:
    if not isinstance(item, dict):
        return False, "Schritt muss ein Objekt sein"
    # Truncate over-long fields rather than reject — the user's free text shouldn't
    # die at a hard boundary they can't see.
    for key in PROCESS_STEP_KEYS:
        val = item.get(key)
        if val is None:
            continue
        if not isinstance(val, (str, int)):
            return False, f"Feld '{key}' muss Text oder Zahl sein"
    auto = (item.get("automatable") or "").lower()
    if auto and auto not in PROCESS_AUTOMATABLE_VALUES:
        return False, "automatable muss yes/partial/no sein"
    return True, ""


@app.route("/api/session/<session_id>/process_map", methods=["GET"])
def get_process_map(session_id):
    if not _valid_session_id(session_id):
        return jsonify({"error": "invalid session id"}), 400
    try:
        from notion_session import get_session as _get, available as notion_available
        if not notion_available():
            return jsonify({"steps": [], "notes": "", "skipped": False})
        state = _get(session_id) or {}
        return jsonify({
            "steps": state.get("process_map", []),
            "notes": state.get("process_map_notes", ""),
            "skipped": bool(state.get("process_map_skipped", False)),
        })
    except Exception as e:
        app.logger.error("get_process_map error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/session/<session_id>/process_map", methods=["POST"])
def post_process_map(session_id):
    if not _valid_session_id(session_id):
        return jsonify({"error": "invalid session id"}), 400
    data = request.get_json(silent=True) or {}
    raw_steps = data.get("steps", [])
    notes = (data.get("notes") or "")[:4000]
    skipped = bool(data.get("skipped", False))

    if not isinstance(raw_steps, list):
        return jsonify({"error": "steps must be a list"}), 400
    if len(raw_steps) > MAX_PROCESS_STEPS:
        return jsonify({"error": f"too many steps (max {MAX_PROCESS_STEPS})"}), 400

    cleaned = []
    for i, item in enumerate(raw_steps, start=1):
        ok, msg = _validate_process_step(item)
        if not ok:
            return jsonify({"error": f"Schritt {i}: {msg}"}), 400
        # Drop fully-empty rows silently (the UI prepopulates blank rows)
        if not any(str(item.get(k, "")).strip() for k in ("who", "action", "tool", "data_in", "data_out")):
            continue
        cleaned.append({
            "step": int(item.get("step") or len(cleaned) + 1),
            "who": str(item.get("who", ""))[:200],
            "action": str(item.get("action", ""))[:500],
            "tool": str(item.get("tool", ""))[:200],
            "data_in": str(item.get("data_in", ""))[:300],
            "data_out": str(item.get("data_out", ""))[:300],
            # V2: automatable is no longer collected from the user — AI infers it
            # at payoff time. Keep the field for backwards-compat (defaults "unknown").
            "automatable": (str(item.get("automatable") or "")).lower() or "unknown",
        })

    try:
        from notion_session import (
            update_process_map, update_session, get_session as _get,
            available as notion_available,
        )
        if not notion_available():
            return jsonify({"error": "notion not configured"}), 503
        if not update_process_map(session_id, cleaned, notes):
            return jsonify({"error": "session not found"}), 404
        update_session(session_id, {"process_map_skipped": bool(skipped)})

        # V2 (path B): if the user already answered identification rounds before
        # reaching the map, fire evaluate_answers now so the next batch of questions
        # is already in the response. Frontend shows them immediately. Path A skips
        # this — the stashed pendingQuestions from /session/start are used instead.
        state = _get(session_id) or {}
        all_qa = state.get("all_qa", []) or []
        if not all_qa:
            return jsonify({"ok": True, "steps": cleaned, "notes": notes, "skipped": skipped, "next": None})

        from claude_client import evaluate_answers
        result = evaluate_answers(
            state.get("context", ""), all_qa,
            process_map=cleaned,
            process_map_notes=notes,
            process_map_skipped=bool(skipped),
            extra_context=state.get("extra_context", "") or "",
            attachments=state.get("attachments", []) or [],
        )
        next_round = (state.get("round") or 0) + 1
        next_payload = {
            "status": result.get("status"),
            "round": next_round,
            "questions": result.get("questions", []),
            "assumptions": result.get("assumptions", []),
            "roi": result.get("roi", {}),
            "process_name": result.get("process_name", ""),
            "tools_identified": result.get("tools_identified", []),
        }
        # Persist whatever the LLM returned so resume picks it up.
        if result.get("status") == "complete":
            update_session(session_id, {
                "status": "complete",
                "current_questions": [],
                "roi": result.get("roi", {}),
                "assumptions": result.get("assumptions", []),
            })
            lead_page_id = state.get("lead_page_id")
            if lead_page_id:
                from notion_session import write_roi_to_page
                write_roi_to_page(lead_page_id, result.get("roi", {}), result.get("assumptions", []))
                _write_payoff_safely(
                    lead_page_id, session_id,
                    context=state.get("context", ""), all_qa=all_qa, roi=result.get("roi", {}),
                    process_map=cleaned, process_map_notes=notes,
                    process_map_skipped=bool(skipped),
                    extra_context=state.get("extra_context", "") or "",
                    attachments=state.get("attachments", []) or [],
                    assumptions=result.get("assumptions", []) or [],
                )
        elif result.get("questions"):
            update_session(session_id, {
                "current_questions": result.get("questions", []),
                "round": next_round,
            })
        return jsonify({"ok": True, "steps": cleaned, "notes": notes, "skipped": skipped, "next": next_payload})
    except Exception as e:
        app.logger.error("post_process_map error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/session/<session_id>/extract_map", methods=["POST"])
def extract_process_map(session_id):
    """V3 P1.4 — Extract a draft process-map from the client's narrative + attachments.

    Returns `{steps, confidence, missing}`. Frontend uses this to prefill the
    review screen instead of showing an empty form. If confidence is low or
    steps is empty, frontend falls back to V2 empty-rows behaviour.
    """
    if not _valid_session_id(session_id):
        return jsonify({"error": "invalid session id"}), 400
    try:
        from claude_client import extract_process_map_draft
        from notion_session import get_session as _get, update_session, available as notion_available
        if not notion_available():
            return jsonify({"error": "notion not configured"}), 503
        state = _get(session_id) or {}
        if not state:
            return jsonify({"error": "session not found"}), 404
        result = extract_process_map_draft(
            state.get("context", "") or "",
            attachments=state.get("attachments", []) or [],
            extra_context=state.get("extra_context", "") or "",
            all_qa=state.get("all_qa", []) or [],
        )
        # Cache so we don't re-extract on resume/refresh.
        try:
            update_session(session_id, {"process_map_draft": result})
        except Exception as e:
            app.logger.warning("extract_map cache write failed: %s", e)
        return jsonify(result)
    except Exception as e:
        app.logger.error("extract_process_map error: %s", e)
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Sidebar: free-text extras (notes pad)
# ---------------------------------------------------------------------------

@app.route("/api/session/<session_id>/extras", methods=["PATCH"])
def patch_extras(session_id):
    if not _valid_session_id(session_id):
        return jsonify({"error": "invalid session id"}), 400
    data = request.get_json(silent=True) or {}
    extras = (data.get("extra_context") or "")[:MAX_EXTRAS_CHARS]
    try:
        from notion_session import update_extras, available as notion_available
        if not notion_available():
            return jsonify({"error": "notion not configured"}), 503
        if not update_extras(session_id, extras):
            return jsonify({"error": "session not found"}), 404
        return jsonify({"ok": True, "length": len(extras)})
    except Exception as e:
        app.logger.error("patch_extras error: %s", e)
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Sidebar: "Weitere Automatisierungs-Ideen" — OTHER automations the interviewee
# mentions in passing. Captured as separate opportunities; NOT part of the current
# build spec (generate_claude_code_prompt never reads State). Autosaved by frontend.
# ---------------------------------------------------------------------------

@app.route("/api/session/<session_id>/additional_automations", methods=["PATCH"])
def patch_additional_automations(session_id):
    if not _valid_session_id(session_id):
        return jsonify({"error": "invalid session id"}), 400
    data = request.get_json(silent=True) or {}
    items = data.get("additional_automations", [])
    if not isinstance(items, list) or len(items) > MAX_ADDITIONAL_AUTOMATIONS:
        return jsonify({"error": f"expected a list of ≤{MAX_ADDITIONAL_AUTOMATIONS} items"}), 400
    try:
        from notion_session import (
            update_additional_automations,
            write_additional_automations_to_page,
            get_session as _get,
            available as notion_available,
        )
        if not notion_available():
            return jsonify({"error": "notion not configured"}), 503
        if not update_additional_automations(session_id, items):
            return jsonify({"error": "session not found"}), 404
        # If the interview already completed, the payoff worker has run — write the
        # ideas section now so late additions still land on the lead page (idempotent).
        try:
            state = _get(session_id) or {}
            if state.get("status") == "complete" and state.get("lead_page_id"):
                write_additional_automations_to_page(
                    state["lead_page_id"], state.get("additional_automations") or []
                )
        except Exception as e:
            app.logger.warning("late additional_automations page write failed: %s", e)
        return jsonify({"ok": True, "count": len(items)})
    except Exception as e:
        app.logger.error("patch_additional_automations error: %s", e)
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Feature C: edit an already-submitted round's answers (back-navigation).
# Replaces that round's answers in-place; does NOT re-run the LLM, re-branch later
# questions, or re-append page blocks. Edits flow into the build spec via all_qa
# when the interview completes.
# ---------------------------------------------------------------------------

@app.route("/api/session/<session_id>/round/<int:round_num>", methods=["PATCH"])
def patch_round(session_id, round_num):
    if not _valid_session_id(session_id):
        return jsonify({"error": "invalid session id"}), 400
    data = request.get_json(silent=True) or {}
    answers = data.get("answers", [])
    err = _validate_answer_list(answers)
    if err:
        return jsonify({"error": err}), 400
    try:
        from notion_session import update_round_answers, available as notion_available
        if not notion_available():
            return jsonify({"error": "notion not configured"}), 503
        if not update_round_answers(session_id, round_num, answers):
            return jsonify({"error": "session or round not found"}), 404
        return jsonify({"ok": True, "round": round_num})
    except Exception as e:
        app.logger.error("patch_round error: %s", e)
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Sidebar: file attachments (extract + persist)
# ---------------------------------------------------------------------------

@app.route("/api/session/<session_id>/attachment", methods=["POST"])
def upload_attachment(session_id):
    """File upload + per-stage wall-clock timing logs.

    Logs `[upload-timing] sid=... file=... size=... stage=multipart_read elapsed=Xs |
                          stage=extract elapsed=Xs | stage=notion_write elapsed=Xs | total=Xs`
    so future slow paths surface in Render logs without re-instrumentation."""
    import time as _t
    t_start = _t.perf_counter()

    if not _valid_session_id(session_id):
        return jsonify({"error": "invalid session id"}), 400

    f = request.files.get("file")
    if not f:
        return jsonify({"error": "file field missing (multipart/form-data)"}), 400

    filename = f.filename or "upload"
    mime = f.mimetype or ""

    t_multipart = _t.perf_counter()
    content = f.read()
    multipart_elapsed = _t.perf_counter() - t_multipart

    if not content:
        return jsonify({"error": "leere Datei"}), 400
    if len(content) > MAX_ATTACHMENT_BYTES:
        return jsonify({"error": f"Datei zu gross (max {MAX_ATTACHMENT_BYTES // (1024*1024)} MB)"}), 413

    size_mb = len(content) / (1024 * 1024)

    try:
        from file_extract import extract, is_allowed
        if not is_allowed(filename, mime):
            return jsonify({"error": f"Dateityp nicht erlaubt: {filename}"}), 415
        t_extract = _t.perf_counter()
        result = extract(filename, content, mime)
        extract_elapsed = _t.perf_counter() - t_extract
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.error("attachment extract error: %s", e)
        return jsonify({"error": "Extraktion fehlgeschlagen"}), 500

    attachment = {
        "filename": filename,
        "mime": mime,
        "size": len(content),
        "kind": result.get("kind", "text"),
        "extracted_text": result["text"],
    }
    try:
        from notion_session import add_attachment, available as notion_available
        if not notion_available():
            return jsonify({"error": "notion not configured"}), 503
        t_notion = _t.perf_counter()
        status = add_attachment(session_id, attachment)
        notion_elapsed = _t.perf_counter() - t_notion

        total_elapsed = _t.perf_counter() - t_start
        print(
            f"[upload-timing] sid={session_id[:8]} file={filename!r} "
            f"size={size_mb:.2f}MB kind={attachment['kind']} "
            f"stage=multipart_read elapsed={multipart_elapsed:.2f}s | "
            f"stage=extract elapsed={extract_elapsed:.2f}s | "
            f"stage=notion_write elapsed={notion_elapsed:.2f}s | "
            f"total={total_elapsed:.2f}s ok={status.get('ok')}",
            flush=True,
        )

        if not status.get("ok"):
            code = 413 if status.get("reason") in ("state_full", "too_many") else 400
            return jsonify({"error": status.get("message", "Konnte nicht hinzufügen")}), code
        preview = attachment["extracted_text"][:300]
        return jsonify({
            "ok": True,
            "filename": filename,
            "size": attachment["size"],
            "kind": attachment["kind"],
            "preview": preview,
            "warning": result.get("warning"),
            "count": status.get("count", 1),
            "timing": {
                "multipart_read_s": round(multipart_elapsed, 3),
                "extract_s": round(extract_elapsed, 3),
                "notion_write_s": round(notion_elapsed, 3),
                "total_s": round(total_elapsed, 3),
            },
        })
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        app.logger.error("attachment persist error: %s", e)
        return jsonify({"error": "Speichern fehlgeschlagen"}), 500


@app.route("/api/session/<session_id>/attachment/<int:idx>", methods=["DELETE"])
def delete_attachment(session_id, idx):
    if not _valid_session_id(session_id):
        return jsonify({"error": "invalid session id"}), 400
    try:
        from notion_session import remove_attachment, available as notion_available
        if not notion_available():
            return jsonify({"error": "notion not configured"}), 503
        if not remove_attachment(session_id, idx):
            return jsonify({"error": "attachment or session not found"}), 404
        return jsonify({"ok": True})
    except Exception as e:
        app.logger.error("delete_attachment error: %s", e)
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# LinkedIn Engagement Bot
#
# DELIBERATE FALLBACK — DO NOT DELETE. The live engagement path runs entirely
# inside the n8n LinkedIn Engagement Bot (voice prompt embedded in a Code node).
# These /api/linkedin/* endpoints are kept as a backup for when n8n cloud is
# unavailable; they are smoke-tested but not on the production hot path. See
# decisions/log.md (2026-05-02 "LinkedIn Engagement Bot: full n8n architecture,
# Render endpoints kept as backup"). prompts/linkedin_voice.md is the canonical
# prompt source for both this path and the n8n copy
# (drift guard: tools/check_linkedin_prompt_sync.py).
# ---------------------------------------------------------------------------

@app.route("/api/linkedin/comments", methods=["POST"])
def linkedin_comments():
    if not _auth_ok():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    try:
        from linkedin_comment_gen import generate_from_text, generate_from_image
        if data.get("image_b64"):
            result = generate_from_image(
                data["image_b64"],
                data.get("media_type", "image/jpeg"),
            )
        else:
            post_text = (data.get("post_text") or "").strip()
            if not post_text:
                return jsonify({"error": "post_text or image_b64 required"}), 400
            result = generate_from_text(post_text)
        return jsonify(result)
    except Exception as e:
        app.logger.error("linkedin_comments error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/linkedin/leads-top20", methods=["GET"])
def linkedin_leads_top20():
    if not _auth_ok():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        from notion_linkedin import top20_leads, format_top20_markdown
        leads = top20_leads()
        return jsonify({
            "count": len(leads),
            "markdown": format_top20_markdown(leads),
            "leads": leads,
        })
    except Exception as e:
        app.logger.error("linkedin_leads_top20 error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/linkedin/log", methods=["POST"])
def linkedin_log():
    if not _auth_ok():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    try:
        from notion_linkedin import log_activity
        page = log_activity(
            typ=data.get("typ", "Comment"),
            post_summary=data.get("post_summary", ""),
            branche=data.get("branche", "Andere"),
            variant=data.get("variant", "keine"),
            comment_text=data.get("comment_text", ""),
            post_source=data.get("post_source", ""),
            outcome=data.get("outcome", "offen"),
        )
        return jsonify({"ok": True, "page_id": page.get("id")})
    except Exception as e:
        app.logger.error("linkedin_log error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/linkedin/setup-db", methods=["POST"])
def linkedin_setup_db():
    if not _auth_ok():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    parent = (data.get("parent_page_id") or "").replace("-", "")
    if len(parent) != 32:
        return jsonify({"error": "parent_page_id must be a 32-char Notion page ID"}), 400
    formatted = f"{parent[0:8]}-{parent[8:12]}-{parent[12:16]}-{parent[16:20]}-{parent[20:32]}"
    try:
        from notion_linkedin import create_activity_db
        db_id = create_activity_db(formatted)
        return jsonify({
            "ok": True,
            "database_id": db_id,
            "next_step": f"Set NOTION_LINKEDIN_DB_ID={db_id} in Render env vars",
        })
    except Exception as e:
        app.logger.error("linkedin_setup_db error: %s", e)
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Script-Tuner — voice cold-call session store (file-based, self-contained)
# ---------------------------------------------------------------------------
import json as _json          # local alias to avoid colliding with lazy json imports
from pathlib import Path as _Path

VOICE_SESSIONS_DIR = _Path(__file__).resolve().parent / "data" / "voice_sessions"
VOICE_SYSTEM_PROMPT_PATH = _Path(__file__).resolve().parent / "prompts" / "voice_agent_system.txt"
VOICE_CHANGELOG_PATH = _Path(__file__).resolve().parent / "prompts" / "voice_agent_changelog.md"

MAX_VOICE_TRANSCRIPT_CHARS = 20000   # per-call transcript hard cap
MAX_VOICE_CALLS_PER_SESSION = 500    # sane upper bound per batch


def _voice_session_path(session_id: str) -> _Path:
    """Absolute path to a session's JSON file. Caller MUST have validated session_id
    via _valid_session_id first (defends against path traversal — the UUID regex
    forbids '/' and '.')."""
    return VOICE_SESSIONS_DIR / f"{session_id}.json"


def _load_voice_session(session_id: str) -> "dict | None":
    """Read + parse a session file. Returns None if missing/corrupt."""
    p = _voice_session_path(session_id)
    if not p.exists():
        return None
    try:
        return _json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        app.logger.error("voice session load failed (%s): %s", session_id, e)
        return None


def _save_voice_session(session: dict) -> None:
    """Atomic write: tmp file + os.replace. Creates the dir on first use."""
    VOICE_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    sid = session["session_id"]
    p = _voice_session_path(sid)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(_json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)


def _read_voice_system_prompt() -> str:
    """Current deployed system prompt (canonical machine-readable source)."""
    if not VOICE_SYSTEM_PROMPT_PATH.exists():
        raise RuntimeError(f"voice_agent_system.txt missing at {VOICE_SYSTEM_PROMPT_PATH}")
    return VOICE_SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


def _current_voice_version() -> str:
    """Parse the highest 'vN' from the changelog. Returns e.g. 'v3'. Falls back to
    'v3' if unparseable."""
    try:
        text = VOICE_CHANGELOG_PATH.read_text(encoding="utf-8")
        nums = [int(m) for m in re.findall(r"\*\*v(\d+)\b", text)]
        if nums:
            return f"v{max(nums)}"
    except Exception:
        pass
    return "v3"


def _append_voice_changelog(version, session_id, n_approve, n_edit, n_reject, n_skipped):
    """Prepend a Script-Tuner apply entry to voice_agent_changelog.md (newest-first)."""
    from datetime import date as _date
    entry = (
        f"- **{version} · {_date.today().isoformat()} · Script-Tuner apply · "
        f"session {session_id[:8]}** — {n_approve} übernommen, {n_edit} bearbeitet, "
        f"{n_reject} verworfen, {n_skipped} übersprungen. *Why:* operator review post-session. "
        f"(voice_agent_conversation.md prompt block + Current-version line: manuell nachziehen.)\n"
    )
    text = VOICE_CHANGELOG_PATH.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    # Insert as the first '- **' bullet (newest-first). Find first existing bullet.
    insert_at = next((i for i, ln in enumerate(lines) if ln.lstrip().startswith("- **")), len(lines))
    lines.insert(insert_at, entry)
    VOICE_CHANGELOG_PATH.write_text("".join(lines), encoding="utf-8")


def _compute_voice_stats(calls: list) -> dict:
    """Deterministic stats over the session's calls. Pure function — no LLM.

    Buckets each call as hot / borderline / cold and computes connect_rate plus an
    A/B split on disclose_ai. Never raises; tolerates missing keys.
    """
    total = len(calls)
    if total == 0:
        return {
            "calls": 0,
            "connect_rate": 0.0,
            "hot": 0, "borderline": 0, "cold": 0,
            "top_failure_mode": "—",
            "disclose_ab": {
                "disclosed":     {"calls": 0, "hot": 0, "hot_rate": 0.0},
                "not_disclosed": {"calls": 0, "hot": 0, "hot_rate": 0.0},
            },
        }

    _NOT_CONNECTED = {"direct-abwimmlung", "wrong-person", "no-answer", "voicemail"}

    def _bucket(call):
        outcome = str(call.get("outcome", "") or "").lower()
        analysis = call.get("analysis") or {}
        interest = str(analysis.get("interest_level", "") or "").lower()
        # connected?
        if analysis.get("connected") is True:
            connected = True
        elif analysis.get("connected") is False:
            connected = False
        else:
            connected = outcome not in _NOT_CONNECTED
        # bucket
        if "hot" in outcome or interest == "hot":
            bucket = "hot"
        elif "cold" in outcome or "skep" in outcome or interest == "none":
            bucket = "cold"
        elif connected:
            bucket = "borderline"
        else:
            # not connected and not clearly hot/cold → treat as cold (failure)
            bucket = "cold"
        return bucket, connected

    hot = borderline = cold = connected_count = 0
    failure_modes = {}
    for call in calls:
        bucket, connected = _bucket(call)
        if connected:
            connected_count += 1
        if bucket == "hot":
            hot += 1
        elif bucket == "borderline":
            borderline += 1
        else:
            cold += 1
        if bucket in ("borderline", "cold"):
            raw = str(call.get("outcome", "") or "").lower().strip()
            if raw:
                failure_modes[raw] = failure_modes.get(raw, 0) + 1

    top_failure_mode = "—"
    if failure_modes:
        top_failure_mode = max(failure_modes.items(), key=lambda kv: kv[1])[0]

    def _ab(partition):
        n = len(partition)
        h = sum(1 for c in partition if _bucket(c)[0] == "hot")
        return {"calls": n, "hot": h, "hot_rate": round(h / n, 2) if n else 0.0}

    disclosed = [c for c in calls if bool(c.get("disclose_ai"))]
    not_disclosed = [c for c in calls if not bool(c.get("disclose_ai"))]

    return {
        "calls": total,
        "connect_rate": round(connected_count / total, 2),
        "hot": hot, "borderline": borderline, "cold": cold,
        "top_failure_mode": top_failure_mode,
        "disclose_ab": {
            "disclosed": _ab(disclosed),
            "not_disclosed": _ab(not_disclosed),
        },
    }


@app.route("/api/voice/session/start", methods=["POST"])
def voice_session_start():
    if not _auth_ok():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    batch_meta = data.get("batch_meta") or {}
    if not isinstance(batch_meta, dict):
        return jsonify({"error": "batch_meta must be an object"}), 400
    try:
        import uuid
        from datetime import datetime, timezone
        session_id = str(uuid.uuid4())
        session = {
            "session_id": session_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "batch_meta": batch_meta,
            "calls": [],
            "report": None,
        }
        _save_voice_session(session)
        return jsonify({"session_id": session_id})
    except Exception as e:
        app.logger.error("voice_session_start error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/voice/session/<session_id>/call", methods=["POST"])
def voice_session_add_call(session_id):
    if not _auth_ok():
        return jsonify({"error": "Unauthorized"}), 401
    if not _valid_session_id(session_id):
        return jsonify({"error": "invalid session id"}), 400
    data = request.get_json(silent=True) or {}
    transcript = str(data.get("transcript") or "").strip()
    if not transcript:
        return jsonify({"error": "transcript required"}), 400
    if len(transcript) > MAX_VOICE_TRANSCRIPT_CHARS:
        transcript = transcript[:MAX_VOICE_TRANSCRIPT_CHARS]
    try:
        session = _load_voice_session(session_id)
        if session is None:
            return jsonify({"error": "session not found"}), 404
        if len(session.get("calls", [])) >= MAX_VOICE_CALLS_PER_SESSION:
            return jsonify({"error": "session full"}), 413
        analysis = data.get("analysis")
        if analysis is not None and not isinstance(analysis, dict):
            analysis = None
        call = {
            "lead_id": str(data.get("lead_id") or "")[:128],
            "firma": str(data.get("firma") or "")[:200],
            "branche": str(data.get("branche") or "")[:120],
            "disclose_ai": bool(data.get("disclose_ai", False)),
            "transcript": transcript,
            "outcome": str(data.get("outcome") or "")[:80],
            "analysis": analysis or {},
        }
        session.setdefault("calls", []).append(call)
        # Adding a call invalidates any cached report.
        session["report"] = None
        # Deliberate transcript-based evaluation drives BOTH the cockpit bucket and the
        # follow-up booking — instead of trusting Vapi's live structuredData (which
        # over-extracts interview_proposed/appointment on polite rejections).
        from claude_client import classify_call_outcome
        cls = classify_call_outcome(
            transcript,
            ended_reason=str(data.get("endedReason") or ""),
            duration_s=data.get("duration_s"))
        call["classified"] = cls.get("bucket")
        call["eval"] = cls
        _apply_classification_to_fired(session, call["lead_id"], cls,
                                       call_id=str(data.get("call_id") or "")[:128])
        followup_booked = _book_followup_from_eval(session, call["lead_id"], cls)
        # Write the extracted info back to the Lead-DB record (reached/interview flags,
        # top problem, schmerzscore, payment, summary, + advance Pipeline Stage by
        # outcome → which is also what the dedup filter reads).
        _enrich_lead(call["lead_id"], cls)
        _save_voice_session(session)
        return jsonify({"ok": True, "count": len(session["calls"]),
                        "bucket": cls.get("bucket"), "followup_booked": followup_booked})
    except Exception as e:
        app.logger.error("voice_session_add_call error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/voice/session/<session_id>", methods=["GET"])
def voice_session_get(session_id):
    if not _auth_ok():
        return jsonify({"error": "Unauthorized"}), 401
    if not _valid_session_id(session_id):
        return jsonify({"error": "invalid session id"}), 400
    try:
        session = _load_voice_session(session_id)
        if session is None:
            return jsonify({"error": "session not found"}), 404
        return jsonify(session)
    except Exception as e:
        app.logger.error("voice_session_get error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/voice/session/<session_id>/report", methods=["POST"])
def voice_session_report(session_id):
    if not _auth_ok():
        return jsonify({"error": "Unauthorized"}), 401
    if not _valid_session_id(session_id):
        return jsonify({"error": "invalid session id"}), 400
    force = bool((request.get_json(silent=True) or {}).get("force"))
    try:
        session = _load_voice_session(session_id)
        if session is None:
            return jsonify({"error": "session not found"}), 404
        calls = session.get("calls", [])
        if not calls:
            return jsonify({"error": "no calls in session"}), 409

        # Return cached report unless force=true.
        if session.get("report") and not force:
            return jsonify(session["report"])

        stats = _compute_voice_stats(calls)
        current_prompt = _read_voice_system_prompt()
        transcripts = [
            {
                "firma": c.get("firma", ""),
                "branche": c.get("branche", ""),
                "disclose_ai": c.get("disclose_ai", False),
                "outcome": c.get("outcome", ""),
                "analysis": c.get("analysis", {}),
                "transcript": c.get("transcript", ""),
            }
            for c in calls
        ]

        from claude_client import generate_script_suggestions
        suggestions = generate_script_suggestions(transcripts, current_prompt, stats)

        report = {"stats": stats, "suggestions": suggestions}
        session["report"] = report
        _save_voice_session(session)
        return jsonify(report)
    except Exception as e:
        app.logger.error("voice_session_report error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/voice/script/apply", methods=["POST"])
def voice_script_apply():
    if not _auth_ok():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    session_id = str(data.get("session_id") or "")
    if not _valid_session_id(session_id):
        return jsonify({"error": "invalid session id"}), 400
    decisions = data.get("decisions") or []
    if not isinstance(decisions, list):
        return jsonify({"error": "decisions must be a list"}), 400
    dry_run = data.get("dry_run", True)        # SAFETY: default True
    dry_run = True if dry_run is None else bool(dry_run)
    try:
        import difflib
        from datetime import datetime, timezone
        session = _load_voice_session(session_id)
        if session is None:
            return jsonify({"error": "session not found"}), 404
        report = session.get("report")
        if not report or not report.get("suggestions"):
            return jsonify({"error": "run report first"}), 409
        sugg_by_id = {s["id"]: s for s in report["suggestions"]}

        current = _read_voice_system_prompt()
        new_prompt = current
        skipped = []
        n_approve = n_edit = n_reject = 0
        for d in decisions:
            sid = d.get("suggestion_id")
            action = d.get("action")
            sugg = sugg_by_id.get(sid)
            if action == "reject":
                n_reject += 1
                continue
            if not sugg:
                skipped.append({"suggestion_id": sid, "reason": "unknown suggestion id"})
                continue
            target = sugg.get("current", "")
            if action == "approve":
                replacement = sugg.get("proposed", "")
                n_approve += 1
            elif action == "edit":
                replacement = str(d.get("edited_text") or "")
                n_edit += 1
            else:
                skipped.append({"suggestion_id": sid, "reason": f"unknown action {action!r}"})
                continue
            if target and target in new_prompt:
                new_prompt = new_prompt.replace(target, replacement, 1)
            else:
                skipped.append({"suggestion_id": sid, "reason": "current snippet not found"})

        diff = "".join(difflib.unified_diff(
            current.splitlines(keepends=True),
            new_prompt.splitlines(keepends=True),
            fromfile="voice_agent_system.txt (current)",
            tofile="voice_agent_system.txt (proposed)",
        ))

        if dry_run:
            return jsonify({
                "dry_run": True, "applied": False,
                "new_prompt": new_prompt, "diff": diff, "skipped": skipped,
            })

        # ---- LIVE PATH (only when dry_run is explicitly False) ----
        from vapi_client import update_system_prompt
        try:
            update_system_prompt(new_prompt)        # PATCHes live Vapi assistant
        except Exception as ve:
            app.logger.error("voice_script_apply: Vapi PATCH failed: %s", ve)
            return jsonify({"error": f"Vapi update failed: {ve}"}), 502

        # persist .txt atomically (only after the live PATCH succeeded)
        tmp = VOICE_SYSTEM_PROMPT_PATH.with_suffix(".txt.tmp")
        tmp.write_text(new_prompt, encoding="utf-8")
        os.replace(tmp, VOICE_SYSTEM_PROMPT_PATH)

        old = _current_voice_version()
        new_version = "v" + str(int(old[1:]) + 1)
        # prepend changelog entry (newest-first)
        _append_voice_changelog(new_version, session_id, n_approve, n_edit, n_reject, len(skipped))

        now = datetime.now(timezone.utc).isoformat()
        session["applied"] = {"version": new_version, "at": now, "decisions": decisions}
        session["report"] = report  # unchanged
        _save_voice_session(session)
        return jsonify({"version": new_version, "applied": True, "skipped": skipped})
    except Exception as e:
        app.logger.error("voice_script_apply error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/voice/tuner/<session_id>", methods=["GET"])
def voice_tuner_page(session_id):
    # No auth on the HTML shell (mirrors GET /). The page's JS authenticates its
    # data fetches with X-API-Key. session_id is consumed client-side from the URL.
    return send_from_directory("static", "tuner.html")


# ---------------------------------------------------------------------------
# Cold-Call Cockpit — live batch dialer + color barometers (Phase 1)
# ---------------------------------------------------------------------------
import threading as _threading

COCKPIT_BUDGET_PATH = _Path(__file__).resolve().parent / "data" / "cockpit_budget.json"
COLD_CALL_BUDGET_CHF = float(os.environ.get("COLD_CALL_BUDGET_CHF", "700") or 700)
_USD_TO_CHF = 0.90                       # rough; Vapi reports cost in USD
COCKPIT_DEFAULT_GAP_SEC = int(os.environ.get("COCKPIT_GAP_SEC", "30") or 30)
COCKPIT_MAX_CALLS = 200                  # hard cap per batch
WORKFLOW_D_DIAL_WEBHOOK = os.environ.get(
    "COLD_CALL_DIAL_WEBHOOK", "https://oojoaquin.app.n8n.cloud/webhook/cold-call-dial")
WORKFLOW_F_BOOK_WEBHOOK = os.environ.get(
    "COLD_CALL_BOOK_WEBHOOK", "https://oojoaquin.app.n8n.cloud/webhook/book-followup")
# Shared secret so only this app can trigger a booking (Workflow F drops requests
# whose body.secret doesn't match). Set the same value in F's Parse Slot node.
WORKFLOW_F_WEBHOOK_SECRET = os.environ.get("WORKFLOW_F_WEBHOOK_SECRET", "ab-followup-2026-x7k2")
# Phase 3 — durable per-batch analytics (survives Render restarts). Notion DB owned
# by the same integration NOTION_API_KEY uses, so writes are guaranteed.
VOICE_SESSIONS_DB_ID = os.environ.get(
    "VOICE_SESSIONS_DB_ID", "377bebb0-c2f9-8109-ad8b-c6aab96640dd")
# Phase 4 — durable per-call store (one row per fired call) feeding the Analyse page.
VOICE_CALLS_DB_ID = os.environ.get(
    "VOICE_CALLS_DB_ID", "37cbebb0-c2f9-818b-8c77-d635fbfd61cc")
CHANGELOG_PATH = _Path(__file__).resolve().parent / "prompts" / "voice_agent_changelog.md"

# Process-local cache of ENDED Vapi calls so status polls don't re-fetch finished calls.
_CALL_CACHE: dict = {}


def _now_iso() -> str:
    from datetime import datetime as _dt, timezone as _tz
    return _dt.now(_tz.utc).isoformat()


# ---- budget -----------------------------------------------------------------

def _seed_budget_from_notion() -> float:
    """Sum 'Cost CHF' across all Voice Sessions rows → USD, so the budget cap can
    survive Render's ephemeral disk (the local budget file is wiped on restart)."""
    try:
        key = os.environ.get("NOTION_API_KEY", "").strip()
        if not key:
            return 0.0
        import requests as _rq
        h = {"Authorization": f"Bearer {key}", "Notion-Version": "2022-06-28",
             "Content-Type": "application/json"}
        total_chf, cursor = 0.0, None
        while True:
            body = {"page_size": 100}
            if cursor:
                body["start_cursor"] = cursor
            r = _rq.post(f"https://api.notion.com/v1/databases/{VOICE_SESSIONS_DB_ID}/query",
                         headers=h, json=body, timeout=20)
            r.raise_for_status()
            data = r.json()
            for pg in data.get("results", []):
                v = (pg.get("properties", {}).get("Cost CHF") or {}).get("number")
                total_chf += float(v or 0)
            cursor = data.get("next_cursor")
            if not (data.get("has_more") and cursor):
                break
        return round(total_chf / _USD_TO_CHF, 4) if _USD_TO_CHF else 0.0
    except Exception as e:
        app.logger.error("budget seed from Notion failed: %s", e)
        return 0.0


def _cockpit_budget() -> dict:
    try:
        if COCKPIT_BUDGET_PATH.exists():
            d = _json.loads(COCKPIT_BUDGET_PATH.read_text(encoding="utf-8"))
            d.setdefault("spent_usd", 0.0)
            d.setdefault("counted", [])
            return d
    except Exception as e:
        app.logger.error("cockpit budget read failed: %s", e)
    # File missing (fresh process after a Render restart) → reseed spent from the
    # durable Notion session totals, then persist so we don't re-query every read.
    b = {"spent_usd": _seed_budget_from_notion(), "counted": []}
    try:
        COCKPIT_BUDGET_PATH.parent.mkdir(parents=True, exist_ok=True)
        COCKPIT_BUDGET_PATH.write_text(_json.dumps(b), encoding="utf-8")
    except Exception as e:
        app.logger.error("cockpit budget seed-write failed: %s", e)
    return b


def _add_cockpit_spend(call_id: str, usd) -> None:
    """Idempotent: add a call's cost to the running total ONCE (keyed by call_id)."""
    if not call_id or not usd:
        return
    try:
        b = _cockpit_budget()
        if call_id in b["counted"]:
            return
        b["spent_usd"] = round(float(b["spent_usd"]) + float(usd), 4)
        b["counted"].append(call_id)
        COCKPIT_BUDGET_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = COCKPIT_BUDGET_PATH.with_suffix(".json.tmp")
        tmp.write_text(_json.dumps(b), encoding="utf-8")
        os.replace(tmp, COCKPIT_BUDGET_PATH)
    except Exception as e:
        app.logger.error("cockpit spend update failed: %s", e)


_SPEND_CACHE = {"usd": None, "ts": 0.0}
_SPEND_TTL = 60


def _cockpit_spent_usd() -> float:
    """Total USD spent on the campaign = sum of every Vapi call's cost. Vapi is the
    source of truth — it survives Render restarts and counts calls the cockpit never
    polled (the old file/Notion tracker undercounted ~15×). Cached ~60s so the 4s
    poll + the runner's per-call budget check don't hammer the API."""
    import time as _t
    now = _t.time()
    if _SPEND_CACHE["usd"] is not None and (now - _SPEND_CACHE["ts"]) < _SPEND_TTL:
        return _SPEND_CACHE["usd"]
    try:
        import requests as _rq
        key = os.environ.get("VAPI_API_KEY", "").strip()
        if not key:
            return _SPEND_CACHE["usd"] or 0.0
        h = {"Authorization": f"Bearer {key}"}
        params = {"limit": 1000}
        total = 0.0
        for _ in range(20):                       # cap 20 pages (~20k calls)
            r = _rq.get("https://api.vapi.ai/call", headers=h, params=params, timeout=20)
            r.raise_for_status()
            calls = r.json()
            if not isinstance(calls, list) or not calls:
                break
            for c in calls:
                total += float(c.get("cost") or 0)
            if len(calls) < 1000:
                break
            oldest = min((c.get("createdAt") for c in calls if c.get("createdAt")), default=None)
            if not oldest:
                break
            params = {"limit": 1000, "createdAtLt": oldest}
        _SPEND_CACHE["usd"], _SPEND_CACHE["ts"] = round(total, 4), now
        return _SPEND_CACHE["usd"]
    except Exception as e:
        app.logger.error("_cockpit_spent_usd (Vapi) failed: %s", e)
        return _SPEND_CACHE["usd"] or 0.0


def _budget_remaining_chf() -> float:
    return round(COLD_CALL_BUDGET_CHF - _cockpit_spent_usd() * _USD_TO_CHF, 2)


# ---- eligibility (reuse Workflow D dry-run) + Notion mark-dialed -------------

def _fetch_eligible(max_calls: int, branche) -> list:
    """POST Workflow D's webhook in dry_run to reuse its exact eligibility logic.
    Returns [{lead_id, firma, branche, phone, kontakt_nachname, disclosure_line}].
    Best-effort; [] on failure (monkeypatched in tests)."""
    try:
        import requests as _rq
        body = {"max_calls": max_calls, "dry_run": True}
        if branche:
            body["branche"] = branche if isinstance(branche, list) else [branche]
        r = _rq.post(WORKFLOW_D_DIAL_WEBHOOK, json=body, timeout=60)
        r.raise_for_status()
        return r.json().get("eligible") or []
    except Exception as e:
        app.logger.error("cockpit _fetch_eligible failed: %s", e)
        return []


# ---- follow-up booking (fire Workflow F when Lena books a meeting) -----------

_CLASSIFYING: set = set()   # call_ids being classified by the poll fallback (process-local dedup)

# Per-session write locks: serialize the load->modify->save cycle so concurrent
# fallback-classify threads (and the runner appending fired entries) can't stomp each
# other's writes. _save_voice_session is atomic per-write but NOT serialized, so two
# threads that each load → change one row → save will silently lose one update.
_SESSION_LOCKS: dict = {}
_SESSION_LOCKS_GUARD = _threading.Lock()


def _session_lock(batch_id: str):
    """Return the (lazily created) write lock for one session/batch."""
    with _SESSION_LOCKS_GUARD:
        lk = _SESSION_LOCKS.get(batch_id)
        if lk is None:
            lk = _threading.Lock()
            _SESSION_LOCKS[batch_id] = lk
        return lk


def _apply_classification_to_fired(session: dict, lead_id: str, cls: dict,
                                   call_id: str = None) -> None:
    """Store the deliberate transcript classification on the matching cockpit fired
    entry. Matches by call_id FIRST (unique per call) and only falls back to lead_id
    (most recent still-unclassified, else any) so the live poll path — which always
    knows the exact call_id — can never mis-assign to a same-lead re-dial or silently
    drop on an empty lead_id. No-op for non-cockpit sessions; the barometer reads
    fired[i]['classified']."""
    ck = session.get("cockpit")
    if not ck:
        return
    fired = ck.get("fired") or []
    lead_id = (lead_id or "").strip()
    call_id = (call_id or "").strip()
    target = None
    # 1) exact, unique match on call_id (the reliable key)
    if call_id:
        for f in fired:
            if (f.get("call_id") or "").strip() == call_id:
                target = f
                break
    # 2) fall back to lead_id (most recent unclassified for this lead, else any)
    if target is None and lead_id:
        for f in fired:
            if (f.get("lead_id") or "").strip() == lead_id and not f.get("classified"):
                target = f          # most recent unclassified match for this lead
        if target is None:
            for f in fired:
                if (f.get("lead_id") or "").strip() == lead_id:
                    target = f
    if target is None:
        app.logger.warning(
            "transcript classification UNASSIGNED — no fired row for call_id=%r lead_id=%r (bucket=%r)",
            call_id, lead_id, cls.get("bucket"))
        return
    target["classified"] = cls.get("bucket")
    target["appt"] = {"agreed": cls.get("appointment_agreed") is True,
                      "day": cls.get("appointment_day") or "",
                      "time": cls.get("appointment_time") or ""}
    target["eval_summary"] = cls.get("summary") or ""
    # also persist the rich eval fields for the durable Voice Calls store
    target["top_problem"] = cls.get("top_problem") or ""
    target["schmerzscore"] = cls.get("schmerzscore")
    target["payment"] = cls.get("payment_discussed") is True
    target["interview_completed"] = cls.get("interview_completed") is True


def _fire_followup_booking(lead_id: str, availability: str, transcript_link: str = "") -> bool:
    """POST Workflow F's webhook to book the follow-up (calendar + team Telegram +
    Notion). Returns True ONLY on a confirmed 2xx, so the caller marks the lead
    booked only when it really succeeded; a failure is logged loudly and left
    un-booked so the next end-of-call delivery retries instead of silently losing it."""
    try:
        import requests as _rq
        r = _rq.post(WORKFLOW_F_BOOK_WEBHOOK, json={
            "lead_id": lead_id,
            "callback_availability": availability,
            "transcript_link": transcript_link or "",
            "secret": WORKFLOW_F_WEBHOOK_SECRET,
        }, timeout=25)
        r.raise_for_status()
        return True
    except Exception as e:
        app.logger.error("followup booking POST failed (%s): %s", lead_id, e)
        return False


def _book_followup_from_eval(session: dict, lead_id: str, cls: dict) -> bool:
    """Book a follow-up ONLY when the deliberate transcript evaluation confirms a real
    agreed appointment (cls['appointment_agreed']) — never off Vapi's raw live signal.
    Synchronous + success-gated; idempotent per lead via session['booked_followups']."""
    if cls.get("appointment_agreed") is not True:
        return False
    lead_id = (lead_id or "").strip()
    if not lead_id:
        return False
    booked = session.setdefault("booked_followups", [])
    if lead_id in booked:
        return False
    availability = (str(cls.get("appointment_day") or "").strip() + " "
                    + str(cls.get("appointment_time") or "").strip()).strip() or "(kein Slot genannt)"
    if _fire_followup_booking(lead_id, availability):
        booked.append(lead_id)
        return True
    return False


def _call_ended_seconds_ago(c: dict):
    e = c.get("endedAt")
    if not e:
        return None
    try:
        from datetime import datetime as _dt, timezone as _tz
        de = _dt.fromisoformat(str(e).replace("Z", "+00:00"))
        return (_dt.now(_tz.utc) - de).total_seconds()
    except Exception:
        return None


def _classify_fired_async(batch_id: str, call_id: str, lead_id: str,
                          transcript: str, ended_reason: str, dur) -> None:
    """Fallback classification (when the E webhook never delivered the transcript):
    classify from get_call's transcript, apply to the fired entry (matched by call_id —
    the reliable key the poll path always knows), gate booking, persist. The Claude call
    and Notion write-backs run OUTSIDE the per-session lock; only the load→apply→save of
    the session file is serialized, so parallel fallback threads can't stomp each other.
    Process-local dedup via _CLASSIFYING (cleared in finally)."""
    try:
        from claude_client import classify_call_outcome
        cls = classify_call_outcome(transcript, ended_reason=ended_reason, duration_s=dur)
        with _session_lock(batch_id):
            session = _load_voice_session(batch_id)
            if not session:
                return
            _apply_classification_to_fired(session, lead_id, cls, call_id=call_id)
            _book_followup_from_eval(session, lead_id, cls)   # rare; no-op unless an appt was agreed
            _save_voice_session(session)
        _enrich_lead(lead_id, cls)   # Notion write-back (here too, not just via E, so it's not single-point-of-failure)
        _sync_voice_calls(batch_id, only_call_id=call_id)   # durable per-call row, now final
    except Exception as e:
        app.logger.error("fallback classify failed (%s): %s", call_id, e)
    finally:
        _CLASSIFYING.discard(call_id)


def _maybe_spawn_fallback_classify(batch_id: str, f: dict, c: dict) -> None:
    """If a connected call has been ended >25s with a transcript but the E-webhook
    classification never arrived, classify it here so it doesn't sit on 'auswerten'."""
    call_id = f.get("call_id")
    if not call_id or f.get("classified") or call_id in _CLASSIFYING:
        return
    transcript = (c.get("transcript") or "").strip()
    if not transcript:
        return
    secs = _call_ended_seconds_ago(c)
    if secs is not None and secs < 25:
        return                      # give the E webhook a head start
    _CLASSIFYING.add(call_id)
    _threading.Thread(
        target=_classify_fired_async,
        args=(batch_id, call_id, f.get("lead_id") or "", transcript,
              str(c.get("endedReason") or ""), _call_duration_s(c)),
        name=f"classify-{call_id[:8]}", daemon=True).start()


def _sweep_unclassified(batch_id: str) -> None:
    """Synchronous catch-up at batch end. The live fallback only fires while the
    frontend polls _batch_status, so a call that ended after the operator closed the
    cockpit would sit on 'auswerten' forever — never classified, never written to the
    Voice Calls DB, never on the Analyse page. Classify any connected+ended fired call
    that still has no classification, in-thread. Bounded by the fired list; one Haiku
    call each. Reuses _classify_fired_async (which applies by call_id, enriches, syncs)."""
    session = _load_voice_session(batch_id)
    ck = (session or {}).get("cockpit") or {}
    for f in (ck.get("fired") or []):
        call_id = f.get("call_id")
        if not call_id or f.get("classified") or call_id in _CLASSIFYING:
            continue
        c = _fetch_call_cached(call_id)
        if _bucket_call(c, f) != "auswerten":
            continue                      # only connected+ended-with-transcript stragglers
        transcript = (c.get("transcript") or "").strip()
        if not transcript:
            continue
        _classify_fired_async(batch_id, call_id, f.get("lead_id") or "", transcript,
                              str(c.get("endedReason") or ""), _call_duration_s(c))


def _mark_lead_dialed(lead_id: str) -> None:
    """Best-effort post-dial Notion update: Contacted, Last contacted=now,
    Outreach Channel='AI Cold Call', Call Attempts +1. Non-fatal."""
    if not lead_id:
        return
    try:
        import requests as _rq
        key = os.environ.get("NOTION_API_KEY", "").strip()
        if not key:
            return
        h = {"Authorization": f"Bearer {key}", "Notion-Version": "2022-06-28",
             "Content-Type": "application/json"}
        g = _rq.get(f"https://api.notion.com/v1/pages/{lead_id}", headers=h, timeout=20)
        attempts = 0
        if g.ok:
            ca = ((g.json().get("properties") or {}).get("Call Attempts") or {}).get("number")
            attempts = int(ca) if isinstance(ca, (int, float)) else 0
        body = {"properties": {
            "Contacted": {"checkbox": True},
            "Last contacted": {"date": {"start": _now_iso()}},
            "Outreach Channel": {"select": {"name": "AI Cold Call"}},
            "Call Attempts": {"number": attempts + 1},
        }}
        _rq.patch(f"https://api.notion.com/v1/pages/{lead_id}", headers=h, json=body, timeout=20)
    except Exception as e:
        app.logger.error("_mark_lead_dialed failed (%s): %s", lead_id, e)


# Pipeline-Stage advancement by call outcome (also the dedup "done" marker D reads).
# followup → leave at "Problem Interview" (the booking handles the human callback;
# Outreach Gemacht?=true already removes it from the auto-dial pool).
_BUCKET_TO_STAGE = {"hot": "Workflow Interview", "cold": "OUT", "hangup": "OUT"}


def _enrich_lead(lead_id: str, cls: dict, call_start: str = None) -> None:
    """Best-effort post-call write-back to the Lead-DB record from the transcript
    evaluation: reached/interview flags, extracted problem/score, and the Pipeline
    Stage by outcome (which doubles as the dedup 'done' marker). Non-fatal. Does NOT
    touch Fit / Fit Score (separate workflow). Runs only for connected calls (a
    transcript reached the handler)."""
    if not lead_id:
        return
    try:
        import requests as _rq
        key = os.environ.get("NOTION_API_KEY", "").strip()
        if not key:
            return
        h = {"Authorization": f"Bearer {key}", "Notion-Version": "2022-06-28",
             "Content-Type": "application/json"}
        props = {
            "Outreach Gemacht?": {"checkbox": True},                       # they picked up
            "Interview Abgeschlossen": {"checkbox": bool(cls.get("interview_completed"))},
            "Gesprächsdatum": {"date": {"start": call_start or _now_iso()}},
        }
        tp = str(cls.get("top_problem") or "").strip()
        if tp:
            props["Top Problem"] = {"rich_text": [{"text": {"content": tp[:1900]}}]}
        sc = cls.get("schmerzscore")
        if isinstance(sc, (int, float)):
            props["Schmnerzscore (1-5)"] = {"number": sc}
        if cls.get("payment_discussed") is True:
            props["Zahlungsindikator"] = {"checkbox": True}
        summ = str(cls.get("summary") or "").strip()
        if summ:
            props["Context"] = {"rich_text": [{"text": {"content": summ[:1900]}}]}
        stage = _BUCKET_TO_STAGE.get(cls.get("bucket"))
        if stage:
            props["Pipeline Stage"] = {"status": {"name": stage}}
        _rq.patch(f"https://api.notion.com/v1/pages/{lead_id}", headers=h,
                  json={"properties": props}, timeout=20)
    except Exception as e:
        app.logger.error("_enrich_lead failed (%s): %s", lead_id, e)


# ---- live call status + barometer bucketing ---------------------------------

def _call_duration_s(c: dict):
    try:
        s, e = c.get("startedAt"), c.get("endedAt")
        if s and e:
            from datetime import datetime as _dt
            ds = _dt.fromisoformat(str(s).replace("Z", "+00:00"))
            de = _dt.fromisoformat(str(e).replace("Z", "+00:00"))
            return int((de - ds).total_seconds())
    except Exception:
        pass
    return None


def _fetch_call_cached(call_id: str) -> dict:
    if not call_id:
        return {}
    if call_id in _CALL_CACHE:
        return _CALL_CACHE[call_id]
    try:
        from vapi_client import get_call
        c = get_call(call_id)
    except Exception as e:
        app.logger.error("cockpit get_call failed (%s): %s", call_id, e)
        return {"status": "unknown", "_error": str(e)}
    if str(c.get("status")) == "ended":
        if len(_CALL_CACHE) >= 5000:           # bound memory; evict oldest (FIFO)
            try:
                _CALL_CACHE.pop(next(iter(_CALL_CACHE)))
            except StopIteration:
                pass
        _CALL_CACHE[call_id] = c
    return c


def _bucket_call(c: dict, f: dict = None) -> str:
    """Barometer bucket for a fired call. The deliberate transcript classification
    (f['classified']) is the source of truth for connected calls; Vapi flags are only
    used to detect 'not reached' (no transcript to evaluate).
      not ended              → live
      place_call errored     → noanswer (not reached)
      not connected / VM / NA→ noanswer (immediate; no transcript)
      connected + classified → hot | followup | cold | hangup
      connected, unclassified→ auswerten (evaluating)"""
    f = f or {}
    if f.get("error"):
        return "noanswer"
    if str(c.get("status")) != "ended":
        return "live"
    sd = ((c.get("analysis") or {}).get("structuredData") or {})
    ended = str(c.get("endedReason") or "").lower()
    dur = _call_duration_s(c)
    connected = sd.get("connected")
    if connected is None:
        connected = bool(c.get("transcript")) and (dur is None or dur >= 8)
    if (not connected) or "voicemail" in ended or "no-answer" in ended or "no_answer" in ended \
            or "did-not-answer" in ended:
        return "noanswer"     # grey — not reached
    classified = f.get("classified")
    if classified in ("hot", "followup", "cold", "hangup"):
        return classified     # the deliberate transcript evaluation
    return "auswerten"        # purple — connected + ended, transcript not yet evaluated


def _batch_status(session: dict) -> dict:
    ck = session.get("cockpit") or {}
    fired = ck.get("fired") or []
    buckets = {"hot": 0, "followup": 0, "cold": 0, "hangup": 0, "noanswer": 0, "auswerten": 0, "live": 0}
    rows, total_cost, connected = [], 0.0, 0
    for f in fired:
        cid = f.get("call_id")
        c = _fetch_call_cached(cid) if cid else {}
        status = str(c.get("status") or ("error" if f.get("error") else "queued"))
        bucket = _bucket_call(c, f)
        if bucket == "auswerten":               # transcript ready but no classification yet → fallback
            _maybe_spawn_fallback_classify(session.get("session_id"), f, c)
        buckets[bucket] = buckets.get(bucket, 0) + 1
        cost = float(c.get("cost") or 0)
        total_cost += cost
        sd = ((c.get("analysis") or {}).get("structuredData") or {})
        _conn = sd.get("connected")
        if _conn is None:                       # mirror _bucket_call's inference
            _dur = _call_duration_s(c)
            _conn = bool(c.get("transcript")) and (_dur is None or _dur >= 8)
        if _conn:
            connected += 1
        rows.append({
            "firma": f.get("firma"), "phone": f.get("phone"), "branche": f.get("branche"),
            "call_id": cid, "status": status, "bucket": bucket,
            "duration_s": _call_duration_s(c), "cost": round(cost, 4),
            "outcome": f.get("classified") or sd.get("interest_level") or "", "error": f.get("error"),
        })
    params = ck.get("params") or {}
    eligible_total = len(ck.get("eligible") or [])
    target = min(int(params.get("max_calls", 0)), eligible_total) if eligible_total else int(params.get("max_calls", 0))
    return {
        "batch_id": session.get("session_id"), "status": ck.get("status"),
        "thread_alive": ck.get("thread_alive", False), "stop_requested": ck.get("stop_requested", False),
        "loading_eligible": ck.get("loading_eligible", False),
        "note": ck.get("note"), "barometers": buckets,
        "aggregates": {
            "fired": len(fired), "target": target, "eligible_total": eligible_total,
            "connected": connected, "cost_usd": round(total_cost, 2),
            "cost_chf": round(total_cost * _USD_TO_CHF, 2),
            "budget_chf": COLD_CALL_BUDGET_CHF, "remaining_chf": _budget_remaining_chf(),
        },
        "calls": rows,
    }


# ---- Phase 3: durable session summaries (Notion) ----------------------------

def _script_version() -> str:
    """Current voice-agent script version (e.g. 'v7.1') from the changelog's newest
    entry. Read fresh each call (the file is tiny and this runs once per batch
    finalization) so it stays correct after a changelog redeploy. 'unbekannt' if the
    file isn't deployed."""
    ver = "unbekannt"
    try:
        if CHANGELOG_PATH.exists():
            for line in CHANGELOG_PATH.read_text(encoding="utf-8").splitlines():
                m = re.match(r"^-\s*\*\*(v[\d.]+)", line.strip())
                if m:
                    ver = m.group(1)
                    break
    except Exception as e:
        app.logger.error("_script_version parse failed: %s", e)
    return ver


def _write_session_summary(batch_id: str) -> None:
    """Upsert ONE durable row per cockpit batch into the Voice Sessions Notion DB
    (survives Render's ephemeral disk). Called from the runner's finally. Skips
    empty batches. Idempotent: stores the page_id on the session and PATCHes it on
    later finalizations (e.g. after resume) instead of creating a duplicate."""
    try:
        session = _load_voice_session(batch_id)
        if not session or "cockpit" not in session:
            return
        st = _batch_status(session)
        a = st.get("aggregates") or {}
        b = st.get("barometers") or {}
        fired = int(a.get("fired") or 0)
        if fired <= 0:
            return                      # don't log empty/aborted-before-dial batches
        key = os.environ.get("NOTION_API_KEY", "").strip()
        if not key:
            return
        ck = session["cockpit"]
        params = ck.get("params") or {}
        connected = int(a.get("connected") or 0)
        hot = int(b.get("hot") or 0)
        followup = int(b.get("followup") or 0)

        def _rate(x):
            return round(x / fired, 4) if fired else 0

        branche = params.get("branche")
        branche_txt = ", ".join(branche) if isinstance(branche, list) else (branche or "Alle ICP")
        created = session.get("created_at") or _now_iso()
        ver = _script_version()
        title = f"{created[:10]} · {branche_txt} · {fired} Calls"
        props = {
            "Session": {"title": [{"text": {"content": title[:200]}}]},
            "Date": {"date": {"start": created}},
            "Branche": {"rich_text": [{"text": {"content": branche_txt[:200]}}]},
            "Script Version": {"select": {"name": ver}},
            "Status": {"select": {"name": st.get("status") or "done"}},
            "Max Calls": {"number": int(params.get("max_calls") or 0)},
            "Fired": {"number": fired},
            "Connected": {"number": connected},
            "Hot": {"number": hot},
            "Follow-up": {"number": followup},
            "Cold": {"number": int(b.get("cold") or 0)},
            "Hang-up": {"number": int(b.get("hangup") or 0)},
            "No-Answer": {"number": int(b.get("noanswer") or 0)},
            "Connect Rate": {"number": _rate(connected)},
            "Hot Rate": {"number": _rate(hot)},
            "Follow-up Rate": {"number": _rate(followup)},
            "Cost CHF": {"number": float(a.get("cost_chf") or 0)},
            "Disclose Ratio": {"number": float(params.get("disclose_ratio") or 0)},
            "Batch ID": {"rich_text": [{"text": {"content": batch_id}}]},
        }
        import requests as _rq
        h = {"Authorization": f"Bearer {key}", "Notion-Version": "2022-06-28",
             "Content-Type": "application/json"}
        page_id = ck.get("summary_page_id")
        if page_id:
            _rq.patch(f"https://api.notion.com/v1/pages/{page_id}",
                      headers=h, json={"properties": props}, timeout=25)
        else:
            r = _rq.post("https://api.notion.com/v1/pages", headers=h,
                         json={"parent": {"database_id": VOICE_SESSIONS_DB_ID}, "properties": props},
                         timeout=25)
            if r.ok:
                new_id = r.json().get("id")
                fresh = _load_voice_session(batch_id)
                if fresh and "cockpit" in fresh:
                    fresh["cockpit"]["summary_page_id"] = new_id
                    _save_voice_session(fresh)
            else:
                app.logger.error("voice session summary create failed: %s %s",
                                 r.status_code, r.text[:200])
    except Exception as e:
        app.logger.error("_write_session_summary failed (%s): %s", batch_id, e)


# ---- Phase 4: durable per-call rows (Voice Calls DB) → Analyse page ----------

def _write_voice_call_row(props: dict) -> None:
    """Best-effort create of one Voice Calls row. Non-fatal; no-op without creds/DB."""
    key = os.environ.get("NOTION_API_KEY", "").strip()
    if not key or not VOICE_CALLS_DB_ID:
        return
    try:
        import requests as _rq
        h = {"Authorization": f"Bearer {key}", "Notion-Version": "2022-06-28",
             "Content-Type": "application/json"}
        r = _rq.post("https://api.notion.com/v1/pages", headers=h,
                     json={"parent": {"database_id": VOICE_CALLS_DB_ID}, "properties": props},
                     timeout=20)
        if not r.ok:
            app.logger.error("voice call row create failed: %s %s", r.status_code, r.text[:200])
    except Exception as e:
        app.logger.error("_write_voice_call_row failed: %s", e)


def _voice_call_props(f: dict, c: dict, bucket: str, ver: str, batch_id: str) -> dict:
    """Build Notion props for one fired call (fired entry f + Vapi call c)."""
    sd = ((c.get("analysis") or {}).get("structuredData") or {})
    dur = _call_duration_s(c)
    connected = sd.get("connected")
    if connected is None:
        connected = bool(c.get("transcript")) and (dur is None or dur >= 8)
    when = c.get("startedAt") or f.get("fired_at") or _now_iso()
    firma = str(f.get("firma") or "—")
    props = {
        "Call": {"title": [{"text": {"content": f"{firma} · {str(when)[:10]}"[:200]}}]},
        "Date": {"date": {"start": str(when)}},
        "Firma": {"rich_text": [{"text": {"content": firma[:200]}}]},
        "Connected": {"checkbox": bool(connected)},
        "Bucket": {"select": {"name": bucket}},
    }
    if f.get("call_id"):
        props["Call ID"] = {"rich_text": [{"text": {"content": str(f["call_id"])[:200]}}]}
    if f.get("lead_id"):
        props["Lead ID"] = {"rich_text": [{"text": {"content": str(f["lead_id"])[:200]}}]}
    if batch_id:
        props["Batch ID"] = {"rich_text": [{"text": {"content": str(batch_id)[:200]}}]}
    if f.get("branche"):
        props["Branche"] = {"select": {"name": str(f["branche"])[:100]}}
    if ver:
        props["Script Version"] = {"select": {"name": str(ver)[:100]}}
    if dur is not None:
        props["Duration s"] = {"number": int(dur)}
    cost = float(c.get("cost") or 0)
    if cost:
        props["Cost CHF"] = {"number": round(cost * _USD_TO_CHF, 4)}
    tp = str(f.get("top_problem") or "").strip()
    if tp:
        props["Top Problem"] = {"rich_text": [{"text": {"content": tp[:1900]}}]}
    sc = f.get("schmerzscore")
    if isinstance(sc, (int, float)):
        props["Schmerzscore"] = {"number": sc}
    if f.get("payment"):
        props["Payment"] = {"checkbox": True}
    if f.get("interview_completed"):
        props["Interview Completed"] = {"checkbox": True}
    if f.get("disclose_ai") is not None:
        props["Disclose AI"] = {"checkbox": bool(f.get("disclose_ai"))}
    return props


def _sync_voice_calls(batch_id: str, only_call_id: str = None) -> None:
    """Append a durable Voice Calls row per fired call (no-answer included). Skips
    still-'live'/'auswerten' calls (the fallback-classify thread re-syncs each once its
    bucket resolves). Dedup is at READ time (insights keeps the latest per Call ID).
    Best-effort / non-fatal."""
    if not VOICE_CALLS_DB_ID or not os.environ.get("NOTION_API_KEY", "").strip():
        return
    try:
        session = _load_voice_session(batch_id)
        ck = (session or {}).get("cockpit") or {}
        fired = ck.get("fired") or []
        if not fired:
            return
        ver = _script_version()
        for f in fired:
            cid = f.get("call_id")
            if only_call_id and cid != only_call_id:
                continue
            c = _fetch_call_cached(cid) if cid else {}
            bucket = _bucket_call(c, f)
            if bucket in ("live", "auswerten"):
                continue                      # not final yet
            _write_voice_call_row(_voice_call_props(f, c, bucket, ver, batch_id))
    except Exception as e:
        app.logger.error("_sync_voice_calls failed (%s): %s", batch_id, e)


# --- insights aggregation (read) ---------------------------------------------

_INSIGHTS_CACHE: dict = {}
_INSIGHTS_TTL = 300        # 5 min


def _vc_rt(prop):
    arr = (prop or {}).get("rich_text") or (prop or {}).get("title") or []
    return "".join(t.get("plain_text", "") for t in arr)


def _vc_sel(prop):
    s = (prop or {}).get("select")
    return (s or {}).get("name") if s else None


def _vc_cb(prop):
    return bool((prop or {}).get("checkbox"))


def _vc_num(prop):
    return (prop or {}).get("number")


def _vc_date(prop):
    d = (prop or {}).get("date")
    return (d or {}).get("start") if d else None


def _vc_local_dt(s):
    """Parse an ISO ts and convert to Europe/Zurich (so heatmap hours are local)."""
    try:
        from datetime import datetime as _dt, timezone as _tz
        d = _dt.fromisoformat(str(s).replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=_tz.utc)
        try:
            from zoneinfo import ZoneInfo
            return d.astimezone(ZoneInfo("Europe/Zurich"))
        except Exception:
            return d
    except Exception:
        return None


def _query_voice_calls(days: int, branche: str = None) -> list:
    """Paginated Voice Calls query (Date ≥ cutoff, optional Branche)."""
    key = os.environ.get("NOTION_API_KEY", "").strip()
    if not key or not VOICE_CALLS_DB_ID:
        return []
    import requests as _rq
    from datetime import datetime as _dt, timezone as _tz, timedelta as _td
    h = {"Authorization": f"Bearer {key}", "Notion-Version": "2022-06-28",
         "Content-Type": "application/json"}
    filters = []
    if days and days > 0:
        cutoff = (_dt.now(_tz.utc) - _td(days=days)).isoformat()
        filters.append({"property": "Date", "date": {"on_or_after": cutoff}})
    if branche:
        filters.append({"property": "Branche", "select": {"equals": branche}})
    body = {"page_size": 100}
    if len(filters) == 1:
        body["filter"] = filters[0]
    elif len(filters) > 1:
        body["filter"] = {"and": filters}
    results, cursor = [], None
    while True:
        if cursor:
            body["start_cursor"] = cursor
        r = _rq.post(f"https://api.notion.com/v1/databases/{VOICE_CALLS_DB_ID}/query",
                     headers=h, json=body, timeout=30)
        if not r.ok:
            app.logger.error("voice calls query failed: %s %s", r.status_code, r.text[:200])
            break
        data = r.json()
        results.extend(data.get("results", []))
        cursor = data.get("next_cursor")
        if not (data.get("has_more") and cursor):
            break
    return results


def _compute_insights(days: int, branche: str = None) -> dict:
    pages = _query_voice_calls(days, branche)
    # dedupe by Call ID (latest last_edited_time wins)
    by_key = {}
    for p in pages:
        pr = p.get("properties") or {}
        cid = _vc_rt(pr.get("Call ID")) or p.get("id")
        ledit = p.get("last_edited_time") or ""
        if cid not in by_key or ledit > by_key[cid][0]:
            by_key[cid] = (ledit, p)
    rows = [v[1] for v in by_key.values()]

    tod, problems = {}, {}
    schmerz = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    n = conn = hot = interview = pay = hot_n = 0
    cost_sum = 0.0
    hot_dur, cold_dur = [], []
    for p in rows:
        pr = p.get("properties") or {}
        bucket = _vc_sel(pr.get("Bucket"))
        connected = _vc_cb(pr.get("Connected"))
        dur = _vc_num(pr.get("Duration s"))
        cost = _vc_num(pr.get("Cost CHF")) or 0
        tp = _vc_rt(pr.get("Top Problem"))
        sc = _vc_num(pr.get("Schmerzscore"))
        n += 1
        cost_sum += cost
        if connected:
            conn += 1
        if bucket == "hot":
            hot += 1
            hot_n += 1
        if _vc_cb(pr.get("Interview Completed")):
            interview += 1
        if _vc_cb(pr.get("Payment")):
            pay += 1
        dt = _vc_local_dt(_vc_date(pr.get("Date")))
        if dt:
            t = tod.setdefault((dt.weekday(), dt.hour), {"calls": 0, "connected": 0, "hot": 0})
            t["calls"] += 1
            if connected:
                t["connected"] += 1
            if bucket == "hot":
                t["hot"] += 1
        if dur is not None:
            (hot_dur if bucket == "hot" else cold_dur if bucket in ("cold", "hangup") else []).append(dur)
        if tp:
            e = problems.setdefault(tp.strip().lower(),
                                    {"count": 0, "score_sum": 0, "score_n": 0, "label": tp.strip()})
            e["count"] += 1
            if isinstance(sc, (int, float)):
                e["score_sum"] += sc
                e["score_n"] += 1
        if isinstance(sc, (int, float)):
            si = int(round(sc))
            if 1 <= si <= 5:
                schmerz[si] += 1

    top = sorted(problems.values(), key=lambda x: -x["count"])[:10]

    def _avg(a):
        return round(sum(a) / len(a), 1) if a else None

    return {
        "total_calls": n,
        "time_of_day": [{"dow": k[0], "hour": k[1], **v} for k, v in sorted(tod.items())],
        "top_problems": [{"problem": e["label"], "count": e["count"],
                          "avg_schmerz": round(e["score_sum"] / e["score_n"], 1) if e["score_n"] else None}
                         for e in top],
        "schmerzscore": {str(k): v for k, v in schmerz.items()},
        "kpis": {
            "interview_completion_rate": round(interview / n, 4) if n else 0,
            "payment_rate": round(pay / n, 4) if n else 0,
            "chf_per_hot": round(cost_sum / hot, 2) if hot else None,
            "avg_dur_hot": _avg(hot_dur),
            "avg_dur_cold": _avg(cold_dur),
        },
    }


def _insights_cached(days: int, branche: str = None) -> dict:
    import time as _t
    ckey = f"{days}:{branche or ''}"
    now = _t.time()
    hit = _INSIGHTS_CACHE.get(ckey)
    if hit and (now - hit[0]) < _INSIGHTS_TTL:
        return hit[1]
    data = _compute_insights(days, branche)
    _INSIGHTS_CACHE[ckey] = (now, data)
    return data


# ---- the batch runner (daemon) ----------------------------------------------

def _run_cockpit_batch(batch_id: str) -> None:
    """Fire eligible leads one at a time, paced, stoppable. State persisted to the
    session file each step so status polls + stop/resume work across the thread."""
    try:
        from vapi_client import place_call
        base = _load_voice_session(batch_id)
        if not base:
            return
        params = base["cockpit"].get("params") or {}
        # Lazy-fetch eligibility OFF the request thread (Workflow D's dry-run is ~20s).
        if base["cockpit"].get("loading_eligible"):
            eligible = _fetch_eligible(int(params.get("max_calls", 0)), params.get("branche"))
            fresh = _load_voice_session(batch_id)
            fresh["cockpit"]["eligible"] = eligible
            fresh["cockpit"]["loading_eligible"] = False
            if not eligible:
                fresh["cockpit"]["status"], fresh["cockpit"]["thread_alive"] = "done", False
                _save_voice_session(fresh)
                return
            _save_voice_session(fresh)
        base = _load_voice_session(batch_id)
        eligible = (base["cockpit"].get("eligible") or [])
        max_calls = min(int(params.get("max_calls", 0)), len(eligible))
        gap = int(params.get("gap_sec", COCKPIT_DEFAULT_GAP_SEC))
        while True:
            fresh = _load_voice_session(batch_id)
            if not fresh:
                return
            ck = fresh["cockpit"]
            i = int(ck.get("cursor", 0))
            if ck.get("stop_requested"):
                ck["status"], ck["thread_alive"] = "stopped", False
                _save_voice_session(fresh); return
            if i >= max_calls:
                ck["status"], ck["thread_alive"] = "done", False
                _save_voice_session(fresh); return
            if _budget_remaining_chf() <= 1.0:
                ck["status"], ck["thread_alive"], ck["note"] = "stopped", False, "Budget erreicht"
                _save_voice_session(fresh); return
            lead = eligible[i]
            entry = {"lead_id": lead.get("lead_id"), "firma": lead.get("firma"),
                     "phone": lead.get("phone"), "branche": lead.get("branche"),
                     "call_id": None, "fired_at": _now_iso(), "error": None}
            try:
                call = place_call(
                    number=lead.get("phone"), session_id=batch_id, lead_id=lead.get("lead_id", ""),
                    firma=lead.get("firma", ""), branche=lead.get("branche", ""),
                    kontakt_nachname=lead.get("kontakt_nachname", ""),
                    disclosure_line=lead.get("disclosure_line", ""),
                    context=lead.get("context", ""))
                entry["call_id"] = call.get("id")
            except Exception as e:
                entry["error"] = str(e)[:300]
            # reload → append → advance cursor (preserves any stop flag set meanwhile).
            # Under the session lock so a concurrent fallback-classify save can't drop
            # this freshly dialed row (or vice-versa).
            with _session_lock(batch_id):
                fresh = _load_voice_session(batch_id)
                fresh["cockpit"]["fired"].append(entry)
                fresh["cockpit"]["cursor"] = i + 1
                _save_voice_session(fresh)
            if entry.get("call_id"):
                _mark_lead_dialed(lead.get("lead_id"))
            # pace, re-checking stop every ~2s
            import time as _t
            waited, stopped = 0, False
            while waited < gap:
                _t.sleep(min(2, gap - waited)); waited += 2
                f2 = _load_voice_session(batch_id)
                if f2 and f2["cockpit"].get("stop_requested"):
                    stopped = True; break
            if stopped:
                fresh = _load_voice_session(batch_id)
                fresh["cockpit"]["status"], fresh["cockpit"]["thread_alive"] = "stopped", False
                _save_voice_session(fresh); return
    except Exception as e:
        app.logger.error("cockpit runner crashed (%s): %s", batch_id, e)
        try:
            fresh = _load_voice_session(batch_id)
            if fresh:
                fresh["cockpit"]["status"], fresh["cockpit"]["thread_alive"] = "error", False
                fresh["cockpit"]["note"] = str(e)[:200]
                _save_voice_session(fresh)
        except Exception:
            pass
    finally:
        with _RUNNER_LOCK:
            if _RUNNER_THREADS.get(batch_id) is _threading.current_thread():
                _RUNNER_THREADS.pop(batch_id, None)
        # Terminal state reached (done / stopped / error). First classify any straggler
        # calls that ended without a frontend poll to pick them up, so top_problem /
        # schmerzscore are filled before the durable rows are written. Then persist a
        # summary + one durable row per fired call. Safe on empty/missing batches.
        try:
            _sweep_unclassified(batch_id)    # catch-up: classify 'auswerten' stragglers
        except Exception as e:
            app.logger.error("post-batch classify sweep failed (%s): %s", batch_id, e)
        _write_session_summary(batch_id)
        _sync_voice_calls(batch_id)          # + one durable row per fired call (Analyse page)


# Real thread handles per batch (the persisted thread_alive flag is NOT a sync
# primitive). Guards against a second runner being spawned by a double-click on
# Weiter/resume or a stop→resume race → which would double-dial real leads.
_RUNNER_THREADS: dict = {}
_RUNNER_LOCK = _threading.Lock()


def _spawn_cockpit_runner(batch_id: str) -> bool:
    """Start the runner for batch_id unless one is already alive. Returns True if a
    new thread was started, False if an existing live runner blocked the spawn."""
    with _RUNNER_LOCK:
        existing = _RUNNER_THREADS.get(batch_id)
        if existing is not None and existing.is_alive():
            return False
        t = _threading.Thread(target=_run_cockpit_batch, args=(batch_id,),
                              name=f"cockpit-{batch_id[:8]}", daemon=True)
        _RUNNER_THREADS[batch_id] = t
        t.start()
        return True


# ---- routes -----------------------------------------------------------------

@app.route("/voice/cockpit", methods=["GET"])
def voice_cockpit_page():
    return send_from_directory("static", "cockpit.html")


@app.route("/voice/overview", methods=["GET"])
def voice_overview_page():
    return send_from_directory("static", "overview.html")


@app.route("/voice/analyse", methods=["GET"])
def voice_analyse_page():
    return send_from_directory("static", "analyse.html")


@app.route("/api/cockpit/login", methods=["POST"])
def cockpit_login():
    data = request.get_json(silent=True) or {}
    if str(data.get("password") or "") == COCKPIT_PASSWORD:
        session["cockpit_auth"] = True
        session.permanent = True
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Falsches Passwort"}), 401


@app.route("/api/cockpit/logout", methods=["POST"])
def cockpit_logout():
    session.pop("cockpit_auth", None)
    return jsonify({"ok": True})


@app.route("/api/cockpit/auth", methods=["GET"])
def cockpit_auth_status():
    return jsonify({"authed": _cockpit_auth_ok()})


@app.route("/api/cockpit/budget", methods=["GET"])
def cockpit_budget_status():
    """Read-only budget snapshot for the always-visible sidebar gauge.
    Reuses _budget_remaining_chf() so spent/cap/remaining stay consistent."""
    if not _cockpit_auth_ok():
        return jsonify({"error": "Unauthorized"}), 401
    remaining = _budget_remaining_chf()
    spent = round(max(0.0, COLD_CALL_BUDGET_CHF - remaining), 2)
    return jsonify({"spent_chf": spent, "cap_chf": COLD_CALL_BUDGET_CHF, "remaining_chf": remaining})


@app.route("/api/cockpit/insights", methods=["GET"])
def cockpit_insights():
    """Aggregated deep analytics for the Analyse page (time-of-day, top problems,
    Schmerzscore, KPIs) from the durable Voice Calls DB. 5-min cached, read-only."""
    if not _cockpit_auth_ok():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        days = int(request.args.get("days") or 0)
    except Exception:
        days = 0
    branche = request.args.get("branche") or None
    return jsonify(_insights_cached(days, branche))


@app.route("/api/cockpit/preview", methods=["POST"])
def cockpit_preview():
    if not _cockpit_auth_ok():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    max_calls = min(int(data.get("max_calls") or 5), COCKPIT_MAX_CALLS)
    eligible = _fetch_eligible(max_calls, data.get("branche"))
    return jsonify({
        "eligible_count": len(eligible),
        "sample": [{"firma": e.get("firma"), "branche": e.get("branche"), "phone": e.get("phone")}
                   for e in eligible[:10]],
    })


@app.route("/api/cockpit/batch/start", methods=["POST"])
def cockpit_batch_start():
    if not _cockpit_auth_ok():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    max_calls = min(int(data.get("max_calls") or 1), COCKPIT_MAX_CALLS)
    branche = data.get("branche")
    gap_sec = int(data.get("gap_sec")) if data.get("gap_sec") is not None else COCKPIT_DEFAULT_GAP_SEC
    try:
        import uuid
        batch_id = str(uuid.uuid4())
        session = {
            "session_id": batch_id, "created_at": _now_iso(),
            "batch_meta": {"source": "cockpit", "branche": branche or None},
            "calls": [], "report": None,
            "cockpit": {"status": "running", "stop_requested": False,
                        "params": {"max_calls": max_calls, "branche": branche,
                                   "gap_sec": gap_sec, "disclose_ratio": 0},
                        "cursor": 0, "eligible": [], "loading_eligible": True,
                        "fired": [], "thread_alive": True},
        }
        _save_voice_session(session)
        _spawn_cockpit_runner(batch_id)   # fetches eligibility off-thread, then dials
        return jsonify({"batch_id": batch_id})
    except Exception as e:
        app.logger.error("cockpit_batch_start error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/cockpit/batch/<batch_id>", methods=["GET"])
def cockpit_batch_status(batch_id):
    if not _cockpit_auth_ok():
        return jsonify({"error": "Unauthorized"}), 401
    if not _valid_session_id(batch_id):
        return jsonify({"error": "invalid batch id"}), 400
    session = _load_voice_session(batch_id)
    if not session or "cockpit" not in session:
        return jsonify({"error": "batch not found"}), 404
    status = _batch_status(session)
    # The runner's finally wrote an in-flight snapshot (calls were still ringing →
    # all-zero barometers). Re-write the durable summary (upsert) the moment every
    # call has reached a terminal state, so history/trends reflect real outcomes.
    ck = session.get("cockpit") or {}
    if (status["status"] in ("done", "stopped", "error")
            and status["aggregates"]["fired"] > 0
            and not any(c.get("bucket") in ("live", "auswerten") for c in status.get("calls", []))
            and not ck.get("summary_finalized")):
        _write_session_summary(batch_id)
        fresh = _load_voice_session(batch_id)
        if fresh and "cockpit" in fresh:
            fresh["cockpit"]["summary_finalized"] = True
            _save_voice_session(fresh)
    return jsonify(status)


@app.route("/api/cockpit/call/<call_id>", methods=["GET"])
def cockpit_call_detail(call_id):
    if not _cockpit_auth_ok():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        c = _fetch_call_cached(call_id)
        return jsonify({"status": c.get("status"), "cost": c.get("cost"),
                        "endedReason": c.get("endedReason"),
                        "transcript": c.get("transcript") or "", "analysis": c.get("analysis") or {}})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/cockpit/batch/<batch_id>/stop", methods=["POST"])
def cockpit_batch_stop(batch_id):
    if not _cockpit_auth_ok():
        return jsonify({"error": "Unauthorized"}), 401
    if not _valid_session_id(batch_id):
        return jsonify({"error": "invalid batch id"}), 400
    session = _load_voice_session(batch_id)
    if not session or "cockpit" not in session:
        return jsonify({"error": "batch not found"}), 404
    session["cockpit"]["stop_requested"] = True
    _save_voice_session(session)
    return jsonify({"ok": True, "stop_requested": True})


@app.route("/api/cockpit/batch/<batch_id>/resume", methods=["POST"])
def cockpit_batch_resume(batch_id):
    if not _cockpit_auth_ok():
        return jsonify({"error": "Unauthorized"}), 401
    if not _valid_session_id(batch_id):
        return jsonify({"error": "invalid batch id"}), 400
    session = _load_voice_session(batch_id)
    if not session or "cockpit" not in session:
        return jsonify({"error": "batch not found"}), 404
    ck = session["cockpit"]
    ck["stop_requested"], ck["status"], ck["thread_alive"] = False, "running", True
    _save_voice_session(session)
    _spawn_cockpit_runner(batch_id)
    return jsonify({"ok": True})


@app.route("/voice/sessions", methods=["GET"])
def voice_sessions_page():
    return send_from_directory("static", "sessions.html")


@app.route("/api/cockpit/sessions", methods=["GET"])
def cockpit_sessions():
    """Durable session history for the history + trends views. Reads the Voice
    Sessions Notion DB, oldest-first (so the trends chart plots left→right)."""
    if not _cockpit_auth_ok():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        key = os.environ.get("NOTION_API_KEY", "").strip()
        if not key:
            return jsonify({"sessions": []})
        import requests as _rq
        h = {"Authorization": f"Bearer {key}", "Notion-Version": "2022-06-28",
             "Content-Type": "application/json"}
        results, cursor = [], None
        while True:
            body = {"sorts": [{"property": "Date", "direction": "ascending"}], "page_size": 100}
            if cursor:
                body["start_cursor"] = cursor
            r = _rq.post(f"https://api.notion.com/v1/databases/{VOICE_SESSIONS_DB_ID}/query",
                         headers=h, json=body, timeout=30)
            r.raise_for_status()
            data = r.json()
            results.extend(data.get("results", []))
            cursor = data.get("next_cursor")
            if not (data.get("has_more") and cursor):
                break

        def _num(p, n):
            v = (p.get(n) or {}).get("number")
            return v if v is not None else 0

        def _txt(p, n):
            return "".join(x.get("plain_text", "") for x in ((p.get(n) or {}).get("rich_text") or []))

        def _sel(p, n):
            return ((p.get(n) or {}).get("select") or {}).get("name")

        def _date(p, n):
            return ((p.get(n) or {}).get("date") or {}).get("start")

        sessions = []
        for pg in results:
            p = pg.get("properties", {})
            sessions.append({
                "date": _date(p, "Date"), "branche": _txt(p, "Branche"),
                "script_version": _sel(p, "Script Version"), "status": _sel(p, "Status"),
                "max_calls": _num(p, "Max Calls"), "fired": _num(p, "Fired"),
                "connected": _num(p, "Connected"),
                "barometers": {
                    "hot": _num(p, "Hot"), "followup": _num(p, "Follow-up"),
                    "cold": _num(p, "Cold"), "hangup": _num(p, "Hang-up"),
                    "noanswer": _num(p, "No-Answer"),
                },
                "connect_rate": _num(p, "Connect Rate"), "hot_rate": _num(p, "Hot Rate"),
                "followup_rate": _num(p, "Follow-up Rate"), "cost_chf": _num(p, "Cost CHF"),
                "batch_id": _txt(p, "Batch ID"),
            })
        return jsonify({"sessions": sessions})
    except Exception as e:
        app.logger.error("cockpit_sessions failed: %s", e)
        return jsonify({"sessions": [], "error": str(e)}), 200


# ---------------------------------------------------------------------------
# Cockpit — public booking ("Prozessermittlung vor Ort") + slot engine
#
# A custom Calendly: prospects book a 60-min on-site process-discovery
# appointment with Automatisierbar (the company, not an individual). The team
# decides who takes it afterward (Phase 2 claim flow). Availability = our weekly
# bookable windows minus busy time on the shared Automatisierbar calendar.
# Confirm → match/create a lead + write an Appointment row + notify the team.
#
# Calendar integration degrades gracefully: with no Google credential bound the
# slot engine serves windows-only slots and the calendar write no-ops, so the
# page is fully usable before the credential lands.
# ---------------------------------------------------------------------------

from datetime import (datetime as _dt2, timedelta as _td2, date as _date2,
                      time as _time2, timezone as _tz2)

BOOKING_TZ = "Europe/Zurich"
SLOT_MINUTES = int(os.environ.get("COCKPIT_SLOT_MINUTES", "60"))
# Weekly bookable windows in local time, keyed by weekday() (Mon=0 … Sun=6).
# All 7 days open for the current push (weekends included, when we're in town); the
# blackout ranges below carve out the weeks we're away, and the linked calendar's
# free/busy carves out the real openings. Edit here to change availability.
BOOKING_WINDOWS = {
    0: [("08:00", "18:00")],  # Mon
    1: [("08:00", "18:00")],  # Tue
    2: [("08:00", "18:00")],  # Wed
    3: [("08:00", "18:00")],  # Thu
    4: [("08:00", "18:00")],  # Fri
    5: [("08:00", "18:00")],  # Sat
    6: [("08:00", "18:00")],  # Sun
}
BOOKING_LEAD_DAYS = int(os.environ.get("COCKPIT_LEAD_DAYS", "1"))      # earliest = now +N days (24h)
BOOKING_HORIZON_DAYS = int(os.environ.get("COCKPIT_HORIZON_DAYS", "75"))
# Fixed last bookable date — an absolute cap that overrides the rolling horizon above.
# Set to "" to disable the cap and fall back to the rolling BOOKING_HORIZON_DAYS window.
BOOKING_HORIZON_DATE = os.environ.get("COCKPIT_HORIZON_DATE", "2026-09-30").strip()
# Vacation / blackout ranges — inclusive local-date spans with NO bookable slots.
# Hand-managed availability config (mirrors BOOKING_WINDOWS). Edit here for future
# absences, or override without a redeploy via COCKPIT_BLACKOUT_RANGES, e.g.
# "2026-07-17:2026-07-27,2026-08-11:2026-09-02".
BOOKING_BLACKOUT_RANGES = [
    (_date2(2026, 7, 17), _date2(2026, 7, 27)),  # Sommerpause
    (_date2(2026, 8, 11), _date2(2026, 9, 2)),   # Abwesenheit
]


def _parse_blackout_env(raw: str) -> list:
    ranges = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            a, b = chunk.split(":")
            ranges.append((_date2.fromisoformat(a.strip()), _date2.fromisoformat(b.strip())))
        except ValueError:
            app.logger.warning("ignoring bad COCKPIT_BLACKOUT_RANGES chunk: %r", chunk)
    return ranges


_blackout_env = os.environ.get("COCKPIT_BLACKOUT_RANGES", "").strip()
if _blackout_env:
    BOOKING_BLACKOUT_RANGES = _parse_blackout_env(_blackout_env)
# Buffer (min) added around every busy block so back-to-back/near bookings are blocked
# (≈ travel time for on-site visits). Mirrors Google's 45-min buffer.
COCKPIT_BUFFER_MINUTES = int(os.environ.get("COCKPIT_BUFFER_MINUTES", "45"))
# Hide a day once this many calendar events already sit in its window (≈ Google's
# "max bookings per day"; counted from busy blocks as a proxy). 0 disables the cap.
COCKPIT_MAX_PER_DAY = int(os.environ.get("COCKPIT_MAX_PER_DAY", "6"))

# --- Remote availability config (Hub v2·M5a) ---------------------------------
# JSON override file merged over the env/hardcoded defaults above, so the Hub's
# booking page can change availability remotely. Lazily created; read per-request
# via an mtime cache so edits apply WITHOUT a restart and both gunicorn workers
# converge on their next request. No file ⇒ byte-identical to the constants-only
# behavior. Endpoints are inert (404) until COCKPIT_CONFIG_SECRET is set.
BOOKING_CONFIG_PATH = _Path(__file__).resolve().parent / "data" / "booking_config.json"
COCKPIT_CONFIG_SECRET = os.environ.get("COCKPIT_CONFIG_SECRET", "").strip()
_BOOKING_CFG_LOCK = _threading.Lock()
_BOOKING_OV_CACHE = {"mtime": None, "data": {}}
_BOOKING_CFG_KEYS = ("slot_minutes", "lead_days", "horizon_days", "horizon_date",
                     "buffer_minutes", "max_per_day", "blackout_ranges", "windows")


def _booking_overrides() -> dict:
    """Raw override dict from data/booking_config.json ({} if absent/corrupt).
    mtime-cached: re-parsed only when the file changes (os.replace bumps mtime)."""
    try:
        st = os.stat(BOOKING_CONFIG_PATH)
    except OSError:
        _BOOKING_OV_CACHE.update(mtime=None, data={})
        return {}
    if _BOOKING_OV_CACHE["mtime"] != st.st_mtime_ns:
        try:
            data = _json.loads(BOOKING_CONFIG_PATH.read_text(encoding="utf-8"))
            data = ({k: v for k, v in data.items() if k in _BOOKING_CFG_KEYS}
                    if isinstance(data, dict) else {})
        except Exception as e:
            app.logger.error("booking_config.json unreadable — ignoring overrides: %s", e)
            data = {}
        _BOOKING_OV_CACHE.update(mtime=st.st_mtime_ns, data=data)
    return _BOOKING_OV_CACHE["data"]


def _booking_cfg() -> dict:
    """Effective availability config: JSON overrides merged over the module
    defaults, with Python-native types (drop-in for the constants). Never raises —
    a bad override falls back to the defaults (this engine takes real bookings)."""
    cfg = {
        "slot_minutes": SLOT_MINUTES,
        "lead_days": BOOKING_LEAD_DAYS,
        "horizon_days": BOOKING_HORIZON_DAYS,
        "horizon_date": BOOKING_HORIZON_DATE,          # "" = no fixed cap
        "buffer_minutes": COCKPIT_BUFFER_MINUTES,
        "max_per_day": COCKPIT_MAX_PER_DAY,
        "blackout_ranges": BOOKING_BLACKOUT_RANGES,    # list[(date, date)]
        "windows": BOOKING_WINDOWS,                    # {int: [(hh:mm, hh:mm)]}
    }
    ov = _booking_overrides()
    try:
        for k in ("slot_minutes", "lead_days", "horizon_days",
                  "buffer_minutes", "max_per_day"):
            if k in ov:
                cfg[k] = int(ov[k])
        if "horizon_date" in ov:
            cfg["horizon_date"] = (ov["horizon_date"] or "").strip()
        if "blackout_ranges" in ov:
            cfg["blackout_ranges"] = [
                (_date2.fromisoformat(a), _date2.fromisoformat(b))
                for (a, b) in ov["blackout_ranges"]]
        if "windows" in ov:
            cfg["windows"] = {int(k): [tuple(w) for w in v]
                              for k, v in ov["windows"].items()}
    except Exception as e:
        app.logger.error("booking override merge failed — using defaults: %s", e)
    return cfg

COCKPIT_APPOINTMENTS_DB_ID = os.environ.get("COCKPIT_APPOINTMENTS_DB_ID", "")
COCKPIT_CALENDAR_ID = os.environ.get("COCKPIT_CALENDAR_ID", "")
COCKPIT_BOOK_SECRET = os.environ.get("COCKPIT_BOOK_SECRET", "")        # optional confirm gate
COCKPIT_TEAM_CHAT_ID = os.environ.get("COCKPIT_TEAM_CHAT_ID", "-5026363666")
COCKPIT_TELEGRAM_BOT_TOKEN = (os.environ.get("COCKPIT_TELEGRAM_BOT_TOKEN")
                              or os.environ.get("OPERATOR_TELEGRAM_BOT_TOKEN", ""))

# --- Phase 2: per-person team login (magic link) + claim-button bot ----------
# The claim buttons + webhook use a DEDICATED team bot (COCKPIT_TEAM_BOT_TOKEN),
# separate from the operator bot — setting a webhook on the operator bot would
# 409-break its getUpdates polling (see feedback_telegram_credentials). When the
# team bot is unset the booking alert falls back to the plain operator-bot ping;
# the team PWA claim covers the gap either way.
COCKPIT_TEAM_BOT_TOKEN = os.environ.get("COCKPIT_TEAM_BOT_TOKEN", "")
COCKPIT_TELEGRAM_WEBHOOK_SECRET = os.environ.get("COCKPIT_TELEGRAM_WEBHOOK_SECRET", "")
COCKPIT_TEAM_MEMBERS = ("Tej", "Joaquin", "Nico", "Patrik")

# 365-day session so an installed team PWA isn't logged out every month.
app.config["PERMANENT_SESSION_LIFETIME"] = _td2(days=365)


def _team_tokens() -> dict:
    """{token: name} from COCKPIT_TEAM_TOKENS (JSON). Empty ⇒ team login disabled."""
    raw = os.environ.get("COCKPIT_TEAM_TOKENS", "").strip()
    if not raw:
        return {}
    try:
        import json as _json
        m = _json.loads(raw)
        return {str(k): str(v) for k, v in m.items() if k and v in COCKPIT_TEAM_MEMBERS}
    except Exception:
        app.logger.warning("COCKPIT_TEAM_TOKENS invalid JSON — team login disabled")
        return {}


def _team_member():
    """Identify the logged-in team member: a validated session, else a ?k=/header
    token. Returns the member name or None."""
    who = session.get("team_member")
    if who in COCKPIT_TEAM_MEMBERS:
        return who
    tok = request.args.get("k") or request.headers.get("X-Team-Token") or ""
    return _team_tokens().get(tok)


def _dash_uuid(h: str) -> str:
    """32-hex → dashed UUID (Notion page id). '' if not 32 hex chars."""
    h = (h or "").replace("-", "")
    if len(h) != 32:
        return ""
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def _claim_keyboard(page_id: str) -> dict:
    """Inline keyboard of the 4 team names; callback_data 'c:<32hex>:<idx>' (≤64 B)."""
    pid = page_id.replace("-", "")
    return {"inline_keyboard": [[
        {"text": n, "callback_data": f"c:{pid}:{i}"}
        for i, n in enumerate(COCKPIT_TEAM_MEMBERS)
    ]]}


def _team_bot_api(method: str, payload: dict):
    """Call the dedicated team bot's API. Returns the response, or None if unset/failed."""
    if not COCKPIT_TEAM_BOT_TOKEN:
        return None
    try:
        import requests as _rq
        return _rq.post(
            f"https://api.telegram.org/bot{COCKPIT_TEAM_BOT_TOKEN}/{method}",
            json=payload, timeout=10)
    except Exception as e:
        app.logger.error("team bot %s failed: %s", method, e)
        return None


def _send_team_claim_message(text: str, page_id: str) -> bool:
    """Post the booking alert WITH inline claim buttons via the team bot."""
    r = _team_bot_api("sendMessage", {
        "chat_id": COCKPIT_TEAM_CHAT_ID, "text": text, "parse_mode": "HTML",
        "disable_web_page_preview": True, "reply_markup": _claim_keyboard(page_id)})
    return bool(r is not None and r.status_code < 300)


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_CAL_DISABLED_LOGGED = False
_GCAL_SVC = None
_GCAL_TRIED = False


def _zurich():
    from zoneinfo import ZoneInfo
    return ZoneInfo(BOOKING_TZ)


def _now_local():
    return _dt2.now(_zurich())


def _parse_hhmm(s: str) -> _time2:
    h, m = s.split(":")
    return _time2(int(h), int(m))


def _is_blacked_out(d: _date2, cfg: dict = None) -> bool:
    """True if local date `d` falls in any configured blackout (vacation) range."""
    cfg = cfg or _booking_cfg()
    return any(a <= d <= b for (a, b) in cfg["blackout_ranges"])


def _booking_end_date(today: _date2, cfg: dict = None) -> _date2:
    """Last bookable local date: the fixed horizon_date if configured, else the
    rolling horizon_days window from `today`."""
    cfg = cfg or _booking_cfg()
    if cfg["horizon_date"]:
        try:
            return _date2.fromisoformat(cfg["horizon_date"])
        except ValueError:
            app.logger.warning("bad horizon_date %r — using rolling horizon",
                               cfg["horizon_date"])
    return today + _td2(days=cfg["horizon_days"])


def _window_slots_for_date(d: _date2, cfg: dict = None) -> list:
    """Tz-aware (start,end) slot candidates for local date `d`, pre busy-filter."""
    cfg = cfg or _booking_cfg()
    tz = _zurich()
    out = []
    step = _td2(minutes=cfg["slot_minutes"])
    for (w_start, w_end) in cfg["windows"].get(d.weekday(), []):
        ws = _dt2.combine(d, _parse_hhmm(w_start), tzinfo=tz)
        we = _dt2.combine(d, _parse_hhmm(w_end), tzinfo=tz)
        cur = ws
        while cur + step <= we:
            out.append((cur, cur + step))
            cur += step
    return out


def _overlaps(a_s, a_e, b_s, b_e) -> bool:
    return a_s < b_e and b_s < a_e


def _gcal_credentials():
    """Load Google credentials from a service-account JSON (GOOGLE_SERVICE_ACCOUNT_JSON,
    raw or base64) or an OAuth token file (GOOGLE_TOKEN_JSON). Returns None if none
    configured."""
    import base64
    import json as _json2
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if raw:
        try:
            if not raw.lstrip().startswith("{"):
                raw = base64.b64decode(raw).decode("utf-8")
            info = _json2.loads(raw)
            from google.oauth2 import service_account
            return service_account.Credentials.from_service_account_info(
                info, scopes=["https://www.googleapis.com/auth/calendar"])
        except Exception as e:
            app.logger.error("service-account creds load failed: %s", e)
            return None
    token_path = os.environ.get("GOOGLE_TOKEN_JSON", "")
    if token_path and os.path.exists(token_path):
        try:
            from google.oauth2.credentials import Credentials
            return Credentials.from_authorized_user_file(
                token_path, scopes=["https://www.googleapis.com/auth/calendar"])
        except Exception as e:
            app.logger.error("oauth token creds load failed: %s", e)
            return None
    return None


def _gcal_service():
    """Build a Google Calendar API client, or None if unavailable. Imports are
    guarded so the app runs without the google libraries installed (degradation)."""
    global _GCAL_SVC, _GCAL_TRIED
    if _GCAL_SVC is not None:
        return _GCAL_SVC
    if _GCAL_TRIED:
        return None
    _GCAL_TRIED = True
    try:
        from googleapiclient.discovery import build
    except Exception:
        app.logger.warning("google-api-python-client not installed — calendar disabled")
        return None
    creds = _gcal_credentials()
    if creds is None:
        return None
    try:
        _GCAL_SVC = build("calendar", "v3", credentials=creds, cache_discovery=False)
        return _GCAL_SVC
    except Exception as e:
        app.logger.error("gcal service build failed: %s", e)
        return None


def _calendar_busy(start_dt, end_dt) -> list:
    """Busy (start,end) intervals on the shared calendar in [start_dt, end_dt].
    Returns [] when no calendar is configured/reachable — graceful degradation to
    windows-only availability."""
    global _CAL_DISABLED_LOGGED
    if not COCKPIT_CALENDAR_ID:
        if not _CAL_DISABLED_LOGGED:
            app.logger.warning("COCKPIT_CALENDAR_ID unset — serving windows-only slots")
            _CAL_DISABLED_LOGGED = True
        return []
    svc = _gcal_service()
    if svc is None:
        return []
    try:
        body = {
            "timeMin": start_dt.astimezone(_tz2.utc).isoformat(),
            "timeMax": end_dt.astimezone(_tz2.utc).isoformat(),
            "timeZone": BOOKING_TZ,
            "items": [{"id": COCKPIT_CALENDAR_ID}],
        }
        resp = svc.freebusy().query(body=body).execute()
        out = []
        for blk in resp.get("calendars", {}).get(COCKPIT_CALENDAR_ID, {}).get("busy", []):
            bs = _dt2.fromisoformat(blk["start"].replace("Z", "+00:00"))
            be = _dt2.fromisoformat(blk["end"].replace("Z", "+00:00"))
            out.append((bs, be))
        return out
    except Exception as e:
        app.logger.error("freebusy query failed (degrading to windows-only): %s", e)
        return []


def _bookable_slots(date_from: _date2, date_to: _date2) -> list:
    """All free (start,end) slots between two local dates inclusive. Honours lead time,
    'now', the per-day booking cap, and busy intervals (expanded by the buffer) from the
    linked calendar (if configured)."""
    tz = _zurich()
    cfg = _booking_cfg()
    earliest = _dt2.now(tz) + _td2(days=cfg["lead_days"])
    cand_by_day: dict = {}
    d = date_from
    while d <= date_to:
        if not _is_blacked_out(d, cfg):
            for (s, e) in _window_slots_for_date(d, cfg):
                if s >= earliest:
                    cand_by_day.setdefault(d, []).append((s, e))
        d += _td2(days=1)
    if not cand_by_day:
        return []

    span_start = min(s for slots in cand_by_day.values() for (s, _e) in slots)
    span_end = max(e for slots in cand_by_day.values() for (_s, e) in slots)
    raw_busy = _calendar_busy(span_start, span_end)
    buf = _td2(minutes=cfg["buffer_minutes"])
    busy_exp = [(bs - buf, be + buf) for (bs, be) in raw_busy]

    out = []
    for day, slots in cand_by_day.items():
        # Per-day cap: count raw busy blocks intersecting this calendar day.
        if cfg["max_per_day"]:
            day_start = _dt2.combine(day, _time2(0, 0), tzinfo=tz)
            day_end = _dt2.combine(day, _time2(23, 59, 59), tzinfo=tz)
            booked = sum(1 for (bs, be) in raw_busy if _overlaps(bs, be, day_start, day_end))
            if booked >= cfg["max_per_day"]:
                continue
        for (s, e) in slots:
            if not any(_overlaps(s, e, bs, be) for (bs, be) in busy_exp):
                out.append((s, e))
    out.sort()
    return out


def _gcal_create_event(start_dt, end_dt, summary, description, location, attendee_email,
                       send_updates="all") -> str:
    """Create the event on the shared calendar (prospect invited). Returns the event
    id, or '' if the calendar isn't configured / fails — booking still proceeds.
    `send_updates` controls Google's own invite email ('all' or 'none')."""
    if not COCKPIT_CALENDAR_ID:
        return ""
    svc = _gcal_service()
    if svc is None:
        return ""
    try:
        ev = {
            "summary": summary,
            "description": description,
            "location": location,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": BOOKING_TZ},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": BOOKING_TZ},
            "guestsCanInviteOthers": True,  # mirrors Google "guests can invite others"
        }
        if attendee_email:
            ev["attendees"] = [{"email": attendee_email}]
        created = svc.events().insert(
            calendarId=COCKPIT_CALENDAR_ID, body=ev, sendUpdates=send_updates).execute()
        return created.get("id", "")
    except Exception as e:
        app.logger.error("gcal create event failed: %s", e)
        return ""


def _send_team_telegram(text: str) -> bool:
    """Notify the team group of a new booking. No-ops (logged) if no bot token."""
    if not COCKPIT_TELEGRAM_BOT_TOKEN:
        app.logger.warning("COCKPIT_TELEGRAM_BOT_TOKEN unset — booking Telegram skipped")
        return False
    try:
        import requests as _rq
        r = _rq.post(
            f"https://api.telegram.org/bot{COCKPIT_TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": COCKPIT_TEAM_CHAT_ID, "text": text,
                  "parse_mode": "HTML", "disable_web_page_preview": True},
            timeout=15)
        r.raise_for_status()
        return True
    except Exception as e:
        app.logger.error("team telegram failed: %s", e)
        return False


def _parse_plz_city(addr: str):
    """Best-effort: pull a 4-digit Swiss PLZ + city out of a free-text address."""
    m = re.search(r"(\d{4})\s+([A-Za-zÄÖÜäöüéèàç .\-]{2,40})", addr or "")
    if m:
        return m.group(1), m.group(2).strip().rstrip(",")
    return "", ""


@app.route("/book", methods=["GET"])
def book_page():
    return send_from_directory("static", "book.html")


# --- Team PWA (Phase 2): magic-link login + booking claim queue ---------------

@app.route("/team", methods=["GET"])
def team_page():
    # Magic link: ?k=<token> establishes the session identity, then redirect to a
    # clean /team URL (keeps the secret token out of history / the installed scope).
    tok = request.args.get("k")
    if tok:
        name = _team_tokens().get(tok)
        if name:
            session["team_member"] = name
            session.permanent = True
        return redirect("/team")
    return send_from_directory("static", "team.html")


@app.route("/team-sw.js", methods=["GET"])
def team_sw():
    # Served from root so the service-worker scope can cover /team and /api/team.
    resp = send_from_directory("static", "team-sw.js")
    resp.headers["Content-Type"] = "application/javascript"
    resp.headers["Service-Worker-Allowed"] = "/"
    resp.headers["Cache-Control"] = "no-cache"
    return resp


@app.route("/team.webmanifest", methods=["GET"])
def team_manifest():
    return send_from_directory("static", "team.webmanifest")


@app.route("/api/team/whoami", methods=["GET"])
def team_whoami():
    who = _team_member()
    if not who:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"name": who, "members": list(COCKPIT_TEAM_MEMBERS)})


@app.route("/api/team/appointments", methods=["GET"])
def team_appointments():
    if not _team_member():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        import notion_session as _ns
        if not (_ns.available() and COCKPIT_APPOINTMENTS_DB_ID):
            return jsonify({"appointments": [], "me": _team_member(),
                            "warning": "Notion/Termine DB not configured"})
        rows = _ns.list_appointments(COCKPIT_APPOINTMENTS_DB_ID)
        return jsonify({"appointments": rows, "me": _team_member()})
    except Exception as e:
        app.logger.error("team appointments failed: %s", e)
        return jsonify({"error": "fetch failed"}), 500


@app.route("/api/team/appointments/<page_id>/claim", methods=["POST"])
def team_claim(page_id):
    who = _team_member()
    if not who:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    # Claim as yourself by default; allow claiming on behalf of another member.
    person = data.get("person") if data.get("person") in COCKPIT_TEAM_MEMBERS else who
    try:
        import notion_session as _ns
        _ns.claim_appointment(COCKPIT_APPOINTMENTS_DB_ID, page_id, person)
        appt = _ns.get_appointment(COCKPIT_APPOINTMENTS_DB_ID, page_id) or {}
    except Exception as e:
        app.logger.error("team claim failed: %s", e)
        return jsonify({"error": "claim failed"}), 500
    _send_team_telegram(f"✅ <b>{person}</b> übernimmt — {appt.get('name', 'Termin')}")
    return jsonify({"ok": True, "appointment": appt})


@app.route("/api/team/appointments/<page_id>/unclaim", methods=["POST"])
def team_unclaim(page_id):
    if not _team_member():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        import notion_session as _ns
        _ns.unclaim_appointment(COCKPIT_APPOINTMENTS_DB_ID, page_id)
        appt = _ns.get_appointment(COCKPIT_APPOINTMENTS_DB_ID, page_id) or {}
    except Exception as e:
        app.logger.error("team unclaim failed: %s", e)
        return jsonify({"error": "unclaim failed"}), 500
    return jsonify({"ok": True, "appointment": appt})


@app.route("/api/team/telegram/webhook", methods=["POST"])
def team_telegram_webhook():
    # Dedicated team bot's callback webhook (secret in the query string).
    if not COCKPIT_TELEGRAM_WEBHOOK_SECRET or \
            request.args.get("secret") != COCKPIT_TELEGRAM_WEBHOOK_SECRET:
        return jsonify({"ok": False}), 403
    update = request.get_json(silent=True) or {}
    cq = update.get("callback_query")
    if not cq:
        return jsonify({"ok": True})  # ignore non-callback updates
    data = cq.get("data") or ""
    msg = cq.get("message") or {}
    chat_id = (msg.get("chat") or {}).get("id")
    msg_id = msg.get("message_id")
    person = page_id = None
    try:
        if data.startswith("c:"):
            _, pid, idx = data.split(":", 2)
            person = COCKPIT_TEAM_MEMBERS[int(idx)]
            page_id = _dash_uuid(pid)
    except Exception:
        pass
    if not (person and page_id):
        _team_bot_api("answerCallbackQuery",
                      {"callback_query_id": cq.get("id"), "text": "Ungültig"})
        return jsonify({"ok": True})
    ok = False
    try:
        import notion_session as _ns
        ok = _ns.claim_appointment(COCKPIT_APPOINTMENTS_DB_ID, page_id, person)
    except Exception as e:
        app.logger.error("telegram claim failed: %s", e)
    _team_bot_api("answerCallbackQuery", {
        "callback_query_id": cq.get("id"),
        "text": f"✅ {person} übernimmt" if ok else "Fehler beim Übernehmen"})
    if ok and chat_id and msg_id:
        new_text = (msg.get("text") or "Buchung") + f"\n\n✅ {person} übernimmt."
        _team_bot_api("editMessageText", {
            "chat_id": chat_id, "message_id": msg_id, "text": new_text,
            "reply_markup": {"inline_keyboard": []}})
    return jsonify({"ok": True})


@app.route("/api/team/telegram/setup-webhook", methods=["POST"])
def team_setup_webhook():
    if not _cockpit_auth_ok():
        return jsonify({"error": "Unauthorized"}), 401
    if not (COCKPIT_TEAM_BOT_TOKEN and COCKPIT_TELEGRAM_WEBHOOK_SECRET):
        return jsonify({"error": "COCKPIT_TEAM_BOT_TOKEN or COCKPIT_TELEGRAM_WEBHOOK_SECRET unset"}), 400
    data = request.get_json(silent=True) or {}
    base = (data.get("base_url") or "https://cockpit.automatisierbar.ch").rstrip("/")
    url = f"{base}/api/team/telegram/webhook?secret={COCKPIT_TELEGRAM_WEBHOOK_SECRET}"
    r = _team_bot_api("setWebhook", {"url": url, "allowed_updates": ["callback_query"]})
    if r is None:
        return jsonify({"ok": False, "error": "team bot call failed"}), 500
    return jsonify(r.json()), r.status_code


@app.route("/api/book/slots", methods=["GET"])
def book_slots():
    """Bookable slots. ?date=YYYY-MM-DD for one day, else the next horizon grouped
    by day. Public (no auth)."""
    cfg = _booking_cfg()
    try:
        if request.args.get("date"):
            d = _date2.fromisoformat(request.args["date"])
            slots = _bookable_slots(d, d)
        else:
            today = _now_local().date()
            slots = _bookable_slots(today, _booking_end_date(today, cfg))
    except ValueError:
        return jsonify({"error": "bad date"}), 400
    days: dict = {}
    for (s, e) in slots:
        days.setdefault(s.date().isoformat(), []).append(
            {"start": s.isoformat(), "label": s.strftime("%H:%M")})
    out = [{"date": k, "slots": v} for k, v in sorted(days.items())]
    return jsonify({"slot_minutes": cfg["slot_minutes"], "tz": BOOKING_TZ, "days": out})


@app.route("/api/book/confirm", methods=["POST"])
def book_confirm():
    """Confirm a booking: validate → re-check slot → calendar event → match/create
    lead → Appointment row → team Telegram. Public (optional secret gate)."""
    data = request.get_json(silent=True) or {}
    if COCKPIT_BOOK_SECRET and data.get("secret") != COCKPIT_BOOK_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    phone = (data.get("phone") or "").strip()
    firma = (data.get("firma") or "").strip()
    adresse = (data.get("adresse") or "").strip()
    notiz = (data.get("notiz") or "").strip()[:2000]
    start_raw = (data.get("start") or "").strip()

    missing = [k for k, v in {"name": name, "email": email, "phone": phone,
                              "firma": firma, "adresse": adresse,
                              "start": start_raw}.items() if not v]
    if missing:
        return jsonify({"error": "Bitte alle Felder ausfüllen.", "fields": missing}), 400
    if not _EMAIL_RE.match(email):
        return jsonify({"error": "Bitte eine gültige E-Mail-Adresse angeben."}), 400

    tz = _zurich()
    try:
        start_dt = _dt2.fromisoformat(start_raw)
        start_dt = (start_dt.replace(tzinfo=tz) if start_dt.tzinfo is None
                    else start_dt.astimezone(tz))
    except ValueError:
        return jsonify({"error": "Ungültiger Termin."}), 400
    # Snapshot the config once; a config write landing mid-request could otherwise
    # give end_dt and the slot re-check different slot lengths (the re-check inside
    # _bookable_slots re-derives cfg — harmless, it's the stricter gate).
    cfg = _booking_cfg()
    slot_minutes = cfg["slot_minutes"]
    end_dt = start_dt + _td2(minutes=slot_minutes)

    # Enforce the booking horizon — the per-day re-check below doesn't bound the range.
    if start_dt.date() > _booking_end_date(_now_local().date(), cfg):
        return jsonify({"error": "Dieser Termin liegt außerhalb des Buchungszeitraums.",
                        "code": "out_of_horizon"}), 409

    # Re-check the slot is still offered + free (guards races + tampering).
    same_day = _bookable_slots(start_dt.date(), start_dt.date())
    if not any(abs((s - start_dt).total_seconds()) < 60 for (s, _e) in same_day):
        return jsonify({"error": "Dieser Termin ist leider nicht mehr verfügbar.",
                        "code": "slot_taken"}), 409

    when_label = start_dt.strftime("%d.%m.%Y %H:%M")
    summary = f"Prozessermittlung — {firma}"
    description = (f"Prozessermittlung (vor Ort) mit {name}\n"
                   f"Firma: {firma}\nTelefon: {phone}\nE-Mail: {email}\n"
                   f"Adresse: {adresse}"
                   + (f"\nNotiz: {notiz}" if notiz else "")
                   + "\n\nGebucht über cockpit.automatisierbar.ch")
    # If we'll send our own branded confirmation, suppress Google's duplicate invite.
    try:
        import cockpit_email as _ce
        _own_email = _ce.smtp_configured()
    except Exception:
        _own_email = False
    event_id = _gcal_create_event(start_dt, end_dt, summary, description, adresse, email,
                                  send_updates=("none" if _own_email else "all"))

    # Match or create the lead (best-effort — never blocks the booking).
    lead_id = ""
    try:
        import notion_session as _ns
        if _ns.available():
            plz, city = _parse_plz_city(adresse)
            lead_fields = {
                "Firma": firma, "Geschäftsführer / CEO": name,
                "email": email, "phone": phone,
            }
            if plz:
                lead_fields["postalCode"] = plz
            if city:
                lead_fields["city"] = city
            existing = _ns.find_lead_by_email_or_phone(email=email, phone=phone)
            if existing:
                lead_id = _ns.expand_lead(existing, lead_fields)
            else:
                lead_fields["Name"] = (f"{firma} {city}".strip() or firma or name)
                lead_fields["Context"] = (
                    "INBOUND BOOKING (Prozessermittlung vor Ort)\n"
                    f"Kontakt: {name}\nAdresse: {adresse}\nTermin: {when_label}")
                lead_fields["Outreach Channel"] = "E-Mail"
                lead_fields["Pipeline Stage"] = "Problem Interview"
                lead_fields["War-Room Status"] = "◑ Reagiert – Termin fixieren"
                lead_id = _ns.create_inbound_lead(lead_fields)
            _ns.append_booking_note(
                lead_id, f"Termin gebucht: {when_label}",
                [f"Prozessermittlung vor Ort bei {firma}",
                 f"Adresse: {adresse}",
                 f"Kontakt: {name} · {phone} · {email}",
                 (f"Notiz: {notiz}" if notiz else ""),
                 "Quelle: cockpit.automatisierbar.ch"])
    except Exception as e:
        app.logger.error("booking lead upsert failed: %s", e)

    # Write the Appointment row.
    appt_id = ""
    try:
        import notion_session as _ns
        if _ns.available() and COCKPIT_APPOINTMENTS_DB_ID:
            appt = _ns.create_appointment(COCKPIT_APPOINTMENTS_DB_ID, {
                "Name": f"Prozessermittlung — {firma} ({when_label})",
                "Lead": [lead_id] if lead_id else None,
                "Start": start_dt.isoformat(),
                "End": end_dt.isoformat(),
                "Status": "Gebucht",
                "Claimed By": "(unassigned)",
                "Calendar Event ID": event_id,
                "Quelle": "Cockpit Booking",
                "Kontakt": f"{name} · {phone} · {email}",
                "Adresse": adresse,
                "Notiz": notiz,
            })
            appt_id = (appt or {}).get("id", "")
    except Exception as e:
        app.logger.error("appointment write failed: %s", e)

    # Branded confirmation email + calendar invite (.ics) to the prospect. Graceful —
    # the booking is already done; a send failure just logs.
    try:
        import cockpit_email as _ce
        if not _ce.send_confirmation(
                to_email=email, to_name=name, when_label=when_label, address=adresse,
                slot_minutes=slot_minutes, start_dt=start_dt, end_dt=end_dt,
                summary=summary, description=description):
            app.logger.warning("confirmation email not sent (no mail credential or send failed)")
    except Exception as e:
        app.logger.error("confirmation email failed: %s", e)

    # Notify the team. With a dedicated team bot configured, the alert carries inline
    # claim buttons (taps handled by /api/team/telegram/webhook); otherwise the plain
    # operator-bot ping (the team PWA claim covers it either way).
    team_msg = ("📅 <b>Neue Buchung</b> (Prozessermittlung vor Ort) — <b>UNASSIGNED</b>\n"
                f"🏢 {firma}\n👤 {name} · {phone}\n📍 {adresse}\n"
                f"🕐 {when_label} ({slot_minutes} Min)\n❓ Wer übernimmt?")
    if not (COCKPIT_TEAM_BOT_TOKEN and appt_id and _send_team_claim_message(team_msg, appt_id)):
        _send_team_telegram(team_msg)

    return jsonify({"ok": True, "when": when_label, "slot_minutes": slot_minutes,
                    "calendar": bool(event_id)})


CONTACT_EMAIL = os.environ.get("COCKPIT_CONTACT_EMAIL", "info@automatisierbar.ch")


@app.route("/api/book/request", methods=["POST"])
def book_request():
    """Custom-request fallback: when no listed slot fits, capture a free-text request +
    contact details → notify the team on Telegram + log/upsert a Notion lead. Public."""
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    phone = (data.get("phone") or "").strip()
    firma = (data.get("firma") or "").strip()
    message = (data.get("message") or "").strip()

    missing = [k for k, v in {"name": name, "email": email,
                              "message": message}.items() if not v]
    if missing:
        return jsonify({"error": "Bitte Name, E-Mail und Ihre Nachricht ausfüllen.",
                        "fields": missing}), 400
    if not _EMAIL_RE.match(email):
        return jsonify({"error": "Bitte eine gültige E-Mail-Adresse angeben."}), 400

    try:
        import notion_session as _ns
        if _ns.available():
            existing = _ns.find_lead_by_email_or_phone(email=email, phone=phone)
            fields = {"Firma": firma, "Geschäftsführer / CEO": name,
                      "email": email, "phone": phone}
            if existing:
                lead_id = _ns.expand_lead(existing, fields)
            else:
                fields["Name"] = (firma or name)
                fields["Context"] = ("INBOUND TERMINANFRAGE (kein passender Slot)\n"
                                     f"Kontakt: {name}\nWunsch: {message}")
                fields["Outreach Channel"] = "E-Mail"
                fields["Pipeline Stage"] = "Problem Interview"
                fields["War-Room Status"] = "◑ Reagiert – Termin fixieren"
                lead_id = _ns.create_inbound_lead(fields)
            _ns.append_booking_note(
                lead_id, "Custom Terminanfrage (kein passender Slot)",
                [f"Von: {name} · {firma}", f"Kontakt: {phone} · {email}",
                 f"Wunsch: {message}", "Quelle: cockpit.automatisierbar.ch/book"])
    except Exception as e:
        app.logger.error("book_request lead upsert failed: %s", e)

    _send_team_telegram(
        "📨 <b>Custom Terminanfrage</b> (kein passender Slot)\n"
        f"🏢 {firma or '—'}\n👤 {name} · {phone or '—'}\n✉️ {email}\n📝 {message}")
    return jsonify({"ok": True})


# --- Remote availability-config endpoints (Hub v2·M5a) ------------------------

_HHMM_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _validate_booking_patch(patch: dict):
    """Validate + normalize a partial config update. Returns (clean, errors).
    A key set to JSON null means 'remove this override' and passes through as None."""
    clean, errors = {}, []
    int_rules = {"slot_minutes": (5, 480), "lead_days": (0, 60),
                 "horizon_days": (1, 365), "buffer_minutes": (0, 240),
                 "max_per_day": (0, 24)}
    for k, v in patch.items():
        if k not in _BOOKING_CFG_KEYS:
            errors.append(f"unknown key: {k}")
            continue
        if v is None:                                  # override removal
            clean[k] = None
            continue
        if k in int_rules:
            lo, hi = int_rules[k]
            if not (isinstance(v, int) and not isinstance(v, bool) and lo <= v <= hi):
                errors.append(f"{k}: expected int {lo}..{hi}")
            else:
                clean[k] = v
        elif k == "horizon_date":                      # "" = disable the fixed cap
            if not isinstance(v, str):
                errors.append("horizon_date: expected ISO date string, '' or null")
                continue
            v = v.strip()
            if v:
                try:
                    _date2.fromisoformat(v)
                except ValueError:
                    errors.append(f"horizon_date: bad ISO date {v!r}")
                    continue
            clean[k] = v
        elif k == "blackout_ranges":                   # whole-list replacement
            ok, out = isinstance(v, list) and len(v) <= 50, []
            if ok:
                for pair in v:
                    try:
                        a, b = pair
                        da, db = _date2.fromisoformat(a), _date2.fromisoformat(b)
                        if da > db:
                            raise ValueError
                        out.append([da.isoformat(), db.isoformat()])
                    except Exception:
                        ok = False
                        break
            if ok:
                clean[k] = out
            else:
                errors.append("blackout_ranges: expected list of [start,end] ISO dates,"
                              " start<=end, max 50")
        elif k == "windows":                           # whole-map replacement; absent day = closed
            ok, out = isinstance(v, dict), {}
            if ok:
                for day, wins in v.items():
                    if (str(day) not in {"0", "1", "2", "3", "4", "5", "6"}
                            or not isinstance(wins, list) or len(wins) > 4):
                        ok = False
                        break
                    dw = []
                    for w in wins:
                        try:
                            s, e = w
                        except Exception:
                            ok = False
                            break
                        if not (isinstance(s, str) and isinstance(e, str)
                                and _HHMM_RE.match(s) and _HHMM_RE.match(e) and s < e):
                            ok = False
                            break
                        dw.append([s, e])
                    if not ok:
                        break
                    out[str(day)] = dw
            if ok:
                clean[k] = out
            else:
                errors.append('windows: expected {"0".."6": [["HH:MM","HH:MM"], ...]}'
                              " with start<end, max 4 windows/day")
    return clean, errors


def _config_auth():
    """(ok, status). Inert by default: no COCKPIT_CONFIG_SECRET ⇒ 404 for everyone.
    Set ⇒ require X-Config-Secret (constant-time compare) OR the cockpit session."""
    if not COCKPIT_CONFIG_SECRET:
        return False, 404
    import hmac as _hmac
    if _hmac.compare_digest(request.headers.get("X-Config-Secret", ""),
                            COCKPIT_CONFIG_SECRET) or _cockpit_auth_ok():
        return True, 200
    return False, 403


@app.route("/api/book/config", methods=["GET"])
def book_config_get():
    """Effective availability config + which keys are overridden. Gated (see
    _config_auth); serves the Hub's /app/booking availability panel."""
    ok, status = _config_auth()
    if not ok:
        return jsonify({"error": "not found" if status == 404 else "Unauthorized"}), status
    cfg = _booking_cfg()
    effective = dict(
        cfg,
        blackout_ranges=[[a.isoformat(), b.isoformat()] for (a, b) in cfg["blackout_ranges"]],
        windows={str(k): [list(w) for w in v] for k, v in cfg["windows"].items()},
        horizon_date=cfg["horizon_date"] or None)
    ov = _booking_overrides()
    return jsonify({"effective": effective, "overrides": ov,
                    "overridden_keys": sorted(ov.keys()), "tz": BOOKING_TZ})


@app.route("/api/book/config", methods=["PUT", "POST"])
def book_config_put():
    """Partial availability-config update. null clears a key's override; an empty
    override set deletes the file (pristine defaults). Whole-value replacement for
    blackout_ranges/windows; a day absent from an overridden windows map is closed."""
    ok, status = _config_auth()
    if not ok:
        return jsonify({"error": "not found" if status == 404 else "Unauthorized"}), status
    patch = request.get_json(silent=True)
    if not isinstance(patch, dict):
        return jsonify({"error": "expected a JSON object"}), 400
    clean, errors = _validate_booking_patch(patch)
    if errors:
        return jsonify({"error": "validation failed", "details": errors}), 400
    with _BOOKING_CFG_LOCK:   # in-worker read-modify-write guard; cross-worker
        merged = dict(_booking_overrides())   # PUTs are last-write-wins (single admin)
        for k, v in clean.items():
            if v is None:
                merged.pop(k, None)
            else:
                merged[k] = v
        try:
            BOOKING_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            if merged:
                tmp = BOOKING_CONFIG_PATH.with_suffix(".json.tmp")
                tmp.write_text(_json.dumps(merged, indent=2), encoding="utf-8")
                os.replace(tmp, BOOKING_CONFIG_PATH)   # atomic; bumps mtime ⇒ cache busts
            else:
                BOOKING_CONFIG_PATH.unlink(missing_ok=True)  # empty ⇒ pristine default state
        except Exception as e:
            app.logger.error("booking config write failed: %s", e)
            return jsonify({"error": "write failed"}), 500
    return book_config_get()


# Default parent for the appointments DB: the Operations Cockpit page (the prod
# integration already has access to that page tree, so the new DB inherits it).
COCKPIT_PARENT_PAGE_ID = os.environ.get(
    "COCKPIT_PARENT_PAGE_ID", "311bebb0c2f980de89a0f3d463a0fbce")


@app.route("/api/cockpit/setup-appointments-db", methods=["POST"])
def cockpit_setup_appointments_db():
    """One-time: create the Termine/Appointments DB (owned by the prod Notion
    integration). Returns the new id to set as COCKPIT_APPOINTMENTS_DB_ID."""
    if not _cockpit_auth_ok():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    parent = (data.get("parent_page_id") or COCKPIT_PARENT_PAGE_ID).replace("-", "")
    if len(parent) != 32:
        return jsonify({"error": "parent_page_id must be a 32-char Notion page ID"}), 400
    formatted = f"{parent[0:8]}-{parent[8:12]}-{parent[12:16]}-{parent[16:20]}-{parent[20:32]}"
    try:
        import notion_session as _ns
        db_id = _ns.create_appointments_db(formatted)
        return jsonify({"ok": True, "database_id": db_id,
                        "next_step": f"Set COCKPIT_APPOINTMENTS_DB_ID={db_id}"})
    except Exception as e:
        app.logger.error("setup-appointments-db error: %s", e)
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Walk-in mode (Phase 1): field PWA — capture leads + record voice memos.
# Served at walkin.automatisierbar.ch (same app, own Caddy host + PWA scope).
# Reuses the team magic-link auth (same COCKPIT_TEAM_TOKENS, same 4 members).
# ---------------------------------------------------------------------------

@app.route("/walkin", methods=["GET"])
def walkin_page():
    # Magic link: ?k=<token> sets the session identity then redirects to a clean
    # /walkin (keeps the token out of history + the installed PWA scope).
    tok = request.args.get("k")
    if tok:
        name = _team_tokens().get(tok)
        if name:
            session["team_member"] = name
            session.permanent = True
        return redirect("/walkin")
    return send_from_directory("static", "walkin.html")


@app.route("/walkin-sw.js", methods=["GET"])
def walkin_sw():
    resp = send_from_directory("static", "walkin-sw.js")
    resp.headers["Content-Type"] = "application/javascript"
    resp.headers["Service-Worker-Allowed"] = "/"
    resp.headers["Cache-Control"] = "no-cache"
    return resp


@app.route("/walkin.webmanifest", methods=["GET"])
def walkin_manifest():
    return send_from_directory("static", "walkin.webmanifest")


@app.route("/api/walkin/whoami", methods=["GET"])
def walkin_whoami():
    who = _team_member()
    if not who:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"name": who, "members": list(COCKPIT_TEAM_MEMBERS)})


@app.route("/api/walkin/lead", methods=["POST"])
def walkin_create_lead():
    """Capture a walk-in: create/expand a Leads-DB row (tagged WALK IN BUT NO BAMFAM), paste
    the verbatim notes onto the lead page, and — when the chosen next step is the default
    E-Mail-Entwurf — enqueue an auto-draft job so the walk-in follow-up lands in the ENTERING
    person's mailbox (drafted server-side at /walkinmail quality by the walk-in-draft cron).
    Each write is best-effort + isolated."""
    who = _team_member()
    if not who:
        return jsonify({"error": "Unauthorized"}), 401
    p = request.get_json(silent=True) or {}

    import walkin_capture as _wc
    bad = _wc.validate_lead_payload(p)
    if bad:
        return jsonify({"error": "Pflichtfelder fehlen oder ungültig", "fields": bad}), 400
    walkin_date = (p.get("walkin_date") or "").strip() or _now_local().date().isoformat()
    next_action = (p.get("next_action") or "E-Mail-Entwurf erstellen").strip()
    next_detail = (p.get("next_action_detail") or "").strip()
    follow_up_date = (p.get("follow_up_date") or "").strip()
    # Cc addresses chosen at entry (the 5 mailboxes + none). Keep only @automatisierbar.ch, cap 5.
    cc = [a.strip() for a in (p.get("cc") or []) if isinstance(a, str)
          and a.strip().lower().endswith("@automatisierbar.ch")][:5]
    # Phase B interim storage: the next-step choice + specifics live in the lead note (no live
    # Leads-DB schema change yet). Migrates to real Nächster-Schritt / Follow-up-Datum props later.
    next_line = f"Nächster Schritt: {next_action}"
    if next_detail:
        next_line += f" — {next_detail}"
    if follow_up_date:
        next_line += f" (bis {follow_up_date})"

    import notion_session as _ns
    if not _ns.available():
        return jsonify({"error": "notion not configured"}), 503

    result = {"ok": True, "lead_id": None, "expanded": False, "draft_queued": False, "warnings": []}

    # (a) Leads DB — dedup by email/phone, then expand (empty-only) or create.
    try:
        fields = _wc.build_lead_fields(p, walkin_date)
        existing = _ns.find_lead_by_email_or_phone(
            email=fields.get("email", ""), phone=fields.get("phone", ""))
        if existing:
            result["lead_id"] = _ns.expand_lead(existing, fields)
            result["expanded"] = True
        else:
            result["lead_id"] = _ns.create_inbound_lead(fields)
        # Paste the verbatim notes onto the lead page body (1:1 traceability).
        _ns.append_booking_note(
            result["lead_id"], f"Walk-In Notiz ({walkin_date})",
            [(p.get("notes") or "").strip(), f"Erfasst von {who} · Walk-in mode", next_line])
    except Exception as e:
        app.logger.error("walkin lead write failed: %s", e)
        result["warnings"].append("lead_write_failed")

    if result["lead_id"] is None:
        return jsonify({"error": "Speichern fehlgeschlagen", **result}), 500

    # (b) Enqueue the auto-draft — for the next-step choices that warrant an email
    #     (E-Mail-Entwurf / Wir melden uns / Follow-up bis Datum). The chosen step shapes the
    #     draft's CTA + tone downstream. "Kein Interesse" / "Sonstiges" record intent + draft nothing.
    if next_action in _wc.DRAFTING_NEXT_ACTIONS:
        try:
            import walkin_draft_queue as _wq
            _wq.enqueue_job({
                "entering_person": who, "cc": cc, "next_action": next_action,
                "next_action_detail": next_detail, "follow_up_date": follow_up_date,
                "lead_page_id": result["lead_id"], "walkin_date": walkin_date,
                "company": (p.get("company") or "").strip(),
                "contact": (p.get("contact") or "").strip(),
                "role": (p.get("role") or "").strip(),
                "email": (p.get("email") or "").strip(),
                "website": (p.get("website") or "").strip(),
                "phone": (p.get("phone") or "").strip(),
                "city": (p.get("city") or "").strip(),
                "notes": (p.get("notes") or "").strip(),
            })
            result["draft_queued"] = True
        except Exception as e:
            app.logger.error("walkin draft enqueue failed: %s", e)
            result["warnings"].append("draft_enqueue_failed")

    return jsonify(result)


@app.route("/api/walkin/card-ocr", methods=["POST"])
def walkin_card_ocr():
    """Read a business-card photo with Claude Vision and return prefill fields for the
    Neuer-Lead form (name/company/role/email/phone/website/city/…). Advisory only, like
    /api/spesen/ocr: even a failure returns 200 with ok=false so the operator just fills
    the form manually and saves via /api/walkin/lead. The photo is used for extraction
    only and is never stored."""
    if not _team_member():
        return jsonify({"error": "Unauthorized"}), 401
    f = request.files.get("file") or request.files.get("beleg")
    if not f:
        return jsonify({"error": "Bild fehlt (multipart 'file')"}), 400
    content = f.read()
    if not content:
        return jsonify({"error": "leeres Bild"}), 400
    if len(content) > SPESEN_MAX_IMAGE_BYTES:  # reuse the shared image size cap
        return jsonify({"error": f"Bild zu gross (max {SPESEN_MAX_IMAGE_MB} MB)"}), 413
    import walkin_card_ocr as _card
    return jsonify(_card.extract_card(content, f.mimetype or ""))


@app.route("/api/walkin/memo", methods=["POST"])
def walkin_upload_memo():
    """Accept a recorded voice memo (multipart), store it on the VPS with a pending
    sidecar. The daily cron transcribes it later — the app never plays it back."""
    who = _team_member()
    if not who:
        return jsonify({"error": "Unauthorized"}), 401
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "file field missing (multipart/form-data)"}), 400
    content = f.read()
    if not content:
        return jsonify({"error": "leere Datei"}), 400
    if len(content) > WALKIN_MAX_AUDIO_BYTES:
        return jsonify({"error": f"Audio zu gross (max {WALKIN_MAX_AUDIO_MB} MB)"}), 413

    import walkin_capture as _wc
    try:
        sidecar = _wc.save_voice_memo(
            recorder=who, content=content, mime=(f.mimetype or ""),
            orig_filename=(f.filename or ""), duration_sec=request.form.get("duration_sec"))
    except ValueError as e:
        return jsonify({"error": str(e)}), 415
    except Exception as e:
        app.logger.error("walkin memo save failed: %s", e)
        return jsonify({"error": "Speichern fehlgeschlagen"}), 500
    return jsonify({"ok": True, "memo": sidecar["audio"], "status": "pending"})


@app.route("/api/walkin/memos", methods=["GET"])
def walkin_list_memos():
    """Read-only status list so the PWA can confirm memos landed + show counts."""
    if not _team_member():
        return jsonify({"error": "Unauthorized"}), 401
    import walkin_capture as _wc
    try:
        return jsonify({"memos": _wc.list_memos_compact(), **_wc.memo_stats()})
    except Exception as e:
        app.logger.error("walkin list memos failed: %s", e)
        return jsonify({"error": "list failed"}), 500


@app.route("/api/walkin/setup-kb-db", methods=["POST"])
def walkin_setup_kb_db():
    """One-time (operator only): create the Walk-in Knowledge Base DB (owned by the
    prod integration). Returns the id to set as WALKIN_KB_DB_ID."""
    if not _cockpit_auth_ok():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    parent = (data.get("parent_page_id") or COCKPIT_PARENT_PAGE_ID).replace("-", "")
    if len(parent) != 32:
        return jsonify({"error": "parent_page_id must be a 32-char Notion page ID"}), 400
    formatted = f"{parent[0:8]}-{parent[8:12]}-{parent[12:16]}-{parent[16:20]}-{parent[20:32]}"
    try:
        import notion_session as _ns
        db_id = _ns.create_walkin_kb_db(formatted)
        return jsonify({"ok": True, "database_id": db_id,
                        "next_step": f"Set WALKIN_KB_DB_ID={db_id}"})
    except Exception as e:
        app.logger.error("setup-walkin-kb-db error: %s", e)
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# KnowSpesen — client expense PWA (knowspesen.automatisierbar.ch).
# Separate sibling service (KNOWSPESEN_HOME=1), own SQLite (SPESEN_DB_PATH), own
# per-user tokens (knowbodies.login_token). Isolated from the cockpit ops data.
# Capture a receipt photo -> Claude Vision prefill -> confirm -> save; month-close
# bundles PDF+Excel+receipts into a ZIP the KnowBody mails to the accountant.
# ---------------------------------------------------------------------------

SPESEN_MAX_IMAGE_MB = _env_int("SPESEN_MAX_IMAGE_MB", 12)
SPESEN_MAX_IMAGE_BYTES = SPESEN_MAX_IMAGE_MB * 1024 * 1024
SPESEN_ACCOUNTANT_EMAIL = os.environ.get("SPESEN_ACCOUNTANT_EMAIL", "")


def _spesen_member():
    """Identify the logged-in KnowBody: a validated session, else a ?k=/header
    token. Returns the knowbody dict or None."""
    from spesen import db as _sdb
    kb_id = session.get("spesen_kb_id")
    if kb_id:
        kb = _sdb.get_knowbody(kb_id)
        if kb and kb.get("active"):
            return kb
    tok = request.args.get("k") or request.headers.get("X-Spesen-Token") or ""
    if tok:
        return _sdb.get_knowbody_by_token(tok)
    return None


@app.route("/spesen", methods=["GET"])
def spesen_page():
    # Magic link: ?k=<token> sets the session identity then redirects to a clean
    # /spesen (token out of history + the installed PWA scope).
    tok = request.args.get("k")
    if tok:
        from spesen import db as _sdb
        kb = _sdb.get_knowbody_by_token(tok)
        if kb:
            session["spesen_kb_id"] = kb["id"]
            session.permanent = True
        return redirect("/spesen")
    return send_from_directory("static", "spesen.html")


@app.route("/spesen-sw.js", methods=["GET"])
def spesen_sw():
    resp = send_from_directory("static", "spesen-sw.js")
    resp.headers["Content-Type"] = "application/javascript"
    resp.headers["Service-Worker-Allowed"] = "/"
    resp.headers["Cache-Control"] = "no-cache"
    return resp


@app.route("/spesen.webmanifest", methods=["GET"])
def spesen_manifest():
    return send_from_directory("static", "spesen.webmanifest")


@app.route("/api/spesen/whoami", methods=["GET"])
def spesen_whoami():
    kb = _spesen_member()
    if not kb:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"id": kb["id"], "name": kb["name"], "email": kb.get("email")})


@app.route("/api/spesen/config", methods=["GET"])
def spesen_config():
    if not _spesen_member():
        return jsonify({"error": "Unauthorized"}), 401
    from spesen import db as _sdb, config as _cfg
    prc = {p["code"]: p for p in _sdb.list_pauschalen()}
    meals = {}
    for slot, code in _cfg.VERPFLEGUNG_MEALS.items():
        p = prc.get(code, {})
        meals[slot] = {"code": code, "label": p.get("label", slot),
                       "rate_chf": p.get("rate_chf"), "is_placeholder": bool(p.get("is_placeholder", True))}
    km = prc.get(_cfg.KM_CODE, {})
    return jsonify({
        "categories": _cfg.CATEGORIES,
        "subcategory_hints": _cfg.SUBCATEGORY_HINTS,
        "payment_methods": _cfg.PAYMENT_METHODS,
        "currencies": _cfg.CURRENCIES,
        "pauschalen": _sdb.list_pauschalen(),
        "accountant_email": SPESEN_ACCOUNTANT_EMAIL,
        "attestation_text": _cfg.ATTESTATION_TEXT,
        "verpflegung": {"meals": meals, "deckung_options": _cfg.DECKUNG_OPTIONS},
        "km": {"rate_chf": km.get("rate_chf"), "factor": _cfg.KM_FIRMA_FACTOR,
               "is_placeholder": bool(km.get("is_placeholder", True))},
    })


@app.route("/api/spesen/ocr", methods=["POST"])
def spesen_ocr():
    if not _spesen_member():
        return jsonify({"error": "Unauthorized"}), 401
    f = request.files.get("beleg") or request.files.get("file")
    if not f:
        return jsonify({"error": "Bild fehlt (multipart 'beleg')"}), 400
    content = f.read()
    if not content:
        return jsonify({"error": "leeres Bild"}), 400
    if len(content) > SPESEN_MAX_IMAGE_BYTES:
        return jsonify({"error": f"Bild zu gross (max {SPESEN_MAX_IMAGE_MB} MB)"}), 413
    from spesen import ocr as _ocr
    # OCR is advisory: even a failure returns 200 with ok=false so the form stays manual.
    return jsonify(_ocr.extract_receipt(content, f.mimetype or ""))


@app.route("/api/spesen/convert", methods=["POST"])
def spesen_convert():
    if not _spesen_member():
        return jsonify({"error": "Unauthorized"}), 401
    d = request.get_json(silent=True) or {}
    from spesen import currency as _cur, capture as _cap
    betrag = _cap.parse_amount(d.get("betrag"))
    return jsonify(_cur.convert_to_chf(betrag, d.get("waehrung") or "CHF", d.get("datum") or ""))


@app.route("/api/spesen/beleg", methods=["POST"])
def spesen_create_beleg():
    kb = _spesen_member()
    if not kb:
        return jsonify({"error": "Unauthorized"}), 401
    from spesen import db as _sdb, capture as _cap, currency as _cur, pauschalen as _pau

    form = request.form.to_dict()
    bad = _cap.validate_beleg_payload(form)
    if bad:
        return jsonify({"error": "Pflichtfelder fehlen oder ungültig", "fields": bad}), 400

    art = (form.get("art") or "beleg").strip()
    datum = form.get("datum")
    resolved = {"art": art, "kurs_quelle": None, "wechselkurs": None, "ocr_confidence": None}
    try:
        resolved["ocr_confidence"] = float(form["ocr_confidence"]) if form.get("ocr_confidence") else None
    except (TypeError, ValueError):
        resolved["ocr_confidence"] = None

    if art == "pauschale":
        code = (form.get("pauschale_code") or "").strip()
        res = _pau.resolve_by_code(code, menge=(form.get("menge") or 1), tariffs=_sdb.list_pauschalen())
        if not res["ok"]:
            return jsonify({"error": res.get("error") or "Pauschaltarif nicht verfügbar",
                            "placeholder": res.get("is_placeholder", False)}), 422
        resolved.update({"betrag_chf": res["betrag_chf"], "betrag_original": res["betrag_chf"],
                         "waehrung": "CHF", "kurs_quelle": "PAUSCHALE", "pauschale_code": code})
    else:
        betrag_original = _cap.parse_amount(form.get("betrag_original") or form.get("betrag"))
        if betrag_original is None:
            return jsonify({"error": "Betrag ungültig"}), 400
        waehrung = (form.get("waehrung") or "CHF").strip().upper()
        manual_chf = form.get("betrag_chf")
        if manual_chf not in (None, ""):
            mc = _cap.parse_amount(manual_chf)
            if mc is None:
                return jsonify({"error": "CHF-Betrag ungültig"}), 400
            mc = round(mc, 2)
            resolved.update({"betrag_chf": mc, "betrag_original": betrag_original, "waehrung": waehrung,
                             "kurs_quelle": "MANUELL",
                             "wechselkurs": (round(mc / betrag_original, 6) if betrag_original else None)})
        else:
            conv = _cur.convert_to_chf(betrag_original, waehrung, datum)
            if not conv["ok"]:
                return jsonify({"error": conv.get("error") or "Wechselkurs nicht verfügbar",
                                "need_manual_chf": True}), 422
            resolved.update({"betrag_chf": conv["betrag_chf"], "betrag_original": betrag_original,
                             "waehrung": waehrung, "wechselkurs": conv["wechselkurs"],
                             "kurs_quelle": conv["kurs_quelle"]})

    resolved["ist_kaffeekasse"] = _pau.is_kaffeekasse(resolved["betrag_chf"], ist_pauschale=(art == "pauschale"))

    bild_pfad = None
    f = request.files.get("beleg") or request.files.get("file")
    if f:
        content = f.read()
        if content:
            if len(content) > SPESEN_MAX_IMAGE_BYTES:
                return jsonify({"error": f"Bild zu gross (max {SPESEN_MAX_IMAGE_MB} MB)"}), 413
            try:
                bild_pfad = _cap.save_receipt_image(kb["name"], content, f.mimetype or "", f.filename or "")
            except ValueError as e:
                return jsonify({"error": str(e)}), 415
    resolved["bild_pfad"] = bild_pfad

    fields = _cap.build_beleg_fields(form, kb["id"], resolved)
    try:
        beleg_id = _sdb.insert_beleg(fields)
    except Exception as e:
        app.logger.error("spesen insert failed: %s", e)
        return jsonify({"error": "Speichern fehlgeschlagen"}), 500

    warnung = ""
    if resolved["ist_kaffeekasse"]:
        warnung = ("Unter CHF 50: wird als Kaffeekasse geführt und NICHT in die "
                   "Monatsabrechnung aufgenommen.")
    return jsonify({"ok": True, "beleg_id": beleg_id, "betrag_chf": resolved["betrag_chf"],
                    "ist_kaffeekasse": bool(resolved["ist_kaffeekasse"]), "warnung": warnung})


@app.route("/api/spesen/belege", methods=["GET"])
def spesen_list_belege():
    kb = _spesen_member()
    if not kb:
        return jsonify({"error": "Unauthorized"}), 401
    from spesen import db as _sdb
    month = request.args.get("month") or _now_local().strftime("%Y-%m")
    belege = _sdb.list_belege(kb["id"], month)
    active = [b for b in belege if not b["ist_kaffeekasse"]]
    total = round(sum(float(b["betrag_chf"] or 0) for b in active), 2)
    weiter = round(sum(float(b["betrag_chf"] or 0) for b in active if b["weiterverrechenbar"]), 2)
    kaffee = round(sum(float(b["betrag_chf"] or 0) for b in belege if b["ist_kaffeekasse"]), 2)
    close = _sdb.get_close(kb["id"], month)
    return jsonify({"month": month, "belege": belege, "total_chf": total, "weiter_chf": weiter,
                    "kaffeekasse_chf": kaffee, "anzahl": len(active),
                    "closed": bool(close), "close": close,
                    "receipts_stored": sum(1 for b in belege if b.get("bild_pfad")),
                    "last_backup_at": _sdb.meta_get("last_backup_at")})


@app.route("/api/spesen/kaffeekasse", methods=["GET"])
def spesen_kaffeekasse():
    """Shared Kaffeekasse overview across ALL KnowBodies for a month: team total +
    per-person breakdown + the items. The coffee fund is communal, so every member
    sees it."""
    kb = _spesen_member()
    if not kb:
        return jsonify({"error": "Unauthorized"}), 401
    from spesen import db as _sdb
    month = request.args.get("month") or _now_local().strftime("%Y-%m")
    ov = _sdb.kaffeekasse_overview(month)
    ov["month"] = month
    return jsonify(ov)


@app.route("/api/spesen/beleg/<int:beleg_id>", methods=["PATCH"])
def spesen_update_beleg(beleg_id):
    """Full-fidelity correction: every field the capture form has is editable here
    (the app reuses the capture form as the single editor). Amount/currency go
    through the same FX resolution as create; Kaffeekasse can be forced/unforced via
    an explicit override, else it is recomputed from the new amount."""
    kb = _spesen_member()
    if not kb:
        return jsonify({"error": "Unauthorized"}), 401
    from spesen import db as _sdb, pauschalen as _pau, capture as _cap, currency as _cur
    existing = _sdb.get_beleg(beleg_id)
    if not existing or existing["knowbody_id"] != kb["id"]:
        return jsonify({"error": "Nicht gefunden"}), 404
    if existing["monatsabschluss_id"] is not None:
        return jsonify({"error": "Monat bereits abgeschlossen"}), 409
    d = request.get_json(silent=True) or {}
    art = existing["art"]

    # simple text / flag fields
    allowed = {k: d[k] for k in ("haendler", "beleg_datum", "kategorie", "unterkategorie",
                                 "zahlungsart", "projekt", "notiz") if k in d}
    if "weiterverrechenbar" in d:
        allowed["weiterverrechenbar"] = 1 if _cap.to_bool(d["weiterverrechenbar"]) else 0

    # amount / currency — same resolution path as create (FX or manual CHF)
    if art == "pauschale" and ("pauschale_code" in d or "menge" in d):
        code = (d.get("pauschale_code") or existing.get("pauschale_code") or "").strip()
        res = _pau.resolve_by_code(code, menge=(d.get("menge") or 1), tariffs=_sdb.list_pauschalen())
        if not res["ok"]:
            return jsonify({"error": res.get("error") or "Pauschaltarif nicht verfügbar",
                            "placeholder": res.get("is_placeholder", False)}), 422
        allowed.update({"pauschale_code": code, "betrag_chf": res["betrag_chf"],
                        "betrag_original": res["betrag_chf"], "waehrung": "CHF",
                        "wechselkurs": None, "kurs_quelle": "PAUSCHALE"})
    elif art == "beleg" and ("betrag_original" in d or "waehrung" in d or "betrag_chf" in d):
        bo = _cap.parse_amount(d["betrag_original"]) if "betrag_original" in d else _cap.parse_amount(existing.get("betrag_original"))
        if bo is None:
            return jsonify({"error": "Betrag ungültig"}), 400
        waehrung = (d.get("waehrung") or existing.get("waehrung") or "CHF").strip().upper()
        datum = (d.get("beleg_datum") or existing.get("beleg_datum") or "")
        manual_chf = d.get("betrag_chf")
        if manual_chf not in (None, ""):
            mc = _cap.parse_amount(manual_chf)
            if mc is None:
                return jsonify({"error": "CHF-Betrag ungültig"}), 400
            allowed.update({"betrag_chf": round(mc, 2), "betrag_original": bo, "waehrung": waehrung,
                            "kurs_quelle": "MANUELL",
                            "wechselkurs": (round(mc / bo, 6) if bo else None)})
        elif waehrung == "CHF":
            allowed.update({"betrag_chf": round(bo, 2), "betrag_original": bo, "waehrung": "CHF",
                            "wechselkurs": 1.0, "kurs_quelle": "DIREKT_CHF"})
        else:
            conv = _cur.convert_to_chf(bo, waehrung, datum)
            if not conv["ok"]:
                return jsonify({"error": conv.get("error") or "Wechselkurs nicht verfügbar",
                                "need_manual_chf": True}), 422
            allowed.update({"betrag_chf": conv["betrag_chf"], "betrag_original": bo,
                            "waehrung": waehrung, "wechselkurs": conv["wechselkurs"],
                            "kurs_quelle": conv["kurs_quelle"]})

    # Kaffeekasse: explicit manual override wins; else recompute from the new amount
    if "ist_kaffeekasse" in d:
        allowed["ist_kaffeekasse"] = 1 if _cap.to_bool(d["ist_kaffeekasse"]) else 0
    elif "betrag_chf" in allowed:
        allowed["ist_kaffeekasse"] = 1 if _pau.is_kaffeekasse(
            allowed["betrag_chf"], ist_pauschale=(art == "pauschale")) else 0

    if not allowed:
        return jsonify({"ok": False, "error": "Nichts zu ändern"}), 400
    ok = _sdb.update_beleg(beleg_id, allowed)
    return jsonify({"ok": ok})


@app.route("/api/spesen/beleg/<int:beleg_id>/image", methods=["GET"])
def spesen_beleg_image(beleg_id):
    """Serve the stored receipt (image or PDF) so the KnowBody can re-check it while
    correcting the beleg. Owner-scoped; the image lives on disk, only the basename is
    in the DB."""
    kb = _spesen_member()
    if not kb:
        return jsonify({"error": "Unauthorized"}), 401
    from spesen import db as _sdb, capture as _cap
    b = _sdb.get_beleg(beleg_id)
    if not b or b["knowbody_id"] != kb["id"]:
        return jsonify({"error": "Nicht gefunden"}), 404
    if not b.get("bild_pfad"):
        return jsonify({"error": "Kein Beleg-Bild"}), 404
    # bild_pfad is a server-generated basename; basename() again defends against traversal
    path = _cap.abs_path_for(os.path.basename(b["bild_pfad"]))
    if not os.path.isfile(path):
        return jsonify({"error": "Datei nicht gefunden"}), 404
    import mimetypes
    mt = mimetypes.guess_type(path)[0] or "application/octet-stream"
    return send_file(path, mimetype=mt)


@app.route("/api/spesen/beleg/<int:beleg_id>", methods=["DELETE"])
def spesen_delete_beleg(beleg_id):
    kb = _spesen_member()
    if not kb:
        return jsonify({"error": "Unauthorized"}), 401
    from spesen import db as _sdb
    existing = _sdb.get_beleg(beleg_id)
    if not existing or existing["knowbody_id"] != kb["id"]:
        return jsonify({"error": "Nicht gefunden"}), 404
    if not _sdb.delete_beleg(beleg_id):
        return jsonify({"error": "Monat bereits abgeschlossen"}), 409
    return jsonify({"ok": True})


@app.route("/api/spesen/month-close", methods=["POST"])
def spesen_month_close():
    kb = _spesen_member()
    if not kb:
        return jsonify({"error": "Unauthorized"}), 401
    d = request.get_json(silent=True) or {}
    month = (d.get("month") or "").strip() or _now_local().strftime("%Y-%m")
    from spesen import month_close as _mc, config as _cfg
    # Kontroll-Bestätigung: the KnowBody must type the exact sentence (their liability).
    attest_text = (d.get("bestaetigung_text") or "").strip()
    if not _cfg.attestation_matches(attest_text):
        return jsonify({"error": "Bitte den Bestätigungssatz exakt abtippen.",
                        "need_attest": True}), 400
    attest = {"text": attest_text, "von": kb.get("name", ""),
              "am": _now_local().isoformat(timespec="seconds")}
    try:
        res = _mc.close_month(kb["id"], month, accountant_email=SPESEN_ACCOUNTANT_EMAIL, attest=attest)
    except Exception as e:
        app.logger.error("spesen month-close failed: %s", e)
        return jsonify({"error": "Abschluss fehlgeschlagen"}), 500
    if not res.get("ok"):
        return jsonify({"error": res.get("error", "Abschluss fehlgeschlagen")}), 400
    return jsonify({"ok": True, "month": month, "total_chf": res["total_chf"],
                    "anzahl": res["anzahl"], "summe_weiter_chf": res["summe_weiter_chf"],
                    "email": res["email"], "download": f"/api/spesen/download?month={month}"})


@app.route("/api/spesen/download", methods=["GET"])
def spesen_download_zip():
    kb = _spesen_member()
    if not kb:
        return jsonify({"error": "Unauthorized"}), 401
    from spesen import db as _sdb
    month = request.args.get("month") or _now_local().strftime("%Y-%m")
    close = _sdb.get_close(kb["id"], month)
    if not close or not close.get("zip_pfad") or not os.path.isfile(close["zip_pfad"]):
        return jsonify({"error": "Kein Abschluss-ZIP vorhanden"}), 404
    return send_file(close["zip_pfad"], mimetype="application/zip", as_attachment=True,
                     download_name=os.path.basename(close["zip_pfad"]))


@app.route("/api/spesen/month-reopen", methods=["POST"])
def spesen_month_reopen():
    """Undo a month close so the KnowBody can edit again. Unlocks the belege."""
    kb = _spesen_member()
    if not kb:
        return jsonify({"error": "Unauthorized"}), 401
    d = request.get_json(silent=True) or {}
    month = (d.get("month") or "").strip() or _now_local().strftime("%Y-%m")
    from spesen import db as _sdb
    return jsonify({"ok": _sdb.reopen_close(kb["id"], month)})


# --- Verpflegungs- & Kilometerblatt (monthly per-diem grid) -----------------

_SPESEN_MONTH_RE = re.compile(r"^\d{4}-\d{2}$")
_SPESEN_DAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_WD_DE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


def _verpflegung_scaffold(kb_id, month):
    """Build one entry per calendar day of `month`, merging any stored grid rows onto
    empty defaults, so the UI always gets a full month."""
    import calendar
    from datetime import date
    from spesen import db as _sdb
    y, mo = int(month[:4]), int(month[5:7])
    ndays = calendar.monthrange(y, mo)[1]
    stored = {r["tag_datum"]: r for r in _sdb.list_verpflegung_month(kb_id, month)}
    days = []
    for dd in range(1, ndays + 1):
        dt = date(y, mo, dd)
        iso = dt.isoformat()
        r = stored.get(iso, {})
        days.append({
            "datum": iso, "weekday": _WD_DE[dt.weekday()], "is_weekend": dt.weekday() >= 5,
            "arb_vormittag": r.get("arb_vormittag", 0), "arb_nachmittag": r.get("arb_nachmittag", 0),
            "arb_spaet": r.get("arb_spaet", 0), "arb_frueh": r.get("arb_frueh", 0),
            "fr_claimed": r.get("fr_claimed", 0), "fr_deckung": r.get("fr_deckung"),
            "mi_claimed": r.get("mi_claimed", 0), "mi_deckung": r.get("mi_deckung"),
            "na_claimed": r.get("na_claimed", 0), "na_deckung": r.get("na_deckung"),
            "bemerkung": r.get("bemerkung"),
        })
    return days


@app.route("/api/spesen/verpflegung", methods=["GET"])
def spesen_verpflegung_get():
    kb = _spesen_member()
    if not kb:
        return jsonify({"error": "Unauthorized"}), 401
    month = request.args.get("month") or _now_local().strftime("%Y-%m")
    if not _SPESEN_MONTH_RE.match(month):
        return jsonify({"error": "Monat ungültig (YYYY-MM)"}), 400
    from spesen import db as _sdb
    km = _sdb.get_kilometer_monat(kb["id"], month) or {}
    close = _sdb.get_close(kb["id"], month)
    return jsonify({
        "month": month,
        "days": _verpflegung_scaffold(kb["id"], month),
        "kilometer": {"km_start": km.get("km_start"), "km_end": km.get("km_end"),
                      "km_firma_override": km.get("km_firma_override")},
        "summary": _sdb.compute_verpflegung_summary(kb["id"], month),
        "closed": bool(close),
    })


@app.route("/api/spesen/verpflegung/<datum>", methods=["PATCH"])
def spesen_verpflegung_patch(datum):
    kb = _spesen_member()
    if not kb:
        return jsonify({"error": "Unauthorized"}), 401
    if not _SPESEN_DAY_RE.match(datum or ""):
        return jsonify({"error": "Datum ungültig (YYYY-MM-DD)"}), 400
    from spesen import db as _sdb, config as _cfg, capture as _cap
    month = datum[:7]
    if _sdb.get_close(kb["id"], month):
        return jsonify({"error": "Monat bereits abgeschlossen"}), 409
    d = request.get_json(silent=True) or {}
    fields = {}
    for k in ("arb_vormittag", "arb_nachmittag", "arb_spaet", "arb_frueh",
              "fr_claimed", "mi_claimed", "na_claimed"):
        if k in d:
            fields[k] = 1 if _cap.to_bool(d[k]) else 0
    for k in ("fr_deckung", "mi_deckung", "na_deckung"):
        if k in d:
            v = d[k]
            if v in (None, "", "null"):
                fields[k] = None
            elif v in _cfg.DECKUNG_OPTIONS:
                fields[k] = v
            else:
                return jsonify({"error": f"Deckung ungültig: {v}"}), 400
    if "bemerkung" in d:
        b = (str(d["bemerkung"]).strip() or None)
        fields["bemerkung"] = b[:500] if b else None
    if not fields:
        return jsonify({"error": "Nichts zu ändern"}), 400
    rid = _sdb.upsert_verpflegung_tag(kb["id"], datum, fields)
    if not rid:
        return jsonify({"error": "Monat bereits abgeschlossen"}), 409
    return jsonify({"ok": True, "day": _sdb.get_verpflegung_tag(kb["id"], datum),
                    "summary": _sdb.compute_verpflegung_summary(kb["id"], month)})


@app.route("/api/spesen/kilometer", methods=["PATCH"])
def spesen_kilometer_patch():
    kb = _spesen_member()
    if not kb:
        return jsonify({"error": "Unauthorized"}), 401
    month = request.args.get("month") or _now_local().strftime("%Y-%m")
    if not _SPESEN_MONTH_RE.match(month):
        return jsonify({"error": "Monat ungültig (YYYY-MM)"}), 400
    from spesen import db as _sdb, capture as _cap
    if _sdb.get_close(kb["id"], month):
        return jsonify({"error": "Monat bereits abgeschlossen"}), 409
    d = request.get_json(silent=True) or {}
    fields = {}
    for k in ("km_start", "km_end", "km_firma_override"):
        if k in d:
            fields[k] = _cap.parse_amount(d[k]) if d[k] not in (None, "") else None
    if not fields:
        return jsonify({"error": "Nichts zu ändern"}), 400
    rid = _sdb.upsert_kilometer_monat(kb["id"], month, fields)
    if not rid:
        return jsonify({"error": "Monat bereits abgeschlossen"}), 409
    km = _sdb.get_kilometer_monat(kb["id"], month) or {}
    return jsonify({"ok": True,
                    "kilometer": {"km_start": km.get("km_start"), "km_end": km.get("km_end"),
                                  "km_firma_override": km.get("km_firma_override")},
                    "summary": _sdb.compute_verpflegung_summary(kb["id"], month)})


@app.route("/api/spesen/feedback", methods=["POST"])
def spesen_feedback():
    """A KnowBody sends a message to the developer (stored; alert cron pings us)."""
    kb = _spesen_member()
    if not kb:
        return jsonify({"error": "Unauthorized"}), 401
    text = ((request.get_json(silent=True) or {}).get("text") or "").strip()
    if not text:
        return jsonify({"error": "Nachricht ist leer"}), 400
    from spesen import db as _sdb
    fid = _sdb.add_feedback(kb["id"], kb.get("name", ""), text[:4000])
    try:  # best-effort mirror into the "KnowSpesen Feedback" Notion DB
        from spesen import notion_feedback as _nf
        _nf.mirror(fid, kb.get("name", ""), text[:4000], "Offen", _now_local().date().isoformat())
    except Exception as e:
        app.logger.warning("feedback notion mirror failed: %s", e)
    return jsonify({"ok": True, "id": fid})


@app.route("/api/spesen/feedback", methods=["GET"])
def spesen_feedback_list():
    """Operator-only: list open feedback."""
    if not _cockpit_auth_ok():
        return jsonify({"error": "Unauthorized"}), 401
    from spesen import db as _sdb
    return jsonify({"open": _sdb.open_feedback()})


@app.route("/api/spesen/feedback/<int:feedback_id>/resolve", methods=["POST"])
def spesen_feedback_resolve(feedback_id):
    """Operator-only: mark a feedback item resolved (clears it from the alert backlog)."""
    if not _cockpit_auth_ok():
        return jsonify({"error": "Unauthorized"}), 401
    from spesen import db as _sdb
    return jsonify({"ok": _sdb.resolve_feedback(feedback_id)})


@app.route("/api/spesen/setup-db", methods=["POST"])
def spesen_setup_db():
    """One-time (operator only): create the KnowSpesen tables + seed rates, and
    optionally seed demo KnowBodies + sample belege ({"seed_demo": true})."""
    if not _cockpit_auth_ok():
        return jsonify({"error": "Unauthorized"}), 401
    from spesen import db as _sdb
    _sdb.init_db()
    out = {"ok": True, "pauschalen": _sdb.list_pauschalen()}
    if (request.get_json(silent=True) or {}).get("seed_demo"):
        try:
            from spesen import seed as _seed
            out["demo"] = _seed.seed_demo()
        except Exception as e:
            app.logger.error("spesen seed_demo failed: %s", e)
            out["demo_error"] = str(e)
    return jsonify(out)


@app.route("/api/spesen/health", methods=["GET"])
def spesen_health():
    """Deep liveness check for the KnowSpesen service (the health-check cron polls
    this): DB reachable, receipts dir writable, free disk space, last-backup age.
    Returns 200 when all critical checks pass, else 503. Public (no data leaked)."""
    import shutil
    import tempfile
    from spesen import db as _sdb, capture as _cap
    checks = {}
    ok = True

    # DB reachable + core table present
    try:
        conn = _sdb.get_conn()
        try:
            conn.execute("SELECT COUNT(*) FROM knowbodies").fetchone()
        finally:
            conn.close()
        checks["db"] = "ok"
    except Exception as e:
        checks["db"] = f"error: {type(e).__name__}"
        ok = False

    # receipts dir writable (atomic temp write + remove)
    rdir = _cap.receipt_dir()
    try:
        os.makedirs(rdir, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=rdir, suffix=".healthcheck")
        os.close(fd)
        os.remove(tmp)
        checks["receipts_writable"] = "ok"
    except Exception as e:
        checks["receipts_writable"] = f"error: {type(e).__name__}"
        ok = False

    # free disk space (warn, not fail, unless critically low)
    try:
        free_mb = int(shutil.disk_usage(rdir).free / (1024 * 1024))
        checks["disk_free_mb"] = free_mb
        if free_mb < 200:
            checks["disk"] = "critical"
            ok = False
    except Exception as e:
        checks["disk_free_mb"] = f"error: {type(e).__name__}"

    # last-backup age (informational)
    try:
        last = _sdb.meta_get("last_backup_at")
        checks["last_backup_at"] = last
        checks["last_backup_ok"] = _sdb.meta_get("last_backup_ok")
    except Exception:
        checks["last_backup_at"] = None

    return jsonify({"status": "ok" if ok else "degraded", "checks": checks}), (200 if ok else 503)


# On the KnowSpesen deployment only (KNOWSPESEN_HOME=1), ensure the schema is current
# + rates re-synced on every startup. init_db() is idempotent (CREATE IF NOT EXISTS +
# additive ALTERs), so a redeploy auto-migrates without a manual setup-db call — and the
# guard keeps the shared codebase on Render/cockpit from ever touching /srv/knowspesen.
if os.environ.get("KNOWSPESEN_HOME"):
    try:
        from spesen import db as _sdb_boot
        _sdb_boot.init_db()
        app.logger.info("KnowSpesen schema ensured on startup")
    except Exception as _e:  # never let a DB hiccup crash the whole app import
        app.logger.warning("KnowSpesen init_db on startup failed: %s", _e)


# ---------------------------------------------------------------------------
# Ausgaben — internal expense + reimbursement tracker (ausgaben.automatisierbar.ch).
# Separate sibling service (AUSGABEN_HOME=1), own SQLite (AUSGABEN_DB_PATH), own
# password + secret. A FORK of KnowSpesen that reuses ONLY the two pure helpers
# (spesen.ocr / spesen.currency); it touches no spesen file and no /srv/knowspesen
# path. The routes live in a Blueprint so a bug there can't crash the shared app —
# the registration is guarded (a broken import logs + is skipped, app still boots).
# ---------------------------------------------------------------------------
try:
    from ausgaben.routes import bp as _ausgaben_bp
    app.register_blueprint(_ausgaben_bp)
except Exception as _e:
    app.logger.warning("ausgaben blueprint registration failed: %s", _e)

# On the Ausgaben deployment only (AUSGABEN_HOME=1): ensure schema + founders on every
# startup (idempotent). The guard keeps Render/cockpit/knowspesen from ever touching
# /srv/ausgaben, and this process never sets KNOWSPESEN_HOME → the client DB is safe.
if os.environ.get("AUSGABEN_HOME"):
    try:
        from ausgaben import db as _adb_boot
        _adb_boot.init_db()
        app.logger.info("Ausgaben schema ensured on startup")
    except Exception as _e:
        app.logger.warning("Ausgaben init_db on startup failed: %s", _e)


# ---------------------------------------------------------------------------
# vRv discovery tool — tender-specific discovery companion (/vrv, cockpit VPS
# only; on Render the VRV_* env vars are unset so every gated route is 401/503).
# Blueprint + JSON disk store, fully isolated from the production interview bot.
# Spec: tender-vrv/MASTERPLAN.md (WS1 Detail-Spec). Guarded registration: a
# broken import logs + is skipped, the shared app still boots.
# ---------------------------------------------------------------------------
try:
    from vrv.routes import bp as _vrv_bp
    app.register_blueprint(_vrv_bp)
except Exception as _e:
    app.logger.warning("vrv blueprint registration failed: %s", _e)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
