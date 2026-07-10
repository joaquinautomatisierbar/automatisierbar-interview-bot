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


def test_health_public_and_app_boots_without_vrv_env(client, monkeypatch):
    monkeypatch.delenv("VRV_PASSWORD", raising=False)
    r = client.get("/api/vrv/health")
    assert r.status_code == 200
    assert r.get_json()["store_writable"] is True
    # regression guard: the production interview bot is untouched
    monkeypatch.delenv("COCKPIT_HOME", raising=False)
    monkeypatch.delenv("RENDER", raising=False)
    assert b"Workflow Interview" in client.get("/interview").data
