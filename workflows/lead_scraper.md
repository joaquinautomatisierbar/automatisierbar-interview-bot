---
name: Lead Scraper
n8n-workflow-id: kolnAPK0JyR5SxL8
n8n-workflow-name: ⭐️ Business Scraping Tool
autonomy-level: L4
bike-method-phase: 1
last_validated: 2026-05-09
---

# Lead Scraper

## Purpose

Pull KMU lead data from Google Maps via Apify, dedup against the existing Lead-DB, and write only new leads. Targets are queued in a Notion DB so the user manages scope from Notion UI without touching n8n.

Replaces the manual single-term, no-dedup version. Built to feed the cold-call pipeline at volume — closest cities to Baden 5400 first, daily cron, fire-and-forget.

## Architecture (process map)

| | |
|---|---|
| **Trigger** | Schedule (daily 06:00 local) + Manual fallback |
| **Data sources** | Notion "Scraping Queue" DB (job rows), Notion "Interview Datenbank" (existing-lead placeIds), Apify Google Maps Scraper (`compass/crawler-google-places`) |
| **Transformations** | Sort queue by Distance ASC → resolve search terms (row override or default) → call Apify → bulk fetch existing placeIds → in-memory dedup |
| **Decision points** | "Has Pending?" gate exits early on empty queue. "Has New Leads?" gate routes leads to Notion writes; empty result still triggers Mark Done with addedCount=0. |
| **Destination** | New leads → Notion "Interview Datenbank". Queue row → Status=Done with Last Run, Leads Added, Leads Skipped. |

## Inputs

### Notion "Scraping Queue" DB

DB ID: `4e928a77-cafc-4f62-937f-f59d698ea7b1` (page-id form for n8n notion node).
Data source ID: `319e3164-5be7-45d3-945d-47fb1d11b8bb`.

Properties:

| Property | Type | Notes |
|---|---|---|
| `Name` | title | "Baden 5400" — human-readable |
| `Location` | rich_text | Apify locationQuery — "5400 Baden, Schweiz" |
| `Search Terms` | multi_select | Pre-defined 20 backoffice-heavy categories (color-grouped: orange=real estate, blue=legal/tax, yellow=arch/eng, green=insurance/finance, purple=consulting/IT, pink=marketing). Empty = use full 20-term default list. The Code node joins selected names into a comma-separated string for downstream parsing. |
| `Distance (km)` | number | km from Baden 5400. Cron picks lowest-distance Pending row first. |
| `Tier` | select | T1/T2/T3/T4 — visual grouping only, not used by workflow |
| `Status` | select | Pending / Running / Done / Error |
| `Last Run` | date | written by workflow |
| `Leads Added` | number | written by workflow |
| `Leads Skipped` | number | written by workflow |
| `Notes` | rich_text | error details |

24 rows pre-seeded for Aargau (T1-T3 around Baden). User adds/edits freely in Notion.

### Default backoffice-heavy KMU term list

Hardcoded in the `Resolve Terms` Code node. Used when a queue row's `Search Terms` field is empty.

```
Immobilien, Treuhand, Anwaltskanzlei, Steuerberater, Notar, Architekt,
Ingenieurbüro, Versicherung, Versicherungsmakler, Vermögensverwaltung,
Unternehmensberatung, Personalberatung, IT-Dienstleister, Werbeagentur,
Marketingagentur, Webdesign-Agentur, Hausverwaltung,
Liegenschaftsverwaltung, Buchhaltung, Treuhandbüro
```

ICP rule: backoffice/paperwork-heavy SMEs only. **Don't add walk-in retail** (Coiffeur, Bäckerei, Restaurant, Apotheke, Optiker), **don't add trades** (Sanitär, Elektriker, Schreinerei, Gartenbau) — they have minimal backoffice work and waste call time. See `feedback_lead_icp_backoffice` memory.

### Per-row override

Queue row's `Search Terms` field (comma-separated) overrides the default list for that one row. Useful for niche pushes ("only Notare in Zürich") without touching the workflow.

## Outputs

### Notion "Interview Datenbank" (DB ID `31cbebb0-c2f9-8047-9e9f-fc59851f8a34`)

For each new lead, creates one page with:
- Title (and `Firma|rich_text`): company name from Apify `title`
- `phone|rich_text`
- `placeId|rich_text` — **dedup key**, must be preserved
- `website|url`
- `city|rich_text`
- `postalCode|rich_text`

Schema unchanged from prior version. Downstream consumers (Voice Call Agent workflows) work without modification.

## Dedup logic

In `Dedup Filter` Code node (run once per execution):

