# Projekthandbuch-Vorlagen (PL-Werkzeugkasten)

> Folgearbeit aus Modul 5 (dort §2: "Vorlagen entstehen aus diesem Modul"), geführt als Task 5.6. Doppelter Zweck:
> 1. **Arbeitswerkzeug** ab Phase 1 jedes Kundenprojekts, erster Einsatz vRv.
> 2. **Beweismaterial in der Offerte** (Kap. 11 Projektorganisation): Ein Muster-Statusreport und ein CR-Formular im Anhang zeigen, dass "Projekthandbuch" bei uns keine Floskel ist.
>
> Verwendung: pro Projekt kopieren und füllen, Vorlagen bleiben unverändert. **Team-Durchsicht in S6** (10 min, Joaquin führt), danach gilt der Kasten als Standard.

---

## 0. Übersicht: sechs Artefakte, nicht mehr

| # | Artefakt | Rhythmus | Führt | Geht an |
|---|---|---|---|---|
| 1 | Projektplan | wöchentlich nachgeführt | PL | Kunde, via Statusreport |
| 2 | Statusreport | wöchentlich, genau eine Seite | PL | Ansprechpartner Kunde |
| 3 | Entscheidungs-Log | laufend | PL | geteilt, Kunde kann jederzeit einsehen |
| 4 | RACI-Tabelle | bei Projektstart, bei Scope-Änderung | PL | Offerte/Vertragsbestandteil |
| 5 | Change-Request-Formular | je Änderungswunsch | beide Seiten | Anhang zum Entscheidungs-Log |
| 6 | Abnahmeprotokoll | je Phase/Etappe | PL + Kunde | vertragsrelevant, beidseitig visiert |

Regeln aus Modul 5: Mehr Papier wäre Theater, weniger wäre fahrlässig. Ein benannter Gründer führt das Projekt, mit Stellvertretung; der Kunde hat genau einen Ansprechpartner.

---

## 1. Projektplan (Meilenstein-Gerüst)

```text
PROJEKTPLAN [Projektname] · Stand [Datum] · PL: [Name] · Stv: [Name]

Phase [1 Detailkonzept / 2 Pilot / 3 Rollout + Betrieb] · Preisform: [Festpreis / Kostendach / Pauschale]
```

| Nr | Meilenstein | geplant | neu geplant | Status | hängt ab von | Bemerkung |
|---|---|---|---|---|---|---|
| M1 | Kickoff + Zugänge/Ansprechpartner bestätigt | | | | Vertragsstart | |
| M2 | [z.B. Ist-Prozesse dokumentiert + reviewt] | | | | M1 | kritischer Pfad |
| M3 | [z.B. pebe-Formatklärung schriftlich] | | | | M1 | extern: pebe AG |
| M4 | Phasen-Abnahme (Protokoll, Artefakt 6) | | | | M2, M3 | Gate: Kunde entscheidet über nächste Phase |

**Pflegeregeln:** Nur Meilensteine mit Abnahme- oder Entscheid-Charakter, keine Aufgabenliste. Kritischen Pfad markieren. Ein Datum ändert sich nie stillschweigend: neue Spalte "neu geplant" füllen und im nächsten Statusreport unter Risiken begründen.

---

## 2. Wöchentlicher Statusreport (eine Seite, nie mehr)

```text
STATUSREPORT [Projektname] · Woche [KW/Datum] · Gesamtampel: [GRÜN/GELB/ROT]

Ampel-Definition: GRÜN = Plan hält · GELB = Risiko erkannt, Gegenmassnahme läuft ·
ROT = Meilenstein in Gefahr, Entscheid oder Eingriff nötig
```

**1. Erledigt seit letztem Report** (max. 5 Punkte, Ergebnis statt Tätigkeit)

- …

**2. Nächste Schritte bis zum nächsten Report** (max. 5, mit "wer")

- …

**3. Risiken**

| Risiko | Ampel | Gegenmassnahme |
|---|---|---|
| | | |

**4. Entscheide, die wir von Ihnen brauchen** (der wichtigste Block des Reports)

| Entscheid | Entscheidungsgrundlage | Frist | Wirkung, wenn offen |
|---|---|---|---|
| | | | |

**5. Ohne Verrechnung erledigt** (Kulanz sichtbar machen, Modul 5 §4)

- …

```text
Aufwandstand Phase: [x] von [Budget] Stunden/CHF · Termin-Prognose Phasen-Abnahme: [Datum]
```

**Pflegeregeln:** Block 4 darf nie leer heissen "keine", wenn in Wahrheit etwas hängt; er macht Verzögerungen auf Kundenseite sichtbar, bevor sie als unsere Verspätung erscheinen. Versand jeden [Wochentag] bis [Uhrzeit], auch wenn wenig passiert ist.

---

## 3. Entscheidungs-Log

| Nr | Datum | Entscheid | entschieden von | Begründung | verworfene Alternativen | wirkt auf |
|---|---|---|---|---|---|---|
| E-001 | | | | | | |

**Pflegeregeln:** Jeder Entscheid, der Geld, Termin oder Scope bewegt, steht innert 24 Stunden im Log, auch mündliche aus Sitzungen ("Entscheid im Termin vom …"). Das Log verhindert das "das haben wir nie so besprochen" im Monat vier, in beide Richtungen.

---

## 4. RACI-Tabelle (für vRv vorbefüllt)

