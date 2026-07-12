"""Tests for the vRv discovery tool (tender-vrv). Offline, no network, no Flask app needed yet.

v1 scope: catalog invariants + progress math. Store/route/synthesis tests land
with their modules (see tender-vrv/MASTERPLAN.md, WS1 Detail-Spec).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

from vrv import catalog  # noqa: E402


def test_chapter_ids_unique_and_wellformed():
    ids = [c["id"] for c in catalog.CHAPTERS]
    assert len(ids) == len(set(ids))
    assert ids == ["A", "B", "C", "D", "E", "F", "G", "H"]
    for c in catalog.CHAPTERS:
        assert c["title"].strip()
        assert c["offer_section"].strip()


def test_question_ids_unique():
    ids = [q["id"] for q in catalog.QUESTIONS]
    assert len(ids) == len(set(ids)), "duplicate question ids"


def test_question_schema_complete():
    valid_chapters = {c["id"] for c in catalog.CHAPTERS}
    for q in catalog.QUESTIONS:
        assert q["chapter"] in valid_chapters, q["id"]
        assert q["id"][0].upper() == q["chapter"], f"{q['id']} not in chapter {q['chapter']}"
        assert q["text"].strip(), q["id"]
        assert q["type"] in ("text", "choice"), q["id"]
        assert q["priority"] in ("must", "nice"), q["id"]
        assert isinstance(q["client_visible"], bool), q["id"]
        assert q["why_it_matters"].strip(), q["id"]
        assert q["maps_to_offer_section"].strip(), q["id"]


def test_choice_questions_end_with_andere():
    for q in catalog.QUESTIONS:
        if q["type"] == "choice":
            opts = q.get("options")
            assert opts and len(opts) >= 2, q["id"]
            assert opts[-1] == "Andere…", f"{q['id']} choice must end with 'Andere…'"
        else:
            assert "options" not in q, f"{q['id']} has options but type text"


def test_every_chapter_has_questions_and_musts():
    for c in catalog.CHAPTERS:
        qs = [q for q in catalog.QUESTIONS if q["chapter"] == c["id"]]
        assert qs, f"chapter {c['id']} empty"
        assert any(q["priority"] == "must" for q in qs), f"chapter {c['id']} has no must question"


def test_client_subset_small_and_sie_form():
    visible = catalog.client_visible_questions()
    assert 8 <= len(visible) <= 12, f"client subset should stay ~10, got {len(visible)}"
    for q in visible:
        assert q.get("client_text", "").strip(), f"{q['id']} client_visible without client_text"
        assert "Sie" in q["client_text"] or "Ihre" in q["client_text"] or "Ihnen" in q["client_text"], \
            f"{q['id']} client_text not recognizably Sie-form"


def test_non_visible_questions_carry_no_client_text():
    for q in catalog.QUESTIONS:
        if not q["client_visible"]:
            assert "client_text" not in q, \
                f"{q['id']}: client_text on a non-visible question invites serialization mistakes"


def test_question_by_id():
    assert catalog.question_by_id("a1")["chapter"] == "A"
    assert catalog.question_by_id("nope") is None


def test_progress_all_open_when_no_answers():
    rows = catalog.progress({})
    assert [r["chapter"] for r in rows] == ["A", "B", "C", "D", "E", "F", "G", "H"]
    for r in rows:
        assert r["must_open"] == r["must_total"] > 0
        assert r["nice_open"] == r["nice_total"]


def test_progress_counts_answered_and_skipped_as_done():
    answers = {
        "a1": {"status": "answered"},
        "a2": {"status": "skipped"},
        "a3": {"status": "unclear"},   # still open
        "a4": {"status": "open"},      # still open
        "a5": {"status": "answered"},  # nice
    }
    row_a = catalog.progress(answers)[0]
    musts_a = [q for q in catalog.QUESTIONS if q["chapter"] == "A" and q["priority"] == "must"]
    assert row_a["must_total"] == len(musts_a)
    # a1 answered + a2 skipped are done; a3/a4/a6 remain open
    assert row_a["must_open"] == len(musts_a) - 2
    assert row_a["nice_open"] == row_a["nice_total"] - 1


def test_catalog_size_in_spec_range():
    assert 50 <= len(catalog.QUESTIONS) <= 70


# ---------------------------------------------------------------------------
# Store (JSON on disk, flock-guarded)
# ---------------------------------------------------------------------------

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest  # noqa: E402

from vrv import store  # noqa: E402


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("VRV_DATA_DIR", str(tmp_path))
    return tmp_path


def test_store_roundtrip_and_atomicity(data_dir):
    row = store.upsert_answer("a1", value="rund 180 Objekte", updated_by="Joaquin")
    assert row["value"] == "rund 180 Objekte"
    assert row["status"] == "answered"  # auto-promoted from open on non-empty value
    state = store.load_state()
    assert state["answers"]["a1"]["updated_by"] == "Joaquin"
    assert not [p for p in os.listdir(data_dir) if p.endswith(".tmp")]


def test_store_rejects_unknown_and_oversize(data_dir):
    with pytest.raises(KeyError):
        store.upsert_answer("zz99", value="x")
    with pytest.raises(ValueError):
        store.upsert_answer("a1", value="x" * (store.MAX_VALUE_CHARS + 1))
    with pytest.raises(ValueError):
        store.upsert_answer("a1", note="x" * (store.MAX_NOTE_CHARS + 1))
    with pytest.raises(ValueError):
        store.upsert_answer("a1", status="banana")


def test_store_custom_question_then_answerable(data_dir):
    q = store.add_custom_question("B", "Wie oft eskaliert ein Auftrag zum GF?", origin="ai")
    assert q["id"] == "b_f1"
    row = store.upsert_answer(q["id"], value="selten", source="meeting")
    assert row["source"] == "meeting"


def test_store_client_answer_isolated(data_dir):
    store.upsert_answer("a1", value="Team-Antwort")
    store.upsert_client_answer("a1", "Kunden-Antwort")
    row = store.load_state()["answers"]["a1"]
    assert row["value"] == "Team-Antwort"          # client can never overwrite team value
    assert row["client_value"] == "Kunden-Antwort"
    with pytest.raises(KeyError):
        store.upsert_client_answer("b5", "x")       # b5 is not client_visible


def test_store_corrupt_state_recovers(data_dir):
    with open(os.path.join(data_dir, "state.json"), "w") as fh:
        fh.write("{broken json")
    state = store.load_state()
    assert state["answers"] == {}
    assert os.path.exists(os.path.join(data_dir, "state.json.corrupt"))


def test_store_synthesis_status(data_dir):
    store.set_synthesis("brief", status="pending")
    store.set_synthesis("brief", status="done", markdown="# Brief", stamp=True)
    row = store.load_state()["synthesis"]["brief"]
    assert row["status"] == "done" and row["markdown"] == "# Brief"
    assert row["generated_at"]
    with pytest.raises(KeyError):
        store.set_synthesis("nope", status="done")


# ---------------------------------------------------------------------------
# Routes (Flask test client against the real app, offline)
# ---------------------------------------------------------------------------

import api  # noqa: E402


@pytest.fixture
def client(data_dir, monkeypatch):
    monkeypatch.delenv("VRV_API_KEY", raising=False)
    api.app.config["TESTING"] = True
    return api.app.test_client()


def _login(client, monkeypatch, password="testpw-vrv"):
    monkeypatch.setenv("VRV_PASSWORD", password)
    r = client.post("/api/vrv/login", json={"password": password})
    assert r.status_code == 200
    return client


def test_auth_fail_closed_without_password_env(client, monkeypatch):
    monkeypatch.delenv("VRV_PASSWORD", raising=False)
    assert client.post("/api/vrv/login", json={"password": "x"}).status_code == 503
    for method, path in [
        ("get", "/api/vrv/catalog"), ("get", "/api/vrv/state"),
        ("patch", "/api/vrv/answer/a1"), ("post", "/api/vrv/questions"),
        ("post", "/api/vrv/followups/A"), ("post", "/api/vrv/synthesize/brief"),
        ("get", "/api/vrv/synthesis/brief"), ("get", "/api/vrv/export/brief.md"),
    ]:
        assert getattr(client, method)(path).status_code == 401, path


def test_wrong_password_rejected(client, monkeypatch):
    monkeypatch.setenv("VRV_PASSWORD", "correct")
    assert client.post("/api/vrv/login", json={"password": "wrong"}).status_code == 401
    assert client.get("/api/vrv/state").status_code == 401


def test_answer_flow_and_progress(client, monkeypatch):
    _login(client, monkeypatch)
    r = client.patch("/api/vrv/answer/a1",
                     json={"value": "180 Objekte", "source": "prep", "updated_by": "Nico"})
    assert r.status_code == 200
    assert client.patch("/api/vrv/answer/zz99", json={"value": "x"}).status_code == 404
    assert client.patch("/api/vrv/answer/a1",
                        json={"value": "x" * 5000}).status_code == 400
    state = client.get("/api/vrv/state").get_json()
    row_a = next(p for p in state["progress"] if p["chapter"] == "A")
    assert row_a["must_open"] == row_a["must_total"] - 1
    assert state["answers"]["a1"]["updated_by"] == "Nico"


def test_custom_question_route(client, monkeypatch):
    _login(client, monkeypatch)
    r = client.post("/api/vrv/questions",
                    json={"chapter": "e", "text": "Gibt es Winterdienst-Piketts?"})
    assert r.status_code == 201
    qid = r.get_json()["question"]["id"]
    assert client.patch(f"/api/vrv/answer/{qid}", json={"value": "ja"}).status_code == 200
    assert client.post("/api/vrv/questions",
                       json={"chapter": "ZZ", "text": "x"}).status_code == 404


def test_synthesis_async_roundtrip(client, monkeypatch):
    import time

    from vrv import synthesis as synth_mod
    _login(client, monkeypatch)
    monkeypatch.setattr(synth_mod, "generate_brief", lambda state: "# Offerten-Brief\n\nOK")
    assert client.get("/api/vrv/export/brief.md").status_code == 409
    r = client.post("/api/vrv/synthesize/brief")
    assert r.status_code == 202
    for _ in range(80):
        row = client.get("/api/vrv/synthesis/brief").get_json()
        if row["status"] in ("done", "error"):
            break
        time.sleep(0.05)
    assert row["status"] == "done"
    export = client.get("/api/vrv/export/brief.md")
    assert export.status_code == 200
    assert export.mimetype == "text/markdown"
    assert "Offerten-Brief" in export.get_data(as_text=True)
    assert client.post("/api/vrv/synthesize/nope").status_code == 404


def test_synthesis_error_path_persisted(client, monkeypatch):
    import time

    from vrv import synthesis as synth_mod
    _login(client, monkeypatch)

    def boom(state):
        raise RuntimeError("kaputt")

    monkeypatch.setattr(synth_mod, "generate_spec", boom)
    assert client.post("/api/vrv/synthesize/spec").status_code == 202
    for _ in range(80):
        row = client.get("/api/vrv/synthesis/spec").get_json()
        if row["status"] in ("done", "error"):
            break
        time.sleep(0.05)
    assert row["status"] == "error"
    assert "kaputt" in row["error"]


def test_vrv_page_served_without_auth_but_data_gated(client, monkeypatch):
    monkeypatch.delenv("VRV_PASSWORD", raising=False)
    page = client.get("/vrv")
    assert page.status_code == 200
    assert b'data-page="vrv-hub"' in page.data
    assert client.get("/api/vrv/state").status_code == 401


def test_fragebogen_page_serves_questionnaire(client):
    page = client.get("/vrv/fragebogen")
    assert page.status_code == 200
    assert b'data-page="vrv"' in page.data


# ---------------------------------------------------------------------------
# Client pre-send surface (v2) — isolation is the whole point
# ---------------------------------------------------------------------------

CLIENT_TOKEN = "kunde-token-xyz"


def _client_session(client, monkeypatch):
    monkeypatch.setenv("VRV_CLIENT_TOKEN", CLIENT_TOKEN)
    r = client.get(f"/vrv/kunde?k={CLIENT_TOKEN}")
    assert r.status_code == 302 and r.headers["Location"].endswith("/vrv/kunde")
    return client


def test_client_token_flow_and_revocation(client, monkeypatch):
    _client_session(client, monkeypatch)
    assert client.get("/api/vrv/client/questions").status_code == 200
    # revocation: unsetting the env var kills access despite the live session
    monkeypatch.delenv("VRV_CLIENT_TOKEN", raising=False)
    assert client.get("/api/vrv/client/questions").status_code == 401


def test_client_wrong_token_gets_no_session(client, monkeypatch):
    monkeypatch.setenv("VRV_CLIENT_TOKEN", CLIENT_TOKEN)
    client.get("/vrv/kunde?k=falsch")
    assert client.get("/api/vrv/client/questions").status_code == 401
    # page itself is always served (gate renders client-side)
    assert b'data-page="vrv-kunde"' in client.get("/vrv/kunde").data


def test_client_serialization_whitelist(client, monkeypatch):
    _client_session(client, monkeypatch)
    # plant internal data that must never leak
    from vrv import store
    store.upsert_answer("a1", value="INTERNE-TEAM-ANTWORT", note="INTERNE-NOTIZ")
    raw = client.get("/api/vrv/client/questions").get_data(as_text=True)
    body = client.get("/api/vrv/client/questions").get_json()
    assert "why_it_matters" not in raw
    assert "INTERNE-TEAM-ANTWORT" not in raw
    assert "INTERNE-NOTIZ" not in raw
    assert "client_visible" not in raw
    ids = {q["id"] for q in body["questions"]}
    assert "b5" not in ids and "g5" not in ids     # internal-only questions absent
    assert 8 <= len(ids) <= 12
    for q in body["questions"]:
        assert set(q.keys()) <= {"id", "text", "type", "options", "value"}


def test_client_patch_scope(client, monkeypatch):
    _client_session(client, monkeypatch)
    from vrv import store
    store.upsert_answer("a1", value="Team-Wert")
    assert client.patch("/api/vrv/client/answer/a1",
                        json={"value": "ca. 200 Objekte"}).status_code == 200
    assert client.patch("/api/vrv/client/answer/b5",
                        json={"value": "x"}).status_code == 403
    row = store.load_state()["answers"]["a1"]
    assert row["value"] == "Team-Wert"              # team value untouched
    assert row["client_value"] == "ca. 200 Objekte"


def test_client_session_cannot_reach_internal_routes(client, monkeypatch):
    _client_session(client, monkeypatch)
    monkeypatch.setenv("VRV_PASSWORD", "teampw")    # internal auth configured but not logged in
    assert client.get("/api/vrv/state").status_code == 401
    assert client.get("/api/vrv/catalog").status_code == 401
    assert client.post("/api/vrv/synthesize/brief").status_code == 401


def test_health_public_and_app_boots_without_vrv_env(client, monkeypatch):
    monkeypatch.delenv("VRV_PASSWORD", raising=False)
    r = client.get("/api/vrv/health")
    assert r.status_code == 200
    assert r.get_json()["store_writable"] is True
    # regression guard: the production interview bot is untouched
    monkeypatch.delenv("COCKPIT_HOME", raising=False)
    monkeypatch.delenv("RENDER", raising=False)
    assert b"Workflow Interview" in client.get("/interview").data


# ---------------------------------------------------------------------------
# Hub: docs serving (manifest-exact) + dashboard (TASKS.md parser)
# ---------------------------------------------------------------------------

from vrv import docs  # noqa: E402

_FIXTURE_TASKS = """# Test-Board

