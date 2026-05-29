#!/usr/bin/env node
// pipeline_status.js — single-screen observability for the paperclip build pipeline.
//
// Answers "what's happening and why did it stall" in one command. Read-only.
//
// Dual transport:
//   - On the VPS: hits http://127.0.0.1:3100 directly.
//   - From the MacBook: auto-falls back to `ssh paperclip@host curl localhost:3100/...`.
//
// Usage:
//   node tools/paperclip/pipeline_status.js            # one snapshot
//   node tools/paperclip/pipeline_status.js --watch     # refresh every 30s
//   node tools/paperclip/pipeline_status.js --all        # include done issues
//   node tools/paperclip/pipeline_status.js --json       # raw machine output

const { CFG, probe, mode, api, sshExec, arr } = require("./lib/transport");

const ARGS = new Set(process.argv.slice(2));
const WATCH = ARGS.has("--watch");
const SHOW_ALL = ARGS.has("--all");
const JSON_OUT = ARGS.has("--json");

const C = { reset: "\x1b[0m", dim: "\x1b[2m", red: "\x1b[31m", grn: "\x1b[32m", yel: "\x1b[33m", cyn: "\x1b[36m", bold: "\x1b[1m" };
const paint = (s, c) => (process.stdout.isTTY ? `${c}${s}${C.reset}` : String(s));

// ---- verdict logic ------------------------------------------------------
const T = CFG.thresholds;
const ageSec = (iso) => (iso ? Math.round((Date.now() - new Date(iso).getTime()) / 1000) : null);
const fmtAge = (s) => (s == null ? "-" : s < 90 ? `${s}s` : s < 5400 ? `${Math.round(s / 60)}m` : s < 172800 ? `${Math.round(s / 3600)}h` : `${Math.round(s / 86400)}d`);

function verdict(issue, agentsById, childInReview) {
  const st = issue.status;
  if (st === "done") return { v: "DONE", c: C.dim };
  if (st === "in_review") return { v: "AWAITING-REVIEW", c: C.cyn };
  if (st === "blocked") {
    const ba = issue.blockerAttention || {};
    if (ba.reason === "active_child" && childInReview) return { v: "PARENT-WAIT(child done)", c: C.yel };
    return { v: "BLOCKED", c: C.red };
  }
  const assignee = agentsById[issue.assigneeAgentId];
  const stall = ageSec(issue.updatedAt);
  if (st === "todo") {
    if (stall != null && stall > T.todoStallSec && assignee && assignee.status === "idle") return { v: "TODO-STALLED", c: C.red };
    return { v: "QUEUED", c: C.dim };
  }
  if (st === "in_progress") {
    if (issue.executionRunId) {
      const runAge = ageSec(issue.executionLockedAt || issue.startedAt || issue.updatedAt);
      if (runAge != null && runAge > T.hungRunTimeoutSec) return { v: "RUN-HUNG", c: C.red };
      return { v: "RUNNING", c: C.grn };
    }
    if (assignee && ["idle", "error"].includes(assignee.status) && stall != null && stall > T.stallSec)
      return { v: "STALLED", c: C.red };
    return { v: "RUNNING", c: C.grn };
  }
  return { v: st || "?", c: C.dim };
}

const tagOf = (title = "") => (title.match(/\[(CLIENT|CLIENT-DEMO|CLIENT-PROD|INTERNAL|BRIEF[^\]]*|MARKETING[^\]]*)\]/i) || [, ""])[1];

