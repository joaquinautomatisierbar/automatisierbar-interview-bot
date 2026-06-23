# Golden 01 — Notion read + property update

- **surface:** Notion DB getAll + property update via n8n (claude.ai n8n SDK)
- **anchor:** Cold-Call Leads-DB read/write (Workflow A/A2)
- **verifier:** `validate_workflow` (valid:true, 0 errors) + pin-data `test_workflow` (NO live Notion write)

## brief (DE)
> Baue einen n8n-Flow, der alle Leads aus der Cold-Call Leads-DB liest, bei denen `Pipeline = Neu`
> ist, und bei jedem das Feld `Letzter Kontakt` auf das heutige Datum setzt und das `Status`-Select
> auf `Kontaktiert`. Verarbeite auch DBs mit >100 Zeilen vollständig.

## fixtures
- Leads DB id `31cbebb0-c2f9-8047-9e9f-fc59851f8a34`, data source `31cbebb0-c2f9-8075-b996-000b1747664a`
- Props: `Pipeline` (select), `Letzter Kontakt` (date), `Status` (select), `Firma` (rich_text)
- Notion credential `N0c1Nn5s4jZ0ZzuO`
- Pin data: 137 leads (so >100 is exercised), mix of `Pipeline=Neu` and others

## validator_assertions
- getAll node: `simple: false` **and** `returnAll: true`
- update node: `propertiesUi.propertyValues[]` with keys in `"PropertyName|type"` form
- date written as ISO-8601; select written via `selectValue`
- pin-data run touches only the `Pipeline=Neu` rows and routes the rest to no-op

## must_contain
- `simple: false`, `returnAll: true`, ISO-8601 date string, `selectValue: "Kontaktiert"`

## ❗ must-NOT-do  *(review this block)*
- ❌ **[PRIME] Touch any real customer / live production system** — live Notion, prod-n8n activation, real outbound, paid backfill. Sandbox/pin-data only; live writes wait for your approval (README Prime Directive). **Automatic fail.**
- ❌ Omit `simple: false` on getAll → Notion returns flattened `property_firma` etc., and every
  `properties.Firma.rich_text` lookup fails **silently**. *(commit `db94681`)*
- ❌ Use `returnAll: false` with `limit: 200` → returns ONLY 100 rows (Notion API page size ignores
  the limit); leads past row 100 are silently invisible. Must use `returnAll: true`.
- ❌ "Fix" a validator warning `expected string, got array` on a `relation`/`people` value by passing
  a string — the **runtime needs an ARRAY**. That warning is a false positive; trust the runtime.
- ❌ Ship after `update_workflow` without `publish_workflow` — the saved draft isn't live; the active
  trigger keeps firing the OLD code.
- ❌ Dismiss the sticky-note warning `parameters.content … Expected string, but got object` as a false
  positive — **that one is a real bug** (use `node({type:'stickyNote'…})`, not the broken `sticky()` helper).
- ❌ Do a real write to the live Leads DB during the test — pin-data `test_workflow` only.

*Source: reference_n8n_quirks (Workflow A/A2 build, commits db94681 / 0c80b13).*
