---
name: Build Pipeline
description: The autonomous build team that consumes interview briefs and ships automations to Swiss SME customers — stack-agnostic, intent-anchored, customer-handover-ready.
slug: build-pipeline
manager: ../../agents/cto/AGENTS.md
includes:
  - ../../agents/engineer/AGENTS.md
  - ../../agents/qa-engineer/AGENTS.md
  - ../../agents/product-engineer/AGENTS.md
  - ../../agents/release-engineer/AGENTS.md
tags:
  - build
  - engineering
  - delivery
---

The Build Pipeline handles the full delivery lifecycle from a customer's `claude_code_prompt` brief to a production-ready artifact + customer-handover docs. Led by the **CTO**.

## Flow

```
Build Issue assigned to CTO
   │
   ├──► CTO locks plan (stack pick, architecture, edge cases, test matrix)
   │     │
   │     ▼
   ├──► Engineer implements (artifact + PRESENTATION.md + TESTING.md)
   │     │
   │     ▼ READY_FOR_TEST
   ├──► QA Engineer validates (stack-specific checks + 3 scenarios)
   │     │
   │     ├─► TEST_FAIL → back to Engineer
   │     └─► TEST_PASS ▼
   ├──► Product Engineer audits intent (Klärungspunkte, customer-vs-spec)
   │     │
   │     ├─► NEEDS_QOL → back to Engineer
   │     └─► SHIP ▼
   └──► Release Engineer publishes (n8n / GitHub branch / Render / Trigger.dev)
        Issue marked done
```

## Outside the team

- **CEO** receives all incoming Build Issues from the dispatch n8n workflow (interview-bot → paperclip) and routes them to CTO. CEO does not touch the build pipeline beyond routing and exception handling.
- **Real-life Tej / Nico / Patrik** (humans, not paperclip agents) are the meeting-runners. They receive build artifacts via the dispatch system's notification once Release Engineer marks the Issue done.
