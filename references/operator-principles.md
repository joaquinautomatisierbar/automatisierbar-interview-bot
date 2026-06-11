# Operator Principles

Decision principles for when to automate, what autonomy to grant, and how to roll changes out without blowing things up. Sits above WAT (which tells you *how* to build) and answers *what to build, when, and how confidently*.

Read once. Refer back when you catch yourself building something complicated and you're not sure why.

> Adapted from common AI-engineering practice and the Three Ms framing (Mindset / Method / Machine — credit Nate Herk). Distilled here in our own voice for repo use.

---

## 1. Default Shift

Before doing any task the old way, ask: *to what extent can AI be leveraged here?* Not binary. Maybe 80%, maybe 10%. You don't know until you ask.

**Practical implication:** when Joaquin (or a teammate) brings a new task, the first response in this session shouldn't be "okay, here's the plan to do it manually." It should be "here's how AI can take a slice of this — what slice should I take?"

If AI couldn't do it last quarter, try again. Models improve faster than habits.

---

## 2. Eliminate before you Automate

The EAD ladder, in order:

1. **Eliminate** — *what happens if we just stop doing this?* If nobody notices, kill it. Don't automate waste. Many recurring tasks exist because they always have, not because they create value.
2. **Automate** — apply the 60/30/10 rule:
   - ~60% fully automated (no human touch)
   - ~30% AI-assisted (AI drafts, human reviews before it goes out)
   - ~10% stays manual (too nuanced, too risky, or too rare)
3. **Delegate** — if a process is too complex / variable / judgment-heavy for 60/30/10, hand it to a person.

**Nothing stays as-is.** Every recurring process gets killed, automated, or handed off.

In this repo: when a `/level-up` candidate surfaces, run EAD before scoping. If the answer is Eliminate, log it to `decisions/log.md` and move on — that's a win, not a failure.

---

## 3. Map the process before you build

Five elements per process. Write them on paper (or in the workflow SOP) before touching n8n / a script / an API:

- **Trigger** — what kicks it off (form submit, schedule, webhook, drive event, manual click)
- **Data sources** — where info comes from (CRM, sheet, inbox, Drive folder)
- **Data transformations** — how data changes shape (parse, filter, combine, classify)
- **Decision points** — where it branches (`IF` qualified → X, else → Y)
- **Destination** — where output goes (back to CRM, email, Slack, Notion DB, Telegram)

**Rule:** if you can't explain it to a person, you can't explain it to an AI. Every n8n workflow in `workflows/` should make these five elements obvious from a skim.

---

## 4. The Autonomy Spectrum (L0–L4)

Every workflow gets an explicit autonomy level. Default to the **lowest level that solves the problem**.

| Level | Name | What happens |
|---|---|---|
| **L0** | Manual | No AI. Human does it. |
| **L1** | Suggested | AI suggests, human decides every step. |
| **L2** | Drafted | AI drafts, human reviews + edits before send. |
| **L3** | Supervised | AI runs end-to-end, human validates periodically (sample audits, dashboards). |
| **L4** | Autonomous | AI handles end-to-end, no per-event review. |

**Governing rule:** workflows beat agents. If a decision doesn't *have* to be made by AI, don't let AI make it. Push autonomy up only when you've proven the lower level works (see Bike Method below).

Every workflow file in `workflows/` declares its current level in YAML frontmatter:

```yaml
---
autonomy-level: L2
bike-method-phase: 2
---
```

---

## 5. The Bike Method (rollout phases)

How to ship an automation without it eating your weekend.

| Phase | Name | What it means |
|---|---|---|
| **1** | Training wheels | Run manually. Watch every output. Correct mistakes by hand. Cost is high, learning is fast. |
| **2** | Guided | Automation runs but you review every output before it ships externally. AI drafts, human approves. |
| **3** | Watched | Runs autonomously. You sample-monitor. Alerts fire on anomalies. Periodic batch review. |
| **4** | Hands-off | Helmet on, go ride. Full autonomy, monitoring on the dashboard not on each event. |

**Even at 90% confidence, roll out 10% of volume first.** Watch a week. Add 20%. Like drug trials — never the full dose to everyone on day one.

