"""Route gating tests: COCKPIT_HOME flips the bare root between the public landing
page (cockpit VPS) and the interview bot (Render), while /interview always serves
the bot and /book is untouched. See api._cockpit_home()."""
import sys
import pathlib

import pytest

# api.py lives at the repo root (one level up from tests/).
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import api  # noqa: E402

# Stable content markers.
BOT_MARKER = b"Workflow Interview"      # <title> in static/index.html
LANDING_MARKER = b'data-page="cockpit-home"'  # body attr in static/cockpit-home.html
BOOK_MARKER = b"Termin buchen"          # <title> in static/book.html


@pytest.fixture
def client():
    api.app.config["TESTING"] = True
    return api.app.test_client()


def test_root_serves_landing_when_cockpit_home(client, monkeypatch):
    monkeypatch.setenv("COCKPIT_HOME", "1")
    r = client.get("/")
    assert r.status_code == 200
    body = r.data
    assert LANDING_MARKER in body
    assert b'href="/book"' in body      # the CTA points at the booking page
    assert BOT_MARKER not in body       # interview bot is NOT the front door here


def test_root_serves_bot_without_cockpit_home(client, monkeypatch):
    # Render behaviour: no COCKPIT_HOME -> root is the interview bot.
    monkeypatch.delenv("COCKPIT_HOME", raising=False)
    r = client.get("/")
    assert r.status_code == 200
    assert BOT_MARKER in r.data
    assert LANDING_MARKER not in r.data


def test_interview_always_serves_bot(client, monkeypatch):
    # /interview serves the bot in BOTH deployment modes.
    monkeypatch.setenv("COCKPIT_HOME", "1")
    assert BOT_MARKER in client.get("/interview").data
    monkeypatch.delenv("COCKPIT_HOME", raising=False)
    assert BOT_MARKER in client.get("/interview").data


def test_book_page_unaffected(client, monkeypatch):
    monkeypatch.setenv("COCKPIT_HOME", "1")
    r = client.get("/book")
    assert r.status_code == 200
    assert BOOK_MARKER in r.data
