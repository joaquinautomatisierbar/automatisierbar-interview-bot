# Workflow: LinkedIn Engagement Bot

> **Architektur-Update (Phase 2)**: Der Bot läuft **vollständig in n8n** ohne Render-Abhängigkeit. Die Render-Endpoints unter `/api/linkedin/*` existieren noch (Phase-1-Smoke-Tests, optional als Backup), werden aber vom Telegram-Bot nicht benutzt. Voice-Prompt ist im n8n-Code-Node embedded; Repo-Datei [`prompts/linkedin_voice.md`](../prompts/linkedin_voice.md) bleibt Master-Quelle für Reviews.
>
> **Importierbarer Workflow**: [`workflows/linkedin_engagement_bot.n8n.json`](linkedin_engagement_bot.n8n.json) — in n8n Cloud per "Import from File" laden.

## Objective

A Telegram bot that turns a LinkedIn post (text, forwarded message, or screenshot) into three substantive comment variants in Joaquin's voice — so the daily LinkedIn engagement ritual takes ~5 min instead of 15 min, and every interaction is logged to Notion for later review.

Kein Auto-Posting, kein Scraping. Der Bot ist Generator + Tracker. Joaquin postet weiterhin manuell — das ist Absicht (Authentizität, ToS, Account-Schutz).

## Bot Commands

| Command | Action |
|---------|--------|
| `/start` | Welcome + kurze Hilfe |
| `/k <text>` oder reiner Text | Generiere 3 Kommentar-Varianten zum gepasteten/geforwardeten Post |
| Photo (Screenshot) | Generiere 3 Varianten — Posttext wird via Vision aus dem Bild extrahiert |
| `/leads` | Top-20 Notion-Leads als Markdown-Liste mit LinkedIn-Suche-URLs |
| Inline-Button "✅ Gewählt: …" | Loggt die gewählte Variante in die LinkedIn Activity DB |

## Required Inputs

- `TELEGRAM_LINKEDIN_BOT_TOKEN` — neuer Bot-Token von @BotFather (n8n-Credential, NICHT in `.env` — wird in n8n cloud als Telegram-Credential "automatisierbar Outreach" gesetzt)
- `ANTHROPIC_API_KEY` — Render env (bereits gesetzt)
- `NOTION_API_KEY` — Render env (bereits gesetzt)
- `NOTION_DATABASE_ID` — Render env (Interview-DB für `/leads`)
- `NOTION_LINKEDIN_DB_ID` — **neu, muss nach DB-Erstellung in Render gesetzt werden**
- `PDF_API_KEY` — Render env (X-API-Key für alle `/api/linkedin/*` Endpoints)
- `RENDER_API_BASE` — z.B. `https://automatisierbar-pdf-api.onrender.com` (in n8n als Variable)

## Required Tools (alle bereits gebaut)

- [`tools/linkedin_comment_gen.py`](../tools/linkedin_comment_gen.py) — Anthropic-Call mit Voice-Prompt, Text + Vision
- [`tools/notion_linkedin.py`](../tools/notion_linkedin.py) — Top-20-Leads, Activity-Log, DB-Setup
- [`prompts/linkedin_voice.md`](../prompts/linkedin_voice.md) — System-Prompt mit Cases, Anti-Patterns, Output-Schema

## API Endpoints (alle in `api.py`)

Alle erfordern `X-API-Key: {{ $env.PDF_API_KEY }}` Header.

### `POST /api/linkedin/comments`
```json
// Request (text):
{ "post_text": "Volle Post-Text..." }

// Request (image):
{ "image_b64": "iVBOR...", "media_type": "image/jpeg" }

// Response:
{
  "post_summary": "...",
  "post_branche": "Recht",
  "comments": [
    {"variant": "Erfahrung", "text": "...", "skip_reason": null},
    {"variant": "Sicht", "text": "..."},
    {"variant": "Frage", "text": "..."}
  ]
}
```

### `GET /api/linkedin/leads-top20`
Response: `{ count, markdown, leads: [...] }`

### `POST /api/linkedin/log`
```json
{
  "typ": "Comment",
  "post_summary": "1-Liner",
  "branche": "Recht",
  "variant": "Erfahrung",
  "comment_text": "Der gewählte Kommentar...",
  "post_source": "https://linkedin.com/...",
  "outcome": "offen"
}
```

### `POST /api/linkedin/setup-db` (einmalig)
```json
{ "parent_page_id": "311bebb0-c2f9-80de-89a0-f3d463a0fbce" }
```
Response: `{ database_id: "..." }` — diesen Wert dann als `NOTION_LINKEDIN_DB_ID` in Render setzen.

