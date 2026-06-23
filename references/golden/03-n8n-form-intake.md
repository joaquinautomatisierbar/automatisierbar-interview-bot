# Golden 03 — n8n Form → UI intake (browser-test mandatory)

- **surface:** n8n Form Trigger → validate → Notion write → confirmation page
- **anchor:** lead intake form; the "a UI must be browser-tested, never just validated" lesson
- **verifier:** `validate_workflow` + **Playwright** (load form, fill, submit, assert) + Notion read-back

## brief (DE)
> Baue ein n8n-Formular (Form Trigger), das Lead-Daten aufnimmt — `Firma`, `Branche`, `Telefon` —
> die Eingaben serverseitig validiert, einen neuen Eintrag in die Leads-DB schreibt und nach dem
> Absenden eine Bestätigungsseite zeigt. Leere Pflichtfelder werden abgewiesen, nicht gespeichert.

## fixtures
- Leads DB id `31cbebb0-c2f9-8047-9e9f-fc59851f8a34`
- Required form fields: `Firma` (text, required), `Branche` (dropdown), `Telefon` (text, required)
- The form's public URL once the workflow is active (Playwright loads this)

## validator_assertions
- `validate_workflow` valid; Form Trigger fields defined with `requiredField` where stated
- **Playwright**: loads the form URL, fills valid data, submits, asserts the confirmation page renders
- **Notion read-back**: the submitted row actually exists in the Leads DB with the right values
- **Playwright (negative)**: submitting with empty `Firma` shows a validation error and writes **no** row

## must_contain
- server-side required-field validation
- a real confirmation/thank-you screen after a valid submit
- a Playwright spec that fills + submits + asserts (not just a screenshot)

## ❗ must-NOT-do  *(review this block)*
- ❌ **[PRIME] Touch any real customer / live production system** — live Notion, prod-n8n activation, real outbound, paid backfill. Sandbox/pin-data only; live writes wait for your approval (README Prime Directive). **Automatic fail.**
- ❌ Mark the build "done" on `validate_workflow` `valid:true` alone — a form is a **UI**; it must be
  browser-tested end-to-end (fill → submit → assert confirmation **and** the Notion row). Same lesson
  as the blank-page dashboard bug: schema-valid ≠ actually works.
- ❌ Skip server-side validation and let an empty `Firma`/`Telefon` write a blank lead row.
- ❌ Write a Notion row on page-load / GET — only on a valid POST submit.
- ❌ Accept a screenshot that "looks fine" as proof — the verifier must assert the row was actually
  created, not just that pixels rendered.
- ❌ Hard-fail the run on a transient form-render timeout without one retry (forms cold-start slowly).

*Source: the no-blank-page / Playwright-gate lesson (Cortana UI rebuild) + n8n Form intake pattern.*
