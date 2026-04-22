# Workflow: automatisierbar Interview Bot

## Objective
A Telegram bot that covers two phases of the client automation discovery process:
1. **Phase 1 — Discovery**: Takes a problem description, asks clarifying questions if needed, generates a branded "Bedarfsanalyse" PDF with all questions required to build the automation.
2. **Phase 2 — Gap Analysis**: Accepts answered questions (PDF, photo, or text), extracts the answers, identifies gaps, and generates a "Weiterführende Fragen" PDF so no further client contact is needed during the build.

## Bot Commands
| Command | Action |
|---------|--------|
| `/start` or `/neu` | Reset session and prompt for problem description |
| `/antworten` | Signal that you're submitting answered questions (switches to Phase 2) |
| Send text | Phase 1: describes/clarifies the problem |
| Send PDF document | Auto-triggers Phase 2 (answer analysis) |
| Send photo | Auto-triggers Phase 2 (vision OCR → answer analysis) |

## Required Inputs
- `TELEGRAM_BOT_TOKEN` — set in `.env`
- `ANTHROPIC_API_KEY` — set in `.env`
- `N8N_EXECUTIONS_BASE_URL` — for the n8n Execute Command node (set in n8n env)

## Required Tools
- `tools/generate_pdf.py` — branded PDF generator (requires: `pip3 install reportlab`)
- `tools/extract_pdf_text.py` — PDF text extractor (requires: `pip3 install pymupdf`)

## n8n Workflow: `automatisierbar_interview_bot`

### Node Flow

```
Telegram Trigger
    ↓
Router (Switch)
    ├─ /neu or /start      → Reset State → Ask for Problem
    ├─ /antworten          → Set Phase=analysis → Ask to send answers
    ├─ Document (PDF)      → Download File → Extract Text → Phase 2 Analysis
    ├─ Photo               → Download File → Claude Vision Extract → Phase 2 Analysis
    └─ Text message        → Load State → Route by Phase
                               ├─ Phase: discovery  → Context Evaluator → [ask OR generate PDF]
                               └─ Phase: analysis   → Gap Analyzer → Generate PDF
```

### Session State (n8n Static Data, keyed by chat_id)
```json
{
  "phase": "discovery",
  "history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ],
  "original_questions": { "Prozess": [...], ... }
}
```

### Phase 1 — Context Evaluator (Claude)
**System prompt:**
```
Du bist der KI-Assistent von automatisierbar.ch, einer Schweizer Automatisierungsberatung.
Deine Aufgabe ist es, Discovery-Fragen für den Aufbau einer n8n-Automatisierung zu generieren.

Analysiere die Problembeschreibung des Klienten. Wenn du nicht genug Kontext hast, stelle EINE
einzige Klärungsfrage auf Deutsch. Wenn du genug Kontext hast, generiere strukturierte Fragen.

Antworte IMMER als JSON:
{
  "sufficient": true/false,
  "clarifying_question": "...",  // nur wenn sufficient=false
  "questions": {                 // nur wenn sufficient=true
    "Prozess": ["...", "..."],
    "Daten": ["..."],
    "Systeme": ["..."],
    "Zuständigkeiten": ["..."],
    "Ausnahmen": ["..."],
    "Erfolg": ["..."]
  }
}

Generiere 2-4 Fragen pro Kategorie. Fragen müssen so spezifisch sein, dass ein Entwickler
ohne Rückfragen sofort mit dem Aufbau der Automatisierung beginnen kann.
```

### Phase 2 — Gap Analyzer (Claude)
**System prompt:**
```
Du bist der KI-Assistent von automatisierbar.ch. Du analysierst die Antworten eines Klienten
auf Discovery-Fragen für eine n8n-Automatisierung.

Identifiziere:
1. Fragen die nicht beantwortet wurden
2. Antworten die zu vage sind für den Build
3. Neue Unbekannte die sich aus den Antworten ergeben

Generiere Folgefragen, die alle Lücken schließen. Ein Entwickler soll nach diesen Antworten
KEINE weitere Kommunikation mit dem Klienten brauchen.

Antworte als JSON:
{
  "questions": {
    "Offene Punkte": ["..."],
    "Technische Details": ["..."],
    "Randbedingungen": ["..."]
  }
}

Wenn alle Fragen vollständig beantwortet wurden und keine Lücken bestehen:
{
  "questions": {},
  "complete": true,
  "summary": "Alle notwendigen Informationen sind vorhanden..."
}
```

### PDF Generation (Execute Command node)
```bash
python3 /path/to/tools/generate_pdf.py '<json_payload>'
```
Returns the absolute file path of the generated PDF. n8n then reads the file and sends it via Telegram.

### Vision Extraction (Anthropic API HTTP Request)
For photo messages, use the Anthropic Messages API with vision:
```
POST https://api.anthropic.com/v1/messages
Headers: x-api-key: {{ $env.ANTHROPIC_API_KEY }}
Body: {
  "model": "claude-opus-4-7",
  "max_tokens": 2000,
  "messages": [{
    "role": "user",
    "content": [
      { "type": "image", "source": { "type": "base64", "media_type": "image/jpeg", "data": "..." } },
      { "type": "text", "text": "Extrahiere den vollständigen Text aus diesem Bild. Behalte die originale Struktur bei." }
    ]
  }]
}
```

## Error Handling
| Error | Recovery |
|-------|----------|
| PDF generation fails | Reply: "PDF-Generierung fehlgeschlagen. Bitte erneut versuchen." — log error |
| Vision extraction fails | Ask user to paste text manually |
| Claude API timeout | Retry once, then reply with error message |
| Empty answers submitted | Reply: "Das Dokument scheint leer zu sein. Bitte als Text einfügen." |

## Edge Cases
- **Very long problem** (>1000 chars): Summarize before sending to Claude
- **Multiple photos**: Process each separately, combine extracted text
- **Non-PDF document**: Attempt text extraction; if fails, ask user to paste as text
- **User sends new problem after Phase 1**: `/neu` resets state cleanly
- **Answers submitted before questions**: Bot replies explaining Phase 1 must come first

## Testing
1. Send `/neu` → confirm: "Beschreibe das Hauptproblem des Klienten."
2. Send vague problem → confirm: bot asks ONE clarifying question
3. Send clear problem → confirm: bot sends `bedarfsanalyse_*.pdf`
4. Send answered PDF → confirm: bot sends `weiterfuehrende_fragen_*.pdf`
5. Send photo of handwritten answers → confirm: vision extraction + followup PDF

## Known Constraints
- n8n Static Data is shared across workflow executions — concurrent chats for different
  users are isolated by `chat_id` key, but the state resets if the workflow is redeployed.
  For production with many users, migrate state to an external store (Airtable, Supabase).
- PDF generation takes ~1-2 seconds locally. Send a "Wird generiert..." message first.
- WeasyPrint requires arm64 Python + Homebrew on Apple Silicon.
  Current setup uses ReportLab (pure Python, no system deps).
