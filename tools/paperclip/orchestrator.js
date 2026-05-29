#!/usr/bin/env node
// orchestrator.js — Build Pipeline safety-net + enforcement loop.
//
// paperclip's wake_assignee + (now-fixed) wakeOnDemand handle the happy path.
// This loop is the backstop that guarantees every issue ends in a NOTIFIED terminal
// state — never silent limbo. It implements the in-flight rows of RELIABILITY.md.
//
// Detects & acts on (per 30s tick):
//   - Stall: watched assignee idle/error, no run, > stallSec        -> resume + heartbeat
//   - Hung run: executionRunId set but no progress > hungRunTimeout  -> halt + notify  (no blind cancel)
//   - Iteration caps: Build<->Test > 8, Build<->Review > 3           -> halt + notify
//   - Pending approval/disposition interaction                       -> escalate (or auto-accept if enabled)
//   - Parent blocked on a child that reached terminal                -> notify "tree review-ready"
//   - Issue reaches done/in_review                                   -> one tag-aware completion ping
//
// Config: ../pipeline.config.json (resolved by urlKey — no hardcoded UUIDs).
// Run:  node orchestrator.js            (loop)
//       node orchestrator.js --once      (single tick)
//       node orchestrator.js --dry-run   (print actions, take none — safe anywhere)

const fs = require("node:fs");
const path = require("node:path");
const { execFile } = require("node:child_process");
const { CFG, probe, api, apiPost, apiPatch, arr, agentsByUrlKey } = require("./lib/transport");

const DRY = process.argv.includes("--dry-run");
const ONCE = process.argv.includes("--once");
const T = CFG.thresholds;
const WATCH = new Set(CFG.buildPipeline.orchestratorWatchUrlKeys);
const AUTONOMOUS_TAGS = new Set(["CLIENT", "CLIENT-DEMO"]);          // run unattended
const APPROVAL_TAGS = new Set(["INTERNAL", "CLIENT-PROD"]);          // require operator
const AUTO_ACCEPT = process.env.ORCH_AUTO_ACCEPT === "1";            // flag-gated; default escalate-only

const EVENTS_LOG = path.join(__dirname, ".pipeline-events.log");
const STATE_FILE = path.join(__dirname, ".orchestrator-state.json");
const TG_TOKEN = process.env.OPERATOR_TELEGRAM_BOT_TOKEN;
const TG_CHAT = process.env.OPERATOR_TELEGRAM_CHAT_ID;

const log = (m) => console.log(`[${new Date().toISOString()}] ${m}`);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const ageSec = (iso) => (iso ? Math.round((Date.now() - new Date(iso).getTime()) / 1000) : null);
const tagOf = (t = "") => (t.match(/\[([A-Z][A-Z0-9-]*)\]/) || [, ""])[1].toUpperCase();

// ---- persistent state (survives restarts) ----
let STATE = { seeded: false, notifiedTerminal: [], halted: [], treeNotified: [], escalated: [] };
function loadState() { try { STATE = { ...STATE, ...JSON.parse(fs.readFileSync(STATE_FILE, "utf8")) }; } catch {} }
function saveState() { try { fs.writeFileSync(STATE_FILE, JSON.stringify(STATE)); } catch (e) { log(`state save failed: ${e.message}`); } }
const sset = (k) => new Set(STATE[k]);
const sadd = (k, v) => { const s = sset(k); if (!s.has(v)) { s.add(v); STATE[k] = [...s]; saveState(); } };

// ---- transient (per-process) ----
const RECENT_TRIGGERS = new Map();
const recentlyTriggered = (id) => { const t = RECENT_TRIGGERS.get(id); return t && Date.now() - t < T.triggerCooldownSec * 1000; };

function logEvent(ev) {
  const line = JSON.stringify({ ts: new Date().toISOString(), dry: DRY, ...ev });
  try { fs.appendFileSync(EVENTS_LOG, line + "\n"); } catch {}
  log(`EVENT ${ev.category} ${ev.identifier || ""} — ${ev.action}${ev.detail ? ": " + ev.detail : ""}`);
}

async function telegram(text) {
  if (DRY) { log(`[dry] telegram: ${text.replace(/\n/g, " ")}`); return; }
  if (!TG_TOKEN || !TG_CHAT) { log(`telegram skipped (env missing): ${text}`); return; }
  try {
    await fetch(`https://api.telegram.org/bot${TG_TOKEN}/sendMessage`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chat_id: TG_CHAT, text, parse_mode: "Markdown" }),
    });
  } catch (e) { log(`telegram POST failed: ${e.message}`); }
}

