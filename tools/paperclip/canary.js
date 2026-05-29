#!/usr/bin/env node
// canary.js — end-to-end pipeline validation. Dispatches a synthetic build through the
// REAL pipeline and asserts each stage emits its marker within budget. The regression test
// that proves "+- works" became "provably works". Implements Phase 5 of the reliability plan.
//
// Usage:
//   node canary.js --mode plumbing            # ~$0: CTO must post BLOCKED immediately (tests dispatch+pickup+watch)
//   node canary.js --tag internal             # real [INTERNAL] build, watch to terminal
//   node canary.js --tag client               # real [CLIENT] build, must reach demo-ready
//   node canary.js --dispatch-only --tag …     # create the issue, don't watch
//   node canary.js --watch AUT-123             # attach to an existing issue
//   --budget <min>                             # override overall budget
//
// Always runs preflight first (aborts if not READY) unless --skip-preflight.

const path = require("node:path");
const { execFileSync } = require("node:child_process");
const { CFG, probe, api, apiPost, arr, agentsByUrlKey } = require("./lib/transport");

const argv = process.argv.slice(2);
const has = (f) => argv.includes(f);
const val = (f, d) => { const i = argv.indexOf(f); return i >= 0 && argv[i + 1] ? argv[i + 1] : d; };
const TAG = (val("--tag", "") || "").toLowerCase();
const MODE = val("--mode", TAG ? "real" : "plumbing");
const DISPATCH_ONLY = has("--dispatch-only");
const WATCH_IDENT = val("--watch", null);
const SKIP_PRE = has("--skip-preflight");

const C = { reset: "\x1b[0m", dim: "\x1b[2m", red: "\x1b[31m", grn: "\x1b[32m", yel: "\x1b[33m", cyn: "\x1b[36m", bold: "\x1b[1m" };
const paint = (s, c) => (process.stdout.isTTY ? `${c}${s}${C.reset}` : String(s));
const log = (m) => console.log(`[${new Date().toLocaleTimeString()}] ${m}`);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const TG_TOKEN = process.env.OPERATOR_TELEGRAM_BOT_TOKEN, TG_CHAT = process.env.OPERATOR_TELEGRAM_CHAT_ID;
async function telegram(text) {
  if (!TG_TOKEN || !TG_CHAT) return;
  try { await fetch(`https://api.telegram.org/bot${TG_TOKEN}/sendMessage`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ chat_id: TG_CHAT, text, parse_mode: "Markdown" }) }); } catch {}
}

const BRIEFS = {
  plumbing: {
    title: "[INTERNAL] Canary plumbing test — no build",
    description: "CANARY PLUMBING TEST. Do NOT plan or build anything. This only validates that dispatch + auto-pickup + the watcher work. Immediately post a single comment containing exactly `BLOCKED: canary plumbing test — no action required` and stop. Do not delegate, do not create child issues.",
  },
  internal: {
    title: "[INTERNAL] Canary — add a build-pipeline heartbeat marker file",
    description: "CANARY BUILD ([INTERNAL]). Small, self-contained internal task to validate the full pipeline end-to-end.\n\nTask: create a new file `tools/paperclip/CANARY_LASTRUN.md` containing a single line: the current UTC timestamp and the words 'pipeline canary ok'. That's the entire deliverable.\n\nThis is a real [INTERNAL] build: lock a tiny plan (CTO), implement (Engineer), QA validates the file content, Product confirms it meets the trivial intent, Release stages it on a feature branch (NO push to main, NO deploy). Keep it minimal — the point is to exercise every handoff, not to do real work.",
  },
  client: {
    title: "[CLIENT] Canary — Schweizer KMU Rechnungs-Erinnerung (synthetic)",
    description: "CANARY BUILD ([CLIENT]) — synthetic interview brief to validate the client track end-to-end (incl. Presentation Designer + ROI). This is a TEST, not a real customer.\n\n## Wer\nSynthetic Treuhand-KMU 'Muster Treuhand AG' (5 Mitarbeiter).\n## Was (Prozess)\nWöchentlich offene Rechnungen aus einer Google-Sheet-Liste prüfen und für überfällige (>30 Tage) eine freundliche Zahlungserinnerung per E-Mail-Entwurf vorbereiten.\n## Tool\nGoogle Sheets (Eingang) → Gmail-Entwurf (Ausgang). (Demo-twin: Google Sheets stand-in is fine.)\n## Daten rein\nSheet-Spalten: Kunde, Rechnungsnummer, Betrag, Fälligkeitsdatum, Status.\n## Daten raus\nPro überfällige Rechnung ein Gmail-Entwurf (kein automatischer Versand) + eine Zusammenfassungszeile.\n## Desired outcome\nDer Treuhänder spart das wöchentliche manuelle Durchgehen der Liste; Erinnerungen sind vorbereitet, er muss nur noch prüfen + senden.\n\nBuild it for real: pick the best stack, deploy an INACTIVE n8n workflow (or equivalent) for QA, produce PRESENTATION.md + TESTING.md + the process diagram + honest ROI page + demo script. Halt-policy applies: nothing activated, no real emails sent.",
  },
};

function brief() {
  if (MODE === "plumbing") return BRIEFS.plumbing;
  if (TAG === "internal") return BRIEFS.internal;
  if (TAG === "client") return BRIEFS.client;
  throw new Error("specify --mode plumbing OR --tag internal|client");
}

