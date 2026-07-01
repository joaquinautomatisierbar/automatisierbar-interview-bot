---
name: walkinleadsconvert
description: Use when the operator types /walkinleadsconvert or asks to "convert the walk-in leads", "put the walk-ins into the database", "walk-ins in die Interview Datenbank", "Leads aus dem Cockpit erstellen" — typically right after running /walkinmail. Takes the already-emailed walk-in lines (the ones marked ✅) from the 💡-callout on the Operations Cockpit, researches each company online, cross-checks the Interview Datenbank (Leads DB), then creates a new lead or expands the existing one — always tagging HOT STATUS = WALK IN BUT NO BAMFAM (so it surfaces in the Hot Leads callout) and pasting the operator's exact callout text 1:1 into the lead page for traceability, then removing the converted line from the callout (its note is preserved on the lead). Writes directly to the live Leads DB.
---

# /walkinleadsconvert — turn emailed walk-ins into real leads

`/walkinmail` drafts the follow-up and marks each callout line `✅ {date}` ("emailed").
This skill is the next step: each **emailed** walk-in becomes a tracked, enriched, hot-tagged
record in the Interview Datenbank. One run = N leads created/expanded + each converted line
**removed from the callout** (its note is safe — it's pasted onto the lead page first).

**It writes directly to the live Leads DB** (operator's explicit choice — this is operator-invoked,
not autonomous). No preview gate; it reports a full summary after. Process **only** lines that already
have `✅` — those are the ones we actually emailed.

## Config — Notion IDs (single source of truth)

Full schema, exact select options, property map, and dedup rules live in
[references/leads-db-schema.md](references/leads-db-schema.md). **Read it before writing anything.**

```
COCKPIT page       = 311bebb0c2f980de89a0f3d463a0fbce   # has the 💡 walk-in callout
💡 callout block    = 389bebb0c2f9804eb2bef28e599c0a68
LEADS DB           = 31cbebb0c2f980479e9ffc59851f8a34
LEADS data source  = collection://31cbebb0-c2f9-8075-b996-000b1747664a
HOT LEADS view     = 388bebb0c2f980139071ce86f2d65923   # linked view; filter widened to include WALK IN BUT NO BAMFAM
```

Markers on a callout line: `✅` = emailed (the gate) · `⚠️` = flagged, no contact. Once converted,
this skill **deletes** the line (older runs stamped a `📇` instead — treat any leftover `📇` line as
already done and skip it).

## Procedure

### 1. Select the entries to convert
- `notion-fetch` the **Cockpit** page → read the 💡-callout.
- Take a line **only if it contains `✅`** (= we emailed them). Converted lines are deleted, so a
  re-run naturally skips them; also skip any legacy line still carrying `📇` (already converted by an
  older run). Skip `⚠️`/`geflaggt` lines and pure learning-notes (e.g. the Autowerkstätte VP-lesson
  line) — they have no contact to log.
- If the operator passed company names as args (e.g. `/walkinleadsconvert Sereo, Codes SA`), process
  only those lines.
- Nothing to do → say so and stop. Capture the `✅ {date}` on each line; that's the walk-in date.

### 2. Parse each line (you do the reasoning — these are messy German free-text)
Extract `{ Firma, contact?, Rolle?, email?, website?, city?, phone?, walk-in date, raw_text }`.
Keep the **full original line** as `raw_text` for the 1:1 paste. Examples:
- `Sereo → Ramona Müller, Prozess und Qualitäts Managerin, mueller@sereo.ch, sereo.ch …`
  → Firma `Sereo`, contact `Ramona Müller`, role hint `Prozess-/Qualitätsmanagerin`, email, website.
- `Onur, Physio und Massage → … (onua.ch, info@onua.ch)` → Firma is the **business** (Onua), contact `Onur`.
- `Mail@stephan-hatt.ch -> Genossenschaft Q27 …` → Firma `Genossenschaft Q27`, email from the line.

### 3. Enrich online (same research as /walkinmail)
For each company: `WebSearch` the name + "Schweiz", open the official site (`WebFetch` Impressum/Kontakt/Über-uns)
and fill what's confidently grounded: `website`, `email`, `postalCode`, `Branche` (**best match from the
existing 153 options in the reference — never create a new one**), `Größe`, and the 5-line `Context` call card.
**Never invent.** If the site is too thin / unreachable, leave those blank (set `Enrichment Status` = `Website zu dünn`).

### 4. Cross-check the database (dedup)
For each company: `notion-search` scoped to the LEADS data source by company name → `notion-fetch` the top
1–2 hits → confirm same company by `Firma` / website domain / email. Confident match → **expand** it; no
match → **create**. (SQL `query-data-sources` is plan-gated, so use search — see reference.)

