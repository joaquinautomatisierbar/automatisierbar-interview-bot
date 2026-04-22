#!/usr/bin/env python3
"""Flask API for automatisierbar PDF generation.

Deployed to Render.com so the n8n cloud workflow can generate branded PDFs
without needing a local machine running.

Endpoints:
  GET  /health          — health check
  POST /generate-pdf    — generate branded PDF, returns binary

Auth: X-API-Key header (set PDF_API_KEY env var on Render)
"""

import io
import os
import sys
import json

from flask import Flask, request, jsonify, send_file

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tools"))

app = Flask(__name__)

API_KEY = os.environ.get("PDF_API_KEY", "")


def _auth_ok() -> bool:
    if not API_KEY:
        return True
    return request.headers.get("X-API-Key") == API_KEY


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
