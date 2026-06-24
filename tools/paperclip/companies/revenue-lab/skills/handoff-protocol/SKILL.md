---
name: handoff-protocol
description: >
  The marker-based handoff protocol for Revenue Lab so work moves Builder -> QA -> operator with
  no silent gaps and a hard iteration cap. Use whenever handing a deliverable between agents.
  Ported from the Automatisierbar build pipeline.
---

# Handoff Protocol

Work moves between agents via explicit comment markers on the issue. No deliverable reaches the
operator until QA has passed it. Every handoff leaves durable context (what, where, what's next).

## The markers (put the marker at the START of the comment)

| Marker | Who posts | Meaning / next |
|---|---|---|
| `READY_FOR_REVIEW` | Builder | "Artifacts done + paths/links listed. QA: render and check." → wakes QA |
| `REVIEW_PASS` | QA | "I rendered/read it; checklist passes." → CEO summarizes to operator |
| `REVIEW_FAIL: <defects>` | QA | numbered defect list → back to Builder to fix |
| `READY_TO_SHIP` | CEO | "QA passed; summarized for operator." → operator's go-live gate |

## The loop

```
Builder builds → READY_FOR_REVIEW ─► QA renders + checks
                                        ├─ REVIEW_FAIL: <defects> ─► Builder fixes ─► READY_FOR_REVIEW (loop)
                                        └─ REVIEW_PASS ─► CEO: READY_TO_SHIP ─► operator approves go-live
```

## Hard rules

- **Builder may NOT mark READY_FOR_REVIEW without listing the exact artifact paths/links** it
  produced. QA reviews the artifact, never the description of it.
- **QA may NOT REVIEW_PASS without having rendered/observed the artifact** (see `verify-deliverable`).
- **Iteration cap: max 3 Builder↔QA rounds.** If a defect survives 3 rounds, STOP and escalate to
  the operator with the open defect — do not loop forever (this bounds cost against the $300 cap).
- **Nothing ships to a real customer without `REVIEW_PASS` then operator approval.** QA passing is
  necessary but not sufficient; the operator still gates go-live (LIVE Stripe + real outbound).
- Each handoff comment names: what was done, where it is (paths), and the single next action.

## Waking the next agent

Because `wakeOnDemand:true`, posting a handoff comment on the assignee's issue wakes them (the
self-comment guard prevents self-loops). If an agent must hand to a different agent, create/assign
the child issue and post the marker there. The CEO routes; reports execute one cognitive mode each:
Builder builds, QA verifies, Finance-Ops runs money/Stripe.