> Status: `[ ]` offen · `[~]` läuft · `[x]` erledigt. Stand: 10.7.2026.

## Lane WS0: Recherche (Kern)

- [x] 0.1 Dossier fertig
- [~] 0.2 Hub-Projekt läuft
- [ ] 0.3 Recon offen

## Lane WS1: Tool

- [x] 1.1 gebaut

```text
- [x] fake task inside fence
```

## Meilensteine

| Datum | Meilenstein |
|---|---|
| 21.7. | Scope-Entscheid |
| 3./4.8. | Generalprobe |
| **5.8.** | **Termin** |
"""


@pytest.fixture
def docs_fixture_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("VRV_DOCS_DIR", str(tmp_path))
    (tmp_path / "TASKS.md").write_text(_FIXTURE_TASKS, encoding="utf-8")
    (tmp_path / "naechste-schritte.md").write_text(
        "# Nächste Schritte\n\n## Joaquin\n\n- [ ] Termine festlegen\n",
        encoding="utf-8",
    )
    return tmp_path


def test_docs_manifest_requires_auth(client):
    assert client.get("/api/vrv/docs").status_code == 401


def test_dashboard_requires_auth(client):
    assert client.get("/api/vrv/dashboard").status_code == 401


def test_docs_and_dashboard_reject_client_session(client, monkeypatch):
    _client_session(client, monkeypatch)
    assert client.get("/api/vrv/docs").status_code == 401
    assert client.get("/api/vrv/docs/TASKS.md").status_code == 401
    assert client.get("/api/vrv/dashboard").status_code == 401


def test_docs_manifest_shape_and_all_files_exist(client, monkeypatch):
    monkeypatch.delenv("VRV_DOCS_DIR", raising=False)  # default: repo tender-vrv/
    _login(client, monkeypatch)
    sections = client.get("/api/vrv/docs").get_json()["sections"]
    assert [s["id"] for s in sections] == [
        "lernen", "termin", "praesentation", "offerte", "vertraege", "wissen", "plan"]
    items = [item for s in sections for item in s["items"]]
    assert len(items) == 46
    paths = [item["path"] for item in items]
    assert len(set(paths)) == 46
    for item in items:
        assert item["title"] and item["desc"]
        assert item["kind"] in ("md", "pdf", "pptx", "html")
        # deploy-completeness drift guard: every manifest file exists on disk
        assert item["exists"] is True, item["path"]


def test_docs_fetch_md_ok_utf8(client, monkeypatch):
    monkeypatch.delenv("VRV_DOCS_DIR", raising=False)
    _login(client, monkeypatch)
    r = client.get("/api/vrv/docs/TASKS.md")
    assert r.status_code == 200
    assert r.mimetype == "text/markdown"
    text = r.get_data(as_text=True)
    assert "Aufgaben-Board" in text and "für" in text  # umlaut chain intact
    assert client.get("/api/vrv/docs/upskilling/modul-1-primer.md").status_code == 200


def test_docs_kind_dispositions(client, monkeypatch):
    monkeypatch.delenv("VRV_DOCS_DIR", raising=False)
    _login(client, monkeypatch)
    deck = client.get("/api/vrv/docs/deck/deck.html")
    assert deck.status_code == 200 and deck.mimetype == "text/html"
    assert "attachment" not in (deck.headers.get("Content-Disposition") or "")
    pdf = client.get("/api/vrv/docs/ausschreibung-anfrage-2026-07-02.pdf")
    assert pdf.status_code == 200 and pdf.mimetype == "application/pdf"
    assert "attachment" not in (pdf.headers.get("Content-Disposition") or "")
    pptx = client.get("/api/vrv/docs/entscheidungsgrundlage-team-2026-07.pptx")
    assert pptx.status_code == 200
    assert "attachment" in pptx.headers.get("Content-Disposition", "")
    assert pptx.mimetype == docs.MIME_BY_KIND["pptx"]


def test_docs_reject_non_manifest_paths(client, monkeypatch):
    _login(client, monkeypatch)
    for path in [
        "/api/vrv/docs/../../api.py",
        "/api/vrv/docs/..%2f..%2fapi.py",
        "/api/vrv/docs//etc/passwd",
        "/api/vrv/docs/tools/vrv/store.py",
        "/api/vrv/docs/.DS_Store",
    ]:
        # follow_redirects: werkzeug 308-normalizes '//' before routing
        assert client.get(path, follow_redirects=True).status_code == 404, path
    # dot-segments that survive HTTP normalization are rejected server-side
    assert docs.resolve("TASKS.md/../README.md") is None
    assert docs.resolve("./TASKS.md") is None


def test_resolve_manifest_only():
    resolved = docs.resolve("research/dossier-a-pebe-integration.md")
    assert resolved is not None
    path, item = resolved
    assert item["kind"] == "md"
    assert str(path).endswith("research/dossier-a-pebe-integration.md")
    assert docs.resolve("../api.py") is None
    assert docs.resolve("MASTERPLAN.MD") is None  # case-sensitive: dev-macOS vs prod-Linux
    assert docs.resolve("") is None


def test_dashboard_parses_fixture_tasks(client, monkeypatch, docs_fixture_dir):
    _login(client, monkeypatch)
    body = client.get("/api/vrv/dashboard").get_json()
    assert body["ok"] is True
    assert body["countdown_target"] == "2026-08-05"
    lanes = body["tasks"]["lanes"]
    assert [lane["id"] for lane in lanes] == ["WS0", "WS1"]
    ws0 = lanes[0]
    assert ws0["title"] == "Recherche (Kern)"
    assert (ws0["done"], ws0["doing"], ws0["open"], ws0["total"]) == (1, 1, 1, 3)
    assert [item["state"] for item in ws0["items"]] == ["done", "doing", "open"]
    assert lanes[1]["total"] == 1  # fenced fake task not counted
    milestones = body["tasks"]["milestones"]
    assert len(milestones) == 3
    assert milestones[0] == {"date": "21.7.", "label": "Scope-Entscheid", "emph": False}
    assert milestones[2] == {"date": "5.8.", "label": "Termin", "emph": True}
    assert body["tasks"]["stand"] == "10.7.2026"
    assert "Termine festlegen" in body["naechste_schritte_md"]


def test_dashboard_survives_missing_files(client, monkeypatch, tmp_path):
    monkeypatch.setenv("VRV_DOCS_DIR", str(tmp_path))
    _login(client, monkeypatch)
    r = client.get("/api/vrv/dashboard")
    assert r.status_code == 200
    body = r.get_json()
    assert body["tasks"] is None
    assert body["tasks_error"]
    assert body["naechste_schritte_md"] is None


def test_parse_tasks_ignores_legend_and_fences():
    text = (
        "> Status: `[ ]` offen · `[x]` erledigt.\n\n"
        "## Lane WS9: Test\n\n"
        "```text\n- [x] fake\n- [ ] fake2\n```\n\n"
        "- [ ] real\n"
    )
    parsed = docs.parse_tasks(text)
    assert len(parsed["lanes"]) == 1
    assert parsed["lanes"][0]["total"] == 1
    assert parsed["lanes"][0]["items"][0]["text"] == "real"


def test_parse_tasks_real_tasks_file(monkeypatch):
    monkeypatch.delenv("VRV_DOCS_DIR", raising=False)
    parsed = docs.parse_tasks(docs.read_doc_text("TASKS.md"))
    assert [lane["id"] for lane in parsed["lanes"]] == [
        "WS0", "WS1", "WS2", "WS3", "WS4", "WS5", "WS6"]
    for lane in parsed["lanes"]:
        assert lane["total"] >= 1
        for item in lane["items"]:
            assert item["state"] in ("done", "doing", "open")
    assert len(parsed["milestones"]) >= 8
    assert any(m["emph"] and m["date"] == "5.8." for m in parsed["milestones"])
    assert parsed["stand"]


def test_lernen_paths_follow_module_prefix_convention():
    """The hub's renderLernen groups by 'upskilling/modul-N-<role>' prefix;
    every lernen item except the fragen-bank must obey the convention."""
    lernen = [s for s in docs.DOCS_MANIFEST if s["id"] == "lernen"][0]
    pattern = re.compile(
        r"^upskilling/modul-\d+-(primer|quiz|deck|handout)\.(md|html|pdf)$")
    for item in lernen["items"]:
        if "fragen-bank" in item["path"]:
            continue
        assert pattern.match(item["path"]), item["path"]


# ---------------------------------------------------------------------------
# Hub: homework uploads (Abgaben)
# ---------------------------------------------------------------------------

import io  # noqa: E402
import re  # noqa: E402

from vrv import uploads as vrv_uploads  # noqa: E402


def _post_upload(client, *, modul="modul-2", who="Joaquin", comment="ok",
                 content=b"\x89PNG fake", mime="image/png", name="beweis.png"):
    return client.post("/api/vrv/uploads", data={
        "modul": modul, "who": who, "comment": comment,
        "file": (io.BytesIO(content), name, mime),
    }, content_type="multipart/form-data")


def test_uploads_fail_closed_and_reject_client_session(client, monkeypatch):
    monkeypatch.delenv("VRV_PASSWORD", raising=False)
    assert _post_upload(client).status_code == 401
    assert client.get("/api/vrv/uploads").status_code == 401
    assert client.get("/api/vrv/uploads/deadbeef/file").status_code == 401
    assert client.delete("/api/vrv/uploads/deadbeef").status_code == 401
    _client_session(client, monkeypatch)
    assert _post_upload(client).status_code == 401
    assert client.get("/api/vrv/uploads").status_code == 401
    assert client.get("/api/vrv/uploads/deadbeef/file").status_code == 401
    assert client.delete("/api/vrv/uploads/deadbeef").status_code == 401


def test_upload_roundtrip(client, monkeypatch, data_dir):
    _login(client, monkeypatch)
    r = _post_upload(client)
    assert r.status_code == 201
    body = r.get_json()["upload"]
    assert body["id"] and body["who"] == "Joaquin"
    assert "stored" not in body                      # on-disk name never leaves
    assert client.get("/api/vrv/uploads?modul=modul-2").get_json()["uploads"][0]["id"] == body["id"]
    assert client.get("/api/vrv/uploads?modul=modul-1").get_json()["uploads"] == []
    f = client.get(f"/api/vrv/uploads/{body['id']}/file")
    assert f.status_code == 200
    assert f.mimetype == "image/png"
    assert f.headers["X-Content-Type-Options"] == "nosniff"
    assert "attachment" not in (f.headers.get("Content-Disposition") or "")
    assert client.delete(f"/api/vrv/uploads/{body['id']}").status_code == 200
    assert client.get("/api/vrv/uploads").get_json()["uploads"] == []
    leftovers = [p for p in os.listdir(os.path.join(data_dir, "uploads"))
                 if not p.startswith(".")]
    assert leftovers == []


def test_upload_validation(client, monkeypatch):
    _login(client, monkeypatch)
    assert client.post("/api/vrv/uploads", data={"modul": "modul-2", "who": "Joaquin"},
                       content_type="multipart/form-data").status_code == 400
    assert _post_upload(client, content=b"").status_code == 400
    assert _post_upload(client, who="Eve").status_code == 400
    assert _post_upload(client, modul="hack").status_code == 400
    assert _post_upload(client, comment="x" * 501).status_code == 400
    assert _post_upload(client, mime="application/octet-stream",
                        name="run.exe").status_code == 415
    assert _post_upload(client, mime="text/html",
                        name="evil.html").status_code == 415


def test_upload_size_cap_and_413_json(client, monkeypatch):
    _login(client, monkeypatch)
    r = _post_upload(client, content=b"x" * (vrv_uploads.MAX_UPLOAD_BYTES + 1))
    assert r.status_code == 413
    assert r.get_json()["ok"] is False               # JSON body, not HTML page


def test_upload_heic_md_and_filename_hygiene(client, monkeypatch):
    _login(client, monkeypatch)
    heic = _post_upload(client, mime="application/octet-stream", name="IMG_1.HEIC")
    assert heic.status_code == 201
    hid = heic.get_json()["upload"]["id"]
    assert client.get(f"/api/vrv/uploads/{hid}/file").mimetype == "image/heic"
    md = _post_upload(client, content=b"# audit <script>alert(1)</script>",
                      mime="text/markdown", name="audit.md")
    assert md.status_code == 201
    mres = client.get(f"/api/vrv/uploads/{md.get_json()['upload']['id']}/file")
    assert mres.mimetype == "text/plain"             # never rendered as html
    weird = _post_upload(client, name="bö\"se\r\nname.png")
    assert weird.status_code == 201
    entry = weird.get_json()["upload"]
    assert "\r" not in entry["orig_name"] and "\n" not in entry["orig_name"]
    assert client.get(f"/api/vrv/uploads/{entry['id']}/file").status_code == 200


def test_upload_unknown_id_404(client, monkeypatch):
    _login(client, monkeypatch)
    assert client.get("/api/vrv/uploads/deadbeefdeadbeef/file").status_code == 404
    assert client.delete("/api/vrv/uploads/deadbeefdeadbeef").status_code == 404
    assert client.get("/api/vrv/uploads/%2e%2e%2fetc/file").status_code == 404


def test_uploads_index_corruption_recovers(client, monkeypatch, data_dir):
    _login(client, monkeypatch)
    with open(os.path.join(data_dir, "uploads.json"), "w") as fh:
        fh.write("{broken")
    assert client.get("/api/vrv/uploads").get_json()["uploads"] == []
    assert os.path.exists(os.path.join(data_dir, "uploads.json.corrupt"))


def test_uploads_dir_created_at_runtime(client, monkeypatch, data_dir):
    _login(client, monkeypatch)
    assert not os.path.exists(os.path.join(data_dir, "uploads"))
    assert _post_upload(client).status_code == 201
    assert os.path.isdir(os.path.join(data_dir, "uploads"))


def test_upload_does_not_touch_state(client, monkeypatch, data_dir):
    _login(client, monkeypatch)
    assert _post_upload(client).status_code == 201
    assert store.load_state()["answers"] == {}
