# Workflow-Interview — Discovery-Leitfaden (20–30 Min)

> Was du im gebuchten Termin machst. Ziel: genug **Schmerz + Prozess-Detail**, dass wir innert 72 h einen gratis Prototyp bauen können — UND emotionaler Buy-in. Geerdet auf das 9-Step Discovery (*ACQ Closer Handbook*) + den bestehenden Web-Interview-Bot (`workflows/web_interview_bot.md`).

## Mindset

- **Rede nicht über Technik.** Kein „n8n", „API", „KI-Agent". Du redest über SEINEN Montagmorgen.
- **Ziehe den emotionalen Schmerz** (Wochenend-Arbeit, Fehler-Angst), nicht nur die Fakten. „Pulling Teeth."
- **Give Away the Farm:** der gratis 2-Wochen-Pilot ist das Grand Slam Offer — er eliminiert jedes Risiko für den skeptischen Schweizer KMU-Inhaber.

## Ablauf

### 1. Rahmen setzen (1 Min)
> „Danke, dass Sie sich die Zeit nehmen. Plan ist: ich stell Ihnen ein paar Fragen zu dem Prozess, dann verstehe ich's gut genug, um Ihnen in den nächsten Tagen gratis was zu bauen, das Sie zwei Wochen testen können. Passt das?"

### 2. Pain-Cycle — pro Problem die 9 Schritte (*ACQ Closer Handbook*)

| Schritt | Frage |
|---|---|
| Current | „Erzählen Sie mir den Prozess — wie läuft das heute ab?" |
| Desired | „Und wie sollte es idealerweise laufen?" |
| Obstacle | „Was ist das Mühsamste daran?" |
| Reason | „Warum? Haben Sie ein konkretes Beispiel von letzter Woche?" |
| **Pull Teeth** | „Erzählen Sie mir mehr… wie sieht das an einem normalen Tag aus?" |
| Recap | „Also: [Schmerz] kostet Sie [X Std], läuft von Hand…" |
| Label | „Das ist im Grunde ein [Prozess]-Thema." |
| Confirm | „Stimmt das so?" |
| Repeat | „Was ist das **nächst**grösste Zeitfresser-Thema?" |

### 3. Die drei „Zähne-zieh"-Kernfragen (immer stellen)
1. „Wie viele **Stunden pro Woche** gehen da drauf — und wer macht das?"
2. „Was passiert, wenn das mal **NICHT** rechtzeitig erledigt ist?" (→ emotionale Konsequenz)
3. „Wenn das morgen weg wäre — was würden Sie mit der Zeit machen?"

### 4. Quantifizieren (für den ROI + spätere Proof-Story)
- Std/Woche × Stundensatz (intern grob CHF 40–80/Std) → **CHF/Monat** Kosten des Ist-Zustands.
- Fehler-/Verzugskosten? (Mahnungen, verlorene Kunden, Nacharbeit.)
- Diese Zahl ist später euer Hook-Treibstoff („Frau X tippt 4 Std/Woche Rechnungen ab = ~CHF 700/Monat").

### 5. Prozess mappen (die 5 Elemente — damit der Build zero-followup ist)
Trigger · Datenquellen · Schritte/Transformationen · Entscheidungspunkte · Ziel/Output.
→ Am einfachsten **live im Web-Interview-Bot** (`automatisierbar-interview-bot.onrender.com`) erfassen: er extrahiert die Prozess-Map + generiert den Build-Prompt automatisch. Sonst Stichworte notieren.

### 6. Nächsten Schritt fixieren (BAMFAM, wieder)
> „Super, das reicht mir. Ich bau Ihnen das bis [konkreter Tag] und wir schauen's zusammen an — passt [Tag/Zeit] für die Präsentation?"

→ **Verlasse auch dieses Meeting mit einem nächsten Termin.** Setz `War-Room Status = ● BAMFAM` und Pipeline Stage entsprechend hoch.

## Anti-Patterns
- Über Technik/Tools reden statt über seinen Schmerz.
- Den Prozess nur halb verstehen → führt zu Rückfragen beim Build (Ziel: **zero followup**).
- Kein nächster Termin → Lead kühlt aus.
- Den Gratis-Pilot „verkaufen" statt ihn einfach anzubieten.

→ Cold-Call davor: [cold_call_script.md](cold_call_script.md) · Roadmap: [README.md](README.md)
