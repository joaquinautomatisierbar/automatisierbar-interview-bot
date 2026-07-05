"""Company Brief automation (Hub M9) — cockpit-side tests.

Covers the deterministic pieces (stage->type mapping, HTML render) and the endpoint's
auth / validation / serve path. The LLM call (brief_generator.generate) is monkeypatched so
these tests never hit the network or spend API credits.
"""
import os
import pathlib
import sys

import pytest

_REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "tools"))

import api  # noqa: E402
import brief_generator as bg  # noqa: E402


# ---------------------------------------------------------------------------
# brief_generator: stage -> type
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("stage,expected", [
    ("Workflow Interview", "wf"),
    ("Process Mapping", "wf"),
    ("Problem Interview", "wf"),
    ("Prototype Building", "pilot"),
    ("Prototype Testing", "pilot"),
    ("Pilot Client", "pilot"),
    ("Paying Client", "general"),
    ("OUT", ""),
    ("", ""),
    ("Nonsense Stage", ""),
])
def test_classify_brief_type(stage, expected):
    assert bg.classify_brief_type(stage) == expected


# ---------------------------------------------------------------------------
# brief_generator: deterministic HTML render
# ---------------------------------------------------------------------------

def _sample_content():
    return {
        "firma": "KnowGravity Inc.",
        "summary": "Zürcher Beratungs-Boutique; ihr trefft vermutlich Markus Schacher.",
        "eli5_simple": "Diese Firma hilft grossen Firmen, komplizierte Regeln klar aufzuschreiben.",
        "eli5_grownup": "Boutique für modellbasiertes Requirements/Business-Rules-Engineering.",
        "sections": [
            {"type": "factsheet", "title": "Firmensteckbrief", "rows": [["Sitz", "Zürich"], ["Gegründet", "~2001"]]},
            {"type": "prose", "title": "Was die Firma konkret macht", "paragraphs": ["Sie beraten.", "Modellbasiert."]},
            {"type": "people", "title": "Entscheidungsträger", "people": [{"name": "Markus Schacher", "role": "Mitgründer", "note": "Autorität."}]},
            {"type": "hypotheses", "title": "Hypothesen", "items": [{"prozess": "Offerten", "haeufig": "?", "teuer": "?", "strukturiert": "eher ja", "pruefen": "Wie viele pro Woche?"}]},
            {"type": "questions", "title": "Kluge Fragen", "items": ["Wie relevant geblieben?"]},
            {"type": "gates", "title": "Gates", "rows": [["Häufig", "Oft genug?"]]},
            {"type": "qa", "title": "Was sie fragen könnten", "items": [{"q": "Preis?", "a": "Start gratis."}]},
            {"type": "callout", "variant": "grownup", "title": "Kontext", "body": "Aus Mail: ..."},
        ],
        "sources": ["knowgravity.com", "Moneyhouse"],
    }


def test_render_html_is_self_contained_and_has_eli5():
    html = bg.render_html(_sample_content(), "wf", meta={"firma": "KnowGravity Inc."})
    assert "<style>" in html
    assert "<script" not in html.lower()          # no external/inline JS — safe to iframe
    assert "http://" not in html                    # no insecure external refs
    assert "Was macht diese Firma eigentlich?" in html
    assert "Für Erwachsene" in html
    assert "KnowGravity Inc." in html
    assert "WF Brief" in html
    assert "Markus Schacher" in html and "Firmensteckbrief" in html
    assert 'name="robots" content="noindex' in html


def test_render_html_survives_missing_fields():
    # Empty / partial content must not raise (fail-safe rendering).
    assert bg.render_html({"sections": []}, "pilot") .startswith("<!doctype html>")
    assert bg.render_html({"firma": "X", "sections": [{"type": "prose", "title": "T"}]}, "general")


def test_pill_and_slug_helpers():
    assert "pill-yes" in bg._pill("ja")
    assert "pill-q" in bg._pill("?")
    assert bg._slugify("KnowGravity Inc.!") == "knowgravity-inc"
    assert bg._slugify("") == "firma"


