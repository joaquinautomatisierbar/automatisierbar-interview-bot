#!/usr/bin/env python3
"""
fitness_sync.py — Comeback tracking sync.

Pulls daily recovery/performance from Garmin (via garth, token-resume — NO login
in the loop) + strength from Hevy, computes adherence/HRV-Ampel/trends, and writes
to Notion (Daily Log + Workouts + Weekly Summary). Also emits a compact widget JSON.

Design principles (see workflows/fitness_tracking.md):
- Compute everything here; Notion is just a display surface.
- null -> skip a field (never null -> 0), so a missing day never wipes good values.
- Per-source try/except: one source down never aborts the run.
- Idempotent upsert by key (Tag=ISO date / Woche=ISO week).
- Trailing-window reprocessing self-heals missed days.
- Graceful, non-blocking failure (Telegram notify); never wait on stdin.

Modes:
  --mode daily      today + trailing N days (default 3)  -> Notion + widget
  --mode weekly     last complete ISO week               -> Notion
  --mode backfill   last N days (default 30)              -> Notion + weekly rows
  --mode emit       print computed rows as JSON (for MCP seeding) — no writes
  --mode widget     build + push only the widget JSON

Env (.env): INTERVALS_API_KEY, INTERVALS_ATHLETE_ID, HEVY_API_KEY,
  GARMIN_TOKEN_DIR, GARMIN_DISPLAY_NAME, NOTION_TOKEN (opt), N8N_INGEST_URL (opt),
  N8N_WIDGET_PUSH_URL (opt), OPERATOR_TELEGRAM_BOT_TOKEN, OPERATOR_TELEGRAM_CHAT_ID
"""
import os, sys, json, time, argparse, traceback
from datetime import date, datetime, timedelta, timezone

# ---------- config ----------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Look for .env next to the script first (deployed copy in ~/.comeback-sync to avoid
# macOS TCC restrictions on ~/Desktop), then fall back to the repo root (3 levels up).
_ENV_CANDIDATES = [os.path.join(_SCRIPT_DIR, ".env"),
                   os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), ".env")]
ENV_PATH = next((p for p in _ENV_CANDIDATES if os.path.exists(p)), _ENV_CANDIDATES[0])
TZ = "Europe/Zurich"
os.environ["TZ"] = TZ
try:
    time.tzset()
except Exception:
    pass

PROGRAM_START = date(2026, 6, 22)   # Week 1 Monday
HRV_BASELINE_LOW, HRV_BASELINE_HIGH = 78, 98   # ms, from the plan

# Notion data sources (created 2026-06-09)
NOTION = {
    "daily":   {"db": "551b60032992485c8caa47ae1ca4f447", "ds": "215e466b-f99a-419b-99b2-2de7f903a626"},
    "workouts":{"db": "bce09993b23d4c8da3ce8144d9bcc5c0", "ds": "a90f41d0-327c-4c61-9685-16e35a0c4e10"},
    "weekly":  {"db": "c2fa8adb06774a11809040e1c6574c97", "ds": "0929c338-d3ee-4a3b-b8ba-96f104ecb9b6"},
}

