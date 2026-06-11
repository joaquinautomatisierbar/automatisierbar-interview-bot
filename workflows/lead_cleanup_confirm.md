---
autonomy-level: L2
bike-method-phase: 1
kpi-bucket: less-cost
kpi-metric: cold-call connect-to-qualified-conversation rate (proxy = % of dials that capture a Top Problem)
---

# Lead Cleanup — Confirm (Workflow C-2)

**Step 2 of 2** in the Lead-DB hygiene flow. Notion-button-triggered. Archives every row currently flagged with `Cleanup Status = Pending Removal`. Reversible from Notion trash for 30 days.

## Workflow

| ID | Name | Trigger | URL |
|---|---|---|---|
| `e5q3mlrYzrGkltCI` | Lead Cleanup — Confirm | Webhook POST `/lead-cleanup-confirm` | https://oojoaquin.app.n8n.cloud/workflow/e5q3mlrYzrGkltCI |

Pair: `workflows/lead_cleanup_preview.md` (workflow `vHiLceheTFzyTj92`).

## What it does

1. Webhook receives POST (Notion button or curl).
2. Notion `getAll` on Interview Datenbank with filter `Cleanup Status = Pending Removal`.
3. SplitInBatches (3) → for each row, HTTP Request `PATCH api.notion.com/v1/pages/{id}` with body `{"archived": true}`. Uses the predefined `notionApi` credential type — Notion handles auth + version header, we just set `Notion-Version: 2022-06-28` explicitly for safety.
4. 1-second `Archive Pacing Wait` between batches to stay below Notion's 3 req/sec rate limit.
5. `Aggregate Confirm Summary` (onDone) → counts the archived rows from `$('Fetch Flagged Rows').all()`. Returns `nothing_to_archive` if zero.
6. `Respond Confirm` → JSON summary back to caller.

## Inputs

POST to webhook. Body ignored.

## Outputs

```json
{
  "status": "confirm_complete",
  "archived": 84,
  "message": "Archived 84 lead(s). Restorable from Notion trash for 30 days.",
  "nextStep": "Re-run Preview anytime to scan and flag the next batch of low-quality leads."
}
```

Or if no flagged rows exist:

```json
{
  "status": "nothing_to_archive",
  "message": "No rows currently flagged with Cleanup Status = Pending Removal. Run Preview first to flag candidates.",
  "archived": 0
}
```

## Credentials

- `Notion account` (notionApi) — auto-attached on the `Fetch Flagged Rows` Notion node, **manual attach required** on the `Archive Notion Page` HTTP Request node (predefined credential type doesn't auto-bind via SDK create).

## Why HTTP Request, not the Notion node

n8n's Notion node `page` resource exposes `create`, `get`, `search` operations — not `archive`. The Notion API archives via `PATCH /v1/pages/{id}` with body `{"archived": true}`. Using HTTP Request with `predefinedCredentialType: notionApi` reuses the same Notion credential the rest of our workflows use. (See `n8n_archive_notion_page` exploration in execution 837.)

## Halt-conditions per CLAUDE.md

- **First live run** archives real production rows. User must explicitly trigger after Preview has flagged a reviewed batch. Once archived, restoration is one-click in Notion's trash but only available for 30 days.
- The 30-day Notion trash window IS the safety net — there is no separate halt-and-poll guard inside this workflow. If you accidentally archive the wrong batch, restore from trash same day.

## Verification

1. `validate_workflow` clean (7 nodes).
2. `test_workflow` with pin data (4 mock flagged rows): execution 837, archived=4 reported. Loop ran 2 batches at batchSize 3.
3. **0-flagged edge case:** execution 841 — `nothing_to_archive` reported correctly.
4. **Live first run:** trigger Preview first → review flags in Notion → curl POST `/lead-cleanup-confirm` → check the response + Notion trash to verify expected pages got archived.

## Lessons

- Notion `databasePage` filter for select fields uses `{ select: { equals: "Option Name" } }` — note the property type is `select`, not `status` (which is for the Pipeline Stage status property type).
- `splitInBatches` with batchSize 3 + 1s wait between batches keeps us under Notion's 3 req/sec rate limit even on a 100+ row archive run.
