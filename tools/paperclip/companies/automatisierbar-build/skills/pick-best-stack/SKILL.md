---
name: pick-best-stack
description: >
  Pick the best implementation stack for a Build brief on its merits — n8n / Trigger.dev / Render+Flask / Vercel / native script. NEVER default to n8n. Justify the pick in the plan.
---

# Pick Best Stack

Automatisierbar uses multiple stacks. Each has a sweet spot. **Never default to n8n** just because most existing automations are n8n — that's path-of-least-resistance, not best-fit. Pick on merit.

## Decision matrix

Score each option on the brief's constraints. Pick the highest-scoring stack.

| Stack | Best for | Avoid when |
|---|---|---|
| **n8n** | Visual workflow the customer or our team needs to maintain. Linear webhook → integration → notify. Single-purpose interconnects. Heavy integration count with built-in nodes. | Complex business logic, custom Python deps, heavy cron + retry semantics, stateful APIs, anything the user wants to fork into TS later. |
| **Trigger.dev** | TypeScript-native cron-heavy work, retries, queues, fan-out, statefulness. AI agent loops with tool use. Anything that doesn't need a visual editor for the customer. | Customer needs to visually edit the workflow themselves. Pure no-code customer. |
| **Render + Flask / FastAPI** | Long-running HTTP services. Stateful APIs. Custom Python deps (pandas, PyMuPDF, openpyxl). Background workers. Anything with heavy data processing. | Simple webhook-to-notify (n8n is faster to build). One-shot scripts (overkill). |
| **Vercel + Next.js** | Customer-facing UI tied to an automation. Edge functions with regional latency requirements. | Pure backend (Render is cheaper). |
| **Native script (Python / Node)** | One-shot tools. Cron via system crontab or trigger.dev. Local CLI usage. No scheduler needed. | Anything multi-step that needs observability / retries / queueing — promote to Trigger.dev. |

## How to choose

Ask these in order and let the answer drive the pick:

1. **Does the customer (not Tej/Nico/Patrik — the *customer*) need to visually edit this themselves over time?**
   - Yes → strong pull toward **n8n**.
   - No → continue.
2. **Is there heavy cron / scheduled / queued logic with retry semantics?**
   - Yes → **Trigger.dev** unless the integration set is overwhelmingly n8n-native.
   - No → continue.
3. **Does it need custom Python deps (pandas, ML libs, PyMuPDF, etc.) or long-running stateful HTTP?**
   - Yes → **Render + Flask / FastAPI**.
   - No → continue.
4. **Is it customer-facing UI?**
   - Yes → **Vercel + Next.js** (back-end can be Render or Trigger.dev).
   - No → continue.
5. **Is it a one-shot script with no scheduler need?**
   - Yes → **native script**.

## Justification format

In the CTO plan document, include a stack-pick section with this exact format:

```
## Stack Pick

**Chosen:** <stack>

**Why:** <2-line rationale tying back to specific brief constraints, e.g. "Customer described 'every 14 days from first-of-month' and runs 200+ Belege per cycle — cron + retry is the dominant requirement, n8n's scheduler is fragile for that volume.">

**Rejected alternatives:**
- n8n: <one-line why not, or "primary alternative — close call">
- Trigger.dev: <one-line why not>
- Render+Flask: <one-line>
- Native script: <one-line>
```

## Customer-existing-stack signal

If the brief mentions "Klient hat schon n8n" or "wir nutzen Trigger.dev" — that's a hard constraint, use the customer's existing stack unless there's a technical reason it can't work. Reducing the customer's mental load wins over picking the technically purer stack.

## Things this skill does NOT do

- It does not choose the stack for you — you reason. The skill gives you the framework.
- It does not promise a perfect pick on every brief. When two stacks are close, lean toward the one that's lower in operational surface area (one less system to maintain).
- It does not consider cost-per-run unless the brief mentions volume that would push you above Render free tier or Trigger.dev paid tier.

## Anti-patterns

- "n8n because that's what we always use" → write a different reason or pick a different stack.
- "Render because Flask is comfortable" → don't pick on personal preference, pick on customer need.
- "Trigger.dev because it's modern" → don't pick on novelty.
- "Native script because it's quick" → fine for prototypes; never for handover to customer unless the customer is technical.
