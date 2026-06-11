---
autonomy-level: L2
bike-method-phase: 1
kpi-bucket: less-cost
kpi-metric: cold-call connect-to-qualified-conversation rate (proxy = % of dials that capture a Top Problem)
---

# Lead Cleanup — Preview (Workflow C-1)

**Step 1 of 2** in the Lead-DB hygiene flow. Notion-button-triggered. AI-flags non-ICP leads but does **not** archive — operator reviews flags in Notion before clicking Confirm.

## Workflow

| ID | Name | Trigger | URL |
|---|---|---|---|
| `vHiLceheTFzyTj92` | Lead Cleanup — Preview | Webhook POST `/lead-cleanup-preview` | https://oojoaquin.app.n8n.cloud/workflow/vHiLceheTFzyTj92 |

Pair: `workflows/lead_cleanup_confirm.md` (workflow `e5q3mlrYzrGkltCI`).

## What it does

1. Webhook receives POST (Notion button or curl).
2. Notion `getAll` on Interview Datenbank with filter:
   - `Pipeline Stage` = `Problem Interview`
   - `Outreach Gemacht?` = `false`
   - `Interview Abgeschlossen` = `false`
   - `Do Not Remove` = `false`
3. Code node `Build Claude Prompt` aggregates all candidates into ONE batched Claude request (name + firma + website + city + branche per lead).
4. IF `skip = true` (0 candidates) → `Respond No Candidates` and stop.
5. HTTP Request → `api.anthropic.com/v1/messages` with Claude Haiku 4.5 (`claude-haiku-4-5-20251001`).
6. Code `Parse Claude Response` → one item per lead with `decision` (KEEP | REMOVE | UNCLEAR). UNCLEAR is normalized to KEEP downstream (safety bias).
7. SplitInBatches (5) → for each item, Notion update sets `Cleanup Status = Pending Removal` + `Cleanup Reason` for REMOVE rows; clears the same fields for KEEP rows. **Idempotent** — re-running Preview correctly resets stale flags.
8. `Aggregate Summary` (onDone) → counts + top reasons + safety warning if flag rate > 50%.
9. `Respond Preview` → JSON summary back to caller.

## Inputs

POST to webhook. Body is currently ignored (the workflow always scans the full untouched cohort). Future param ideas: `city: "Baden"` for sub-segment runs.

## Outputs

JSON response body:

```json
{
  "status": "preview_complete",
  "totalScanned": 87,
  "flaggedForRemoval": 41,
  "keptAsFit": 44,
  "unclearDefaultedToKeep": 2,
  "flagRatePercent": 47,
  "safetyWarning": null,
  "topReasons": [{ "reason": "coiffeur walk-in retail", "count": 12 }, ...],
  "nextStep": "Open the Lead Ops page in Notion → review → click Confirm Cleanup when ready."
}
```

Notion side-effect: each REMOVE-flagged row gets `Cleanup Status = "Pending Removal"` + `Cleanup Reason = <AI's reason>`. KEEP rows get those fields cleared.

## ICP rules embedded in the prompt

**KEEP (backoffice-heavy):** Treuhand, Anwaltskanzlei, Steuerberater, Notar, Architekt, Ingenieurbüro, Versicherung, Vermögensverwaltung, Unternehmensberatung, Personalberatung, IT-Dienstleister, Werbeagentur, Marketingagentur, Webdesign-Agentur, Hausverwaltung, Immobilien (multi-agent firms).

**REMOVE (no/minimal backoffice):** Walk-in retail (Coiffeur, Restaurant, Bäckerei, Apotheke, Optiker, Metzgerei, Konditorei, Pizzeria), trades (Sanitär, Elektriker, Schreinerei, Gartenbau, Maler, Dachdecker, Garagist, Carrosserie), single-person freelancers, medical PHI, banking, FINMA-regulated.

**UNCLEAR → KEEP:** Generic names without website context (e.g. "Schmidt AG"). Conservative bias.

If you tune the ICP boundaries, edit the `Build Claude Prompt` Code node directly in n8n and re-run Preview to validate.

## Credentials

- `Notion account` (notionApi) — auto-attached on create
- `Anthropic Header Auth` (httpHeaderAuth, `x-api-key` header) — **manual attach required** on the `Call Anthropic API` HTTP Request node. Reuse the same cred the Lead Fit Scorer uses.

## Halt-conditions per CLAUDE.md

- **First live run** is a real Notion mutation (writes flags to production rows). User must explicitly trigger from Notion button or `execute_workflow` after activation. Phase-1 expectation: the operator runs Preview once, eyeballs the flagged set in the linked DB view on the `Lead Ops — Cleanup` page, then decides whether to proceed.
- **>50% flag-rate warning** is informational only — workflow still writes flags. The Confirm step is the operator's chance to abort by simply not clicking it.

## Verification (when iterating)

1. `validate_workflow` with the SDK code (clean — 12 nodes, no errors).
2. `prepare_test_pin_data` + `test_workflow` with mixed-decision pin data:
   - 5 leads (Treuhand=KEEP, Coiffeur=REMOVE, Pizzeria=REMOVE, Architekt=KEEP, Schmidt-AG-no-website=UNCLEAR→KEEP)
   - Mocked Claude response in JSON-array form
   - Verify: `Aggregate Summary` shows `flaggedForRemoval: 2, keptAsFit: 3, unclearDefaultedToKeep: 1, flagRatePercent: 40`.
3. **Edge cases tested (executions 836-840):**
   - 0 candidates → routes to `Respond No Candidates`
   - Markdown-fenced JSON (` ```json ... ``` `) → parser strips fences via indexOf('[') / lastIndexOf(']')
   - Garbage Claude response ("I'm sorry...") → throws clear error from `Parse Claude Response` line 20
   - 100% flag rate → `safetyWarning` populated
4. **Live first run:** invoke via `curl -X POST https://oojoaquin.app.n8n.cloud/webhook/lead-cleanup-preview` after activating the workflow. Eyeball the response + the flagged rows in Notion before any Confirm.

## Lessons

- `.join()` is a **disallowed method** in the n8n SDK validator. Build long jsCode strings via `+` concatenation, not `[...].join('\n')`.
- `predefinedCredentialType: notionApi` does NOT auto-attach via `create_workflow_from_code` — the operator has to attach the credential manually on the `Archive Notion Page` node in the Confirm workflow. (Pattern works fine at runtime once attached.)
- Notion `databasePage.update` with `selectValue: ""` correctly **clears** a select field, which gives us idempotent re-runs (KEEP decisions wipe stale Pending Removal flags).
- Claude Haiku 4.5 batches ~150-200 leads per call comfortably (~10K output tokens, fits within 64K cap).
