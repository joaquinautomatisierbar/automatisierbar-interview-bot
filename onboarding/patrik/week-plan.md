# Week-by-Week Plan (W0–W8)

*Your master reference. Each week = ONE competency, a concrete deliverable, an acceptance bar, and a guidance-fade level. Every task is framed "chasch mer mit X hälfe?", runs in Patrik's sandbox fork, and hits the PR-gate. Nothing goes live.*

**Guidance fade:** I-DO (fully worked, he follows) → WE-DO (he drives, you co-pilot) → YOU-DO (he owns, you review).
**Autonomy:** L1 (suggested, one right answer) → L2 (drafts, you review before "done") → L3 (he picks the approach, sample-monitored).

| Week | Bike | Autonomy | Fade | Competency |
|---|---|---|---|---|
| W0 | 1 | L1 | I-DO | Setup — the machine runs |
| W1 | 1 | L1 | I-DO | Operate the machine + name what you did |
| W2 | 1 | L1→L2 | I-DO→WE-DO | One tiny safe change + read a tool's output |
| **W3** | 1 | L1 | I-DO | **Deliberate guaranteed win — ⚠️ ANTI-GHOST WEEK** |
| W4 | 2 | L2 | WE-DO | Copy-modify a real build (first code) |
| W5 | 2 | L2→L3 | WE-DO→YOU-DO | Build one small thing + self-verify it |
| W6 | 3 | L3 | YOU-DO w/ net | Take a scoped brief end-to-end |
| W7 | 3 | L3 | YOU-DO | Broader ops task + a netted debug |
| W8 | 3 | L3 | YOU-DO | Scoped build + present = graduation |

---

## W0 — Setup (~30 min, I-DO)
- **Deliverable:** fork clones + runs; sandbox `.env` loads; one trivial command responds. He follows [w0-setup-sop.md](w0-setup-sop.md).
- **Acceptance bar:** screenshot of a successful trivial run + he confirms he's read the one rule (*nüt gaat live ohni Review*).
- **Support:** the 6-step SOP + a 3-min Loom of you doing it.

## W1 — Operate the machine + name what you did (non-coding, L1, I-DO)
- **(A) Read-and-map:** he reads one existing workflow SOP (e.g. `workflows/lead_context_enrichment.md` or another clean one). You've **pre-filled the Map-5** in the card; he confirms/corrects it *in his own words* in a comment.
- **(B) 3 mock cold-calls:** off `references/war-room/cold_call_script.md`. **Mock only — zero real dials.** You play prospect on one; 2 solo voice memos. A non-technical guaranteed early win that also repairs his outreach fragility safely.
- **Diagnostic:** seed ONE wrong line in the SOP. Does he notice / freeze / recover? This calibrates how fast W2+ can fade. **Freezing silently is the only fail; "i bi da ghange" passes.**
- **Acceptance bar:** Map correct; 3 mock calls hit the opener + book the mock termin; he named the seeded error *or* honestly flagged where he stalled.

## W2 — One tiny safe change + read a tool's output (L1 → early WE-DO)
- **(A) Run a deterministic tool** on sandbox data (e.g. `tools/war_room_scoreboard.py` selftest, or any zero-AI tool), paste the output, explain in 2 sentences what it computed. Teaches *"a script is done — Boring is Beautiful"* — no authoring yet.
- **(B) Change ONE prompt line / field** in a sandbox copy of a workflow, run it, post before/after. Reversible, git-tracked.
- **Ambiguity micro-drill:** the brief omits one trivial detail ("mach's chli chürzer" — how short?). Success = reasonable call + *states the assumption*, doesn't stall.
- **Acceptance bar:** before/after visibly differs; tool output explained correctly; change reversible.
- ### 🎓 GATE 1 → Phase 2
  1. Ran an existing workflow/tool end-to-end with correct output.
  2. Confirmed/corrected a Map-5.
  3. Hit ≥1 snag and recovered via the Escape-Hatch (proved he can get unstuck the sanctioned way).
  *No hours criterion. Miss = repeat the phase, logged neutrally as "Baustein hät na nöd validiert".*

## W3 — Deliberate guaranteed win (non-coding, L1, I-DO) ⚠️ ANTI-GHOST WEEK
*The honeymoon-ends, silence-risk week. **Do NOT ramp ambiguity here.** This week's job is a bankable win + proof he can recover, not new difficulty.*
- **(A) Data-hygiene by hand** in the throwaway **test** Leads DB: dedupe by firma, normalize casing, flag rows missing a website. Safe copy. Then name one step that "could become a script someday" (plants EAD by osmosis, zero build pressure). *This is the first touch of his owned surface — see [owned-surface.md](owned-surface.md).*
- **(B) Research dossier**, fixed template: one real open question (e.g. "chäibigscht Transkriptions-Option für Walk-in-Memos"), 1 page: 3 options + tradeoffs + a recommendation. Open inputs, **fixed output structure** so it isn't ambiguous.
- **First Bug-of-the-Week** slot at Friday Show-&-Tell — normalizes "stuck is showable".
- **Acceptance bar:** clean DB; dossier has 3 real sourced options + one clear recommendation.
- **If this week goes silent → that's the emergency.** Warm call, halve scope, re-anchor ownership before anything technical.