A workflow's `bike-method-phase` should *only* advance after explicit validation. Don't let a `/level-up` run scaffold a Phase-3 workflow on day one.

---

## 6. Boring is Beautiful

When picking *how* to build something, prefer the most deterministic option that works:

1. **Prompt-only template** — saved prompt the user runs by hand. Zero infra.
2. **Deterministic skill / script** — runs without an AI step. Best for transformations with clear rules. Done is done.
3. **AI-assisted skill / workflow** — one focused AI call. Drafts, classifies, summarizes.
4. **Sub-agent** — multi-step agent with tool use. Last resort. Only if the work genuinely needs reasoning across multiple turns.

Default = the highest non-AI option that solves the problem. If you find yourself reaching for option 4, it's usually because option 2 or 3 wasn't tried hard enough.

> Deterministic steps can be *finished*. AI steps are always evolving. Set expectations — yours and any client's — accordingly. A regex filter is done. An AI classifier needs tuning forever.

---

## 7. Lego Principle + Validation Chain

Build in the smallest possible blocks. One input, one output per block. **Output of block N becomes input of block N+1.**

**Validate each block's output before chaining.** Don't build the whole pipeline and then test end-to-end — that's a recipe for "it doesn't work and I have no idea why." This is exactly what `validate_workflow` + `test_workflow` (pin-data smoketest) + `execute_workflow` give us in n8n: three rungs on the validation ladder before real-write activation.

Start with **zero-AI steps first**. Get the deterministic pieces working (data fetch, format, route). Then layer in AI where actually needed. If block 3 is producing garbage, you know exactly where to look.

---

## 8. Tie every automation to a KPI

If your automation doesn't move a number, why are you building it?

**The Three Buckets** (every business metric falls in one):

1. **Get more customers** — content, prospecting, outreach, ads, lead gen.
2. **Make each customer worth more** — premium services at lower cost, upselling, retention, faster delivery.
3. **Cut costs** — eliminate drudgery, reduce errors, boost productivity.

Plus a *specific* metric: response time, error rate, conversion rate, time-to-completion, hot-lead count per week.

When `/level-up` scopes a new automation, the entry in `decisions/log.md` MUST name a bucket and a metric. If it can't, the automation gets killed before it ships.

---

## 9. Intern Rule

Treat every AI-driven automation like a brand-new hire on day one:

- **Own identity.** Its own credentials, its own bot account, its own service-account API keys. Never the operator's personal account.
- **Read-only by default.** Don't grant write access until read-only has been validated.
- **Never impersonates the operator.** Outbound messages either name the bot, or include "AI assistant" framing.
- **No personal credentials.** No passwords, bank info, personal logins.
- **Full audit trail.** Every external action (Notion write, Telegram send, email out) is logged where the operator can grep it after the fact.
- **Scoped permissions.** API keys with the minimum scope. If it doesn't need calendar.write, don't grant calendar.write.

In this repo: `OPERATOR_TELEGRAM_*` is its own bot, separate from the LinkedIn engagement bot, separate from the interview bot. Pattern stays.

---

## 10. Kill Switch

Monitor what's running. If an automation:

- consistently needs patches,
- produces low-quality output the operator silently fixes,
- costs more (in API credits or attention) to maintain than it saves,

**tear it down.** Don't fall into sunk-cost. *"But I spent three weeks building this"* is not a reason to keep something running. Good operators know when to build AND when to destroy.

The kill switch is just as important as the launch button. Every workflow's SOP in `workflows/*.md` should have a "When to retire" line — even if it's just "when the underlying business process stops existing."

---

## How these connect to the rest of the AIOS

- `/level-up` walks the **EAD → Map → Autonomy → KPI** ladder when scoping a new automation. The Method interview is operationalized.
- `/audit` rewards workflows that declare `autonomy-level` + `bike-method-phase` in frontmatter. Missing means assumed L4 / Phase 4 — usually a yellow flag.
- `decisions/log.md` captures KPI-tied scoping decisions and EAD outcomes (especially "this was Eliminate, not Automate").
- Halt-before-acting policy in `CLAUDE.md` is the operational expression of the Bike Method — semantic checkpoints before something irreversible.
