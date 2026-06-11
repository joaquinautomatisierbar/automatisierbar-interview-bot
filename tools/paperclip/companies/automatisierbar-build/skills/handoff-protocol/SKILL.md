---
name: handoff-protocol
description: >
  The comment-marker handoff protocol for inter-agent routing in the Build Pipeline. Every transition between Engineer / QA / Product / Release / CTO uses one of six markers as the comment's first line.
---

# Handoff Protocol

The Build Pipeline runs as a state machine where state transitions are signaled by **markers as the first line of an Issue comment**. The orchestrator (and humans) parse these to route work.

## The six markers

| Marker | Posted by | Posted when | Reassign to |
|---|---|---|---|
| `READY_FOR_TEST` | Engineer | After implementation + validation + 3 artifacts written | QA Engineer |
| `TEST_PASS` | QA Engineer | After all 3 test scenarios pass | Product Engineer |
| `TEST_FAIL: <reason>` | QA Engineer | When any scenario fails | Engineer |
| `SHIP` | Product Engineer | After intent review passes | Release Engineer |
| `NEEDS_QOL: <reason>` | Product Engineer | When intent gap surfaced | Engineer |
| `BLOCKED: <reason>` | Any agent | When stuck after 3 attempts or hitting a constraint that needs human decision | CTO (or CEO if CTO already escalated) |

## Comment body format

Marker as first line. Then 1-3 paragraphs of detail. Then reassign the Issue (`POST /api/issues/<id>` with new `assigneeAgentId`).

### Example `READY_FOR_TEST`

```
READY_FOR_TEST

Built `priority-inbox-slack.workflow.code.js` per the locked plan. Validated via `validate_workflow` (no errors). Pin-data tested with three Gmail-message shapes covering golden/edge/failure paths.

Artifacts in workspace:
- workflow.code.js (n8n SDK)
- PRESENTATION.md (handover-ready, all 3 Klärungspunkte surfaced)
- TESTING.md (curl + n8n editor walkthrough, non-developer-executable)

Test inputs used: see `pin-data-golden.json`, `pin-data-edge.json`, `pin-data-failure.json` in workspace.
```

### Example `TEST_FAIL`

```
TEST_FAIL: golden-path output missing `gmail_link` field

Scenario: golden-path pin-data (subject="Dringend - Termin verschoben").
Expected: Slack message body contains "[Im Gmail öffnen](<link>)".
Actual: Slack message body has "[Im Gmail öffnen]()" — empty parentheses, link missing.

Node: `Format Message` (line 47 in workflow.code.js). The format string references `{{$json.gmail_link}}` but the upstream node `Gmail: Get Message` doesn't emit that field by default — needs to set `Include Web Link` option to true OR construct the link from `{{$json.id}}` manually.

Suggested fix: easiest is to construct manually as `https://mail.google.com/mail/u/0/#inbox/{{$json.id}}`.
```

### Example `SHIP`

```
SHIP

Artifact honors brief intent. ROI claim in PRESENTATION.md is honest (system: 0 min; human residual: 0 min on golden path, since Slack notification is fire-and-forget). All 3 Klärungspunkte are surfaced with MVP defaults + flagged for human confirmation.

Move-the-needle: `desired_outcome` "Ruths inbox-check time / Tag → <5 Min" — artifact removes the periodic-check pattern entirely, replaced with reactive Slack ping. Will move the needle.

Klärungspunkte flagged in PRESENTATION.md:
1. `eilt` in body but not subject → MVP default: NOT high. Confirm with customer.
2. Dedup behavior → MVP default: no dedup, each messageId triggers. Confirm.
3. Ruth seeing notifications → MVP default: all channel members see them. Confirm Ruth's channel membership.

Tej should focus the meeting on confirming (1), (2), (3) and watching the workflow fire on a real high-priority test message.
```

## Anti-patterns

- **Don't post mixed markers in one comment.** One marker per comment. If you have a partial result, hold the comment until you have a complete one.
- **Don't post a marker without reassigning the Issue.** Markers without reassignment leave the Issue stuck on you.
- **Don't manually flip Issue status.** `in_progress` / `in_review` flow from check-out and the marker semantics. The orchestrator (or paperclip itself) handles status.
- **Don't post a marker for a different agent's role.** Engineer never posts `TEST_PASS`. QA never posts `SHIP`.

## Why marker-first

The orchestrator (Phase 3 of the build) parses comment text via a regex `^(READY_FOR_TEST|TEST_PASS|TEST_FAIL|SHIP|NEEDS_QOL|BLOCKED)(:\s.*)?$` on the first line. Any other format requires human routing. Stay machine-parseable.
