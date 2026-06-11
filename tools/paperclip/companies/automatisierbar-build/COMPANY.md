---
name: Automatisierbar Build Pipeline
description: Multi-agent build pipeline that consumes interview briefs and ships production-ready automations to Swiss SME customers — stack-agnostic (n8n, Trigger.dev, Render, Flask, native scripts), intent-anchored, customer-handover-ready.
slug: automatisierbar-build
schema: agentcompanies/v1
version: 0.1.0
license: MIT
authors:
  - name: Joaquin Gamonal Demann
  - name: Automatisierbar
goals:
  - Turn a `claude_code_prompt` brief from the web interview bot into a production-ready automation in under 60 minutes wall-clock
  - Pick the right stack per problem (n8n, Trigger.dev, Render-hosted Flask, Vercel, native scripts) — not default to n8n
  - Honor the customer's *intent*, not just the literal spec — surface Klärungspunkte rather than silently invent answers
  - Produce three artifacts per build: working code + PRESENTATION.md (handover-ready) + TESTING.md (non-developer-executable)
  - Stay inside the WAT framework: Workflows (markdown SOPs), Agents (intelligent coordination), Tools (deterministic execution)
---

Automatisierbar's autonomous build pipeline. Consumes the `claude_code_prompt` artifact produced by the web interview bot ([api.py](../../../api.py) on Render) for each completed customer interview, and ships the implementation without a human opening VS Code.

## How the company works

```
[Interview Brief]
       │
       ▼
   CTO ─── locks technical plan (stack pick + architecture + edge cases + test matrix)
       │
       ├──► Engineer ─── implements the plan in the chosen stack
       │                  │
       │                  └──► commits artifacts (code + PRESENTATION.md + TESTING.md) to the issue workspace
       │                       posts READY_FOR_TEST → QA Engineer
       │
       ├──► QA Engineer ─── validates: stack-specific checks + browser test if relevant
       │                    posts TEST_PASS or TEST_FAIL: <details>
       │
       ├──► Product Engineer ─── intent-anchor reviewer: customer-intent gap analysis
       │                         posts SHIP or NEEDS_QOL: <details>
       │
       └──► Release Engineer ─── publishes the artifact (GitHub branch push, n8n workflow publish, Render deploy)
                                 marks issue done
```

The pipeline is a sequence of **distinct cognitive modes**, not a single mega-agent. CTO does planning. Engineer codes. QA tests. Product Engineer reviews intent. Release Engineer ships. Each agent owns one mode.

## Triggering

Each Build issue carries a brief in its description and gets assigned to **CTO** first. CTO locks the plan and routes implementation work to Engineer. The handoff protocol uses comment markers (`READY_FOR_TEST`, `TEST_PASS`, `TEST_FAIL`, `NEEDS_QOL`, `SHIP`) so an orchestrator (Phase 3) can move issues between agents automatically.

## Reporting line

All five pipeline agents report to the firm-level **CEO** (existing agent, owns Automatisierbar strategy + non-build work). CEO routes incoming Build Issues to CTO and otherwise leaves the pipeline alone.

## Skills

This company brings six original skills covering the parts of the Automatisierbar build flow that gstack and other published companies don't address:

- `automatisierbar-context` — every agent reads this on wake; points at the project's CLAUDE.md, business-context.md, connections.md, operator-principles.md, and decisions/log.md so the agent has firm + system context, not just task context
- `pick-best-stack` — given a brief, evaluate n8n / Trigger.dev / Render + Flask / Vercel / native script options on merit, justify the pick in PRESENTATION.md
- `read-claude-code-prompt-brief` — parse the structured brief format the web interview bot emits (`## MVP Assumptions`, `## Offene Klärungspunkte`, process map)
- `surface-klaerungspunkte` — for Product Engineer; verify every Klärungspunkt is surfaced in PRESENTATION.md, not silently overridden
- `write-presentation-doc` — produce the customer-handover-ready PRESENTATION.md (Hochdeutsch, no jargon, ties to `desired_outcome`)
- `write-testing-doc` — produce TESTING.md a non-developer (real Tej/Nico/Patrik) can follow to verify the artifact locally
- `handoff-protocol` — the marker-based comment protocol for inter-agent handoff (READY_FOR_TEST/TEST_PASS/etc.)

It also references skills from paperclipai's bundled set (`paperclip-converting-plans-to-tasks`, `para-memory-files`, `diagnose-why-work-stopped`, `terminal-bench-loop`) and where appropriate from gstack (`plan-eng-review`, `qa`, `browse`, `benchmark`).