// expected stage markers for the scorecard
function expectedStages() {
  if (MODE === "plumbing") return [{ urlKey: "cto", marker: "BLOCKED", terminal: true }];
  const isClient = TAG === "client";
  const stages = [
    { urlKey: "cto", marker: "ENGINEER_START|Plan locked|plan document" },
    { urlKey: "engineer", marker: "READY_FOR_TEST" },
    { urlKey: "qa-engineer", marker: "TEST_PASS" },
    { urlKey: "product-engineer", marker: "SHIP" },
  ];
  if (isClient) stages.push({ urlKey: "presentation-designer", marker: "PRESENTATION_READY" });
  stages.push({ urlKey: "release-engineer", marker: "RELEASE|staged|in_review", terminal: true });
  return stages;
}

async function dispatch() {
  const { byUrlKey } = await agentsByUrlKey();
  const cto = byUrlKey["cto"];
  if (!cto) throw new Error("CTO agent not found");
  const b = brief();
  log(`dispatching: ${b.title}`);
  const created = await apiPost(`/api/companies/${CFG.company.id}/issues`, {
    title: b.title, description: b.description, assigneeAgentId: cto.id, priority: "medium",
  });
  const issue = created.issue || created;
  log(paint(`created ${issue.identifier || issue.id} (status=${issue.status}, assignee=${cto.urlKey})`, C.cyn));
  return issue;
}

async function resolveByIdent(ident) {
  const issues = arr(await api(`/api/companies/${CFG.company.id}/issues`), "issues");
  const i = issues.find((x) => x.identifier === ident);
  if (!i) throw new Error(`issue ${ident} not found`);
  return i;
}

async function watch(issue, budgetMin) {
  const stages = expectedStages();
  const seen = {};                 // marker label -> {at, runs}
  const started = Date.now();
  const budgetMs = budgetMin * 60_000;
  log(paint(`watching ${issue.identifier} — budget ${budgetMin}m, expecting: ${stages.map((s) => s.urlKey).join(" → ")}`, C.dim));

  let terminalReached = false, blocked = false, finalStatus = issue.status;
  while (Date.now() - started < budgetMs) {
    await sleep(20_000);
    let cur, comments;
    try {
      cur = await resolveByIdent(issue.identifier);
      comments = arr(await api(`/api/issues/${cur.id}/comments`), "comments");
    } catch (e) { log(`poll err: ${e.message}`); continue; }
    finalStatus = cur.status;
    const blob = comments.map((c) => String(c.body || c.content || "")).join("\n");
    for (const st of stages) {
      const label = st.urlKey;
      if (seen[label]) continue;
      const re = new RegExp(st.marker, "i");
      if (re.test(blob)) { seen[label] = { at: Math.round((Date.now() - started) / 1000) }; log(paint(`  ✓ ${label} (${st.marker.split("|")[0]}) @ ${seen[label].at}s`, C.grn)); }
    }
    const elapsed = Math.round((Date.now() - started) / 1000);
    log(paint(`  … status=${cur.status} seen=[${Object.keys(seen).join(",")}] ${elapsed}s`, C.dim));
    if (["in_review", "done"].includes(cur.status)) { terminalReached = true; break; }
    if (cur.status === "blocked") { blocked = true; break; }
  }

  // scorecard
  const elapsedMin = ((Date.now() - started) / 60000).toFixed(1);
  console.log(paint(`\n══ CANARY SCORECARD — ${issue.identifier} (${MODE === "plumbing" ? "plumbing" : TAG}) ══`, C.bold));
  let pass = 0;
  for (const st of stages) {
    const ok = !!seen[st.urlKey];
    if (ok) pass++;
    console.log(`  ${paint(ok ? "PASS" : "MISS", ok ? C.grn : C.red)}  ${st.urlKey.padEnd(22)} ${ok ? seen[st.urlKey].at + "s" : "(marker not seen)"}`);
  }
  const allStages = pass === stages.length;
  const verdict = MODE === "plumbing"
    ? (seen["cto"] && (terminalReached || blocked) ? "PASS (plumbing: dispatch+pickup+watch work)" : "FAIL (no BLOCKED marker / never terminal)")
    : (terminalReached && allStages ? "PASS (all stages + terminal)" : terminalReached ? "PARTIAL (terminal but missed a marker)" : blocked ? "BLOCKED (halted mid-run)" : "TIMEOUT");
  const good = verdict.startsWith("PASS");
  console.log(`  status=${finalStatus}  stages=${pass}/${stages.length}  elapsed=${elapsedMin}m`);
  console.log("\n" + paint(`Verdict: ${verdict}`, good ? C.grn + C.bold : C.red + C.bold));
  await telegram(`🧪 *Canary ${MODE === "plumbing" ? "plumbing" : TAG}* — ${issue.identifier}\nVerdict: ${verdict}\nStages ${pass}/${stages.length}, ${elapsedMin}m, status=${finalStatus}`);
  return good;
}

(async () => {
  await probe();
  if (WATCH_IDENT) { const i = await resolveByIdent(WATCH_IDENT); const ok = await watch(i, Number(val("--budget", 60))); process.exit(ok ? 0 : 1); }

  if (!SKIP_PRE) {
    log("running preflight…");
    try { execFileSync("node", [path.join(__dirname, "preflight.js")], { stdio: "inherit" }); }
    catch { console.error(paint("preflight FAILED — aborting canary (run preflight.js --fix)", C.red + C.bold)); process.exit(1); }
  }

  const issue = await dispatch();
  if (DISPATCH_ONLY) { log(`dispatched ${issue.identifier} (--dispatch-only). Attach later: node canary.js --watch ${issue.identifier}`); return; }
  const budget = Number(val("--budget", MODE === "plumbing" ? 6 : TAG === "client" ? 75 : 35));
  const ok = await watch(issue, budget);
  process.exit(ok ? 0 : 1);
})().catch((e) => { console.error("fatal:", e.message); process.exit(2); });