## n8n Workflow: `automatisierbar_linkedin_bot`

### Node Flow

```
Telegram Trigger (Bot: automatisierbar Outreach)
    ↓
Switch (auf message/callback_query)
    ├─ callback_query                  → Handle Variant Choice
    │
    ├─ message.photo                   → Download Photo → Base64 → /comments → Render & Send
    │
    └─ message.text
         ├─ /start                     → Send Welcome
         ├─ /leads                     → /leads-top20 → Send Markdown
         └─ <text> oder /k <text>      → /comments → Render & Send
```

### Welcome-Message (auf `/start`)

```
Hi. Schick mir einen LinkedIn-Post — als Text, Forward oder Screenshot.
Ich gebe dir 3 Kommentar-Varianten in deiner Stimme zurück:
  • Erfahrung (mit konkretem Case)
  • Sicht (eigene Linse)
  • Frage (an den Author)

Befehle:
  /leads – Top-20 Notion-Leads für LinkedIn-Outreach
  /start – diese Hilfe
```

### Render & Send (nach Comment-Generierung)

Pro Variante eine separate Telegram-Message (1-Tap-Copy auf Mobile durch monospace + langes Drücken):

```
*🟢 Variante 1 — Erfahrung*

```
{variant.text}
```
```

(Markdown-V2 Parsemode. Der innere Code-Block sorgt dafür dass Long-Press → Copy in Telegram-Mobile sauber funktioniert.)

Wenn `text === null`: Variante NICHT senden, stattdessen kurz: `_⏭ Erfahrung übersprungen: {skip_reason}_`

Nach den 3 Messages eine **vierte Message mit Inline-Keyboard**:
```
Welche hast du verwendet?
[ ✅ Erfahrung ] [ ✅ Sicht ]
[ ✅ Frage ]    [ ⏭ keine ]
```

`callback_data` der 4 Buttons: `log:{variant}:{message_id}` (max 64 Bytes — `message_id` ist die ID der Welcome-Message, der State-Key in Static Data).

### Session State (n8n Static Data, keyed by `<chat_id>:<message_id>`)

```json
{
  "post_summary": "...",
  "post_branche": "Recht",
  "post_source": "",         // wenn URL erkennbar im Original-Text
  "variants": {
    "Erfahrung": "...",
    "Sicht": "...",
    "Frage": "..."
  }
}
```

Auf Callback `log:Erfahrung:42`:
1. Lookup `state[chat_id][42]`
2. POST `/api/linkedin/log` mit `variant`, `comment_text=state.variants[variant]`, `post_summary`, `branche`
3. answerCallbackQuery: "Geloggt ✅"
4. Optional: editMessageReplyMarkup um Buttons zu entfernen

State expiry: nach 24h löschen (cleanup im Trigger oder separater Schedule-Trigger).

### Photo Path Detail

Bei `message.photo`:
1. Telegram-Trigger gibt `photo[]` (verschiedene Auflösungen). Nimm die grösste (`photo[-1].file_id`).
2. Telegram-Node `getFile(file_id)` → `file_path`
3. HTTP-Request `GET https://api.telegram.org/file/bot{TOKEN}/{file_path}` → Binary
4. Code-Node: Buffer → Base64
5. POST `/api/linkedin/comments` mit `{image_b64, media_type: "image/jpeg"}`
6. Weiter wie Text-Pfad

**Optimierung**: Wenn das Bild >5 MB ist, vorher mit Sharp-Node oder per Code resizen — Anthropic-API erwartet sinnvoll-grosse Bilder.

### Text Pfad — Command-Parsing

Erste Zeile prüfen:
- Beginnt mit `/start` → Welcome
- Beginnt mit `/leads` → Leads-Pfad
- Beginnt mit `/k ` → strip prefix, rest als post_text
- Sonst: ganzer Message-Text als post_text

Wenn post_text < 30 Zeichen: kurze Hilfe statt Generierung ("Schick mir einen Post (mind. 30 Zeichen) oder ein Screenshot.")

## One-Time Setup Checklist

