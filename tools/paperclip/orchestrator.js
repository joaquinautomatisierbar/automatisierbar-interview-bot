#!/usr/bin/env node
// Build Pipeline Orchestrator — safety net + iteration cap enforcement.
//
// paperclip's auto-pickup handles the common case (assignee idle → wakes on assignment).
// This orchestrator handles edge cases:
//   1. Sibling agent crashed mid-handoff, next agent never woke
//   2. Iteration cap reached (Build↔Test > 8, Build↔Review > 3) — halt the issue + ping operator
//   3. Stale in_progress issues that lost their execution path — escalate
//
// Run: node tools/paperclip/orchestrator.js
// Or via launchd plist (see tools/paperclip/launchd/).

const API = "http://localhost:3100";
const COMPANY = "47196d38-2f19-4168-af8f-fe9451dff910";
const POLL_INTERVAL_MS = 30_000;        // tick every 30s
const STALL_THRESHOLD_MS = 120_000;     // assignee idle for 2 min with no executionRunId → trigger
const ITERATION_CAP_BUILD_TEST = 8;     // Engineer↔QA loops
const ITERATION_CAP_BUILD_REVIEW = 3;   // Engineer↔Product loops
const PROJECT_ROOT = "/home/paperclip";
const TELEGRAM_BOT_TOKEN = process.env.OPERATOR_TELEGRAM_BOT_TOKEN;
const TELEGRAM_CHAT_ID = process.env.OPERATOR_TELEGRAM_CHAT_ID;

const PIPELINE_URLKEYS = new Set(["cto", "engineer", "qa-engineer", "product-engineer", "release-engineer"]);

// Agent registry populated on startup
const AGENTS_BY_ID = {};

// Track which (issue, agent) pairs we've already triggered to avoid duplicate kicks
const RECENT_TRIGGERS = new Map();  // `${issueId}:${agentId}` -> timestamp
const TRIGGER_COOLDOWN_MS = 60_000;

// Track halted issues so we don't re-halt every tick
const HALTED_ISSUES = new Set();

const { execFile } = require("node:child_process");
const log = (msg) => console.log(`[${new Date().toISOString()}] ${msg}`);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function jget(path) {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`);
  return res.json();
}

async function jpatch(path, body) {
  const res = await fetch(`${API}${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`PATCH ${path} → ${res.status}: ${await res.text()}`);
  return res.json();
}

async function refreshAgents() {
  const agents = await jget(`/api/companies/${COMPANY}/agents`);
  for (const a of agents) AGENTS_BY_ID[a.id] = a;
  const pipelineCount = agents.filter((a) => PIPELINE_URLKEYS.has(a.urlKey)).length;
  log(`refreshed agent registry — ${agents.length} total, ${pipelineCount} in Build Pipeline`);
}

function isPipelineAgent(agentId) {
  const a = AGENTS_BY_ID[agentId];
  return a && PIPELINE_URLKEYS.has(a.urlKey);
}

function triggerHeartbeat(agentId) {
  // background-fire the CLI; don't await (each heartbeat run streams for 5-25 min)
  log(`→ triggering heartbeat for agent ${AGENTS_BY_ID[agentId]?.name || agentId.slice(0, 8)}`);
  const proc = execFile(
    "npx",
    [
      "paperclipai",
      "heartbeat",
      "run",
      "--agent-id",
      agentId,
      "--source",
      "on_demand",
      "--trigger",
      "ping",
      "--json",
    ],
    { cwd: PROJECT_ROOT, env: process.env, stdio: "ignore" },
    (err) => {
      if (err) log(`heartbeat ${agentId.slice(0, 8)} exited: ${err.message}`);
      else log(`heartbeat ${agentId.slice(0, 8)} completed`);
    }
  );
  proc.unref();
  RECENT_TRIGGERS.set(agentId, Date.now());
}

function recentlyTriggered(agentId) {
  const t = RECENT_TRIGGERS.get(agentId);
  return t && Date.now() - t < TRIGGER_COOLDOWN_MS;
}

async function notifyTelegramHalt(reason) {
  if (!TELEGRAM_BOT_TOKEN || !TELEGRAM_CHAT_ID) {
    log(`telegram halt skipped (env vars missing): ${reason}`);
    return;
  }
  const text = `🛑 *paperclip orchestrator HALT*\n\n${reason}`;
  try {
    await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chat_id: TELEGRAM_CHAT_ID,
        text,
        parse_mode: "Markdown",
      }),
    });
  } catch (e) {
    log(`telegram halt POST failed: ${e.message}`);
  }
}

