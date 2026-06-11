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

from flask import Flask, request, jsonify, send_file, send_from_directory, session

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
MAX_PROCESS_STEPS = 30    # sane upper bound for the A→Z walkthrough

# Flask-level request body cap. Slightly above per-file cap to leave room for
# multipart overhead. Anything larger fails fast at the WSGI layer.
app.config["MAX_CONTENT_LENGTH"] = MAX_ATTACHMENT_BYTES + 64 * 1024

SESSION_ID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def _valid_session_id(sid: str) -> bool:
    return bool(sid and SESSION_ID_RE.match(sid))


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
    return send_from_directory("static", "index.html")


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
        err = str(e)
        if "404" in err and "notion.com" in err:
            return jsonify({"error": "lead_not_found"}), 404
        return jsonify({"error": "KI-Service vorübergehend nicht verfügbar — bitte erneut versuchen"}), 500


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
            from notion_session import write_payoff_to_page, get_lead_by_page_id, update_session

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

            # generate_claude_code_prompt is a 25-40 s Sonnet call that can fail due to
            # rate limits, a missing API key, or a gunicorn worker timeout on Render free tier.
            # Wrap it so Q&A Archive + process-map still land on the Notion page even when
            # the LLM call fails — write_payoff_to_page already skips the build-prompt block
            # when claude_code_prompt is falsy.
            prompt_text = None
            try:
                prompt_text = generate_claude_code_prompt(
                    context, all_qa, roi or {}, lead_info,
                    process_map=process_map,
                    process_map_notes=process_map_notes,
                    process_map_skipped=process_map_skipped,
                    extra_context=extra_context,
                    attachments=attachments,
                    assumptions=assumptions or [],
                )
            except Exception as e:
                app.logger.error("payoff: generate_claude_code_prompt failed: %s", e)

            # Cache the prompt in session state so /prompt returns instantly when
            # the user clicks "Claude Code Prompt" instead of re-running the 30 s LLM call.
            if prompt_text:
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
                all_qa=all_qa or [],
            )
            app.logger.info("payoff written for session %s (lead %s): %s",
                            session_id, lead_page_id, wrote)

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

    if not isinstance(answers, list) or len(answers) > 20:
        return jsonify({"error": "answers must be a list of ≤20 items"}), 400
    for a in answers:
        if not isinstance(a, dict):
            return jsonify({"error": "each answer must be an object"}), 400
        if len(str(a.get("answer", ""))) > MAX_ANSWER_CHARS:
            return jsonify({"error": f"answer too long (max {MAX_ANSWER_CHARS} chars)"}), 400

    if not answers:
        return jsonify({"error": "answers required"}), 400
    if not any(str(a.get("answer", "")).strip() for a in answers):
        return jsonify({"error": "at least one non-empty answer required"}), 400
    # Defense in depth — reject the literal "Andere…" placeholder. Frontend already
    # validates, but if a third-party API client posts it directly we'd otherwise
    # feed a useless answer to the LLM.
    for a in answers:
        ans = str(a.get("answer", "")).strip()
        if ans in ("Andere…", "Andere...", "Andere"):
            return jsonify({"error": "Bitte deine Antwort eingeben — 'Andere…' braucht Freitext."}), 400

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

        context = context or data.get("context", "")
        all_qa.append({"round": round_num, "qa": answers})

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


@app.route("/api/session/<session_id>/reevaluate", methods=["POST"])
def reevaluate_session(session_id):
    if not _valid_session_id(session_id):
        return jsonify({"error": "invalid session id"}), 400
    data = request.get_json(silent=True) or {}
    correction_note = (data.get("correction_note") or "").strip()
    if not correction_note:
        return jsonify({"error": "correction_note required"}), 400
    if len(correction_note) > 2000:
        return jsonify({"error": "correction_note too long (max 2000 chars)"}), 400

    try:
        from claude_client import evaluate_answers
        from notion_session import get_session as _get, update_session, available as notion_available

        context = ""
        all_qa = []
        process_map = []
        process_map_notes = ""
        process_map_skipped = False
        extra_context = ""
        attachments = []

        if notion_available():
            state = _get(session_id)
            if state:
                context = state.get("context", "")
                all_qa = state.get("all_qa", [])
                process_map = state.get("process_map", []) or []
                process_map_notes = state.get("process_map_notes", "") or ""
                process_map_skipped = bool(state.get("process_map_skipped", False))
                extra_context = state.get("extra_context", "") or ""
                attachments = state.get("attachments", []) or []

        # APPEND — never overwrite existing extra_context
        extra_context = extra_context + f"\n[RE-EVALUATE NOTE]: {correction_note}"

        if notion_available():
            update_session(session_id, {"extra_context": extra_context})

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
                    "roi": roi,
                    "assumptions": assumptions,
                })
            return jsonify({"status": "complete", "assumptions": assumptions, "roi": roi})

        next_questions = result.get("questions", [])
        last_round = all_qa[-1].get("round", 1) if all_qa else 1
        next_round = last_round + 1
        if notion_available():
            update_session(session_id, {
                "current_questions": next_questions,
                "round": next_round,
            })
        return jsonify({
            "status": result.get("status", "needs_more"),
            "round": next_round,
            "questions": next_questions,
            "assumptions": result.get("assumptions", []),
        })

    except Exception as e:
        app.logger.error("reevaluate error: %s", e)
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