- [ ] Bot via @BotFather erstellen, Token kopieren
- [ ] In n8n Cloud: Telegram-Credential "automatisierbar Outreach" anlegen mit dem Token
- [ ] In Render: PDF API redeployen (Code-Änderungen in `api.py` greifen erst nach Deploy)
- [ ] LinkedIn Activity DB erstellen: `curl -X POST $RENDER_API_BASE/api/linkedin/setup-db -H "X-API-Key: $PDF_API_KEY" -H "Content-Type: application/json" -d '{"parent_page_id":"311bebb0c2f980de89a0f3d463a0fbce"}'`
- [ ] DB-ID aus Response → in Render als `NOTION_LINKEDIN_DB_ID` setzen → Redeploy
- [ ] In Notion: Workspace-Member hinzufügen für die neue DB (Notion-Integration braucht Page-Access — Parent-Page sollte bereits Integration-Access haben, dann erbt die DB diesen)
- [ ] n8n Workflow erstellen nach Node-Flow oben
- [ ] Smoke-Test: 1 echter Post als Text durchschicken

## Error Handling

| Error | Recovery |
|-------|----------|
| `/api/linkedin/comments` 5xx | Reply: "Generator gerade nicht erreichbar — kurz warten und nochmal." |
| Image >20 MB (Telegram-Limit) | Fängt Telegram bereits ab; bot reagiert nur auf valide photo-Messages |
| Claude liefert kein valides JSON | API-Endpoint catched + 500. Bot zeigt: "Konnte den Post nicht parsen, paste den Text mal direkt." |
| Notion-Log fehlt (DB-ID nicht gesetzt) | Bot zeigt "Logging übersprungen (DB nicht konfiguriert)" — Generator funktioniert trotzdem |
| User klickt "Gewählt"-Button mehrfach | answerCallbackQuery mit `"already logged"` (idempotency-flag im State) |

## Edge Cases

- **Englischer Post**: Voice-Prompt instruiert Claude auf Englisch zu antworten. Logging-Branche fällt auf "Andere".
- **Sehr kurzer Post (<30 Zeichen)**: Bot antwortet mit Hilfe-Text, ruft Generator nicht.
- **Mehrere Bilder im Burst**: jeder Photo-Update separat behandeln, drei separate Generierungen.
- **Forward von Channel-Post**: Telegram zeigt forward header. Im Generator nur den eigentlichen Text relevant — Header rausstrippen wenn erkennbar (Code-Node mit Regex).
- **Post mit eingebettetem Link**: URL wird als `post_source` extrahiert (regex `https?://\S+`) und im Log mitgeführt.

## Testing

1. Send `/start` → Welcome-Message
2. Paste deutscher KMU-Post (Personalmangel-Thema) → erwarte 3 unterschiedliche Varianten, Erfahrung referenziert Bieri/Gränacher/Interview-App
3. Paste Post zu völlig themenfremdem Inhalt (z.B. Marathon-Training) → erwarte: Erfahrung-Variante = `null`, Sicht und Frage gefüllt
4. Paste-Test mit verbotenem Buzzword im Original-Post — eigener Kommentar darf das Buzzword NICHT übernehmen
5. Screenshot eines deutschen LinkedIn-Posts → erwarte korrekt extrahierter Text + 3 Varianten
6. `/leads` → Liste mit klickbaren LinkedIn-Suche-URLs, Top-Branchen (Recht/Treuhand/Immobilien) zuerst
7. Inline-Button "✅ Sicht" klicken → Notion-DB hat einen neuen Eintrag, callback-toast zeigt "Geloggt ✅"
8. Bei `text: null` für Erfahrung → entsprechende Telegram-Message zeigt "⏭ Erfahrung übersprungen"

## Known Constraints

- **n8n Static Data Lifecycle**: State pro `<chat_id>:<message_id>` lebt bis zum nächsten Workflow-Redeploy. Für die Use Case (Click innerhalb von Sekunden bis Minuten) reicht das. Bei Redeploy mitten in einer Session: Click loggt nicht, aber Bot crasht nicht.
- **LinkedIn-Suche-URLs**: führen zur Personensuche mit Stichwort `Inhaber <Firma>`. Bei einigen Firmen-Namen (zu generisch) zeigt LinkedIn keine eindeutigen Treffer — manuelle Verfeinerung notwendig.
- **Voice-Drift**: Nach 4 Wochen die Notion-Daten reviewen — wenn eine Variante nie gewählt wird, Voice-Prompt entsprechend anpassen (z.B. Frage-Format unbeliebt → schärferes Frage-Pattern erzwingen).
- **Case-Pool**: Aktuell 3 Cases im Voice-Prompt. Sobald ein vierter echter Case mit Zahlen verfügbar ist → in `prompts/linkedin_voice.md` ergänzen.
