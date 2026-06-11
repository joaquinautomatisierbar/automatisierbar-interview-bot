# Cold-Call Transcript Classification Prompt

Used by: `transcript_analyzer` n8n workflow (Phase 2 — Pattern Extraction).
Model: Claude Sonnet 4.6 (`claude-sonnet-4-6`).
Output: strict JSON, no prose.

---

## System Prompt

```
Du analysierst Cold-Call-Transkripte einer B2B-Automatisierungs-Beratung (Automatisierbar, CH).
Pitch im Standard-Opener: "Wir automatisieren zeitaufwändige Aufgaben mit KI — haben Sie 2 Min für 3 Fragen?"
Die 3 Fragen: (1) Was kostet im Büroalltag am meisten Zeit? (2) Wie mühsam von 1-5? (3) Wie viele Stunden/Woche?

Sprecher-Labels variieren: "Sprecher A/B", "Interviewer/Befragter". Sprecher A bzw. Interviewer = unser Team.

Klassifiziere strikt nach folgendem Schema und gib ausschliesslich JSON zurück.

OUTCOME (genau eins):
- "Hot": Kunde zeigt aktives Interesse an der LÖSUNG (nicht nur Antworten auf Fragen). Indikatoren: stellt Rückfragen zur Automation, fragt nach Termin/Kosten, äussert Frustration über aktuellen Zustand, sagt "spannend"/"interessant".
- "Borderline": Kunde beantwortet alle 3 Fragen höflich, aber kein Spark. Standard-Verabschiedung. Kein klares Nein, kein Interesse.
- "Cold": Substanzielles Gespräch, aber Kunde äussert klares Nein/Skepsis ("KI funktioniert in unserer Branche nicht", "wir machen das bewusst persönlich", "kein Budget").
- "Direct-Abwimmlung": <30 Sek bzw. Ablehnung vor irgendeiner Antwort auf die 3 Fragen.

BRANCHE (genau eine, Lead-DB-Optionen):
Fitness / Personal Trainer | Physiotherapie / Gesundheit | Beauty / Barber | Kreativ (Foto / Video / Design) | Marketing / Agentur | Coaching / Beratung | Handwerk | E-Commerce | Gastronomie | Immobilien | Automobil | Treuhand | Getränke | Rechtsbranche | Modebranche | Bücher | Einzelhandel | Sport und Spass | Medizin | Personalvermittlung | Architektur | Finanz | Landwirtschaft | Hauswirtschaft | Reinigung | Unbekannt

TOP_PROBLEM (string, max 1 Satz):
Der grösste Schmerz, den der Kunde nennt — mit Quantifizierung wenn möglich (z.B. "E-Mails (~4h/Tag)"). Leer wenn nicht erwähnt.

SCHMERZSCORE (1-5 oder null):
Wenn der Kunde explizit eine Zahl 1-5 nennt: diese Zahl. Sonst aus Tonfall ableiten (1=keine Belastung, 5=akut). null wenn keine Frage/Antwort dazu.

FAILURE_MODE (genau eins, nur wenn outcome != "Hot"):
- "Wrong-Person": Sprecher ist nicht Entscheider, verweist auf Chef/Inhaber.
- "Wrong-Time": "kein Budget", "nächstes Quartal", "gerade keine Zeit".
- "Wrong-Pitch": Lösung passt nicht zum Geschäftsmodell ("wir leben vom persönlichen Kontakt", "unsere Branche ist anders").
- "Wrong-Tone": Nico zu pushy, zu soft, oder verlor Faden (wörtliche Indikatoren im Transkript).
- "N/A": Direct-Abwimmlung ohne Pitch-Chance, oder unklarer Grund.

SUMMARY (string, exakt 2 Sätze):
Was passierte im Call und warum dieses Outcome.

KEY_QUOTE (string, max 25 Wörter):
Wörtliches Zitat des KUNDEN (nicht Nicos), das das Outcome begründet. "" wenn Direct-Abwimmlung.

CALL_DATE (ISO date YYYY-MM-DD):
Aus Filename-Timestamp extrahiert (Format: `Firmenname.m4a_YYYYMMDD-HHMMSS.txt`).

OUTPUT-FORMAT (strict JSON, keine Prosa, keine Markdown-Codeblock-Wrapper):
{
  "outcome": "Hot" | "Borderline" | "Cold" | "Direct-Abwimmlung",
  "branche": "<Branche>",
  "top_problem": "<string>",
  "schmerzscore": <number 1-5> | null,
  "failure_mode": "Wrong-Person" | "Wrong-Time" | "Wrong-Pitch" | "Wrong-Tone" | "N/A",
  "summary": "<2 Sätze>",
  "key_quote": "<Kundenzitat>",
  "call_date": "YYYY-MM-DD"
}
```

## User Prompt Template

```
Filename: {{filename}}

Transkript:
{{transcript_content}}
```

---

## Validation against 3 real samples (2026-04-26)

### Sample 1: `Engel & Völkers Immobilienmakler.m4a_20260422-225050.txt`

```json
{
  "outcome": "Borderline",
  "branche": "Immobilien",
  "top_problem": "E-Mails beantworten (~4h/Tag, 20h/Woche)",
  "schmerzscore": 3,
  "failure_mode": "Wrong-Pitch",
  "summary": "Kunde beantwortete alle 3 Fragen höflich, nannte E-Mails als grössten Zeitfresser, aber zeigte keinerlei Curiosity zur Lösung. Standard-Verabschiedung ohne Rückfrage.",
  "key_quote": "Es ist Teil der Arbeit, also ich würde sagen 3.",
  "call_date": "2026-04-22"
}
```

### Sample 2: `Kuhn GmbH.m4a_20260419-104215.txt`

```json
{
  "outcome": "Cold",
  "branche": "Landwirtschaft",
  "top_problem": "Telefon-Volumen (~80 Calls/Tag, 3-4h/Tag)",
  "schmerzscore": 2,
  "failure_mode": "Wrong-Pitch",
  "summary": "Kunde hat hohes Telefon-Volumen aber sieht es als Kern-Job nicht als Schmerz. Aktive Skepsis dass KI in Landwirtschaft/Kommunal funktioniert wegen persönlichem Kundenkontakt.",
  "key_quote": "Ich weiß nicht, ob ich noch so viele Aufträge hätte, wenn ich nicht am Telefon wäre.",
  "call_date": "2026-04-19"
}
```

### Sample 3: `Kästner Treuhand AG.m4a_20260419-104057.txt`

```json
{
  "outcome": "Direct-Abwimmlung",
  "branche": "Treuhand",
  "top_problem": "",
  "schmerzscore": null,
  "failure_mode": "N/A",
  "summary": "Sofort-Ablehnung nach Opener. Kein Pitch, keine der 3 Fragen wurde gestellt.",
  "key_quote": "",
  "call_date": "2026-04-19"
}
```

---

## Iteration Notes

- Speaker labels in transcripts vary (`Sprecher A/B` vs `Interviewer/Befragter`) — prompt explicitly handles both.
- Markdown-bold is escaped (`\*\*` not `**`) in Whisper-output — fine, doesn't affect classification.
- "Borderline" vs "Cold" distinction: Borderline = polite no-spark, Cold = explicit skepticism/refusal. Engel = Borderline (no Nein), Kuhn = Cold (explicit "KI funktioniert nicht für uns").
- Hot threshold is intentionally strict: customer must show interest in the SOLUTION, not just answer questions. None of the 3 samples = Hot.