1. Pulls every existing page from Lead-DB via `Get Existing Lead placeIds` node (`returnAll: true`, `simple: false`).
2. Extracts `placeId` rich_text into a `Set<string>`. Items with empty placeId are skipped (can't dedup; usually malformed Maps entries).
3. Iterates Apify items: drop if no placeId (`noPlaceIdCount++`), skip if placeId in existing set (`skippedCount++`), else push to `newLeads` with `__stats` metadata.
4. After loop, finalizes `addedCount`/`skippedCount`/`noPlaceIdCount` on every output item (must happen post-loop — capturing at push time gives stale counts; was a bug, fixed).
5. If 0 new leads: emits one sentinel item with `__isLead: false` so Mark Done still receives data.

`Has New Leads?` IF gate routes real leads to `Edit Fields → Create Lead Page`; empty sentinel falls off into nothing. `Mark Done` runs `executeOnce: true` regardless, reading stats via `$('Dedup Filter').first().json.__stats`.

## Edge cases handled

1. **No Pending rows** → `Has Pending?` exits early. No Apify spend.
2. **Apify returns 0 results** → marks Done with `Leads Added: 0`.
3. **All scraped items already in Lead-DB** → marks Done with `Leads Added: 0, Leads Skipped: N`. Signal that this region is exhausted; user can move it to T4 or delete row.
4. **Apify item missing placeId** → dropped, counted in `noPlaceIdCount` (logged in execution data; can be surfaced in Notes if needed).
5. **Lead-DB grows past 10k rows** → Notion `getAll` paginates automatically. Set fits in memory at any reasonable scale (~30 bytes per ID).
6. **Crashed previous execution leaving Status=Running** → not currently picked up; only `Status=Pending` is queried. If stuck Running becomes a problem, manually toggle the row back to Pending. Happened 2026-05-10 after the 50-place OOM crash — Ennetbaden was stuck Running for ~24h until reset.
7. **n8n OOM at Apify node** → cause is too much data in one Apify response. Symptom: execution status `crashed`, error `NodeCrashedError` at `Run Google Maps Scraper`. Fix: lower `maxCrawledPlacesPerSearch` further, or split a row into multiple smaller rows with fewer Search Terms each. Memory budget is roughly `terms × placesPerTerm × 5 KB ≈ payload size`; n8n cloud handles ~500 places × 5 KB = 2.5 MB comfortably, ~1000 places crashes.
8. **Intra-batch duplicates (same placeId returned by multiple search terms)** → dedup filter tracks them via `seenInBatch` Set, counted in `__stats.intraBatchDupes`, and only the first occurrence is written. Common when overlapping terms are used (e.g. "Treuhand" + "Treuhandbüro" both return the same Treuhand AG).

## Halt-before-acting (Phase 1)

First real run: limited to 3 terms ("Immobilien, Treuhand, Anwaltskanzlei") on Baden 5400 only. Uses `executeMode: manual` so cron stays off until verified. Halt is the explicit AskUserQuestion gate before triggering — paid Apify credits + live Notion writes.

After Phase-1 verification: increase per-row Search Terms or use defaults, advance `bike-method-phase` to 2, then 3 once a week of cron runs has been clean.

## Verification flow

1. **`mcp__claude_ai_n8n__validate_workflow`** — schema/expression validation. Must pass before update.
2. **`mcp__claude_ai_n8n__test_workflow`** with pin data — verifies dedup logic on a synthetic Apify response. Validated 2026-05-09: 4 Apify items → 2 new leads, 1 skipped (existing placeId), 1 dropped (empty placeId). Stats correct on every output item.
3. **`mcp__claude_ai_n8n__execute_workflow`** with manual mode + Baden Search Terms restricted — first paid run.

## Operating tips

- **Volume math:** `terms × maxCrawledPlacesPerSearch (20)` = upper bound on Apify dataset size per row. Default 20 terms × 20 = 400 places gross; usually ~150-360 unique after Google's own dedup. Cost: ~$0.20-0.60 per location. Cap was lowered from 50 to 20 on 2026-05-10 after a 20-term × 50-place run OOM-crashed n8n at the Apify node — current cap fits comfortably in n8n cloud memory.
- **Per-run cap:** workflow processes **1 queue row per execution** (Sort & Take First node returns single item). Daily cron = 1 city per day. To accelerate, manually trigger multiple times — but watch Apify spend.
- **Adding a new city:** create a row in "Scraping Queue" with Name, Location, Distance (km), Tier=appropriate, Status=Pending. Search Terms optional.
- **Re-running a Done row:** flip Status back to Pending in Notion. The dedup will skip everything already in Lead-DB, so cost is the same as first run but `Leads Added` will be 0 if region was exhausted.
- **Killing a stuck run:** in n8n UI, stop the execution. Then in Notion, flip the row's Status from Running → Pending so cron picks it up again.

## Common failure patterns

- **"Apify rate limited"** — manifested as 429 in execution logs. Solution: wait a few hours, re-trigger. The dedup makes retries safe.
- **Notion `simple:false` produces nested `properties.X.rich_text` arrays** — every Code node must extract via `props.X.rich_text.map(t => t.plain_text).join("")`. Don't trust top-level field shortcuts when `simple:false`. The `Get Pending Queue Rows` node uses `simple:false` (we need the property structure for multi_select/select fields).
- **Notion `simple:true` flattens to direct values** — `Get Existing Lead placeIds` uses `simple:true` to drastically reduce payload (used to be `simple:false`, contributed to OOM pressure). The Dedup Filter Code node now reads `j.placeId` directly. Defensive code in Dedup Filter still tolerates the legacy nested shape in case `simple` toggles back.
- **Multi-select property in n8n Notion node** — outputs as `properties["Search Terms"].multi_select = [{name: "Immobilien"}, ...]`. The Sort & Take First Code node has an `ms()` helper that flattens the array of `{name}` objects into a comma-separated string.
- **`__stats` carries internal flags into Notion writes** — the `Edit Fields` Set node strips them by only listing public fields (`Firma, phone, placeId, website, city, postalCode`). Don't add `__isLead` or `__stats` to the assignment list.

## Schedule

- Daily 06:00 local (Schedule Trigger config: `{ field: 'days', daysInterval: 1, triggerAtHour: 6, triggerAtMinute: 0 }`).
- Manual trigger remains in parallel for ad-hoc runs / catch-up after holidays.
- **Note:** workflow needs to be `active: true` in n8n UI for cron to fire. Currently inactive (Phase 1). Activate after Phase-1 verification.

## Related

- `connections.md` — links Lead-DB, Voice Call Agent, transcript pipeline.
- Memory `project_call_analytics_pipeline.md` — downstream consumers of Lead-DB.
- Memory `feedback_lead_icp_backoffice.md` — ICP filter rule for term lists.
- Memory `reference_n8n_quirks.md` — `simple:false`, `returnAll:true`, publish-after-update gotchas.