def load_env():
    env = {}
    try:
        with open(ENV_PATH) as f:
            for ln in f:
                ln = ln.strip()
                if not ln or ln.startswith("#") or "=" not in ln:
                    continue
                k, v = ln.split("=", 1)
                env[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    return env

ENV = load_env()
def cfg(k, default=None): return ENV.get(k, os.environ.get(k, default))

import requests
GARMIN_TOKEN_DIR = cfg("GARMIN_TOKEN_DIR", os.path.expanduser("~/.garminconnect"))
GARMIN_GUID = cfg("GARMIN_DISPLAY_NAME", "")
HEVY_KEY = cfg("HEVY_API_KEY", "")

# ---------- utilities ----------
def log(msg): print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def telegram(kind, text):
    """Best-effort operator ping; never raises."""
    try:
        tok = cfg("OPERATOR_TELEGRAM_BOT_TOKEN"); chat = cfg("OPERATOR_TELEGRAM_CHAT_ID")
        if not tok or not chat: return
        requests.post(f"https://api.telegram.org/bot{tok}/sendMessage",
                      json={"chat_id": chat, "text": f"[fitness-sync] {kind}: {text}"}, timeout=15)
    except Exception:
        pass

def retry(fn, tries=3, delays=(2, 8, 30), label=""):
    last = None
    for i in range(tries):
        try:
            return fn()
        except Exception as e:
            last = e
            if i < tries - 1:
                time.sleep(delays[min(i, len(delays)-1)])
    raise last

def emoji_bar(pct, width=10):
    pct = max(0.0, min(1.0, pct or 0.0))
    filled = int(round(pct * width))
    return "▓" * filled + "░" * (width - filled) + f" {int(round(pct*100))}%"

# ---------- Garmin (garth, token resume) ----------
_garth_ready = False
def garmin_ready():
    global _garth_ready
    if _garth_ready: return True
    try:
        import garth
        garth.resume(GARMIN_TOKEN_DIR)
        garth.connectapi("/userprofile-service/socialProfile")  # cheap auth check
        _garth_ready = True
        return True
    except Exception as e:
        log(f"GARMIN token resume FAILED: {e}")
        telegram("halt", f"Garmin token tot/abgelaufen ({e}). Bitte neu einloggen (garth). Sync läuft ohne Garmin weiter.")
        return False

def g_api(path):
    import garth
    return garth.connectapi(path)

def garmin_day(d):
    """Return dict of Garmin metrics for ISO date d (str). Missing -> key absent."""
    out = {}
    if not garmin_ready():
        return out
    ds = d
    def safe(label, fn):
        try:
            return retry(fn, label=label)
        except Exception as e:
            log(f"  garmin {label} miss {ds}: {str(e)[:60]}")
            return None
    # daily summary: RHR, steps
    summ = safe("summary", lambda: g_api(f"/usersummary-service/usersummary/daily/{GARMIN_GUID}?calendarDate={ds}"))
    if isinstance(summ, dict):
        if summ.get("restingHeartRate"): out["rhr"] = summ["restingHeartRate"]
        if summ.get("totalSteps") is not None: out["steps"] = summ["totalSteps"]
    # sleep: hours + score
    sleep = safe("sleep", lambda: g_api(f"/wellness-service/wellness/dailySleepData/{GARMIN_GUID}?date={ds}&nonSleepBufferMinutes=60"))
    if isinstance(sleep, dict):
        dto = sleep.get("dailySleepDTO") or {}
        secs = dto.get("sleepTimeSeconds")
        if secs and secs/3600.0 >= 2.0:   # guard: <2h => watch likely not worn, treat as missing
            out["sleep_h"] = round(secs/3600.0, 2)
        sc = (dto.get("sleepScores") or {}).get("overall") or {}
        if sc.get("value") is not None: out["sleep_score"] = sc["value"]
        if not out.get("rhr") and dto.get("restingHeartRate"): out["rhr"] = dto["restingHeartRate"]
    # HRV: ms + status -> ampel
    hrv = safe("hrv", lambda: g_api(f"/hrv-service/hrv/{ds}"))
    if isinstance(hrv, dict):
        s = hrv.get("hrvSummary") or {}
        if s.get("lastNightAvg"): out["hrv"] = s["lastNightAvg"]
        if s.get("status"): out["hrv_status"] = s["status"]
        bl = s.get("baseline") or {}
        if bl.get("balancedLow"): out["hrv_base_low"] = bl["balancedLow"]
        if bl.get("balancedUpper"): out["hrv_base_high"] = bl["balancedUpper"]
    # body battery (max of day)
    bb = safe("bodybattery", lambda: g_api(f"/wellness-service/wellness/bodyBattery/reports/daily?startDate={ds}&endDate={ds}"))
    if isinstance(bb, list) and bb:
        vals = []
        for rec in bb:
            for pair in (rec.get("bodyBatteryValuesArray") or []):
                if isinstance(pair, list) and len(pair) >= 2 and isinstance(pair[1], (int, float)):
                    vals.append(pair[1])
        if vals: out["body_battery"] = max(vals)
    # vo2max
    vo = safe("vo2max", lambda: g_api(f"/metrics-service/metrics/maxmet/latest/{ds}"))
    if isinstance(vo, dict):
        gen = vo.get("generic") or {}
        v = gen.get("vo2MaxPreciseValue") or gen.get("vo2MaxValue")
        if v: out["vo2max"] = v
    # training readiness (score)
    tr = safe("readiness", lambda: g_api(f"/metrics-service/metrics/trainingreadiness/{ds}"))
    if isinstance(tr, list) and tr and isinstance(tr[0], dict):
        if tr[0].get("score") is not None: out["readiness"] = tr[0]["score"]
    # training status -> acute load (best-effort)
    tst = safe("trainingstatus", lambda: g_api(f"/metrics-service/metrics/trainingstatus/aggregated/{ds}"))
    if isinstance(tst, dict):
        try:
            mr = tst.get("mostRecentTrainingLoadBalance") or {}
            mset = (mr.get("metricsTrainingLoadBalanceDTOMap") or {})
            for _, val in mset.items():
                acwr = val.get("acuteTrainingLoad")
                if acwr: out["training_load"] = acwr; break
        except Exception:
            pass
    return out

def garmin_activities(start_d, end_d):
    """List activities between two ISO dates (inclusive). Returns list of dicts."""
    if not garmin_ready(): return []
    try:
        acts = retry(lambda: g_api("/activitylist-service/activities/search/activities?start=0&limit=60"), label="activities")
    except Exception as e:
        log(f"  garmin activities miss: {str(e)[:60]}")
        return []
    out = []
    if isinstance(acts, list):
        for a in acts:
            stl = (a.get("startTimeLocal") or "")[:10]
            if start_d <= stl <= end_d:
                out.append({
                    "date": stl,
                    "type": ((a.get("activityType") or {}).get("typeKey") or "").lower(),
                    "name": a.get("activityName") or "",
                    "duration_min": round((a.get("duration") or 0)/60.0, 1),
                })
    return out

CARDIO_TYPES = {"running","treadmill_running","trail_running","indoor_running",
                "lap_swimming","open_water_swimming","swimming",
                "cycling","indoor_cycling","road_biking","virtual_ride"}
def classify_activity(a):
    t, n = a["type"], a["name"].lower()
    if t in CARDIO_TYPES: return "cardio"
    if "strength" in t or t == "strength_training" or t == "indoor_cardio" or t == "fitness_equipment":
        if "mobility" in n: return "mobility"
        if "cuff" in n or "schulter" in n: return "cuff"
        return "strength"
    if "yoga" in t or "pilates" in t: return "mobility"
    return None

# ---------- Hevy ----------
def hevy_workouts(max_pages=6):
    """Return list of completed workouts (raw)."""
    if not HEVY_KEY: return []
    out = []
    try:
        for page in range(1, max_pages+1):
            r = retry(lambda: requests.get("https://api.hevyapp.com/v1/workouts",
                      headers={"api-key": HEVY_KEY}, params={"page": page, "pageSize": 10}, timeout=30), label="hevy")
            if r.status_code != 200: break
            data = r.json(); ws = data.get("workouts", [])
            out.extend(ws)
            if page >= (data.get("page_count") or 1): break
    except Exception as e:
        log(f"  hevy fetch miss: {str(e)[:60]}")
    return out

def hevy_metrics_for(workouts, d):
    """Aggregate volume/sets/duration for a given ISO date."""
    vol = 0.0; sets = 0; dur = 0.0; routines = []
    rows = []
    for w in workouts:
        wd = (w.get("start_time") or "")[:10]
        if wd != d: continue
        wv = 0.0; ws = 0
        for ex in (w.get("exercises") or []):
            for s in (ex.get("sets") or []):
                if (s.get("type") or "normal") == "warmup": continue
                wkg = s.get("weight_kg"); reps = s.get("reps")
                if wkg and reps: wv += wkg*reps
                if reps or s.get("duration_seconds"): ws += 1
        st = w.get("start_time"); et = w.get("end_time")
        wdur = 0.0
        try:
            if st and et:
                wdur = (datetime.fromisoformat(et.replace("Z","+00:00")) - datetime.fromisoformat(st.replace("Z","+00:00"))).total_seconds()/60.0
        except Exception:
            pass
        vol += wv; sets += ws; dur += wdur
        title = w.get("title") or "Workout"
        routines.append(title)
        rows.append({"hevy_id": w.get("id"), "date": d, "title": title,
                     "routine": title, "volume": round(wv,1), "sets": ws, "dur": round(wdur,1)})
    return {"volume": round(vol,1), "sets": sets, "dur": round(dur,1), "routines": routines, "rows": rows}

# ---------- plan / adherence ----------
DOW = ["Mo","Di","Mi","Do","Fr","Sa","So"]
def week_index(d):
    if d < PROGRAM_START: return 0
    return (d - PROGRAM_START).days // 7 + 1

def planned_for(d):
    """Set of planned session types for date d (only within the programmed W1-6)."""
    wk = week_index(d)
    if wk < 1 or wk > 6: return set()
    dow = d.weekday()
    p = {"mobility"}                      # daily floor
    if dow in (0,2,4): p.add("cuff")      # Mon/Wed/Fri
    phase = 1 if wk <= 3 else 2
    if dow in (2,5): p.add("cardio")      # Wed + Sat
    if phase == 1:
        if dow in (1,4): p.add("strength")   # Tue legs, Fri full-body
    else:
        if dow in (0,1,2,3): p.add("strength")  # Mon/Tue/Wed/Thu
    return p

def hrv_ampel(metrics):
    """grün/gelb/rot — numeric-primary (HIGH HRV = good), sleep gates green.
    Garmin's 'UNBALANCED' status fires for high *and* low HRV, so we use the number
    vs the (Garmin) baseline window, not the status label."""
    v = metrics.get("hrv")
    sleep_h = metrics.get("sleep_h")
    if v is None:
        st = (metrics.get("hrv_status") or "").upper()
        if st == "BALANCED": base = "grün"
        elif st in ("LOW","POOR"): base = "rot"
        elif st: base = "gelb"
        else: return None
    else:
        lo = metrics.get("hrv_base_low") or HRV_BASELINE_LOW
        if v >= lo:        base = "grün"   # at/above balanced-low = recovered
        elif v >= lo*0.85: base = "gelb"
        else:              base = "rot"
    # poor sleep downgrades a green day (and a glitch/None sleep does not)
    if sleep_h is not None and sleep_h < 6 and base == "grün":
        base = "gelb"
    return base

# ---------- compute ----------
def compute_range(d_start, d_end):
    """Compute daily rows for [d_start, d_end] with rolling HRV trend. Returns list."""
    workouts = hevy_workouts()
    acts = garmin_activities(d_start.isoformat(), d_end.isoformat())
    acts_by_date = {}
    for a in acts:
        acts_by_date.setdefault(a["date"], []).append(a)
    rows = []
    hrv_hist = []   # rolling for trend
    d = d_start
    while d <= d_end:
        ds = d.isoformat()
        m = garmin_day(ds)
        # done detection
        done = set()
        for a in acts_by_date.get(ds, []):
            c = classify_activity(a)
            if c: done.add(c)
        hv = hevy_metrics_for(workouts, ds)
        if hv["volume"] > 0 or hv["sets"] > 0: done.add("strength")
        planned = planned_for(d)
        # adherence
        adh = None
        if planned:
            met = len(planned & done)
            adh = round(met / len(planned), 4)
        ampel = hrv_ampel(m)
        # trend arrow vs trailing-7 HRV avg
        trend = None
        if m.get("hrv") is not None:
            if len(hrv_hist) >= 3:
                avg = sum(hrv_hist[-7:]) / len(hrv_hist[-7:])
                trend = "↑" if m["hrv"] > avg*1.02 else ("↓" if m["hrv"] < avg*0.98 else "→")
            hrv_hist.append(m["hrv"])
        row = {
            "date": ds, "dow": DOW[d.weekday()],
            "phase": (1 if week_index(d) in (1,2,3) else (2 if week_index(d) in (4,5,6) else None)),
            "week": week_index(d) or None,
            "planned": sorted(planned), "done": sorted(done), "adherence": adh,
            "ampel": ampel, "trend": trend,
            "metrics": m,
            "strength_volume": hv["volume"] if hv["volume"] else None,
            "hevy_rows": hv["rows"],
        }
        rows.append(row)
        d += timedelta(days=1)
    return rows

def plan_label(planned):
    names = {"mobility":"Mobility","cuff":"Cuff","cardio":"Cardio","strength":"Kraft"}
    return " · ".join(names[p] for p in ["mobility","cuff","cardio","strength"] if p in planned) or "Ruhe"

# ---------- Notion write (optional: NOTION_TOKEN direct, else n8n relay) ----------
NOTION_TOKEN = cfg("NOTION_TOKEN") or cfg("NOTION_API_KEY")  # reuse existing integration token
NOTION_VER = "2022-06-28"
def _nh():
    return {"Authorization": f"Bearer {NOTION_TOKEN}", "Notion-Version": NOTION_VER, "Content-Type": "application/json"}

def notion_find(db_id, title_prop, title_val):
    r = requests.post(f"https://api.notion.com/v1/databases/{db_id}/query", headers=_nh(),
                      json={"filter": {"property": title_prop, "title": {"equals": title_val}}, "page_size": 1}, timeout=30)
    r.raise_for_status()
    res = r.json().get("results", [])
    return res[0]["id"] if res else None

def _num(v): return {"number": v} if v is not None else {"number": None}
def _txt(v): return {"rich_text": [{"text": {"content": str(v)}}]} if v not in (None,"") else {"rich_text": []}
def _title(v): return {"title": [{"text": {"content": str(v)}}]}
def _chk(v): return {"checkbox": bool(v)}
def _date(v): return {"date": {"start": v}} if v else {"date": None}
def _sel(v): return {"select": {"name": v}} if v else {"select": None}

def daily_props(row):
    m = row["metrics"]
    p = {
        "Tag": _title(row["date"]),
        "Datum": _date(row["date"]),
        "Plan": _txt(plan_label(set(row["planned"]))),
        "Mobility": _chk("mobility" in row["done"]),
        "Cuff": _chk("cuff" in row["done"]),
        "Cardio": _chk("cardio" in row["done"]),
        "Kraft": _chk("strength" in row["done"]),
        "Trend": _txt(row["trend"] or ""),
    }
    if row["phase"] is not None: p["Phase"] = _num(row["phase"])
    if row["week"] is not None: p["Woche"] = _num(row["week"])
    if row["adherence"] is not None: p["Adhärenz"] = _num(row["adherence"])
    if row["ampel"]: p["HRV-Ampel"] = _sel(row["ampel"])
    if m.get("hrv") is not None: p["HRV ms"] = _num(m["hrv"])
    if m.get("rhr") is not None: p["RHR"] = _num(m["rhr"])
    if m.get("sleep_h") is not None: p["Schlaf h"] = _num(m["sleep_h"])
    if m.get("sleep_score") is not None: p["Schlaf-Score"] = _num(m["sleep_score"])
    if m.get("body_battery") is not None: p["Body Battery"] = _num(m["body_battery"])
    if m.get("vo2max") is not None: p["VO2max"] = _num(m["vo2max"])
    if m.get("training_load") is not None: p["Training Load"] = _num(m["training_load"])
    if m.get("readiness") is not None: p["Readiness"] = _num(m["readiness"])
    if m.get("steps") is not None: p["Schritte"] = _num(m["steps"])
    if row.get("strength_volume") is not None: p["Kraft-Volumen kg"] = _num(row["strength_volume"])
    return p

def daily_sqlite_props(row):
    """Flat property map for the claude.ai notion-create-pages MCP (SQLite-style values).
    Null values are omitted so a missing metric never writes a 0."""
    m = row["metrics"]
    p = {
        "Tag": row["date"],
        "date:Datum:start": row["date"],
        "Plan": plan_label(set(row["planned"])),
        "Mobility": "__YES__" if "mobility" in row["done"] else "__NO__",
        "Cuff": "__YES__" if "cuff" in row["done"] else "__NO__",
        "Cardio": "__YES__" if "cardio" in row["done"] else "__NO__",
        "Kraft": "__YES__" if "strength" in row["done"] else "__NO__",
    }
    if row["trend"]: p["Trend"] = row["trend"]
    if row["phase"] is not None: p["Phase"] = row["phase"]
    if row["week"] is not None: p["Woche"] = row["week"]
    if row["adherence"] is not None: p["Adhärenz"] = row["adherence"]
    if row["ampel"]: p["HRV-Ampel"] = row["ampel"]
    keymap = {"hrv":"HRV ms","rhr":"RHR","sleep_h":"Schlaf h","sleep_score":"Schlaf-Score",
              "body_battery":"Body Battery","vo2max":"VO2max","training_load":"Training Load",
              "readiness":"Readiness","steps":"Schritte"}
    for mk, col in keymap.items():
        if m.get(mk) is not None: p[col] = m[mk]
    if row.get("strength_volume") is not None: p["Kraft-Volumen kg"] = row["strength_volume"]
    return p

def notion_upsert(db_id, title_prop, title_val, props):
    pid = notion_find(db_id, title_prop, title_val)
    if pid:
        r = requests.patch(f"https://api.notion.com/v1/pages/{pid}", headers=_nh(), json={"properties": props}, timeout=30)
    else:
        r = requests.post("https://api.notion.com/v1/pages", headers=_nh(),
                          json={"parent": {"database_id": db_id}, "properties": props}, timeout=30)
    r.raise_for_status()
    return r.json()["id"]

def write_daily_to_notion(rows):
    if not NOTION_TOKEN:
        log("NOTION_TOKEN absent -> skipping direct Notion write (use --mode emit + MCP, or set token).")
        return 0
    n = 0
    for row in rows:
        try:
            notion_upsert(NOTION["daily"]["db"], "Tag", row["date"], daily_props(row))
            n += 1
        except Exception as e:
            log(f"  notion daily upsert fail {row['date']}: {str(e)[:80]}")
    return n

# ---------- weekly rollup ----------
def compute_weekly_rows(daily_rows):
    """Aggregate daily rows into ISO-week summaries. PATCH-safe: only sets computed
    fields, leaving any seeded Trajektorie text intact for older weeks."""
    from collections import defaultdict
    groups = defaultdict(list)
    for r in daily_rows:
        y, m, dd = map(int, r["date"].split("-"))
        iso = date(y, m, dd).isocalendar()
        groups[(iso[0], iso[1])].append(r)
    def avg(xs):
        xs = [x for x in xs if x is not None]
        return round(sum(xs) / len(xs), 1) if xs else None
    out, prev = [], None
    for (yr, wn) in sorted(groups.keys()):
        rs = sorted(groups[(yr, wn)], key=lambda r: r["date"])
        hrv = avg([r["metrics"].get("hrv") for r in rs])
        rhr = avg([r["metrics"].get("rhr") for r in rs])
        slp = avg([r["metrics"].get("sleep_h") for r in rs])
        vo2 = avg([r["metrics"].get("vo2max") for r in rs])
        planned = sum(len(r["planned"]) for r in rs)
        done = sum(len(set(r["planned"]) & set(r["done"])) for r in rs)
        vol = sum((r.get("strength_volume") or 0) for r in rs)
        p = {"Woche": f"{yr}-W{wn:02d}", "Zeitraum": f"{rs[0]['date']} – {rs[-1]['date']}",
             "Sessions geplant": planned, "Sessions erledigt": done}
        ph = next((r["phase"] for r in reversed(rs) if r["phase"] is not None), None)
        if ph is not None: p["Phase"] = ph
        if planned: p["Adhärenz"] = round(done / planned, 4)
        if hrv is not None: p["HRV Ø"] = hrv
        if rhr is not None: p["RHR Ø"] = rhr
        if slp is not None: p["Schlaf Ø h"] = slp
        if vo2 is not None: p["VO2max"] = vo2
        if vol: p["Kraft-Volumen kg"] = round(vol, 1)
        if prev:
            if hrv is not None and prev.get("hrv") is not None: p["HRV Δ"] = round(hrv - prev["hrv"], 1)
            if rhr is not None and prev.get("rhr") is not None: p["RHR Δ"] = round(rhr - prev["rhr"], 1)
        if slp:
            fill = int(round(min(1.0, slp / 8.0) * 10)); p["Fortschritt"] = "▓" * fill + "░" * (10 - fill) + f" Schlaf {slp}h"
        out.append((p["Woche"], p)); prev = {"hrv": hrv, "rhr": rhr, "slp": slp}
    return out

def weekly_props_notion(p):
    out = {"Woche": _title(p["Woche"])}
    for k, v in p.items():
        if k == "Woche": continue
        out[k] = _txt(v) if isinstance(v, str) else _num(v)
    return out

def write_weekly_to_notion(weekly):
    if not NOTION_TOKEN: return 0
    n = 0
    for wk_key, props in weekly:
        try:
            notion_upsert(NOTION["weekly"]["db"], "Woche", wk_key, weekly_props_notion(props)); n += 1
        except Exception as e:
            log(f"  notion weekly upsert fail {wk_key}: {str(e)[:80]}")
    return n

# ---------- widget JSON ----------
def build_widget_json(rows):
    today = date.today()
    # Before the program starts, preview Week 1 so the widget isn't an empty "rest" week.
    starts_in = max(0, (PROGRAM_START - today).days)
    if today < PROGRAM_START:
        monday = PROGRAM_START
    else:
        monday = today - timedelta(days=today.weekday())
    by_date = {r["date"]: r for r in rows}
    week = []
    done_cnt = planned_cnt = 0
    for i in range(7):
        dd = monday + timedelta(days=i)
        r = by_date.get(dd.isoformat())
        planned = set(r["planned"]) if r else planned_for(dd)
        done = set(r["done"]) if r else set()
        if dd > today:
            state = "planned" if planned else "rest"
        elif not planned:
            state = "rest"
        elif planned <= done:
            state = "done"
        elif dd == today:
            state = "today"
        else:
            state = "missed" if not (planned & done) else "partial"
        if dd <= today and planned:
            planned_cnt += len(planned); done_cnt += len(planned & done)
        primary = "mobility"
        for t in ("cardio","strength","cuff","mobility"):
            if t in planned: primary = t; break
        week.append({"day": DOW[i], "date": dd.strftime("%d.%m"),
                     "type": primary if planned else "rest",
                     "label": plan_label(planned) if planned else "Ruhetag",
                     "types": sorted(planned), "state": state})
    # today / latest recovery
    latest = None
    for i in range(0, 4):
        r = by_date.get((today - timedelta(days=i)).isoformat())
        if r and r["metrics"].get("hrv") is not None: latest = r; break
    hrv = {}
    if latest:
        m = latest["metrics"]
        verdict = {"grün":"GO","gelb":"EASY","rot":"REST"}.get(latest["ampel"], "—")
        hrv = {"ms": m.get("hrv"), "ampel": latest["ampel"], "arrow": latest["trend"] or "→", "verdict": verdict}
    # streak: consecutive days up to yesterday meeting floor (mobility) or rest.
    # guard bounds total iterations regardless of skipped rest days (and pre-program days).
    streak = 0
    d = today - timedelta(days=1)
    for _ in range(60):
        if d < PROGRAM_START:
            break
        r = by_date.get(d.isoformat())
        planned = set(r["planned"]) if r else planned_for(d)
        done = set(r["done"]) if r else set()
        if not planned:
            d -= timedelta(days=1); continue
        if "mobility" in done or planned <= done:
            streak += 1; d -= timedelta(days=1)
        else:
            break
    pct = (done_cnt/planned_cnt) if planned_cnt else 0.0
    if starts_in > 0:
        headline = f"Comeback startet in {starts_in} Tagen — Woche 1"
    elif pct >= 0.8: headline = "Stark — bleib auf Kurs 💪"
    elif pct >= 0.4: headline = "Floor zählt. Dranbleiben."
    else: headline = "Heute ist ein neuer Tag."
    return {
        "updated": datetime.now(timezone.utc).isoformat(),
        "phase": (rows[-1]["phase"] if rows and rows[-1]["phase"] else 1),
        "week_no": week_index(monday) or 1,
        "starts_in_days": starts_in,
        "week_start": monday.isoformat(),
        "week": week,
        "progress": {"done": done_cnt, "planned": planned_cnt, "pct": round(pct,3)},
        "hrv": hrv, "streak_days": streak, "headline": headline,
    }

def push_widget(payload):
    url = cfg("N8N_WIDGET_PUSH_URL")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "widget_latest.json")
    try:
        with open(out, "w") as f: json.dump(payload, f, ensure_ascii=False, indent=2)
        log(f"widget JSON written -> {out}")
    except Exception as e:
        log(f"widget file write fail: {e}")
    if url:
        try:
            requests.post(url, json=payload, timeout=30)
            log("widget JSON pushed to n8n")
        except Exception as e:
            log(f"widget push fail: {str(e)[:80]}")

