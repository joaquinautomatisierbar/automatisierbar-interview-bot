# Golden 02 — Telegram outbound (credential scoping)

- **surface:** add a Telegram send/notification to an n8n workflow
- **anchor:** per-workflow bot/credential scoping (the 2026-05-05 webhook-collision incident)
- **verifier:** `validate_workflow` + read-only `getWebhookInfo` check + pin-data `test_workflow` (NO live send)

## brief (DE)
> Füge dem Follow-up-Booking-Flow eine Telegram-Benachrichtigung an die Team-Gruppe hinzu, sobald ein
> Termin gebucht wurde. Die Nachricht soll Firma, Datum und Uhrzeit enthalten.

## fixtures
- Team group chat id `-5026363666` (operator bot)
- The follow-up booking workflow `74HCimZRimgpypWc`
- Existing operator Telegram credential (for the team group) — **not** the Interview-Bot cred
- For reference / as a negative: Interview-Bot credential `jSSmkZL5fsg14yCQ` (belongs to workflow `qcoGgfsBcmJ3RvV7`)

## validator_assertions
- the `telegram` (send) node references the workflow's **own** dedicated credential by name
- if a `telegramTrigger` is added, `getWebhookInfo` for that bot points to **this** workflow's `webhookId`
- message body interpolates Firma + Datum + Uhrzeit from upstream data

## must_contain
- explicit `credentials: { telegramApi: '<this workflow's cred>' }` on every Telegram node
- chat id sourced from config/fixture, not a hardcoded real id in test runs

## ❗ must-NOT-do  *(review this block)*
- ❌ **[PRIME] Touch any real customer / live production system** — live Notion, prod-n8n activation, real outbound, paid backfill. Sandbox/pin-data only; live writes wait for your approval (README Prime Directive). **Automatic fail.**
- ❌ Reuse the `Workflow Interview Bot` credential (`jSSmkZL5fsg14yCQ`) on a different workflow's
  Telegram node. Telegram allows **one webhook URL per bot token** → sharing a cred makes one workflow
  silently **steal another bot's incoming messages**. *(2026-05-05 incident: Walk-In bot's messages
  routed into the Interview workflow; ~1h to diagnose.)*
- ❌ Add a generic HTTP `webhook` node and expect Telegram messages to arrive — without a
  `telegramTrigger` node, n8n never `setWebhook`s the bot. Either add the trigger or manually `setWebhook`.
- ❌ Fire to the live team group `-5026363666` during a pin-data test — verify shape only, no live send.
- ❌ Route operator notifications through the **leads/interview bot** — that bot stays clean for real
  lead conversations. Operator pings use the operator bot only.

*Source: feedback_telegram_credentials (incident 2026-05-05).*
