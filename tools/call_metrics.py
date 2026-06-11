"""Per-call quality metrics for the Lena cold-call agent — deterministic, computed
purely from the Vapi call object (no extra API calls). Feeds the Beta->V1 gate
dashboard: call_health (0-100), response latency, hangup attribution, STT-garble
rate. Pure functions; unit-tested in .tmp/test_call_metrics.py.

Design: the deterministic latency number dominates; the LLM-extracted
speech_quality_flag is only secondary confirmation (they can disagree — the number
wins). A non-conversation (no-answer / voicemail / failed-connect) has health=None,
NOT 0, so it never drags down the median of real conversations."""

BOT_MONOLOG_MS = 12000
# a real response latency is at most a few seconds; larger gaps are silence-timeouts
# or Vapi timestamp anomalies (some messages carry an epoch instead of secondsFromStart)
# and must not pollute the latency stats.
MAX_PLAUSIBLE_LATENCY_S = 15.0
NO_CONTACT_REASONS = {
    "customer-did-not-answer", "voicemail", "twilio-failed-to-connect-call",
    "customer-busy", "no-answer", "twilio-failed-to-connect",
}
# known Swiss-German / Treuhand mishear patterns seen in live transcripts
_GARBLE_PATTERNS = ("aufwerten", "auf härten", "härten schreiben", "meinungen schreiben")


def _msg_text(m):
    return str(m.get("message") or m.get("content") or "")


def _user_bot_pairs(messages):
    for i in range(1, len(messages)):
        if messages[i - 1].get("role") == "user" and messages[i].get("role") == "bot":
            yield messages[i - 1], messages[i]


def turn_latencies(call):
    """Response latency = bot_start - user_end, per user->bot turn (seconds).
    Returns {p50, p95, max, n}. Negative gaps (barge-ins / overlap) are excluded."""
    msgs = call.get("messages") or []
    lats = []
    for u, b in _user_bot_pairs(msgs):
        try:
            user_end = float(u.get("secondsFromStart") or 0) + float(u.get("duration") or 0) / 1000.0
            gap = float(b.get("secondsFromStart") or 0) - user_end
        except (TypeError, ValueError):
            continue
        if 0 <= gap <= MAX_PLAUSIBLE_LATENCY_S:
            lats.append(gap)
    if not lats:
        return {"p50": None, "p95": None, "max": None, "n": 0}
    s = sorted(lats)

    def pct(p):
        k = max(0, min(len(s) - 1, int(round((p / 100.0) * (len(s) - 1)))))
        return round(s[k], 2)

    return {"p50": pct(50), "p95": pct(95), "max": round(max(lats), 2), "n": len(lats)}


def stt_garble_rate(call):
    """Heuristic fraction of user turns that look mis-transcribed.
    Signals: known mishear patterns; long audio but empty/tiny final transcript.
    Returns {rate, garbled, total}."""
    users = [m for m in (call.get("messages") or []) if m.get("role") == "user"]
    total = len(users)
    if not total:
        return {"rate": 0.0, "garbled": 0, "total": 0}
    garbled = 0
    for m in users:
        txt = _msg_text(m).lower().strip()
        if any(p in txt for p in _GARBLE_PATTERNS):
            garbled += 1
        elif len(txt) <= 2 and float(m.get("duration") or 0) > 1500:
            garbled += 1
    return {"rate": round(garbled / total, 3), "garbled": garbled, "total": total}


def compute_call_health(call):
    """0-100 technical-quality score, or None for non-conversations.
    Latency (deterministic) dominates; speech_quality_flag is secondary."""
    er = str(call.get("endedReason") or "")
    transcript = str(call.get("transcript") or "").strip()
    if er in NO_CONTACT_REASONS or not transcript:
        return None
    score = 100
    p95 = turn_latencies(call).get("p95")
    if p95 is not None:
        if p95 > 2.5:
            score -= 25
        elif p95 > 1.5:
            score -= 10
    sq = str(((call.get("analysis") or {}).get("structuredData") or {}).get("speech_quality_flag") or "")
    score += {"high_latency": -20, "long_turns": -15, "interruptions": -15}.get(sq, 0)
    if stt_garble_rate(call).get("garbled", 0) > 2:
        score -= 20
    if any(m.get("role") == "bot" and float(m.get("duration") or 0) > BOT_MONOLOG_MS
           for m in (call.get("messages") or [])):
        score -= 15
    return max(0, min(100, score))


def hangup_attribution(call, health="__auto__"):
    """Why the call ended: 'no_contact' / 'agent_fault' (tech broke) / 'lead_choice' (clean no).
    agent_fault = the call was lost to OUR defect (low health, STT garble, high latency,
    or it died in the first bot turn before the lead said anything). Only lead_choice
    hangups are ICP/pitch work; agent_fault hangups are bug backlog."""
    er = str(call.get("endedReason") or "")
    if er in NO_CONTACT_REASONS:
        return "no_contact"
    if health == "__auto__":
        health = compute_call_health(call)
    msgs = call.get("messages") or []
    user_turns = [m for m in msgs if m.get("role") == "user"]
    early = len(user_turns) == 0 or (len(user_turns) == 1 and len(_msg_text(user_turns[0]).strip()) <= 3)
    p95 = turn_latencies(call).get("p95") or 0
    garbled = stt_garble_rate(call).get("garbled", 0)
    if (health is not None and health < 60) or garbled > 2 or p95 > 2.5 or early:
        return "agent_fault"
    return "lead_choice"


def call_duration_s(call):
    """Best-effort call duration in seconds (from the last message timing)."""
    msgs = call.get("messages") or []
    if msgs:
        try:
            last = msgs[-1]
            return float(last.get("secondsFromStart") or 0) + float(last.get("duration") or 0) / 1000.0
        except (TypeError, ValueError):
            pass
    return 0.0


def opener_survived(call):
    """Funnel stage 2: the call survived the opener transition (> 25s AND >= 2 user turns)."""
    if str(call.get("endedReason") or "") in NO_CONTACT_REASONS:
        return False
    user_turns = [m for m in (call.get("messages") or []) if m.get("role") == "user"]
    return call_duration_s(call) >= 25 and len(user_turns) >= 2


def screening_completed(call):
    """Funnel stage 3: all 3 screening questions asked + answered (from the analysis)."""
    sd = (call.get("analysis") or {}).get("structuredData") or {}
    return sd.get("interview_completed") is True


def booked(call):
    """Funnel stage 4: a concrete follow-up appointment was agreed."""
    sd = (call.get("analysis") or {}).get("structuredData") or {}
    return sd.get("appointment_booked") is True or sd.get("appointment_agreed") is True


def score_call(call):
    """All per-call metrics in one dict."""
    health = compute_call_health(call)
    lat = turn_latencies(call)
    garble = stt_garble_rate(call)
    return {
        "health": health,
        "lat_p50": lat["p50"], "lat_p95": lat["p95"], "lat_max": lat["max"], "lat_n": lat["n"],
        "stt_garble_rate": garble["rate"], "stt_garbled": garble["garbled"], "stt_total": garble["total"],
        "hangup_cause": hangup_attribution(call, health),
        "opener_survived": opener_survived(call),
        "screening_completed": screening_completed(call),
        "booked": booked(call),
    }
