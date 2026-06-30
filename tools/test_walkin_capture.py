#!/usr/bin/env python3
"""Offline regression tests for walkin_capture.py (Walk-in mode Phase 1).

Pure/offline — never touches Notion or the network. Uses a temp WALKIN_MEMO_DIR.
Run:
    python3 tools/test_walkin_capture.py     # exit 0 = all pass
"""
import os
import sys
import tempfile

# Isolate the memo dir BEFORE importing the module (memo_dir() reads env at call time).
_TMP = tempfile.mkdtemp(prefix="walkin-test-")
os.environ["WALKIN_MEMO_DIR"] = _TMP
os.environ["WALKIN_TRANSCRIBE_MAX_PER_DAY"] = "10"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import walkin_capture as wc  # noqa: E402

PASS, FAIL = [], []


def check(name, cond):
    (PASS if cond else FAIL).append(name)
    print(("  ok  " if cond else "FAIL  ") + name)


def _raises(fn, exc=ValueError):
    try:
        fn()
        return False
    except exc:
        return True
    except Exception:
        return False


# --- validation ---------------------------------------------------------------
check("validate: ok payload → []",
      wc.validate_lead_payload({"company": "Furness AG", "notes": "x"}) == [])
check("validate: missing company+notes",
      set(wc.validate_lead_payload({})) == {"company", "notes"})
check("validate: bad email flagged",
      "email" in wc.validate_lead_payload({"company": "A", "notes": "b", "email": "nope"}))
check("validate: good email ok",
      "email" not in wc.validate_lead_payload({"company": "A", "notes": "b", "email": "a@b.ch"}))

# --- lead fields --------------------------------------------------------------
f = wc.build_lead_fields(
    {"company": "Furness Shipping AG", "city": "Zürich", "notes": "Remo will Mail",
     "email": "RKortland@Furness.CH", "role": "Operations", "contact": "Remo"},
    "2026-06-30")
check("lead: Name = '{Firma} {City}'", f["Name"] == "Furness Shipping AG Zürich")
check("lead: HOT STATUS fixed", f["HOT STATUS"] == "WALK IN BUT NO BAMFAM")
check("lead: Outreach Channel fixed", f["Outreach Channel"] == "Walk-In")
check("lead: Pipeline Stage fixed", f["Pipeline Stage"] == "Problem Interview")
check("lead: checkboxes true", f["Outreach Gemacht?"] is True and f["Contacted"] is True)
check("lead: dates set", f["Gesprächsdatum"] == "2026-06-30" and f["Last contacted"] == "2026-06-30")
check("lead: email lowercased", f["email"] == "rkortland@furness.ch")
check("lead: Context carries notes", "Remo will Mail" in f["Context"] and f["Context"].startswith("WALK-IN (2026-06-30)"))
check("lead: valid Rolle kept", f.get("Rolle") == "Operations")

f2 = wc.build_lead_fields({"company": "Solo GmbH", "notes": "n", "role": "Chef-irgendwas"}, "2026-06-30")
check("lead: invalid Rolle omitted", "Rolle" not in f2)
check("lead: Name = Firma when no city", f2["Name"] == "Solo GmbH")

# --- callout line -------------------------------------------------------------
line = wc.build_callout_line(
    {"company": "Furness", "contact": "Remo", "email": "r@f.ch",
     "notes": "wollen\nMail\n\nschreiben"})
check("callout: starts 'Company → '", line.startswith("Furness → "))
check("callout: detail folded in", "Remo" in line and "r@f.ch" in line)
check("callout: notes present", "wollen Mail schreiben" in line)
check("callout: single line (no newlines)", "\n" not in line and "\r" not in line)
check("callout: unmarked (no ✅)", "✅" not in line)

# --- mime → ext ---------------------------------------------------------------
check("ext: audio/mp4 → .m4a", wc.ext_for_mime("audio/mp4") == ".m4a")
check("ext: video/mp4 (iOS) → .m4a", wc.ext_for_mime("video/mp4") == ".m4a")
check("ext: audio/webm → .webm", wc.ext_for_mime("audio/webm;codecs=opus") == ".webm")
check("ext: audio/mpeg → .mp3", wc.ext_for_mime("audio/mpeg") == ".mp3")
check("ext: unknown audio/* falls back to filename ext", wc.ext_for_mime("audio/x-weird", "memo.ogg") == ".ogg")
check("ext: non-audio rejected ('')", wc.ext_for_mime("application/pdf", "x.pdf") == "")

# --- save + sidecar round-trip ------------------------------------------------
sc = wc.save_voice_memo("Nico", b"FAKEAUDIOBYTES", "audio/mp4", "memo.m4a", duration_sec="47")
check("save: audio name pattern", sc["audio"].endswith(".m4a") and "__Nico__" in sc["audio"])
check("save: audio file on disk", os.path.exists(os.path.join(_TMP, sc["audio"])))
check("save: sidecar pending", sc["status"] == "pending" and sc["kb_page_id"] is None)
check("save: duration parsed int", sc["duration_sec"] == 47)
check("save: bad audio type raises",
      _raises(lambda: wc.save_voice_memo("Nico", b"x", "image/png", "x.png")))
check("save: empty content raises",
      _raises(lambda: wc.save_voice_memo("Nico", b"", "audio/mp4", "x.m4a")))

cards = wc.list_sidecars()
check("list: one sidecar", len(cards) == 1)
pend = wc.pending_memos()
check("pending: one pending", len(pend) == 1 and pend[0]["audio"] == sc["audio"])
stats = wc.memo_stats()
check("stats: pending=1 today=0 max=10",
      stats["pending"] == 1 and stats["transcribed_today"] == 0 and stats["max_per_day"] == 10)

# mark transcribed → leaves pending, increments today
upd = wc.update_sidecar(sc["audio"], status="transcribed", kb_page_id="pg_1",
                        transcribed_at=wc._now_local().isoformat(timespec="seconds"))
check("update: status flipped", upd["status"] == "transcribed" and upd["kb_page_id"] == "pg_1")
check("pending after transcribe: empty", wc.pending_memos() == [])
check("stats after transcribe: today=1", wc.memo_stats()["transcribed_today"] == 1)

# attempts cap: a pending memo with attempts>=3 is excluded
sc2 = wc.save_voice_memo("Tej", b"AAAA", "audio/webm", "m.webm")
wc.update_sidecar(sc2["audio"], attempts=3)
check("pending: attempts>=3 excluded", all(s["audio"] != sc2["audio"] for s in wc.pending_memos()))

print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
if FAIL:
    print("FAILURES:", FAIL)
    sys.exit(1)
sys.exit(0)
