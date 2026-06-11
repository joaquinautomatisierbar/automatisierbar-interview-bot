---
autonomy-level: L3
bike-method-phase: 1
kpi-bucket: more-customers
kpi-metric: hot-lead count per week + classification accuracy vs. manual review (target: ≥90% on outcome field)
---

# Transcript Analyzer (Workflows A + A2)

**Phase 2 of Cold-Call pipeline.** Klassifiziert eingehende Cold-Call-Transkripte, updatet Lead-DB, loggt Call in Call-Analytics.

## Two workflows, one pipeline

| ID | Name | Trigger | Use Case |
|---|---|---|---|
| **A** (`9kra1rbKJacENksN`) | Cold Call — Transcript Analyzer | Drive fileCreated (Transcripts folder) | Production: feuert auto bei jedem neuen Transkript |
| **A2** (`N0wtRuTFHay6SRVS`) | Cold Call — Transcript Backfill / Test Trigger | Webhook POST `/cold-call-backfill` | Backfill der bestehenden Files + autonome Tests via MCP |

Beide nutzen identische Code-Logic (filename parser, fuzzy match, classification, Notion writes). A2 hat zusätzlich: Idempotenz-Check, Loop über alle Files, configurable via Body-Params.

## Inputs

**Drive-File** (für beide): `<Firmenname>__<nico|joaquin|tej|patrik>.m4a_<YYYYMMDD-HHMMSS>.txt`
- Suffix-Convention: `__nico` etc. setzt den Interviewer
- Ohne Suffix: default = `nico` (backfill-Modus)
- Backfill-Files mit Pattern `<Firmenname>.m4a_<ts>.txt` (kein Suffix) → Nico

**A2-Webhook-Body** (alle optional):
- `{}` → alle unverarbeiteten Files (Idempotenz aktiv)
- `{file_id: "<drive-id>"}` → single file (force-process, ignoriert Idempotenz)
- `{limit: N}` → erste N Files
- `{force: true}` → reprocess all (skip idempotency)

## Pipeline (per File)

```
Drive Download → Parse Filename → Fuzzy Match Lead (vs Lead-DB)
  ↓
IF match_score ≥ 0.85?
  ├── TRUE → Anthropic Classify (Claude Sonnet 4.6)
  │          → Parse JSON
  │          → Notion Update Lead (Branche, Schmerzscore, Top Problem, Interview-geführt-von, Interview-Abgeschlossen)
  │          → Notion Create Call Analytics row
  │          → IF outcome=Hot? → Telegram Alert (A1) / silent (A2)
  └── FALSE → Telegram No-Match Alert (A1) / silent skip (A2)
```

## Outputs

**Lead-DB Update** (Interview Datenbank `31cbebb0-c2f9-8047-9e9f-fc59851f8a34`):
- `Branche` (select), `Schmnerzscore (1-5)` (number, sic Typo), `Top Problem` (text), `Interview geführt von` (people), `Interview Abgeschlossen` (checkbox=true)

**Call Analytics Create** (`ee4e6072-d2b7-41b5-835f-697e6f0becf6`):
- Lead-Relation, Call Date, Outcome, Failure Mode, Branche, Schmerzscore, Summary, Key Quote, Geführt von, Transcript Link, Drive File ID

## Critical Lessons

1. **Notion getAll braucht `simple: false`** — sonst kommt flattened format (`property_firma`) statt `properties.Firma.rich_text[0].plain_text`
2. **Notion getAll braucht `returnAll: true`** — `limit: 200` ohne returnAll cappet bei 100 (Notion-API page size)
3. **Drive Download Binary**: `await this.helpers.getBinaryDataBuffer(0, 'data')` — n8n speichert default als filesystem-v2 reference, nicht inline
4. **Notion property update format**: `propertiesUi.propertyValues[]` mit `key: "Name|type"` und type-specific value field (`selectValue`, `peopleValue: [string]`, `relationValue: [string]`, `textContent` mit `richText: false`)
5. **Validator vs Runtime**: `relationValue` warnt als "expected string got array" — Runtime erwartet aber array. Validator-Schema falsch, ignorieren.

## Credentials

- `Notion account` (auto-assigned)
- `Google Drive account` (auto-assigned)
- `Anthropic Header Auth` (manual: HTTP Header `x-api-key` mit Anthropic API key)
- `Cold Call Bot` (Telegram, A1 only — manual switch nach create)

## Halt-Conditions

A1 + A2 Activation = halt-conditions per CLAUDE.md (real Notion writes + real Telegram alerts). User aktiviert manuell.

## Verification

1. Validate-Workflow: `mcp__claude_ai_n8n__validate_workflow`
2. Logic-Smoketest A2: `test_workflow` mit pin data (siehe execution 785, all green)
3. Real-Run: `execute_workflow` mit `{file_id: "..."}` für single-file test, dann `{limit: 3}`, dann `{}` für full
4. Output check: `get_execution(includeData: true, nodeNames: ["Fuzzy Match Lead", "Parse Classification", "Notion: Create Call Analytics"])`

## Related Files

- Prompt: `prompts/transcript_classification.md`
- Memory: `~/.claude/projects/.../memory/project_call_analytics_pipeline.md`
- Memory n8n quirks: `~/.claude/projects/.../memory/reference_n8n_quirks.md` (TODO)
