# Notion "LinkedIn Posts" DB — schema, write recipe, Hub mapping

> The archive target for `/linkedin-posts`. Created 2026-06-30 under Operations Cockpit. This is the review surface until the Automatisierbar Hub exists; the schema is intentionally flat so it maps 1:1 onto a future Hub table.

## IDs (single source of truth)
- **Database id:** `2ab767833e9b4a0a8a4ab863074d7e01`
- **Data source id (use this as the create-pages parent):** `ef6ed6e4-0103-4286-98d5-8c0e0edc5762`
- **Parent page:** Operations Cockpit `311bebb0c2f980de89a0f3d463a0fbce`
- **Briefs DB (source of angles):** db `35cbebb0-c2f9-812a-9347-cbde09762d0c`, data source `35cbebb0-c2f9-81ec-92ed-000bd0f23098` ("LinkedIn Content Briefs Joaquin"). Env: `NOTION_BRIEFS_DB_ID`.
- Suggested env var for future automation: `NOTION_LINKEDIN_POSTS_DB_ID=2ab767833e9b4a0a8a4ab863074d7e01`.

## Properties
| Property | Type | Values / notes |
|---|---|---|
| `Name` | title | `KW-<iso> · <Person> · <Pillar> · H<x>` (amplification rows: `KW-<iso> · <Person> · amp→<origin Person>`) |
| `Body` | text | canonical post text (plain), first ~2000 chars — the scannable/Hub-migration copy |
| `Person` | select | `Joaquin` `Nico` `Tej` `Patrik` `Automatisierbar` |
| `Account Type` | select | `personal` `company` |
| `Type` | select | `original` `amplification` |
| `Pillar` | select | `build-in-public` `how-to` `proof-story` `industry-observation` `lesson` `team-culture` `announcement` |
| `Hook Type` | select | `H1`…`H10` — **original rows only; leave empty on amplification rows** (a quote-repost has no headline hook) |
| `Effect Goal` | select | `trust-build` `lead-warm` `brand-grow` `proof` |
| `Status` | select | `Draft` `Approved` `Posted` `Skipped` (skill always writes `Draft`) |
| `Calibration` | select | `seeded` `role-based-starter` `calibrated` (the voice confidence used) |
| `Week Of` | date | the Friday anchor of the week (matches the Briefs DB convention) |
| `Posted URL` | url | empty at draft time; operator fills after publishing |
| `Amplifies` | text | amplification rows only: the origin post's `Name` (soft link) |
| `Source Brief` | relation → Briefs ds | optional; the brief page this post drew from |
| `Image Type` | select | `card` / `carousel` / `real-asset` / `none` (Step 4.5) |
| `Image Spec` | text | the JSON spec the image was rendered from (regenerable; empty for real-asset/none) |
| `Image Path` | text | local file path of the rendered PNG/PDF (empty for real-asset/none) |

## Write recipe (use `notion-create-pages`, ONE call per run)
- Parent: `{"data_source_id": "ef6ed6e4-0103-4286-98d5-8c0e0edc5762"}`.
- One entry in `pages[]` per row: every original post row + every amplification commentary row.
- `properties` is a flat map. Set `Name`, `Body`, `Person`, `Account Type`, `Type`, `Pillar`, `Hook Type`, `Effect Goal`, `Calibration`, `Status` (= `Draft`).
  - **Date:** set `"date:Week Of:start": "YYYY-MM-DD"` and `"date:Week Of:is_datetime": 0`.
  - **`Posted URL`:** leave unset at draft time. (It is "Posted URL", not bare "url", so no `userDefined:` prefix is needed.)
  - **`Source Brief`** (optional): value is a JSON array string of the related brief page URL(s), e.g. `"[\"https://app.notion.com/p/<briefpageid>\"]"`. Omit if no brief was used.
  - **`Amplifies`** (amplification rows): the origin row's `Name` string.
- **`content`** = the page body in Notion-flavored markdown. `create-pages` tolerates `\n` escapes (unlike `update-page`, which writes them literally — see `reference_notion_mcp_quirks.md`). So build the body with `\n` freely.

### Body layout — original post row
```
## Post

```
<the full finished post, exactly as it should be pasted to LinkedIn,
including the 3 hashtags on the last line>
```

**Link (set as first comment, not in the post):** <url or "none">

## Amplifikations-Kit
Wer reposted: <Amplifier A>, <Amplifier B>

### Quote-Repost — <Amplifier A>
```
<Amplifier A's 100+ word unique commentary in their voice, Sie>
```

### Quote-Repost — <Amplifier B>
```
<Amplifier B's commentary>
```

**Golden Hour:** <weekday HH:MM Europe/Zurich> — 1–2 Teammates kommentieren echt in den ersten 60–90 Min (kein Pod, kein Pflicht-Like).
```

### Body layout — amplification row
(One row per amplifier, so each person's filter shows what THEY publish.)
```
## Quote-Repost (amplifies: <origin Name>)

```
<the amplifier's commentary, what they paste when quote-reposting the original>
```
```
The fenced code block is for one-click copy. The post text also goes in the `Body` property (plain) for list-view scanning + clean Hub migration.

## Hub-mapping (why the schema is flat)
Every column is a scalar, an enum (select), a date, a url, or a single relation — no multi-select, no nested page-property dependencies. So each row becomes one record in a future `linkedin_posts` table:

| Notion property | Hub column |
|---|---|
| Name | `title` (text) |
| Body | `body` (text) |
| Person | `author` (enum) |
| Account Type | `account_type` (enum) |
| Type | `kind` (enum: original/amplification) |
| Pillar | `pillar` (enum) |
| Hook Type | `hook` (enum) |
| Effect Goal | `goal` (enum) |
| Status | `status` (enum) |
| Calibration | `voice_confidence` (enum) |
| Week Of | `week_of` (date) |
| Posted URL | `posted_url` (url) |
| Amplifies | `amplifies_post` (FK by title → real FK in Hub) |
| Source Brief | `source_brief` (FK) |
| Image Type | `image_type` (enum) |
| Image Spec | `image_spec` (json) |
| Image Path | `image_url` (in the Hub, the MinIO attachment URL replaces the local path) |

## Schema-change safety
If a future edit needs a new property, add it via `update_data_source` and surface it to the operator first — do not silently mutate the schema mid-run.
