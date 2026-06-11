---
autonomy-level: L3
bike-method-phase: 1
kpi-bucket: more-customers
kpi-metric: transcripts processed per week (target: ≥5/wk feeding Workflow A) + transcription error rate (target: <5%)
---

# Audio to Transcript (Workflow C)

**Pipeline-Eingang.** Konvertiert Cold-Call-Audio (Schwizerdütsch m4a) → Schweizer-Hochdeutsch-Transkript via Gemini, schreibt .txt in Transcripts-Drive-Folder. Triggert dann Workflow A automatisch.

| ID | Name | Trigger |
|---|---|---|
| **C** (`dF9cJVYfT10G2ZXr`) | Cold Call — Audio to Transcript | Drive fileCreated (Audiofiles Training folder) |

## Pipeline

```
Drive Trigger (folder: 1cxOnhZH0T_JaFmHhqjBQEj-88MHf4K-k)
  → Filter Audio Files (mime starts with audio/* OR ext in {m4a,mp3,wav,ogg,flac})
  → Drive Download Audio
  → Code: Parse Audio Filename
       (extract Firmenname, interviewer suffix, base64 encode audio)
  → HTTP Gemini: Transcribe (gemini-2.5-flash, inline audio, German prompt with Sprecher-Labels)
  → Code: Parse Gemini Response (extract transcript_text)
  → IF Transcription OK?
     ├── TRUE → Drive: Upload Transcript (.txt to Transcripts folder)
     └── FALSE → Telegram: Transcription Error
```

## Inputs

**Audio-File-Convention** (von Nico):
- `<Firmenname>__<nico|joaquin|tej|patrik>.m4a` (Suffix erforderlich für korrekte Interviewer-Attribution)
- Andere Extensions: `.mp3`, `.wav`, `.ogg`, `.flac` auch supportet
- Ohne Suffix: default = nico (matches A1/A2 backfill convention)

**Folder**:
- Audio-Source: `1cxOnhZH0T_JaFmHhqjBQEj-88MHf4K-k` (Audiofiles Training)
- Transcript-Target: `1PJUP0AOlU3SyT0NZF9_rzKfx19tRTVJh` (Transcripts)

## Output

`<Firmenname>__<interviewer>.m4a_<YYYYMMDD-HHMMSS>.txt` in Transcripts folder.

Workflow A picks it up automatically (Drive fileCreated trigger).

## Gemini API Call

```
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent
Header: x-goog-api-key: <KEY>
Body: {
  contents: [{
    parts: [
      { text: "<TRANSCRIBE_PROMPT>" },
      { inline_data: { mime_type: "audio/mp4", data: "<base64>" } }
    ]
  }],
  generation_config: { temperature: 0.0, max_output_tokens: 8192 }
}
```

### Transcribe Prompt (DE)

> Transkribiere diese Schweizer-Cold-Call-Aufnahme wörtlich. Markiere Sprecher: 'Sprecher A' = unser Team, 'Sprecher B' = Kunde. Bei Schwizerdütsch: ins Hochdeutsche übersetzen aber Slang/Dialekt beibehalten wenn relevant. Format: 'Sprecher A: ...' / 'Sprecher B: ...' jeweils auf neuer Zeile, leere Zeile zwischen Sprecherwechseln. Keine Zeitstempel, keine Kommentare — nur das Transkript.

## Audio Size Limits

- **Inline**: ~20MB (base64-encoded fits in HTTP body without multipart)
- **>20MB**: Use Gemini Files API resumable upload (nicht implementiert v1)
- Typische Cold-Call-Aufnahme (5min m4a): 3-5MB → inline OK

## Credentials

- `Google Drive account` (auto-assigned, 3 Drive nodes)
- `Gemini Header Auth` (manual: HTTP Header Auth, `x-goog-api-key` = Gemini API key from .env)
- `Cold Call Bot` (Telegram for error alerts — manual switch nach create)

## Halt-Conditions

Activation = halt (kann jederzeit feuern wenn Audio uploaded → schreibt echte Drive-Files + spendet API-Credits). User aktiviert manuell.

## Verification

1. Logic-Smoketest: execution 786 (pinned audio metadata + fake Gemini response → 'Filter Audio Files' + 'Parse Gemini Response' + 'Transcription OK?' all green)
2. Real-Run: nach activation, audio file in Audiofiles Training uploaden → in 60-90s sollte .txt in Transcripts erscheinen
3. End-to-End: Workflow A picks up the new .txt → klassifiziert → Notion-Updates (~2 min total)

## Error Handling

- Gemini error → caught in Parse Gemini Response → Telegram alert with file + error
- Empty transcript → Telegram alert
- Drive upload fail → n8n execution-fail (visible in n8n executions tab)

## Known Issues / TODOs

- **Audio >20MB**: not supported v1 (need Files API resumable upload)
- **Multi-language**: only German prompt; if French/Italian audio, results unreliable
- **Cost**: ~$0.001 per minute of audio (Gemini 2.5 Flash). For 100 calls/week × 5min avg = $0.50/week. Acceptable.
- **No idempotency check** in C (unlike A2). If same audio file is re-uploaded with different ID, you get a second transcript. Workflow A handles this via its own idempotency.

## Related

- Downstream: Workflow A (auto-classifies the new .txt)
- Memory: `~/.claude/projects/.../memory/project_call_analytics_pipeline.md`