function triggerHeartbeat(agent) {
  if (recentlyTriggered(agent.id)) return;
  RECENT_TRIGGERS.set(agent.id, Date.now());
  if (DRY) { log(`[dry] would heartbeat ${agent.urlKey}`); return; }
  const proc = execFile("npx",
    ["paperclipai", "heartbeat", "run", "--agent-id", agent.id, "--source", "on_demand", "--trigger", "ping", "--json"],
    { cwd: process.env.HOME || "/home/paperclip", env: process.env, stdio: "ignore" },
    (err) => log(err ? `heartbeat ${agent.urlKey} exited: ${err.message}` : `heartbeat ${agent.urlKey} done`));
  proc.unref();
}

async function haltIssue(issue, category, reason) {
  if (sset("halted").has(issue.id)) return;
  sadd("halted", issue.id);
  logEvent({ category, identifier: issue.identifier, action: "HALT", detail: reason });
  await telegram(`🛑 *Pipeline HALT* — ${issue.identifier}\n_${category}_\n${reason}\n\n${(issue.title || "").slice(0, 80)}`);
  if (!DRY) { try { await apiPatch(`/api/issues/${issue.id}`, { status: "blocked" }); } catch (e) { log(`mark blocked failed ${issue.identifier}: ${e.message}`); } }
}

async function notifyCompletion(issue) {
  const tag = tagOf(issue.title);
  const where = (APPROVAL_TAGS.has(tag) || tag === "INTERNAL" || !AUTONOMOUS_TAGS.has(tag))
    ? "→ staged for your review/merge (no auto-deploy)"
    : "→ demo-ready (workflow inactive + presentation/ROI), awaiting your go-live";
  logEvent({ category: "terminal-notify", identifier: issue.identifier, action: "COMPLETE", detail: `${issue.status} ${tag}` });
  await telegram(`✅ *Build ${issue.status === "done" ? "done" : "ready for review"}* — ${issue.identifier}${tag ? ` [${tag}]` : ""}\n${(issue.title || "").slice(0, 80)}\n${where}`);
}

async function handleInteractions(issue) {
  let inters;
  try { inters = arr(await api(`/api/issues/${issue.id}/interactions`), "interactions"); } catch { return; }
  const pending = inters.filter((x) => (x.status === "pending" || x.status === "open" || x.status == null) && /confirm|disposition|approval/i.test(x.type || x.kind || ""));
  if (!pending.length) return;
  const tag = tagOf(issue.title);
  for (const itx of pending) {
    if (AUTO_ACCEPT && AUTONOMOUS_TAGS.has(tag)) {
      logEvent({ category: "approval-wait", identifier: issue.identifier, action: "AUTO-ACCEPT", detail: `${tag} interaction ${itx.id}` });
      if (!DRY) { try { await apiPost(`/api/issues/${issue.id}/interactions/${itx.id}/accept`, {}); } catch (e) { log(`accept failed: ${e.message}`); } }
    } else {
      const key = `${issue.id}:${itx.id}`;
      if (sset("escalated").has(key)) continue;
      sadd("escalated", key);
      logEvent({ category: "approval-wait", identifier: issue.identifier, action: "ESCALATE", detail: `${tag || "untagged"} needs disposition` });
      await telegram(`⏸ *Awaiting your decision* — ${issue.identifier}${tag ? ` [${tag}]` : ""}\n${(issue.title || "").slice(0, 80)}\nPipeline is waiting on an approval/disposition.`);
    }
  }
}

