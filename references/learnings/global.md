# Global Learnings

Cross-role operational lessons. Every paperclip agent reads this file at activation. Append-only — never edit prior entries; supersede via a newer dated entry with `[[their-slug]]` cross-link.

Frontmatter convention is documented in [INDEX.md](INDEX.md).

---

## client-build-tag-equivalence

---
name: client-build-tag-equivalence
description: "`[CLIENT-BUILD]` (child issue tag) must be treated identically to `[CLIENT]` in every agent's routing logic"
type: learning
scope: global
created: 2026-05-31
issue: AUT-119
tags: [routing, agents-md, client-build, parent-child]
---

`[CLIENT-BUILD]` is the correct tag for implementation children of `[CLIENT]` / `[CLIENT-DEMO]` parents. Every agent's AGENTS.md routing logic must treat `[CLIENT-BUILD]` identically to `[CLIENT]`. Same applies to `[CLIENT-PROD]` for prod-rollout children.

**Why:** AUT-119/122/123 — three roles' routing logic broke because they only matched `[CLIENT]` literal. Manual re-routing burned ~15 min in the first CLIENT canary.

**How to apply:** Anytime adding routing logic to a paperclip agent's AGENTS.md (Engineer, QA, Product, Presentation Designer, Release): include the explicit equivalence note. Reuse the existing wording: *"Note on child-issue tags: `[CLIENT-BUILD]` (in the issue title) is the tag for implementation children spawned from `[CLIENT]` / `[CLIENT-DEMO]` parents. Treat `[CLIENT-BUILD]` as `[CLIENT]` for every rule below."*

Carried forward from [retro AUT-119](../retros/AUT-119-client-canary-rechnungs-erinnerung.md).

---

## marker-detection-first-line-plus-author-id

---
name: marker-detection-first-line-plus-author-id
description: Orchestrator-side marker detection (canary.js / orchestrator.js) must check first-line of comment + comment's authorAgentId, NOT regex over flat-joined comment text
type: learning
scope: global
created: 2026-05-30
issue: AUT-115
tags: [canary, orchestrator, regex-bug, handoff-protocol]
---

`canary.js`'s marker-detection should iterate comments and for each comment check that (a) its first non-blank line starts with the marker token AND (b) the comment's `authorAgentId` resolves to the agent with the expected role's `urlKey`. Plain regex over the flat-joined comment text produces false positives whenever a planning comment mentions downstream markers.

**Why:** AUT-115 — CTO's PLAN_LOCKED comment listed every downstream marker as part of describing the handoff sequence. Canary's regex matched those tokens anywhere → reported all 5 stages PASS at 201s when only CTO had run. Pure false positive; would mask real failures on a bigger Issue.

**How to apply:** Any time `tools/paperclip/canary.js` or other orchestrator-side comment-parsing logic is touched. Mirror the convention codified in `tools/paperclip/companies/automatisierbar-build/skills/handoff-protocol/SKILL.md` — markers ARE first-line, that's the protocol.

Carried forward from [retro AUT-115](../retros/AUT-115-canary-pipeline-heartbeat.md). Related: [[parent-child-pivot]].

---

## parent-child-pivot

---
name: parent-child-pivot
description: When CTO spawns a child Issue, all orchestrator-side watchers (canary, monitors) must retarget polling to the child
type: learning
scope: global
created: 2026-05-30
issue: AUT-115
tags: [orchestrator, parent-child, canary, watcher]
---

When CTO posts `PLAN_LOCKED` and spawns a child Issue, the canary monitor (and any other orchestrator-side script watching an Issue's progress) must shift its polling target from the parent to the child. Read `parentId` / children from the Issue meta and follow the work.

**Why:** AUT-115 — work moved to child AUT-118; canary kept watching AUT-115 (parent) and reported every downstream stage as missing.

**How to apply:** Any orchestrator-side script that watches an Issue's progress (canary.js, orchestrator.js, watchers in `.tmp/`). On detecting a child Issue creation by the current assignee, retarget polling.

Carried forward from [retro AUT-115](../retros/AUT-115-canary-pipeline-heartbeat.md). Related: [[marker-detection-first-line-plus-author-id]].

---

## client-canary-wallclock-budget

---
name: client-canary-wallclock-budget
description: CLIENT/CLIENT-BUILD pipeline runs take ~3x INTERNAL because Presentation Designer adds 15-25 min to the critical path
type: learning
scope: global
created: 2026-05-31
issue: AUT-119
tags: [budgeting, eta, presentation-designer, client-build]
---

When budgeting wall-clock for a CLIENT/CLIENT-BUILD pipeline run, account for Presentation Designer being on the critical path. Realistic min/max: 30-50 min on a simple workflow; 50-90 min on anything with custom SVG diagrams or honest-ROI math beyond defaults.

**Why:** AUT-119 took 60 min vs AUT-115's 8 min; Presentation Designer added ~25 of those (one full heartbeat to draft process-diagram.svg + roi-page.html + live-demo-script.md).

**How to apply:** Any time scoping a CLIENT-build run or quoting an ETA. Don't promise "ships in 15 min" — that's the INTERNAL ETA, not the CLIENT one.

Carried forward from [retro AUT-119](../retros/AUT-119-client-canary-rechnungs-erinnerung.md).

<!--
Entries below. Sorted reverse-chronological (newest first).
Each entry uses the frontmatter + body shape defined in INDEX.md.
Add an `## H2` heading per entry using the slug as anchor.

Example shape:

## paperclip-agent-bootstrap-after-import

---
name: paperclip-agent-bootstrap-after-import
description: Every paperclipai company import must be followed by bootstrap-new-agents.sh — without the bundled `paperclip` skill, new agents never heartbeat
type: learning
scope: global
created: 2026-05-21
issue: —
tags: [paperclip, bootstrap, heartbeat]
---

`npx paperclipai company import …` does NOT auto-wire the paperclipai-bundled
heartbeat skill. New agents stay `lastHeartbeatAt:null` until
`tools/paperclip/scripts/bootstrap-new-agents.sh <company-id>` runs.

**Why:** Discovered 2026-05-21 after three agents sat broken for 4 days.

**How to apply:** After any `paperclipai company import` (including
`--target existing --collision skip`): run the bootstrap script. Idempotent;
re-running on a healthy company is a no-op.

Related: [[telegram-credential-scoping]] (similar "post-action wiring step"
class of bug).

-->
