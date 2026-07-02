"""Remote availability-config API tests (Hub v2·M5a): /api/book/config is inert
without COCKPIT_CONFIG_SECRET, gated with it, and PUT overrides change
/api/book/slots output in-process (no restart) via the file-backed layer."""
import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import api  # noqa: E402

SECRET = "test-secret"
AUTH = {"X-Config-Secret": SECRET}
# Wed 2026-07-08: after the 1-day lead time, before the default Sommerpause
# blackout (2026-07-17+), inside the default horizon (2026-09-30).
WED = "2026-07-08"
THU = "2026-07-09"


@pytest.fixture
def client(tmp_path, monkeypatch):
    api.app.config["TESTING"] = True
    # Config file in a per-test tmp dir; secret set at import time normally.
    monkeypatch.setattr(api, "BOOKING_CONFIG_PATH", tmp_path / "booking_config.json")
    monkeypatch.setattr(api, "COCKPIT_CONFIG_SECRET", SECRET)
    return api.app.test_client()


def _labels(client, date):
    r = client.get(f"/api/book/slots?date={date}")
    assert r.status_code == 200
    days = r.get_json()["days"]
    return [s["label"] for d in days for s in d["slots"]]


def test_inert_without_secret(client, monkeypatch):
    monkeypatch.setattr(api, "COCKPIT_CONFIG_SECRET", "")
    assert client.get("/api/book/config").status_code == 404
    assert client.put("/api/book/config", json={"slot_minutes": 30}).status_code == 404


def test_wrong_secret_403(client):
    assert client.get("/api/book/config",
                      headers={"X-Config-Secret": "wrong"}).status_code == 403
    assert client.put("/api/book/config", json={"slot_minutes": 30},
                      headers={"X-Config-Secret": "wrong"}).status_code == 403


def test_get_effective_defaults(client):
    r = client.get("/api/book/config", headers=AUTH)
    assert r.status_code == 200
    body = r.get_json()
    assert body["overridden_keys"] == []
    eff = body["effective"]
    assert eff["slot_minutes"] == api.SLOT_MINUTES
    assert eff["windows"]["0"] == [["08:00", "18:00"]]
    assert body["tz"] == "Europe/Zurich"


def test_windows_override_changes_slots_without_restart(client):
    baseline = _labels(client, WED)
    assert baseline and baseline[0] == "08:00"          # default 08:00–18:00 window

    r = client.put("/api/book/config", headers=AUTH,
                   json={"windows": {"2": [["09:00", "12:00"]]}})
    assert r.status_code == 200
    assert r.get_json()["overridden_keys"] == ["windows"]

    assert _labels(client, WED) == ["09:00", "10:00", "11:00"]  # Wed trimmed
    assert _labels(client, THU) == []                   # absent day = closed


def test_blackout_override_takes_effect_instantly(client):
    assert _labels(client, WED)                         # open by default
    r = client.put("/api/book/config", headers=AUTH,
                   json={"blackout_ranges": [[WED, WED]]})
    assert r.status_code == 200
    assert _labels(client, WED) == []


def test_validation_rejects_garbage(client):
    r = client.put("/api/book/config", headers=AUTH,
                   json={"slot_minutes": "abc", "windows": {"9": []}, "nope": 1})
    assert r.status_code == 400
    details = " ".join(r.get_json()["details"])
    assert "slot_minutes" in details and "windows" in details and "unknown key" in details
    # Engine untouched by the rejected patch.
    assert client.get("/api/book/config", headers=AUTH).get_json()["overridden_keys"] == []


def test_null_removes_override_and_restores_defaults(client):
    baseline = _labels(client, WED)
    client.put("/api/book/config", headers=AUTH,
               json={"windows": {"2": [["09:00", "12:00"]]}, "slot_minutes": 30})
    assert api.BOOKING_CONFIG_PATH.exists()             # persisted (restart-survival)

    r = client.put("/api/book/config", headers=AUTH,
                   json={"windows": None, "slot_minutes": None})
    assert r.status_code == 200
    assert r.get_json()["overridden_keys"] == []
    assert not api.BOOKING_CONFIG_PATH.exists()         # pristine default state
    assert _labels(client, WED) == baseline


def test_cockpit_session_also_authorizes(client, monkeypatch):
    monkeypatch.setattr(api, "_cockpit_auth_ok", lambda: True)
    assert client.get("/api/book/config").status_code == 200
