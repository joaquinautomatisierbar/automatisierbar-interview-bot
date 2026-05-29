#!/usr/bin/env node
// preflight.js — health gate run BEFORE a build is dispatched (and standalone).
//
// Asserts the pipeline is green: paperclip healthy, services up, OAuth-only auth,
// Postgres sysv shmem, and every agent present/bootstrapped with correct heartbeat config.
// Default is READ-ONLY (reports red/green). `--fix` auto-repairs the cheap classes
// (wakeOnDemand regression, paused agents). Exit non-zero on any remaining FAIL → blocks dispatch.
//
// Usage:
//   node tools/paperclip/preflight.js          # check + report (read-only)
//   node tools/paperclip/preflight.js --fix      # apply auto-fixes, then re-check
//   node tools/paperclip/preflight.js --json     # machine output
//
// Implements the pre-dispatch rows of RELIABILITY.md.

const { CFG, probe, mode, api, apiPatch, apiPost, sshExec, agentsByUrlKey } = require("./lib/transport");

const FIX = process.argv.includes("--fix");
const JSON_OUT = process.argv.includes("--json");

const C = { reset: "\x1b[0m", dim: "\x1b[2m", red: "\x1b[31m", grn: "\x1b[32m", yel: "\x1b[33m", bold: "\x1b[1m" };
const paint = (s, c) => (process.stdout.isTTY ? `${c}${s}${C.reset}` : String(s));
const results = [];
const rec = (name, level, detail) => results.push({ name, level, detail });

async function checkInfra() {
  let health;
  try { health = await api(CFG.api.healthPath); } catch (e) { health = { status: "UNREACHABLE", error: e.message }; }
  rec("paperclip-health", health.status === "ok" && health.authReady ? "PASS" : "FAIL",
    `status=${health.status} authReady=${health.authReady} v${health.version || "?"}`);

  const raw = sshExec("for u in paperclip paperclip-orchestrator paperclip-watchdog.timer paperclip-listener; do printf '%s=%s;' \"$u\" \"$(systemctl is-active $u 2>/dev/null)\"; done");
  const svc = Object.fromEntries(raw.split(";").filter(Boolean).map((s) => s.split("=")));
  rec("svc:paperclip", svc.paperclip === "active" ? "PASS" : "FAIL", svc.paperclip);
  rec("svc:orchestrator", svc["paperclip-orchestrator"] === "active" ? "PASS" : "FAIL", svc["paperclip-orchestrator"]);
  rec("svc:watchdog-timer", svc["paperclip-watchdog.timer"] === "active" ? "PASS" : "WARN", svc["paperclip-watchdog.timer"]);
  rec("svc:listener", svc["paperclip-listener"] === "active" ? "PASS" : "WARN", `${svc["paperclip-listener"]} (deprioritized — dispatcher is primary trigger)`);

  const names = sshExec("cut -d= -f1 /etc/paperclip/secrets 2>/dev/null | grep -vE '^#|^$'").split("\n").map((s) => s.trim());
  rec("auth:oauth-token", names.includes("CLAUDE_CODE_OAUTH_TOKEN") ? "PASS" : "FAIL", "CLAUDE_CODE_OAUTH_TOKEN (Max abo)");
  const hasAnthropic = names.includes("ANTHROPIC_API_KEY");
  rec("auth:no-console-key", hasAnthropic ? "FAIL" : "PASS", hasAnthropic ? "ANTHROPIC_API_KEY present — burns the $100 budget, remove it" : "ANTHROPIC_API_KEY absent (good)");

  const pg = sshExec("grep -E '^dynamic_shared_memory_type' /home/paperclip/.paperclip/instances/default/db/postgresql.conf 2>/dev/null").replace(/\s+/g, " ").trim();
  rec("pg:shmem", /sysv/.test(pg) ? "PASS" : "WARN", pg || "(not found)");
}