# Sessions currently generating a prompt in a background thread.
# Prevents duplicate generation when the user polls before the first thread completes.
_prompt_generating: set = set()
# Stores the last generation error per session so repeated polls surface the real
# error instead of spawning a new LLM thread on every poll when generation fails.
_prompt_errors: dict = {}


@app.route("/api/session/<session_id>/prompt", methods=["GET"])
def session_prompt(session_id):
    """Return the cached Claude Code prompt or 202 while generating it async.

    Design: the LLM call takes 25–40 s, which exceeds Render's HTTP proxy
    idle timeout (~30 s). Blocking the gunicorn worker drops the connection
    before the response is sent, causing the frontend to see a 500 or a reset.
    Solution: return 202 immediately and generate the prompt in a daemon thread.
    The frontend polls every 3 s; once the thread caches the prompt in Notion
    the next poll returns 200 with the prompt text.
    """
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

        state = None
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

        # Fast path: prompt already cached by payoff thread or a prior poll.
        if cached_prompt:
            return jsonify({"prompt": cached_prompt, "cached": True})

        if state is None:
            return jsonify({"error": "session not found"}), 404

        if state.get("status") != "complete":
            return jsonify({"error": "Interview noch nicht abgeschlossen — Build-Prompt fehlt"}), 409

        # If a prior generation attempt failed, surface the error immediately.
        if session_id in _prompt_errors:
            err = _prompt_errors.pop(session_id)
            return jsonify({"error": f"Prompt-Generierung fehlgeschlagen: {err}"}), 500

        # Kick off background generation (idempotent — skips if already running).
        if session_id not in _prompt_generating:
            _prompt_generating.add(session_id)
            import threading

            lead_page_id_snap = lead_page_id
            context_snap, all_qa_snap, roi_snap = context, all_qa, roi
            pm_snap, pmn_snap, pms_snap = process_map, process_map_notes, process_map_skipped
            ec_snap, att_snap, asm_snap = extra_context, attachments, assumptions

            def _generate_prompt():
                try:
                    lead_info = None
                    if lead_page_id_snap:
                        try:
                            from notion_session import get_lead_by_page_id
                            lead_info = get_lead_by_page_id(lead_page_id_snap)
                        except Exception as e:
                            app.logger.warning("async_prompt: get_lead failed: %s", e)

                    prompt_text = generate_claude_code_prompt(
                        context_snap, all_qa_snap, roi_snap, lead_info,
                        process_map=pm_snap,
                        process_map_notes=pmn_snap,
                        process_map_skipped=pms_snap,
                        extra_context=ec_snap,
                        attachments=att_snap,
                        assumptions=asm_snap,
                    )
                    if notion_available():
                        update_session(session_id, {"claude_code_prompt": prompt_text})
                        app.logger.info("async_prompt: cached for session %s", session_id)
                except Exception as e:
                    err_msg = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
                    app.logger.error("async_prompt: generation failed for %s: %s",
                                     session_id, err_msg, exc_info=True)
                    _prompt_errors[session_id] = err_msg
                finally:
                    _prompt_generating.discard(session_id)

            threading.Thread(target=_generate_prompt, daemon=True).start()

        # Tell the frontend to poll again in 3 s.
        return jsonify({"status": "generating", "retry_after_ms": 3000}), 202

    except Exception as e:
        app.logger.error("session_prompt error: %s", e, exc_info=True)
        error_msg = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
        return jsonify({"error": error_msg}), 500


