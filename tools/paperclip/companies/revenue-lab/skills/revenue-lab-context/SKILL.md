---
name: revenue-lab-context
description: >
  Load Revenue Lab's context — the $300 burn cap, legal-shell model, ICP, library, and halt
  policy — before any reasoning. Use on every heartbeat. Without it the agent will mis-scope
  the offer, spend against the cap, or break the legal-shell rules.
---

# Revenue Lab Context

Read these before reasoning about any Revenue Lab task. Project root:
`/Users/sexyjoaquin/Desktop/Claude Code/n8n Workflow Interview/` (mounted read-only at
`~/_context/` on the VPS — prefer that path when running as an agent).

## Required reads (every heartbeat)

1. **`tools/paperclip/companies/revenue-lab/COMPANY.md`** — the mission, the $300 cap, the
   legal-shell rules, the North-Star-vs-Phase-1-target distinction, and the hard rules. This is
   your operating manual. Re-read the "Hard rules" section every wake.
2. **`references/business-context.md`** — the ICP, funnel reality, capacity, constraints. Your
   offer only sells if it fits a real, reachable ICP. The ICP is backoffice-heavy Swiss SMEs
   (Immobilien / Treuhand / Anwalt / Steuerberater) — NOT Coiffeur / Restaurant / trades.
3. **`references/library/INDEX.md`** — the distilled Hormozi + Testing Business Ideas library.
   Ground every offer/pricing/lead/sales decision in a named framework. For Revenue Lab the
   load-bearing ones are: the Value Equation, the Offer/Guarantee construction, Fast-Cash money
   models, and Testing Business Ideas (evidence before build).
4. **`CLAUDE.md`** — the firm's halt-before-acting policy + the Paperclip agent budget policy
   (no auto-loops, wakeOnDemand:false, $5/issue cap). These bind you.

## The non-negotiables (from COMPANY.md — repeated here so you never miss them)

- **$300 lifetime cap on external/business spend.** Compute is on the Claude Max plan (~$0).
  Before ANY spend, run the `check-budget-governor` skill.
- **Legal-shell:** the operator owns the entity, Stripe, and bank. You are a scoped API caller.
  You never create accounts, do KYC, or move money out.
- **No autonomous account creation / signups / CAPTCHA / KYC.** Out of scope, full stop.
- **Halt before** any money-touching or external-trust action — `money-halt-protocol` skill.
- **Self-wake guard:** if the latest comment on your issue is from you, exit silently.
- **Optimize for the first cleared payment**, not $10k-scale plans.

## Memory layer

The operator's auto-memory index is at
`~/.claude/projects/-Users-sexyjoaquin-Desktop-Claude-Code-n8n-Workflow-Interview/memory/MEMORY.md`
and accumulated learnings at `references/learnings/`. Skim before assuming a fresh approach —
past corrections bind you. The `recall-learnings` skill loads these.
