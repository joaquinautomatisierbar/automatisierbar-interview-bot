# Golden 05 — Inbound webhook → integration (idempotent)

- **surface:** webhook-triggered integration that writes to Notion, safe under retries
- **anchor:** lead-scraper webhook + the A2 backfill idempotency pattern
- **verifier:** `validate_workflow` + `execute_workflow` (webhook mode) fired **twice** → second is a no-op

## brief (DE)
> Baue einen Webhook-getriggerten Flow, der einen Lead-Payload empfängt (`placeId`, `Firma`,
> `Telefon`, optional `website`) und als neuen Lead in die Leads-DB schreibt — **idempotent**, sodass
> ein doppelter Aufruf mit demselben `placeId` keinen Duplikat-Eintrag erzeugt.

## fixtures
- Leads DB id `31cbebb0-c2f9-8047-9e9f-fc59851f8a34`; dedup key = `placeId` (stored property)
- Webhook POST body: `{ "placeId": "...", "Firma": "...", "Telefon": "...", "website": "..." }`
- Test: fire the same payload twice via `execute_workflow` `{type:"webhook", webhookData:{method:"POST", body:{…}}}`

## validator_assertions
- Webhook trigger (POST); `validate_workflow` valid
- idempotency: a getAll on the target DB (`executeOnce: true`) builds a Set of existing `placeId`s; the
  filter skips any payload whose `placeId` is already present
- two identical `execute_workflow` calls → exactly **one** Notion row created

## must_contain
- a dedup check on `placeId` before the Notion create
- the getAll-on-target + Set-of-seen-IDs idempotency guard

## ❗ must-NOT-do  *(review this block)*
- ❌ **[PRIME] Touch any real customer / live production system** — live Notion, prod-n8n activation, real outbound, paid backfill. Sandbox/pin-data only; live writes wait for your approval (README Prime Directive). **Automatic fail.**
- ❌ Create the Notion row with no dedup check → duplicate leads on any retry or double-fire.
- ❌ Dedup by `Firma`/name — not unique. Use `placeId`, the stable key.
- ❌ Assume a Drive-Trigger workflow can be fired programmatically — it can't (poll-only; copy_file is
  gateway-blocked). Build a **webhook-triggered sibling** as the test escape-hatch (the A2 pattern,
  `N0wtRuTFHay6SRVS`).
- ❌ Read binary/file content via `item.binary.data.data` → that's the literal string `"filesystem-v2"`,
  not the bytes. Use `await this.helpers.getBinaryDataBuffer(0, 'data')`.
- ❌ Parse an LLM JSON response without regex-extracting `{…}` first — Claude sometimes prepends a
  `Hinweis:` preamble even under "AUSSCHLIESSLICH JSON". Use `cleaned.match(/\{[\s\S]*\}/)[0]` and also
  strip a ```json fence.

*Source: reference_n8n_quirks (idempotency, A2 backfill, binary helper, JSON regex) + project_lead_scraper_v2 (placeId dedup).*