@app.route("/api/session/<session_id>/validate", methods=["POST"])
def validate_session(session_id):
    """Pre-dispatch completeness check (AUT-37). Runs a single Sonnet 4.6 pass
    over the generated claude_code_prompt + process_map and tells the frontend
    whether the brief is concrete enough to hand to the build pipeline.

    Returns 200 with `{status, missing, pass_number, soft_warn, cost_usd_total}`.
    Frontend treats 5xx as fail-open and proceeds with the existing dispatch path.
    """
    if not _valid_session_id(session_id):
        return jsonify({"error": "invalid session id"}), 400

    try:
        from notion_session import get_session as _get_state, update_session
        state = _get_state(session_id) or {}
    except Exception as e:
        app.logger.error("validate_session: get_session failed: %s", e)
        return jsonify({"error": f"session lookup failed: {e}"}), 500

    if not state:
        return jsonify({"error": "session not found"}), 404

    prompt_text = state.get("claude_code_prompt")
    if not prompt_text:
        return jsonify({"error": "Interview noch nicht abgeschlossen — Build-Prompt fehlt"}), 409

    process_map = state.get("process_map") or []
    pass_history = list(state.get("validation_passes") or [])

    # Best-effort: pull just the "## Offene Klärungspunkte" section out of the
    # generated prompt so the validator can score that block separately. If the
    # regex misses we pass an empty string and the validator falls back to scanning
    # the full prompt_text it already receives.
    klär_text = ""
    try:
        import re as _re
        m = _re.search(r"##\s*Offene Klärungspunkte\s*\n([\s\S]*?)(?:\n##\s|\Z)", prompt_text)
        if m:
            klär_text = m.group(1).strip()
    except Exception:
        klär_text = ""

    try:
        from claude_client import validate_brief_completeness
        result = validate_brief_completeness(
            prompt_text=prompt_text,
            process_map=process_map,
            klärungspunkte_text=klär_text,
            pass_history=pass_history,
        )
    except Exception as e:
        app.logger.error("validate_session: validator threw: %s", e)
        # Fail-open: tell the frontend it can proceed with dispatch.
        return jsonify({
            "status": "pass",
            "missing": [],
            "pass_number": len(pass_history) + 1,
            "soft_warn": False,
            "cost_usd_total": float(state.get("validation_cost_usd") or 0.0),
            "reasoning": "validator failed — proceeding fail-open",
        }), 200

    status = result.get("status") or "pass"
    missing = result.get("missing") or []
    cost_call = float(result.get("cost_usd") or 0.0)
    pass_number = len(pass_history) + 1
    cumulative_cost = float(state.get("validation_cost_usd") or 0.0) + cost_call

    from datetime import datetime, timezone
    pass_record = {
        "pass_number": pass_number,
        "status": status,
        "missing": missing,
        "reasoning": result.get("reasoning", ""),
        "cost_usd": cost_call,
        "ts": datetime.now(timezone.utc).isoformat(),
    }

    try:
        update_session(session_id, {
            "validation_passes": pass_history + [pass_record],
            "validation_cost_usd": cumulative_cost,
        })
    except Exception as e:
        app.logger.warning("validate_session: state persist failed (non-fatal): %s", e)

    return jsonify({
        "status": status,
        "missing": missing,
        "pass_number": pass_number,
        "soft_warn": pass_number >= 4,
        "cost_usd_total": cumulative_cost,
        "reasoning": result.get("reasoning", ""),
    })


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
        _apply_classification_to_fired(session, call["lead_id"], cls)
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


def _apply_classification_to_fired(session: dict, lead_id: str, cls: dict) -> None:
    """Store the deliberate transcript classification on the matching cockpit fired
    entry (by lead_id, the most recent still-unclassified one). No-op for non-cockpit
    sessions; the barometer reads fired[i]['classified']."""
    ck = session.get("cockpit")
    if not ck:
        return
    lead_id = (lead_id or "").strip()
    target = None
    for f in (ck.get("fired") or []):
        if (f.get("lead_id") or "").strip() == lead_id and not f.get("classified"):
            target = f          # most recent unclassified match for this lead
    if target is None:
        for f in (ck.get("fired") or []):
            if (f.get("lead_id") or "").strip() == lead_id:
                target = f
    if target is not None:
        target["classified"] = cls.get("bucket")
        target["appt"] = {"agreed": cls.get("appointment_agreed") is True,
                          "day": cls.get("appointment_day") or "",
                          "time": cls.get("appointment_time") or ""}
        target["eval_summary"] = cls.get("summary") or ""


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
    classify from get_call's transcript, apply to the fired entry, gate booking,
    persist. Process-local dedup via _CLASSIFYING (cleared in finally)."""
    try:
        from claude_client import classify_call_outcome
        cls = classify_call_outcome(transcript, ended_reason=ended_reason, duration_s=dur)
        session = _load_voice_session(batch_id)
        if not session:
            return
        _apply_classification_to_fired(session, lead_id, cls)
        _book_followup_from_eval(session, lead_id, cls)
        _enrich_lead(lead_id, cls)   # write-back here too (not just via E) so it's not single-point-of-failure
        _save_voice_session(session)
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
            # reload → append → advance cursor (preserves any stop flag set meanwhile)
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
        # Terminal state reached (done / stopped / error) → persist a durable summary
        # row to Notion. Safe on empty/missing batches (the writer no-ops).
        _write_session_summary(batch_id)


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
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