async function haltIssue(issue, reason) {
  if (HALTED_ISSUES.has(issue.id)) return;
  HALTED_ISSUES.add(issue.id);
  log(`HALT ${issue.identifier}: ${reason}`);
  await notifyTelegramHalt(`[paperclip orchestrator] HALT ${issue.identifier}: ${reason}`);
  try {
    await jpatch(`/api/issues/${issue.id}`, { status: "blocked" });
    log(`  marked ${issue.identifier} blocked`);
  } catch (e) {
    log(`  failed to mark ${issue.identifier} blocked: ${e.message}`);
  }
}

async function tick() {
  await refreshAgents();
  const issues = await jget(`/api/companies/${COMPANY}/issues`);
  const pipelineIssues = issues.filter(
    (i) => i.status === "in_progress" && i.assigneeAgentId && isPipelineAgent(i.assigneeAgentId)
  );
  log(`tick — ${pipelineIssues.length} active pipeline issue(s)`);

  for (const issue of pipelineIssues) {
    const assignee = AGENTS_BY_ID[issue.assigneeAgentId];
    if (!assignee) continue;

    // Count iteration loops by counting runs per role on this issue
    const runs = await jget(`/api/issues/${issue.id}/runs`);
    const runsByRole = { engineer: 0, "qa-engineer": 0, "product-engineer": 0 };
    for (const r of runs) {
      const a = AGENTS_BY_ID[r.agentId];
      if (!a) continue;
      if (r.status !== "succeeded" && r.status !== "failed") continue;
      if (runsByRole[a.urlKey] !== undefined) runsByRole[a.urlKey]++;
    }
    const buildTestLoops = Math.max(runsByRole.engineer, runsByRole["qa-engineer"]);
    const buildReviewLoops = runsByRole["product-engineer"];

    if (buildTestLoops > ITERATION_CAP_BUILD_TEST) {
      await haltIssue(
        issue,
        `Build↔Test iteration cap exceeded (engineer=${runsByRole.engineer}, qa=${runsByRole["qa-engineer"]}, cap=${ITERATION_CAP_BUILD_TEST})`
      );
      continue;
    }
    if (buildReviewLoops > ITERATION_CAP_BUILD_REVIEW) {
      await haltIssue(
        issue,
        `Build↔Review iteration cap exceeded (product=${buildReviewLoops}, cap=${ITERATION_CAP_BUILD_REVIEW})`
      );
      continue;
    }

    // Stall detection — assignee idle/error AND no executionRunId AND issue.updatedAt > threshold ago
    if (issue.executionRunId) continue;
    if (!["idle", "error"].includes(assignee.status)) continue;
    if (recentlyTriggered(assignee.id)) continue;

    const updatedAtMs = new Date(issue.updatedAt).getTime();
    const stallMs = Date.now() - updatedAtMs;
    if (stallMs < STALL_THRESHOLD_MS) continue;

    log(
      `stall on ${issue.identifier} → assignee=${assignee.urlKey} status=${assignee.status} idle for ${Math.round(stallMs / 1000)}s`
    );
    // If agent in error state, try resuming first
    if (assignee.status === "error") {
      try {
        const res = await fetch(`${API}/api/agents/${assignee.id}/resume`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: "{}",
        });
        if (res.ok) log(`  resumed ${assignee.urlKey} out of error state`);
      } catch (e) {
        log(`  resume failed: ${e.message}`);
      }
    }
    triggerHeartbeat(assignee.id);
  }
}

async function main() {
  log(`Build Pipeline Orchestrator starting. Polling every ${POLL_INTERVAL_MS / 1000}s.`);
  log(`Iteration caps: Build↔Test=${ITERATION_CAP_BUILD_TEST}, Build↔Review=${ITERATION_CAP_BUILD_REVIEW}`);
  log(`Stall threshold: ${STALL_THRESHOLD_MS / 1000}s`);

  while (true) {
    try {
      await tick();
    } catch (e) {
      log(`tick error: ${e.message}`);
    }
    await sleep(POLL_INTERVAL_MS);
  }
}

process.on("SIGTERM", () => {
  log("SIGTERM received, exiting");
  process.exit(0);
});

main().catch((e) => {
  log(`fatal: ${e.stack || e.message}`);
  process.exit(1);
});