Legende: **R** = Responsible (macht es) · **A** = Accountable (verantwortet es, **genau EINE Stelle pro Zeile, nie zwei**) · **C** = Consulted (wird vorher einbezogen) · **I** = Informed (wird informiert).

| Aufgabe | Wir | vRv | pebe AG | IT-Partner/Los-Partner |
|---|---|---|---|---|
| Architektur + Detailkonzept | R/A | C | C (Formatfragen) | I |
| Plattform-Bau + Tests | R/A | C (Feedback) | – | – |
| pebe-Formatspezifikation | C | I | R/A | – |
| Import-Freigabe im Betrieb | I | R/A (Buchhaltung) | – | – |
| Testdaten + Beispieldossiers | C | R/A | – | – |
| Pilot-Abnahme | C | R/A | – | – |
| Schulung Hauswarte | R/A | C (Leitung Hauswartung) | – | – |
| Büronetz/Endgeräte | I | A | – | R [je nach E4/E2-Entscheid 21.7.] |
| Betrieb Plattform + SLA | R/A | I | – | – |
| Datenmigration (Skripte, Testläufe) | R/A | C (Stichproben-Abnahme) | C | – |
| Revisionssicheres Archiv (Ablageort) | C | A | – | R [je nach Archiv-Entscheid, Frage g7] |

**Pflegeregeln:** Zeilen pro Projekt anpassen, aber die eiserne Regel bleibt: ein A pro Zeile. Bei jeder Nachfrage "wer ist verantwortlich, wenn X schiefgeht" ist die Antwort eine Zelle dieser Tabelle, nie ein Schulterzucken. Gehört in die Offerte (Kap. 11.4) und wird bei Vertragsschluss Bestandteil.

---

## 5. Change-Request-Formular (halbe Seite)

```text
CHANGE REQUEST CR-[Nr] · Projekt [Name] · Datum [Datum] · eingebracht von [Name, Seite]

1. Beschreibung (was soll anders/zusätzlich sein?)
   …

2. Nutzen (warum lohnt es sich?)
   …

3. Aufwand + Preis
   [x] Stunden · CHF [Betrag] · [Festpreis / nach Aufwand mit Dach]

4. Auswirkung auf den Termin
   [keine / Meilenstein M[x] verschiebt sich um …]

5. Entscheid vRv:   [ ] ja   [ ] nein   [ ] später (Wiedervorlage: Datum)
   Datum + Visum vRv: ____________   Visum PL: ____________
```

**Grundregel (steht so auch in der Offerte):** Kein Mehraufwand ohne schriftlichen CR **vor** der Umsetzung. Keine Überraschung auf der Rechnung, nie. Kleinigkeiten unter ~2 Stunden erledigen wir ohne CR, weisen sie aber im Statusreport Block 5 aus; P4-Wünsche werden gesammelt und in Betriebsreleases gebündelt.

---

## 6. Abnahmeprotokoll

```text
ABNAHMEPROTOKOLL · Projekt [Name] · Phase/Etappe [z.B. Phase 2 Pilot]
Datum [Datum] · Anwesend: [Namen beide Seiten]
Grundlage: Anforderungskatalog Version [x] vom [Datum] + Messkriterien gemäss Offerte Kap. [x]
```

**Messkriterien** (vorab definiert, Modul 5 §5)

| Kriterium | Soll | Ist | erfüllt |
|---|---|---|---|
| z.B. Erfassungsquote Regieleistungen Pilotbereich | ≥ [x] % | | ja/nein |
| z.B. Zeit Leistung bis Rechnung | halbiert ggü. Ist-Aufnahme | | ja/nein |
| z.B. Hauswart-Akzeptanz nach Woche 4 | freiwillige Weiternutzung | | ja/nein |

**Mängelliste**

| Nr | Beschreibung | Klasse | Frist | verantwortlich |
|---|---|---|---|---|
| | | A/B/C | | |

Klassen: **A** = blockierend, wird vor Abnahme behoben · **B** = wesentlich, Behebung mit Frist, Abnahme mit Auflagen möglich · **C** = kosmetisch, nächstes Release.

**Entscheid:** [ ] abgenommen · [ ] abgenommen mit Auflagen (B-Mängel + Fristen oben) · [ ] zurückgestellt (Gründe + neuer Termin)

```text
Datum + Visum vRv: ____________   Visum PL: ____________
```

**Review-Frist-Klausel (in den Vertrag übernehmen):** Der Kunde prüft Abnahmegegenstände innert [10] Arbeitstagen. Schweigen gilt als offene Punkte und wird nachgefasst, nicht als stillschweigende Abnahme; so bleibt die Abnahme ein bewusster Entscheid.

---

## Einsatz-Checkliste (vor erstem Kundeneinsatz)

- [ ] Team-Durchsicht in S6 (gehört zur S6-Agenda nach den drei Entscheiden)
- [ ] Offerten-Anhang wählen: Empfehlung Statusreport-Muster + CR-Formular + RACI; nicht alle sechs, das wirkt nach Bürokratie statt Führung
- [ ] Firmenangaben/Kopf gemäss Rechtsform-Entscheid 6.2 einsetzen
- [ ] Konsistenz-Check: Fristen hier vs. AVV (avv-template.md) vs. SLA (sla-baukasten.md) dürfen sich nicht widersprechen
- [ ] Nach Scope-Entscheid 21.7.: RACI-Zeilen Büronetz/Endgeräte + Archiv konkretisieren
