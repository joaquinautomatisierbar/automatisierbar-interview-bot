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
