# Template: Vorab-Mail an Rolf Schmid (Agenda 5.8.)

> **REVIEW-FASSUNG (finalisiert 10.7.). Versand erst nach Review durch Joaquin + Nico und Halt-Gate (Kundenkontakt!).**
> Ziel-Versand: bis 22.7.2026, von einer persönlichen Adresse (nico@ oder joaquin@), nicht von info@.
> Zweck: Termin professionell rahmen, Teilnehmer klären, Hauswartungs-Besichtigung sichern, Vorab-Fragebogen platzieren.
> Stand Tool: **Kunden-Vorab-Seite ist LIVE und getestet (10.7.)**, Link unten ist der echte. Entscheid "Intern + Vorab-Option" (Joaquin, 10.7.) heisst: Link kommt mit, sofern das Review nichts anderes ergibt.

## Mail-Entwurf

**An:** Rolf H. Schmid
**CC:** Mirjam Böni
**Betreff:** Termin 5. August: Vorschlag für den Ablauf

Sehr geehrter Herr Schmid, sehr geehrte Frau Böni

Vielen Dank für Ihre Anfrage zur Digitalisierung Ihres Order2Cash-Prozesses und für den Termin am **Mittwoch, 5. August 2026** bei Ihnen in Solothurn. Wir freuen uns darauf, Ihre Abläufe kennenzulernen.

Damit der Termin für Sie maximal ergiebig wird, schlagen wir folgenden Ablauf vor (ca. 90 bis 120 Minuten):

1. **Kurzvorstellung Automatisierbar** (10 Min.): wer wir sind, wie wir arbeiten, Beispiele aus laufenden Projekten
2. **Live-Einblick** (15 Min.): wir zeigen Ihnen an unseren eigenen Systemen, wie Auftragsplattform und mobile Erfassung in der Praxis aussehen
3. **Ihre Prozesse im Detail** (60 Min.): vom Auftragseingang über die Hauswartung bis zur Verrechnung in pebeFinance; hier stellen wir strukturiert Fragen, damit unsere Offerte präzise auf Sie passt
4. **Weiteres Vorgehen** (10 Min.): offene Punkte, Zeitplan, nächste Schritte

Drei Bitten vorab:

- Falls möglich, würden wir gerne **kurz die Hauswartung in Aktion sehen** oder mit Herrn Kunz sprechen: die mobile Lösung für Ihr Team vor Ort ist ein Kernstück der Ausschreibung, und wir möchten sie für die echten Abläufe bauen, nicht für die Theorie.
- Es hilft uns zu wissen, **wer von Ihrer Seite am Termin dabei ist**, damit wir die Inhalte passend gewichten.
- Unter folgendem Link finden Sie **zehn kurze Vorab-Fragen** (ca. 10 Minuten). Was Sie dort bereits beantworten, müssen wir am Termin nicht mehr abfragen, so bleibt mehr Zeit für das Wesentliche. Ihre Angaben speichern sich automatisch, Sie können jederzeit unterbrechen und später weitermachen:
  `https://cockpit.automatisierbar.ch/vrv/kunde?k=Y-nEjyA6pcjrL-Qo9DqvZ-it`
  (in der Mail als klickbaren Link einfügen, nichts direkt dahinter anhängen, sonst bricht der Zugangsschlüssel)

Von unserer Seite nehmen [ANZAHL] Personen teil: [NAMEN + ROLLEN gemäss Entscheid 4.2; Vorschlag: "Nico (Gesprächsführung), Joaquin (Architektur und Technik), Tej (Demo)"; Nachnamen ergänzen!].

Freundliche Grüsse
[NAME]
Automatisierbar, [Signatur]

## Checkliste vor Versand (Halt-Gate)

- [x] Tool v2 live und Link getestet? **Ja, 10.7.: Seite live, Autosave verifiziert, Isolation getestet (Kunde sieht nur die 10 Fragen, keine internen Felder)**
- [ ] Teilnehmer + Rollen final entschieden (WS4.2)? Sonst Satz auf "wir kommen zu dritt" vereinfachen und Namen weglassen
- [ ] Absender-Adresse und Signatur (mit Nachnamen!) korrekt?
- [ ] Nico-Review erfolgt?
- [ ] Joaquin-Review erfolgt?
- [ ] Halt-Gate: `bash .claude/hooks/notify-telegram.sh halt "Vorab-Mail an Schmid bereit zum Versand, ok?"` bestätigt?
- [ ] Nach Versand: TASKS.md 4.1 auf erledigt, Antwort-Eingang beobachten; beantwortet Schmid die Vorab-Fragen, erscheinen sie intern als "Vorab vom Kunden"
