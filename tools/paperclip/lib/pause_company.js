#!/usr/bin/env node
// pause_company.js — the hard kill-switch actuator. PATCHes every agent of a given company to
// enabled:false + wakeOnDemand:false, so a tripped governor (tools/revenue_governor.py) can
// actually stop the fleet. Reuses transport.js for dual-mode (direct on VPS / SSH from Mac)
// access — only the company id differs from the build pipeline, and api/apiPatch are path-based.
//
// Usage:  node tools/paperclip/lib/pause_company.js <company-id> [reason]
// Prints a JSON summary: { ok, reason, paused: [urlKey...], failed: [...] }

const { api, apiPatch, arr } = require("./transport");

const PAUSED_HEARTBEAT = {
  runtimeConfig: {
    heartbeat: { enabled: false, wakeOnDemand: false, cooldownSec: 60, intervalSec: 0, maxConcurrentRuns: 1 },
  },
};

async function main() {
  const companyId = process.argv[2];
  const reason = process.argv[3] || "kill-switch";
  if (!companyId) {
    console.error("usage: node pause_company.js <company-id> [reason]");
    process.exit(2);
  }

  let agents;
  try {
    agents = arr(await api(`/api/companies/${companyId}/agents`), "agents");
  } catch (e) {
    console.log(JSON.stringify({ ok: false, reason, error: `list agents failed: ${e.message}` }));
    process.exit(1);
  }

  const paused = [];
  const failed = [];
  for (const a of agents) {
    try {
      await apiPatch(`/api/agents/${a.id}`, PAUSED_HEARTBEAT);
      paused.push(a.urlKey || a.id);
    } catch (e) {
      failed.push({ agent: a.urlKey || a.id, error: e.message });
    }
  }

  const ok = failed.length === 0;
  console.log(JSON.stringify({ ok, reason, paused, failed }, null, 2));
  process.exit(ok ? 0 : 1);
}

main().catch((e) => {
  console.log(JSON.stringify({ ok: false, error: e.message }));
  process.exit(1);
});