# ---------- main ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="daily", choices=["daily","weekly","backfill","emit","widget"])
    ap.add_argument("--days", type=int, default=None)
    args = ap.parse_args()
    today = date.today()
    try:
        if args.mode == "backfill":
            n = args.days or 35
            rows = compute_range(today - timedelta(days=n), today)
            w = write_daily_to_notion(rows)
            ww = write_weekly_to_notion(compute_weekly_rows(rows))
            push_widget(build_widget_json(rows))
            log(f"backfill: {len(rows)} days -> Notion daily {w}, weekly {ww}")
        elif args.mode == "emit":
            n = args.days or 30
            rows = compute_range(today - timedelta(days=n), today)
            print(json.dumps({"daily": rows, "mcp_daily": [daily_sqlite_props(r) for r in rows],
                              "widget": build_widget_json(rows)}, ensure_ascii=False, indent=2))
        elif args.mode == "widget":
            rows = compute_range(today - timedelta(days=10), today)
            push_widget(build_widget_json(rows))
        elif args.mode == "weekly":
            rows = compute_range(today - timedelta(days=21), today)
            ww = write_weekly_to_notion(compute_weekly_rows(rows))
            push_widget(build_widget_json(rows))
            log(f"weekly: wrote {ww} week rows to Notion")
        else:  # daily — also refreshes current+prev ISO week so weekly stays current
            n = args.days or 9
            rows = compute_range(today - timedelta(days=n), today)
            w = write_daily_to_notion(rows)
            ww = write_weekly_to_notion(compute_weekly_rows(rows))
            push_widget(build_widget_json(rows))
            log(f"daily: {len(rows)} days -> Notion daily {w}, weekly {ww}")
    except Exception as e:
        log("FATAL: " + str(e)); traceback.print_exc()
        telegram("halt", f"Sync-Fehler ({args.mode}): {str(e)[:120]}")
        sys.exit(1)

if __name__ == "__main__":
    main()