// Returns the fix list; records one result row per agent.
async function evalAgents(label = "agents") {
  const { byUrlKey } = await agentsByUrlKey();
  const exp = CFG.expectedHeartbeat;
  const fixes = [];
  for (const uk of Object.keys(CFG.agentRoster).filter((k) => !k.startsWith("_"))) {
    const a = byUrlKey[uk];
    if (!a) { rec(`agent:${uk}`, "FAIL", "MISSING — ID drift or not imported"); continue; }
    const probs = [];
    if (a.pausedAt) { probs.push("paused"); fixes.push({ type: "resume", agent: a }); }
    if (a.status === "error") { probs.push("error"); fixes.push({ type: "resume", agent: a }); }
    if (a.lastHeartbeatAt == null) { probs.push("lastHeartbeatAt=null (unbootstrapped)"); fixes.push({ type: "bootstrap", agent: a }); }
    const isBuild = exp.buildClassUrlKeys.includes(uk);
    const isMkt = exp.marketingClassUrlKeys.includes(uk);
    if (isBuild || isMkt) {
      const want = isBuild ? exp.buildClassExpect : exp.marketingClassExpect;
      const hb = a.runtimeConfig?.heartbeat || {};
      if (hb.wakeOnDemand !== want.wakeOnDemand || hb.cooldownSec !== want.cooldownSec) {
        probs.push(`heartbeat wakeOnDemand=${hb.wakeOnDemand} cooldownSec=${hb.cooldownSec}`);
        fixes.push({ type: "heartbeat", agent: a, want });
      }
    }
    rec(`agent:${uk}`, probs.length ? "FAIL" : "PASS", probs.length ? probs.join(", ") : `${a.status}, hb ok`);
  }
  return fixes;
}

async function applyFixes(fixes) {
  // dedupe by agentId+type
  const seen = new Set();
  for (const f of fixes) {
    const k = `${f.agent.id}:${f.type}`;
    if (seen.has(k)) continue; seen.add(k);
    try {
      if (f.type === "heartbeat") {
        const rc = f.agent.runtimeConfig || {};
        const hb = rc.heartbeat || {};
        const newHb = { ...hb, enabled: false, wakeOnDemand: f.want.wakeOnDemand, cooldownSec: f.want.cooldownSec, maxConcurrentRuns: hb.maxConcurrentRuns ?? f.want.maxConcurrentRunsMax ?? 1 };
        await apiPatch(`/api/agents/${f.agent.id}`, { runtimeConfig: { ...rc, heartbeat: newHb } });
        console.log(paint(`  ✓ FIXED heartbeat ${f.agent.urlKey} → wakeOnDemand=true cooldownSec=60 maxConcurrentRuns=${newHb.maxConcurrentRuns}`, C.grn));
      } else if (f.type === "resume") {
        await apiPost(`/api/agents/${f.agent.id}/resume`, {});
        console.log(paint(`  ✓ RESUMED ${f.agent.urlKey}`, C.grn));
      } else if (f.type === "bootstrap") {
        console.log(paint(`  ! ${f.agent.urlKey} needs bootstrap — run: bash tools/paperclip/scripts/bootstrap-new-agents.sh ${CFG.company.id}`, C.yel));
      }
    } catch (e) {
      console.log(paint(`  ✗ fix ${f.type} ${f.agent.urlKey} failed: ${e.message}`, C.red));
    }
  }
}

(async () => {
  await probe();
  await checkInfra();
  let fixes = await evalAgents();

  if (FIX) {
    const actionable = fixes.filter((f) => f.type !== "bootstrap");
    if (actionable.length || fixes.some((f) => f.type === "bootstrap")) {
      console.log(paint(`\nApplying ${fixes.length} fix(es)…`, C.bold));
      await applyFixes(fixes);
      // re-evaluate agents for an accurate final verdict (clear stale FAIL rows)
      for (let i = results.length - 1; i >= 0; i--) if (results[i].name.startsWith("agent:")) results.splice(i, 1);
      fixes = await evalAgents("agents (post-fix)");
    }
  }

  if (JSON_OUT) { console.log(JSON.stringify({ mode: mode(), results }, null, 2)); }
  else {
    console.log(paint("\n══ PREFLIGHT ══", C.bold) + paint(`  (${mode()})  company=${CFG.company.name}`, C.dim));
    for (const r of results) {
      const c = r.level === "PASS" ? C.grn : r.level === "WARN" ? C.yel : C.red;
      console.log(`  ${paint(r.level.padEnd(4), c)} ${r.name.padEnd(24)} ${paint(r.detail, C.dim)}`);
    }
  }

  const fails = results.filter((r) => r.level === "FAIL").length;
  const warns = results.filter((r) => r.level === "WARN").length;
  const line = fails ? paint(`✗ NOT READY — ${fails} FAIL, ${warns} WARN`, C.red + C.bold)
    : paint(`✓ READY${warns ? ` — ${warns} WARN` : ""}`, C.grn + C.bold);
  console.log("\n" + line + (fails && !FIX ? paint("   (run with --fix to auto-repair)", C.dim) : ""));
  process.exit(fails ? 1 : 0);
})().catch((e) => { console.error("fatal:", e.message); process.exit(2); });