# ---------------------------------------------------------------------------
# api: /api/brief/generate auth + validation, and /b/<token> serving
# ---------------------------------------------------------------------------

@pytest.fixture
def client(tmp_path, monkeypatch):
    api.app.config["TESTING"] = True
    monkeypatch.setattr(api, "BRIEFS_DIR", str(tmp_path))
    return api.app.test_client()


def test_generate_refused_without_secret_configured(client, monkeypatch):
    # Fail-closed: no BRIEF_SHARED_SECRET configured -> 401 even with a header.
    monkeypatch.setattr(api, "BRIEF_SHARED_SECRET", "")
    r = client.post("/api/brief/generate", json={"lead_page_id": "x"},
                    headers={"X-Brief-Secret": "anything"})
    assert r.status_code == 401


def test_generate_rejects_wrong_secret(client, monkeypatch):
    monkeypatch.setattr(api, "BRIEF_SHARED_SECRET", "s3cret")
    r = client.post("/api/brief/generate", json={"lead_page_id": "x"},
                    headers={"X-Brief-Secret": "wrong"})
    assert r.status_code == 401


def test_generate_validates_payload(client, monkeypatch):
    monkeypatch.setattr(api, "BRIEF_SHARED_SECRET", "s3cret")
    h = {"X-Brief-Secret": "s3cret"}
    assert client.post("/api/brief/generate", json={}, headers=h).status_code == 400
    r = client.post("/api/brief/generate",
                    json={"lead_page_id": "abc", "brief_type": "bogus"}, headers=h)
    assert r.status_code == 400


def test_generate_writes_file_and_serves_it(client, monkeypatch):
    monkeypatch.setattr(api, "BRIEF_SHARED_SECRET", "s3cret")
    monkeypatch.setattr(api, "BRIEF_BASE_URL", "https://cockpit.automatisierbar.ch")
    token = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"

    def fake_generate(lead_page_id, brief_type=None, **kw):
        return {"ok": True, "html": "<!doctype html><html><body>Brief</body></html>",
                "summary": "sum", "brief_type": "wf", "firma": "Test AG",
                "slug": "test-ag", "token": token}

    monkeypatch.setattr(bg, "generate", fake_generate)
    r = client.post("/api/brief/generate", json={"lead_page_id": "pageid"},
                    headers={"X-Brief-Secret": "s3cret"})
    assert r.status_code == 200, r.data
    body = r.get_json()
    assert body["ok"] and body["brief_type"] == "wf" and body["firma"] == "Test AG"
    assert body["brief_url"] == f"https://cockpit.automatisierbar.ch/b/{token}.html"
    # The file exists and is served back.
    got = client.get(f"/b/{token}.html")
    assert got.status_code == 200 and b"Brief" in got.data


def test_generate_skip_on_valueerror(client, monkeypatch):
    monkeypatch.setattr(api, "BRIEF_SHARED_SECRET", "s3cret")

    def raise_value(lead_page_id, brief_type=None, **kw):
        raise ValueError("no brief type for stage 'OUT'")

    monkeypatch.setattr(bg, "generate", raise_value)
    r = client.post("/api/brief/generate", json={"lead_page_id": "pageid"},
                    headers={"X-Brief-Secret": "s3cret"})
    assert r.status_code == 422 and r.get_json().get("skip") is True


def test_serve_brief_rejects_bad_filenames(client):
    assert client.get("/b/notatoken.html").status_code == 404
    assert client.get("/b/../secret.html").status_code in (404, 308)
    assert client.get("/b/deadbeefdeadbeef.txt").status_code == 404
    # well-formed token but no such file -> 404
    assert client.get("/b/" + "f" * 32 + ".html").status_code == 404


def test_briefs_host_has_no_index(client, monkeypatch):
    monkeypatch.delenv("RENDER", raising=False)
    r = client.get("/", headers={"Host": "briefs.automatisierbar.ch"})
    assert r.status_code == 404
