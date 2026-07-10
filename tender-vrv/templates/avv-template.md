# AVV-Template: Auftragsbearbeitungsvertrag (Entwurf)

> Task WS6.5, Teil 2. Wiederverwendbares Template für Kundenprojekte, erster Einsatz vRv (Offerten-Anhang B).
> **WICHTIG: ENTWURF, kein Rechtsrat.** Vor dem ersten Einsatz: (1) Review Joaquin, (2) **punktueller Anwalts-Review empfohlen** (Dossier E, E16: CHF 500-1'500, gut investiert), (3) Platzhalter [in eckigen Klammern] füllen. Struktur folgt Art. 9 DSG und gängiger Schweizer AVV-Praxis (Dossier D §3).

---

## Auftragsbearbeitungsvertrag

zwischen **[Kunde, Firma, Adresse]** (nachfolgend "Verantwortlicher") und **[Automatisierbar, Rechtsform + Adresse gemäss 6.2]** (nachfolgend "Auftragsbearbeiter"), zusammen "Parteien".

### 1. Gegenstand und Dauer

1.1 Dieser Vertrag regelt die Bearbeitung von Personendaten durch den Auftragsbearbeiter im Auftrag des Verantwortlichen im Rahmen des Hauptvertrags vom [Datum] ([Projektbezeichnung]).
1.2 Dauer entspricht dem Hauptvertrag; Pflichten, die ihrer Natur nach fortbestehen (Vertraulichkeit, Löschung), gelten darüber hinaus.

### 2. Art der Daten, Kategorien betroffener Personen, Zweck

2.1 Datenarten: [z.B. Stammdaten Mieter/Eigentümer, Auftrags- und Leistungsdaten, Fotos von Objekten, Kontaktdaten Mitarbeitende; besonders schützenswerte Daten: keine vorgesehen / falls doch: benennen].
2.2 Betroffene Personen: [z.B. Mieter, Eigentümer, Mitarbeitende des Verantwortlichen, Auftragnehmer].
2.3 Zweck: Betrieb und Support der vereinbarten Lösung gemäss Hauptvertrag. Eine Bearbeitung zu eigenen Zwecken des Auftragsbearbeiters findet nicht statt.

### 3. Weisungsrecht

3.1 Der Auftragsbearbeiter bearbeitet Personendaten ausschliesslich nach dokumentierten Weisungen des Verantwortlichen (Hauptvertrag, dieser Vertrag, Textform-Weisungen).
3.2 Hält der Auftragsbearbeiter eine Weisung für datenschutzwidrig, informiert er den Verantwortlichen unverzüglich und darf die Ausführung bis zur Klärung aufschieben.

### 4. Vertraulichkeit

4.1 Der Auftragsbearbeiter stellt sicher, dass alle mit der Bearbeitung befassten Personen zur Vertraulichkeit verpflichtet sind und die Daten nur bearbeiten, soweit für ihre Aufgabe nötig (Least Privilege, persönliche Konten, Protokollierung).

### 5. Datensicherheit (TOMs)

5.1 Der Auftragsbearbeiter trifft die technischen und organisatorischen Massnahmen gemäss **Anhang 1 (TOMs)** und hält sie dem Stand der Technik entsprechend aktuell; Schutzniveau darf nicht unterschritten werden.
5.2 Kernpunkte (Detail in Anhang 1): Datenhaltung in der Schweiz [Anbieter gemäss 6.3-Entscheid]; Verschlüsselung in transit und at rest; MFA und rollenbasierte Zugriffe; tägliche Backups nach 3-2-1 mit getesteter Wiederherstellung; Protokollierung sicherheitsrelevanter Aktionen.

### 6. Unterauftragsbearbeiter

6.1 Der Einsatz von Unterauftragsbearbeitern bedarf der **vorgängigen Genehmigung** des Verantwortlichen. Die bei Vertragsschluss genehmigten sind in **Anhang 2** aufgeführt [Hosting: gemäss 6.3 · E-Mail-Dienst · KI-Anbieter inkl. Verarbeitungsort/Rechtsgrundlage].
6.2 Beabsichtigte Wechsel oder Ergänzungen zeigt der Auftragsbearbeiter mindestens [30] Tage vorab in Textform an; widerspricht der Verantwortliche nicht innert [14] Tagen aus datenschutzrechtlichen Gründen, gilt die Genehmigung als erteilt.
6.3 Der Auftragsbearbeiter überbindet seinen Unterauftragsbearbeitern gleichwertige Pflichten und bleibt für deren Leistungen verantwortlich wie für eigene.

### 7. Bekanntgabe ins Ausland

7.1 Bearbeitung erfolgt grundsätzlich in der Schweiz. Eine Bekanntgabe ins Ausland erfolgt nur gemäss Anhang 2 (Dienst, Land, Rechtsgrundlage: Angemessenheit nach Staatenliste DSV, Swiss-U.S. Data Privacy Framework oder anerkannte Garantien/Standardklauseln).

### 8. Unterstützung des Verantwortlichen

8.1 Der Auftragsbearbeiter unterstützt den Verantwortlichen im Rahmen des Zumutbaren bei: Begehren betroffener Personen (Auskunft, Berichtigung, Löschung, Datenherausgabe), Datenschutz-Folgenabschätzungen sowie Anfragen von Aufsichtsbehörden.

### 9. Meldung von Datensicherheitsverletzungen

9.1 Der Auftragsbearbeiter meldet dem Verantwortlichen jede Verletzung der Datensicherheit **so rasch als möglich, spätestens innert 24 Stunden nach Feststellung**, mit den verfügbaren Angaben zu Art, betroffenen Daten/Personen, mutmasslichen Folgen und getroffenen bzw. vorgeschlagenen Massnahmen; er dokumentiert Verletzungen und wirkt an der Aufarbeitung mit. Die Beurteilung der Meldepflicht an den EDÖB obliegt dem Verantwortlichen.

### 10. Nachweis und Audit

10.1 Der Auftragsbearbeiter weist die Einhaltung dieses Vertrags auf Anfrage nach (aktuelle TOMs-Dokumentation, Auskünfte, Zertifikate der Infrastrukturanbieter).
10.2 Der Verantwortliche kann höchstens [einmal jährlich] sowie bei begründetem Anlass ein Audit durchführen oder durch einen Dritten durchführen lassen; Ankündigung mindestens [10] Arbeitstage vorab, während üblicher Geschäftszeiten, ohne unverhältnismässige Betriebsstörung; Geheimhaltung Dritter ist sicherzustellen. Zunächst wird ein schriftlicher Frage-/Nachweiskatalog genutzt.

### 11. Löschung und Rückgabe

11.1 Nach Beendigung des Hauptvertrags gibt der Auftragsbearbeiter alle Personendaten in offenen Formaten (CSV, PDF) heraus [Frist: 30 Tage] und löscht sie anschliessend nachweislich bei sich, inklusive Backups nach deren Rotationszyklus [max. 90 Tage]; gesetzliche Aufbewahrungspflichten bleiben vorbehalten und werden angezeigt.

### 12. Haftung, Schlussbestimmungen

12.1 Haftung richtet sich nach dem Hauptvertrag.
12.2 Änderungen bedürfen der Textform. Bei Widerspruch zwischen diesem Vertrag und dem Hauptvertrag geht in Datenschutzfragen dieser Vertrag vor.
12.3 Anwendbares Recht: Schweizer Recht. Gerichtsstand: [Sitz des Verantwortlichen / zu vereinbaren].

**Anhang 1: Technische und organisatorische Massnahmen (TOMs)** [aus datenschutz-statement.md + Dossier D §7 konkretisieren]
**Anhang 2: Genehmigte Unterauftragsbearbeiter** [Tabelle: Dienst · Firma · Sitz · Verarbeitungsort · Zweck · Rechtsgrundlage Auslandsbekanntgabe]

Ort/Datum, Unterschriften beider Parteien.

---

## Checkliste vor erstem Einsatz (nicht Teil des Vertrags)

- [ ] Joaquin-Review inhaltlich
- [ ] Anwalts-Review (empfohlen; Fokus: Ziff. 6.2 Genehmigungsfiktion, Ziff. 10 Audit-Umfang, Ziff. 11 Fristen, Haftungsverweis)
- [ ] Anhang 1 TOMs konkret befüllt (nicht nur Verweis)
- [ ] Anhang 2 vollständig (inkl. KI-Anbieter mit Verarbeitungsort; Hosting gemäss 6.3-Entscheid)
- [ ] Rechtsform/Firmenangaben gemäss 6.2 eingesetzt
- [ ] Konsistenz-Check gegen Offerte Kap. 8.6 und SLA (Fristen dürfen sich nicht widersprechen)