### 5. Write to the Interview Datenbank (direct)
Apply the property map in the reference. Exact spellings matter (incl. the en-dashes in `War-Room Status`).

- **Create** — `notion-create-pages` in the LEADS data source. `Name` = `"{Firma} {City}"` (mirror existing
  rows like "Saxer Treuhand AG Baden"). Page **body** = a labeled callout that holds the operator's note 1:1:

  ```
  📝 Walk-In Notiz ({walk-in date})
  {raw_text, exactly as written in the callout}
  ```

- **Expand** — `notion-update-page`. Fill a property **only if it's currently empty** (never clobber).
  Always set `HOT STATUS = WALK IN BUT NO BAMFAM` — **unless** it's already `HOT`/`QUITE HOT` (keep the hotter
  one, note it). Set `War-Room Status`/`Outreach Channel` only if blank. Append the same `📝 Walk-In Notiz`
  block to the page (don't replace existing content).
  - **Use real line breaks in the content, not `\n`.** `notion-update-page` writes `\n` literally and mangles
    the layout (create-pages tolerates `\n`, update-page does not).

Fixed on every converted lead: `HOT STATUS = WALK IN BUT NO BAMFAM`, `Outreach Channel = Walk-In`,
`Outreach Gemacht? = ✓`, `Contacted = ✓`, `Gesprächsdatum`/`Last contacted` = walk-in date,
`Pipeline Stage = Problem Interview`, `War-Room Status = ○ Offen – keine Antwort` (if blank).

### 6. Delete the converted line
Once the lead write is **confirmed** (Step 5 done — not before; the raw note now lives on the lead
page, so removing the callout line loses nothing), delete that line from the 💡-callout.
- `notion-update-page` (command `update_content`) on the **Cockpit** page: set `old_str` to the **whole
  line including its line break** and `new_str` to an empty string, so no blank gap is left behind.
- Anchor `old_str` on a **unique** trailing chunk of the line — the company note plus its ` ✅ {date}`
  is reliably unique — and avoid the `→`/`->` arrows (they're markdown-escaped; match text after the arrow).
- After the deletes, `notion-fetch` the callout once to confirm the lines are gone and no empty rows
  remain; if a blank line lingers, do a second pass to collapse it.
- If a line can't be matched **uniquely** (risk of deleting the wrong one), leave it in place and list
  it under "needs a human eye" rather than guess — never delete a line you're unsure about.

### 7. Report
A table: **Created** / **Expanded** / **Skipped**, each with the company, the lead-page link, and the
`Branche` + `HOT STATUS` set. Note any lead whose hotter `HOT STATUS` was preserved, and any company left
un-enriched (thin website). Remind the operator the new leads now show in the Hot Leads callout, and
that the converted lines were cleared from the 💡-callout.

## Guardrails
- **Only `✅` lines.** ✅ means we emailed them; converted lines get deleted (a leftover `📇` from an
  older run also means done — skip it). Skip `⚠️`/flagged.
- **Delete only after the write succeeds, never before.** The line's note is preserved verbatim on the
  lead page (Step 5), so deletion is safe once the lead exists — but delete first and a failed write
  loses the note for good. Order: write lead → confirm → delete line.
- **Never fabricate** an email, website, Branche, or Context — leave blank and flag instead.
- **Expand = fill-empty-only.** Never overwrite existing field values; never downgrade a `HOT`/`QUITE HOT`
  status; never replace page body — append.
- **Pick an existing `Branche`/`Rolle`/`Größe` option** verbatim; don't spawn new select options.
- **Real line breaks on `notion-update-page`** (the `\n` quirk). `create-pages` tolerates `\n`.
- Keep exact enum spellings (the `–` en-dashes in `War-Room Status` are intentional). Any *prose* you write
  in German (Context, notes) stays free of em-/en-dashes (—/–) per house style — use comma/colon/period;
  compound hyphens like `30-Minuten-Termin` are fine.
- **Direct write is intentional** and operator-invoked. Still: if you ever can't confidently tell create vs
  expand for a company (ambiguous match), skip that one and list it under "needs a human eye" rather than
  risk a duplicate or a wrong-company write.

## Reference
- [references/leads-db-schema.md](references/leads-db-schema.md) — property map, exact select options, dedup + merge rules.
- Sibling skill `/walkinmail` (`.claude/skills/walkinmail/SKILL.md`) — the email step that runs first and sets the `✅`.
- `Context` call-card format mirrors the daily lead-enrichment workflow (`workflows/daily_lead_enrichment.md`).
