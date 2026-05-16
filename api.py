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

from flask import Flask, request, jsonify, send_file, send_from_directory

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tools"))

app = Flask(__name__, static_folder="static")

PDF_API_KEY = os.environ.get("PDF_API_KEY", "")

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
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
