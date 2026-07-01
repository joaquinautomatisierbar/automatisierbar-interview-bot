# Task-Card Template

Two layers: what **Patrik sees** (exactly 3 fields — no framework jargon) and what **you fill in privately** to keep the autonomy ramp honest. Then the GitHub Issue template to drop on his fork.

---

## Layer 1 — what Patrik sees (the whole card, 3 fields)

```markdown
# 🤝 Chasch mer mit [KURZ-TITEL] hälfe?

**Was ich bruuche:** [the ask in 2–3 sentences. ALWAYS say why it matters + to whom.
e.g. "Mir ziehnd d Leads jedi Wuche vo Hand use — das chostet eus Ziit. Chasch mer
hälfe, das als chlises Tool z löse? Dä Nico bruucht's jede Määntig."]

**Fertig heisst:**
- [ ] [concrete, checkable acceptance criterion #1]
- [ ] [concrete, checkable acceptance criterion #2]
- [ ] (optional) [#3]

**Wenn's hakt:** → Escape-Hatch. Screenshot + was du probiert hesch. Kei Formular nötig.
```

**Rules for writing the card:**
- Verb is always *hälfe / zäme / mir* — never "mach X". (See framing-playbook.md.)
- "Fertig heisst" is the **definition of done** — 2–3 things he can literally tick. If you can't write them concretely, the task is too vague to give him yet.
- Weeks 1–3: keep it fully scoped, one right answer. From W6: a 3-sentence brief is enough (he does the scoping).

---

## Layer 2 — operator-side metadata (Patrik NEVER sees this)

Keep this in the Issue's hidden fields / your own notes. It's how *you* keep the ramp honest — not homework for him.

```
Autonomy level:   L1 / L2 / L3        (default to the lowest that solves it)
Bike phase:       1 / 2 / 3           (must match the week — see week-plan.md)
Guidance mode:    I-DO / WE-DO / YOU-DO
KPI bucket:       more-customers / more-value-per-customer / less-cost
KPI metric:       [the specific number this moves]
Boring rung:      prompt-template / deterministic-script / AI-assisted / sub-agent
Skill taught:     [the one competency this card builds]
Is this a stretch (not a gate)?:  yes / no
Shelf-task if blocked:  [the always-available fallback task]
```

**Map-5 (Trigger / Datenquellen / Transformationen / Entscheidungspunkte / Ziel):**
- **W1–W3:** *you* pre-fill this and paste it in the card as "so lauft das ungefähr" — then ask Patrik to confirm/correct it in his own words in a comment. It's a gentle intro, not a gate.
- **From W5:** Patrik fills it himself (help available) — the "come with a proposal" muscle.

---

## Layer 3 — GitHub Issue template (drop on Patrik's fork)

Until the Hub is confirmed live, run the board on **GitHub Issues on his fork** (explicitly *not* Notion — that's the tool that broke him). Create this file on his fork:

**`.github/ISSUE_TEMPLATE/patrik-task.md`**

```markdown
---
name: "🤝 Ufgab / Task"
about: "Ei Ufgab für s Apprenticeship"
title: "🤝 "
labels: ["bike:1"]
---

**Was ich bruuche:**


**Fertig heisst:**
- [ ]
- [ ]

**Wenn's hakt:** → Escape-Hatch. Screenshot + was du probiert hesch.
```

**Board conventions:**
- Labels `bike:1` / `bike:2` / `bike:3` group the board so his autonomy climb is *visible* left-to-right.
- **WIP-limit = 2 active issues.** More than 2 open "in progress" = pull one back. Prevents the "where do I even start" freeze.
- The **PR that closes an issue links back to it** — that thread (issue comments + PR review) *is* the async mentoring log and the audit trail.
- When a skill is validated, the closing comment says **"Skill validated ✅ — [what]"** and gets copied into [progression-log.md](progression-log.md).

> **Hub migration:** when the Automatisierbar Hub is live, the same 3 fields become the Patrik-facing custom fields, `bike:1..3` becomes *Board by Bike Phase*, and issue comments become task comments. Zero redesign.
