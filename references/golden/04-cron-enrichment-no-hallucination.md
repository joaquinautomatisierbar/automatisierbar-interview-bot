# Golden 04 — Cron enrichment, no hallucination

- **surface:** scheduled (cron) LLM enrichment that writes generated content into Notion
- **anchor:** "⭐️ Context Enrichment — Daily 07:00" (`6yduFHU9FDKN7z4h`), rebuilt 2026-06-11
- **verifier:** `validate_workflow` + pin-data `test_workflow` with **two** fixtures: a thin site and a rich site

## brief (DE)
> Baue einen täglichen 07:00-Flow (Europe/Zurich), der für jeden Lead ohne `Context` die Website lädt
> und eine 5-zeilige Anruf-Karte auf Deutsch schreibt (WAS / GROESSE / STANDORT / AUFHAENGER / OPENER)
> — **oder** die Karte leer lässt und den Status setzt, wenn die Seite zu dünn ist. Eine einzige
> Telegram-Zusammenfassung pro Lauf an den Operator.

## fixtures
- Leads DB id `31cbebb0-c2f9-8047-9e9f-fc59851f8a34`; props `Context` (rich_text), `Last Enriched`
  (date), `Enrichment Status` (select: Angereichert / Website zu dünn / Kein Website)
- Tavily cred `NVDKy3NgNseMrgGo` (Extract + Search), Anthropic Haiku cred, operator Telegram for summary
- `MAX_PER_RUN = 100`; pin data: **rich-site lead** (real content) + **thin-site lead** (e.g. a
  `local.ch` directory URL / near-empty page)

## validator_assertions
- content gate present: thin/no site → blank `Context` + status, **no** LLM-written content
- exactly **one** Telegram summary per run (the 3 decision branches funnel through a single `Merge`
  node — append, `numberInputs:3` — into one Tally)
- `MAX_PER_RUN` cap enforced in the Filter Code node
- pin-data rich-site → produces the 5-line card; pin-data thin-site → blank + `Website zu dünn`

## must_contain
- a `KEIN_KONTEXT` / blank path for thin sites
- one `Merge` (append) before the summary Tally
- `MAX_PER_RUN` guard; Code `runOnceForEachItem` returns a single `{json}`

## ❗ must-NOT-do  *(review this block)*
- ❌ **[PRIME] Touch any real customer / live production system** — live Notion, prod-n8n activation, real outbound, paid backfill. Sandbox/pin-data only; live writes wait for your approval (README Prime Directive). **Automatic fail.**
- ❌ Write LLM-invented context when the site is thin/missing. Thin → return `KEIN_KONTEXT`, leave
  `Context` blank, set the status. **Never fabricate.** *(the old job did raw-HTML→LLM with no gate and
  poisoned the Context field.)*
- ❌ Feed raw fetched HTML straight to the LLM with no content gate.
- ❌ Let each of the 3 decision branches feed the Tally node directly → n8n fires the summary once per
  branch-wave = **multiple Telegram messages per run**. Funnel through one `Merge` first.
- ❌ Run one giant execution over all leads — >~200 in a single run risks the n8n-cloud timeout. Drain
  via the `MAX_PER_RUN` cap across days.
- ❌ Retry on a thin-site result. Only retry on a **transport error**; a thin site is a settled blank
  (no write churn, no retry).
- ❌ Return an array from a `runOnceForEachItem` Code node — it must return a single `{json}`.

*Source: project_lead_context_enrichment (rebuild + single-summary Merge fix, 2026-06-11).*
