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

import io
import os
import json
import re
import sys
from pathlib import Path

from flask import Flask, request, jsonify, send_file, send_from_directory

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tools"))

app = Flask(__name__, static_folder="static")

PDF_API_KEY = os.environ.get("PDF_API_KEY", "")

MAX_CONTEXT_CHARS = 8000  # Notion rich_text safe upper bound for State JSON
MAX_ANSWER_CHARS = 4000   # per-answer cap; 8 answers × 4000 = 32k headroom
SESSION_ID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def _valid_session_id(sid: str) -> bool:
    return bool(sid and SESSION_ID_RE.match(sid))


def _auth_ok() -> bool:
    if not PDF_API_KEY:
        return True
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

        if notion_available():
            state = _get(session_id)
            if state:
                context = state.get("context", "")
                all_qa = state.get("all_qa", [])
                lead_page_id = state.get("lead_page_id")

        context = context or data.get("context", "")
        all_qa.append({"round": round_num, "qa": answers})

        # Write this round's Q&A to the lead's Notion page
        if lead_page_id:
            write_qa_to_page(lead_page_id, round_num, answers)

        result = evaluate_answers(context, all_qa)

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

            # Write ROI to lead page
            if lead_page_id:
                write_roi_to_page(lead_page_id, roi, assumptions)

            return jsonify({
                "status": "complete",
                "assumptions": assumptions,
                "roi": roi,
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

        if notion_available():
            state = _get(session_id)
            if state:
                context = state.get("context", context)
                all_qa = state.get("all_qa", [])

        spec_text = generate_spec_summary(context, all_qa)

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
        from notion_session import get_session as _get, available as notion_available

        context = ""
        all_qa = []
        roi = {}
        lead_page_id = None

        if notion_available():
            state = _get(session_id)
            if state:
                context = state.get("context", "")
                all_qa = state.get("all_qa", [])
                roi = state.get("roi", {}) or {}
                lead_page_id = state.get("lead_page_id")

        lead_info = None
        if lead_page_id:
            try:
                from notion_session import get_lead_by_page_id
                lead_info = get_lead_by_page_id(lead_page_id)
            except Exception as e:
                app.logger.error("get_lead_by_page_id failed: %s", e)

        prompt_text = generate_claude_code_prompt(context, all_qa, roi, lead_info)
        return jsonify({"prompt": prompt_text})

    except Exception as e:
        app.logger.error("session_prompt error: %s", e)
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