// ---- render -------------------------------------------------------------
async function snapshot() {
  const health = await api(CFG.api.healthPath).catch((e) => ({ status: "UNREACHABLE", error: e.message }));
  const agents = arr(await api(`/api/companies/${CFG.company.id}/agents`), "agents");
  const issues = arr(await api(`/api/companies/${CFG.company.id}/issues`), "issues");
  const byId = {}; const byUrlKey = {};
  for (const a of agents) { byId[a.id] = a; byUrlKey[a.urlKey] = a; }
  const idToIdentifier = {}, statusById = {};
  for (const i of issues) { idToIdentifier[i.id] = i.identifier; statusById[i.id] = i.status; }

  // service + systemctl state (SSH only — needs systemctl)
  let svc = "";
  if (!JSON_OUT) {
    const s = sshExec("for u in paperclip paperclip-orchestrator paperclip-listener paperclip-watchdog.timer; do printf '%s=%s ' \"$u\" \"$(systemctl is-active $u)\"; done");
    svc = s;
  }

  if (JSON_OUT) { console.log(JSON.stringify({ health, agents, issues }, null, 2)); return; }

  console.clear?.();
  const exp = CFG.expectedHeartbeat;
  console.log(paint("══ PAPERCLIP PIPELINE STATUS ══", C.bold) + paint(`  (${mode()})  ${new Date().toLocaleTimeString()}`, C.dim));
  const hc = health.status === "ok" ? paint("ok", C.grn) : paint(health.status, C.red);
  console.log(`paperclip: ${hc}  v${health.version || "?"}  authReady=${health.authReady}   services: ${svc}`);

  // ---- agent roster health ----
  console.log(paint("\nAGENTS", C.bold));
  const watch = new Set(CFG.buildPipeline.orchestratorWatchUrlKeys);
  for (const a of agents.sort((x, y) => (x.urlKey > y.urlKey ? 1 : -1))) {
    const hb = (a.runtimeConfig?.heartbeat) || {};
    const isBuild = exp.buildClassUrlKeys.includes(a.urlKey);
    const isMkt = exp.marketingClassUrlKeys.includes(a.urlKey);
    const want = isBuild ? exp.buildClassExpect : isMkt ? exp.marketingClassExpect : null;
    let flags = [];
    if (want && hb.wakeOnDemand !== want.wakeOnDemand) flags.push(paint(`wakeOnDemand=${hb.wakeOnDemand}`, C.red));
    if (want && want.cooldownSec && hb.cooldownSec !== want.cooldownSec) flags.push(paint(`cooldown=${hb.cooldownSec}`, C.yel));
    if (a.lastHeartbeatAt == null) flags.push(paint("lastHeartbeat=null", C.red));
    const stState = a.status === "idle" ? paint("idle", C.dim) : a.status === "error" ? paint("error", C.red) : a.pausedAt ? paint("paused", C.red) : paint(a.status, C.yel);
    const w = watch.has(a.urlKey) ? "" : paint(" (unwatched)", C.dim);
    console.log(`  ${a.urlKey.padEnd(22)} ${stState.padEnd(16)} hb:${fmtAge(ageSec(a.lastHeartbeatAt)).padStart(4)} ${flags.join(" ")}${w}`);
  }

  // verdict closure that resolves child-in-review state internally
  const verdictOf = (i) => {
    const childInReview = i.blockerAttention?.sampleBlockerIdentifier
      ? Object.entries(idToIdentifier).some(([id, ident]) => ident === i.blockerAttention.sampleBlockerIdentifier && statusById[id] === "in_review")
      : false;
    return verdict(i, byId, childInReview);
  };

  // ---- issue board ----
  const show = issues.filter((i) => SHOW_ALL || i.status !== "done");
  show.sort((a, b) => (a.updatedAt < b.updatedAt ? 1 : -1));
  console.log(paint(`\nISSUES (${show.length}${SHOW_ALL ? "" : " open"})`, C.bold));
  console.log(paint("  id       tag        status       verdict                 assignee/state          age   title", C.dim));
  for (const i of show.slice(0, 40)) {
    const vd = verdictOf(i);
    const a = byId[i.assigneeAgentId];
    const who = a ? `${a.urlKey}/${a.status}` : paint("none", C.red);
    console.log(`  ${(i.identifier || "?").padEnd(8)} ${(tagOf(i.title) || "-").slice(0, 10).padEnd(10)} ${(i.status || "").padEnd(12)} ${paint(vd.v.padEnd(23), vd.c)} ${who.padEnd(23)} ${fmtAge(ageSec(i.updatedAt)).padStart(4)}  ${(i.title || "").slice(0, 30)}`);
  }

  // ---- attention summary ----
  const ATTN = new Set(["STALLED", "RUN-HUNG", "BLOCKED", "TODO-STALLED", "PARENT-WAIT(child done)"]);
  const attention = show.filter((i) => ATTN.has(verdictOf(i).v));
  if (attention.length) {
    console.log(paint(`\n⚠ NEEDS ATTENTION (${attention.length}):`, C.red + C.bold));
    for (const i of attention) console.log(`  ${i.identifier}  ${verdictOf(i).v}  — ${(i.title || "").slice(0, 50)}`);
  } else {
    console.log(paint("\n✓ no stalled/hung/blocked in-progress issues", C.grn));
  }
}

(async () => {
  await probe();
  if (WATCH) {
    for (;;) { try { await snapshot(); } catch (e) { console.error("err:", e.message); } await new Promise((r) => setTimeout(r, T.pollIntervalSec * 1000)); }
  } else {
    await snapshot();
  }
})().catch((e) => { console.error("fatal:", e.message); process.exit(1); });