async function tick() {
  await probe();
  const { byId } = await agentsByUrlKey();
  const issues = arr(await api(`/api/companies/${CFG.company.id}/issues`), "issues");
  const identToStatus = {};
  for (const i of issues) identToStatus[i.identifier] = i.status;

  // Seed terminal notifications on first ever run so we don't back-notify the existing backlog.
  if (!STATE.seeded) {
    STATE.notifiedTerminal = issues.filter((i) => ["done", "in_review"].includes(i.status)).map((i) => i.id);
    STATE.seeded = true; saveState();
    log(`seeded ${STATE.notifiedTerminal.length} existing terminal issues (no back-notify)`);
  }

  const active = issues.filter((i) => i.status === "in_progress" && i.assigneeAgentId);
  log(`tick — ${issues.length} issues, ${active.length} in_progress`);

  // ---- terminal-state notification guarantee + parent-child resolution ----
  for (const i of issues) {
    if (["done", "in_review"].includes(i.status) && !sset("notifiedTerminal").has(i.id)) {
      await notifyCompletion(i); sadd("notifiedTerminal", i.id);
    }
    if (i.status === "blocked") {
      const ba = i.blockerAttention || {};
      const childId = ba.sampleBlockerIdentifier;
      if (ba.reason === "active_child" && childId && ["in_review", "done"].includes(identToStatus[childId]) && !sset("treeNotified").has(i.id)) {
        sadd("treeNotified", i.id);
        logEvent({ category: "parent-child", identifier: i.identifier, action: "TREE-READY", detail: `child ${childId} ${identToStatus[childId]}` });
        await telegram(`🌳 *Build tree review-ready* — ${i.identifier}\nChild ${childId} reached \`${identToStatus[childId]}\`. Parent is blocked only on it — review the tree.`);
      }
    }
  }

  // ---- in-flight enforcement on watched pipeline issues ----
  for (const issue of active) {
    const assignee = byId[issue.assigneeAgentId];
    if (!assignee || !WATCH.has(assignee.urlKey)) continue;

    // iteration caps
    const runs = arr(await api(`/api/issues/${issue.id}/runs`), "runs");
    const cnt = { engineer: 0, "qa-engineer": 0, "product-engineer": 0 };
    for (const r of runs) {
      const a = byId[r.agentId]; if (!a) continue;
      if (!["succeeded", "failed"].includes(r.status)) continue;
      if (cnt[a.urlKey] !== undefined) cnt[a.urlKey]++;
    }
    if (Math.max(cnt.engineer, cnt["qa-engineer"]) > T.iterationCapBuildTest) {
      await haltIssue(issue, "iteration-loop", `Build↔Test cap exceeded (eng=${cnt.engineer}, qa=${cnt["qa-engineer"]}, cap=${T.iterationCapBuildTest})`); continue;
    }
    if (cnt["product-engineer"] > T.iterationCapBuildReview) {
      await haltIssue(issue, "iteration-loop", `Build↔Review cap exceeded (product=${cnt["product-engineer"]}, cap=${T.iterationCapBuildReview})`); continue;
    }

    // hung run: execution flagged but no progress past timeout
    if (issue.executionRunId) {
      const runAge = ageSec(issue.executionLockedAt || issue.startedAt || issue.updatedAt);
      if (runAge != null && runAge > T.hungRunTimeoutSec) {
        await haltIssue(issue, "run-hung", `run ${String(issue.executionRunId).slice(0, 8)} no progress for ${Math.round(runAge / 60)}m (timeout ${Math.round(T.hungRunTimeoutSec / 60)}m). Manual check needed.`);
      }
      continue;
    }

    // stall: idle/error assignee, no run, past threshold -> resume + heartbeat
    if (!["idle", "error"].includes(assignee.status)) continue;
    if (recentlyTriggered(assignee.id)) continue;
    const stall = ageSec(issue.updatedAt);
    if (stall == null || stall < T.stallSec) continue;
    logEvent({ category: "post-handoff-stall", identifier: issue.identifier, action: "RECOVER", detail: `${assignee.urlKey} ${assignee.status} idle ${stall}s` });
    if (assignee.status === "error" && !DRY) {
      try { await apiPost(`/api/agents/${assignee.id}/resume`, {}); log(`resumed ${assignee.urlKey}`); } catch (e) { log(`resume failed: ${e.message}`); }
    }
    triggerHeartbeat(assignee);
  }

  // ---- approval / disposition waits (in_progress + blocked) ----
  for (const issue of issues.filter((i) => ["in_progress", "blocked"].includes(i.status))) {
    await handleInteractions(issue);
  }
}

async function main() {
  loadState();
  log(`Orchestrator${DRY ? " [DRY-RUN]" : ""} starting — company=${CFG.company.name}`);
  log(`watch=${[...WATCH].join(",")} | stall=${T.stallSec}s hungRun=${T.hungRunTimeoutSec}s caps=${T.iterationCapBuildTest}/${T.iterationCapBuildReview} | autoAccept=${AUTO_ACCEPT}`);
  if (ONCE || DRY) { await tick(); return; }
  for (;;) { try { await tick(); } catch (e) { log(`tick error: ${e.message}`); } await sleep(T.pollIntervalSec * 1000); }
}

process.on("SIGTERM", () => { log("SIGTERM, exiting"); process.exit(0); });
main().catch((e) => { log(`fatal: ${e.stack || e.message}`); process.exit(1); });