## W4 — Copy-modify a real build (first code, NOT blank-page, L2, WE-DO)
- **Deliverable:** take an existing tool/pattern (e.g. a lead-field normalizer or any small deterministic tool), **change one behavior**, validate before/after **block-by-block** (Lego + Validation Chain), open a PR.
- **Error-recovery drill (real but netted):** it may break. Success = he runs the Escape-Hatch (read error → ask Claude in-repo → one fix) and *only then* pings with a screenshot. No-fault if a service is down.
- **Acceptance bar:** runs green in sandbox; before/after validated; PR opened; **nothing merges.**

## W5 — Build one small thing + self-verify it (L2 → YOU-DO)
*Interleaving/spaced-retrieval week: reuses W1 run + W2 modify + W3 hygiene + W4 validation in one task. First from-scratch deterministic artifact allowed (after W4's worked example).*
- **Deliverable:** a small `tools/*.py` OR a `prompts/*.md` template that does one clean transform. He writes **3 test cases + expected outputs FIRST**, then runs and shows pass/fail. First calibration note (an AI/output step is *tuned*, not "done" — the linkedin-posts pattern).
- **Map-5:** from this week he **fills it himself** (help available) — the "come with a proposal" muscle begins, wins banked.
- **Acceptance bar:** 3 self-authored tests exist and run; **he catches ≥1 bad output himself before a founder sees it** (self-verification is the whole trusted-generalist point).
- ### 🎓 GATE 2 → Phase 3
  1. Two consecutive PRs merged with ≤1 review round each.
  2. Ran the validation chain himself before asking for review.
  3. Escalated cleanly at least once AND self-recovered at least once.
  *No hours criterion.*

## W6 — Take a scoped brief end-to-end (L3, YOU-DO w/ net)
- **Deliverable:** from a 3-sentence brief he does the whole loop — Map-5 (himself) → pick approach (**defend the lowest-that-works** per Boring-is-Beautiful) → build (deterministic where possible, AI only where needed) → self-verify → PR → 2-min Loom walkthrough. n8n **authoring** is allowed now; an AI-classifier node is a **stretch, not a required gate**.
- **Ambiguity drill (real):** the brief is under-specified in ONE material way. Success = he surfaces it *with a proposed resolution* ("i ha aagno X, well Y — okay?"), not an open "was wottsch?".
- **Acceptance bar:** you can approve the PR with ≤2 rounds; decision entry logged in [progression-log.md](progression-log.md).

## W7 — Broader ops task + a netted debug (L3, YOU-DO) — no double-stacking of new hard things
*Both realism-critics flagged W7 as the over-stack risk. Keep it to one build-adjacent + one ops. **Real outreach stays cut** — any live dialing is post-graduation, in person at HSG.*
- **(A) Ops (L2):** a cleaned dataset OR a research brief OR a drafted message set — he drafts, you review before anything's real. Serves the *generalist* half of the goal.
- **(B) Netted debug:** a **founder-seeded broken sandbox workflow** he diagnoses via the n8n validation ladder (`validate_workflow` → `test_workflow` pin-data → `execute_workflow`) and fixes, + a 4-line post-mortem (what broke / how found / fix / prevention). This is the deliberate-practice payoff for his Notion-freeze history.
- **Acceptance bar:** ops task usable with light edits; broken flow validates green after fix; post-mortem shows he *found* the cause, didn't guess blindly.

## W8 — Scoped build + present = graduation (L3, YOU-DO)
*Capstone is a **scoped, pre-seen** brief — NOT a cold live build under curveball fire (that's a senior bar he can't fairly clear).*
- **Deliverable:** one end-to-end sandbox artifact from a brief he's had time with + a decision-log entry + a **prepared Loom** presentation to ≥2 founders + short live Q&A. One "was wenn das bricht?" question he fields *with a proposal*.
- ### 🎓 GATE 3 → Graduation
  1. Prototype works, self-verified, presented, met its acceptance criteria on the **first** review pass.
  2. Handled a broader ops task with light supervision (W7).
  3. **Surfaced ≥1 improvement candidate of his own** during W6–8 (the strongest proof of the work-ethic half).
- **Framing:** real write/deploy still goes through the PR-gate after Sept 7. Graduation = "trusted to be reviewed lightly," ready to contribute as a builder-generalist when the four are in the same room at HSG.

---

## Risks, early-warning & kill-switch

**Disengagement early-warning (you watch privately — remote silence is the killer):**
- A card sits in "Building" untouched past midweek with no comment.
- Two nearby weeks of "nüt Neus" at Show-&-Tell.
- The Monday "womit chan i der hälfe?" gets a vague/quiet reply two weeks running.
- Tej's midweek stuck-swap reports "hemmer nöd gredt."

**Tripwire response (warm, not audit):** two signals stack → warm 1:1 **call** (not text): *"verzell mal, wo hakt's — lömmer's zäme aaluege."*

**Kill-switch / adjust rules:**
- **Slip → shrink the next block, never reassign the surface.** The moment it stops being "his," the engine dies.
- **Repeat-a-phase is neutral** — "Baustein hät na nöd validiert", not a failure event.
- **Genuinely overloaded on holiday → pause, don't push.** A 2h week is data, not a breach. Design assumes 3–5h realistic, *hopes* for 10–15h.
- **W3 is the watched week** — anti-ghost easy win still silent = call, halve scope, re-anchor ownership before touching anything technical.
- **If breakage becomes his first experience in any week, back up a notch.** Never let a red error greet him after a quiet stretch.
