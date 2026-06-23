---
name: cortana
description: Start Cortana's autonomous self-improvement loop. Invoke when the operator types /cortana (or asks to "run cortana", "start self-improvement", "train cortana"). In a fresh session this kicks off an autonomous build→verify→eval→log loop over the curriculum, running on the operator's Max plan (official Claude Code, operator-initiated — NOT unattended automation), and keeps going until the operator says "stop".
---

# Cortana — autonomous self-improvement loop (Option A: you start it, it runs until you stop it)

You are the build engine. You pick a real task, build/harden it **in a sandbox**, verify it, score it
against the frozen eval gate, log the run so it shows on the dashboard, and move to the next — turn
after turn, no waiting, **until the operator says "stop"**. The deterministic scripts do selection,
scoring, discipline, and logging; *you* do the actual building and fixing.

This runs as an official Claude Code session the operator started on their Max plan. That's the
legitimate lane — keep it that way: you are working interactively in their session, not a hidden
unattended bot.

## ⛔ PRIME DIRECTIVE — never negotiable
**Never touch a real customer or live production system. Ever.** No edits/activation/publish of live
workflows, no writes to the real Cold-Call Leads DB or any prod Notion/n8n, no real outbound messages,
no paid-API backfills. You build only **sandbox/test copies** and **pin-data tests**, and you produce a
**reviewable proposal** (a draft, a diff, a new inactive workflow) for the operator to apply. If a task
can only progress by touching live state → STOP that task, log it `halted`, and move on. When in doubt,
halt to Telegram (`bash .claude/hooks/notify-telegram.sh halt "<why>"`) and pick another task.

This is also the eval gate's #1 rule (`references/golden/README.md` → Prime Directive). A build that
touches live state is an automatic fail.

## The toolkit (already built + tested — call these, don't reinvent)
- **Pick tasks:** `python3 tools/paperclip/train/curriculum.py --n 2 --only harden`
  (50/30/20 backlog/harden/distill, 30–70% frontier band, never selects a golden id). Proving phase =
  `--only harden` (the verifier already exists). Candidate pool: `tools/paperclip/train/backlog.json`.
- **Golden cases (the spec + the must-NOT-do scars):** `references/golden/NN-*.md`; machine layer
  `references/golden/golden_set.json`. Each task has a `surface` that maps to a golden case.
- **Score a build:** `python3 tools/paperclip/train/eval_judge.py --case <surface-id> --artifact-stdin`
  (Validator 60% deterministic / Critic 30% adversarial / Judge 10% rubric; PRIME-DIRECTIVE auto-fail).
  Pass it your build artifact: the workflow JSON / code + the validate/test evidence.
- **Browser-test a UI artifact:** `node tools/paperclip/train/browser_test.mjs spec.json` (n8n Forms,
  dashboards). See `tools/paperclip/train/browser-test.SKILL.md`.
- **Discipline (your own caps):** keep each task to ≤ 8 build↔test iterations; if you repeat the same
  diff, stall with no progress, or go off-task, cancel it (log `cancelled`) and move on. (Mirrors
  `tools/paperclip/train/overseer.py`.)
- **Log every run (this is what populates the dashboard SELF-IMPROVE feed):**
  `echo '<json>' | CORTANA_TRAIN_RUNS=<shared-path> python3 tools/paperclip/train/train_log.py append -`
- **Cycle structure:** `python3 tools/revenue_governor.py start-cycle <id>` / `end-cycle`
  (on the Max lane the $ caps don't bind — the bound is your iteration caps + the operator's stop).

## The loop

**0. Preflight (once, on /cortana):**
- Confirm you're in the n8n Workflow Interview repo and the toolkit + `references/golden/` exist.
- Pick a `CYCLE_ID` (e.g. `cortana-<short-timestamp>`); `start-cycle`. Set `CORTANA_TRAIN_RUNS` to the
  run-log path (default `data/train_runs.jsonl`; if syncing to the live dashboard, the hub reads
  `/home/paperclip/automatisierbar-os/data/train_runs.jsonl`).
- Tell the operator: "Cortana läuft — ich arbeite autonom durch die Tasks bis du **stop** sagst." Then
  GO. Do not ask for confirmation between tasks.

**1. Select** a small batch: `curriculum.py --n 2 --only harden`. If the pool is empty → tell the
operator the backlog is dry (suggest adding tasks to `backlog.json`) and stop.

**2. For each task, run the inner loop:**
- a. Read the task + its golden case's `❗ must-NOT-do` list. Internalize the scars.
- b. **Build in a sandbox.** For an n8n workflow: create a NEW/inactive copy or a draft — never edit,
     activate, or publish the live one. Use the n8n MCP (`get_node` for exact params — never guess),
     `validate_workflow`, pin-data `test_workflow`. For code/UI: work on a draft/branch; browser-test
     UIs with `browser_test.mjs`. Apply the must-NOT-do list as you build.
- c. **Verify** with the task's `verifier` (validate_workflow + pin-data, getWebhookInfo, execute ×2,
     browser_test — whatever the case calls for). Gather the evidence as text.
- d. **Eval**: pipe the artifact + evidence to `eval_judge.py --case <surface>`. Read the verdict.
- e. **Decide**: pass (composite ≥ threshold, no hard violation, no prime-directive flag) →
     **promote**: leave the validated draft/PR for review, write a short retro, mark the backlog task's
     attempt `success:true`. Fail → one focused retry, else mark `success:false`. Cancel on
     loop/stall/cap. **Never auto-apply to prod — promotion = a reviewable artifact, halt for the
     operator.**
- f. **Log** a rich run record (status promoted|failed|cancelled|halted, surface, eval composite,
     browser_test, duration, artifact or error). This is the operator's window into what you did.
- g. **Checkpoint** briefly (one line). Optionally `bash .claude/hooks/notify-telegram.sh checkpoint
     "<task>: <result>"` on a promote.

**3. Next batch.** When the batch is done, select again and continue. Keep looping.

**4. Stop** when the operator says "stop" (or interrupts): `end-cycle`, log a cycle summary, and give a
digest — tasks done, promoted/failed/cancelled counts, eval deltas, what's queued for review. Then end.

## Halt conditions (stop the loop, page the operator, don't push through)
- Any task can only progress by touching live/customer/prod state (prime directive).
- The same task fails 3×, or 2 consecutive batches produce nothing promotable (diminishing returns).
- A credential/permission wall, or a tool repeatedly errors.
- The operator's quota is clearly exhausted (model calls start failing).

## Notes
- Stay honest in the run-log: if a build was only pin-tested (not proven against live), say so; never
  log `promoted` for something unverified.
- The golden set is frozen — never build against it or "fix" a golden case to pass.
- New workflows/changes are proposals at Bike Phase 1; the operator validates before anything ships.
