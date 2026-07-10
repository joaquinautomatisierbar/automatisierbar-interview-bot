# SLA-Baukasten: Bronze / Silber / Gold

> Task WS5.5. Antwort auf die Ausschreibungs-Zeile "SLAs: Reaktionszeiten, Lösungszeiten, Verfügbarkeiten". Speist Offerten-Kapitel 10.4 und macht uns am 5.8. sprechfähig. Preise je Stufe folgen im Preismodell (5.3).
> Ehrlichkeits-Grundsatz (Dossier D/E): Monitoring und Alarmierung laufen automatisiert rund um die Uhr; **Menschen reagieren in definierten Fenstern.** Ein 24/7-Pikett ist bei vier Personen kein Standardversprechen, sondern eine ausdrücklich vereinbarte (und ehrlich bepreiste) Option.
> **[Team-Check vor Offerte]:** Zahlen sind Angebots-Vorschlag; in S6 gegen Kapazität + E4-Entscheid validieren.

## 1. Prioritätsdefinitionen (gelten für alle Stufen)

| Prio | Definition | vRv-Beispiel |
|---|---|---|
| **P1 kritisch** | Plattform für alle unbenutzbar oder Datenverlust droht | Hauswarte können nicht erfassen, Login für alle unmöglich |
| **P2 hoch** | Wesentliche Funktion gestört, Umgehung existiert | Fakturavorschlag-Export defekt, Erfassung läuft aber weiter |
| **P3 mittel** | Einzelne Funktion/Person betroffen, Prozess läuft | Ein Foto-Upload schlägt bei einem Gerät fehl |
| **P4 tief** | Frage, Kleinanpassung, kosmetisch | Bezeichnung ändern, neue Auswertungs-Spalte gewünscht |

Einstufung zuerst durch den Melder, verbindlich durch uns innert der Reaktionszeit; bei Uneinigkeit gilt bis zur Klärung die höhere Prio.

## 2. Die drei Stufen

| Merkmal | **Bronze** | **Silber** (Empfehlung) | **Gold** |
|---|---|---|---|
| Servicezeiten (Support durch Menschen) | Mo-Fr 08-17 | Mo-Fr 08-17 | Mo-Sa 07-19 |
| Reaktionszeit P1 | 8 Arbeitsstunden | **4 Arbeitsstunden** | 2 Stunden (innerhalb Servicezeit) |
| Reaktionszeit P2 | nächster Arbeitstag | 8 Arbeitsstunden | 4 Stunden |
| Reaktionszeit P3/P4 | 3 Arbeitstage | 2 Arbeitstage | 1 Arbeitstag |
| Lösungsziel P1 (Umgehung / Behebung) | 2 / 5 Arbeitstage | 8 Arbeitsstunden / 2 Arbeitstage | 4 Stunden / 1 Arbeitstag |
| Lösungsziel P2 | 5 / 10 Arbeitstage | 2 / 5 Arbeitstage | 1 / 3 Arbeitstage |
| Verfügbarkeitsziel (Monat, Plattform-HTTP) | 99.0% | 99.5% | 99.7% |
| Support-Kanäle | E-Mail | E-Mail + Telefon | E-Mail + Telefon + Direktnummer Ansprechpartner |
| Status-Report | quartalsweise | monatlich | monatlich + Quartals-Review-Gespräch |
| Optionales Add-on | — | — | Pikett ausserhalb Servicezeiten (separat vereinbart + bepreist) |

**Lösungszeiten sind Ziele, keine Garantien** (branchenüblich; garantiert sind Reaktionszeiten und das Verfügbarkeitsziel). Umgehung = Prozess läuft wieder, ggf. eingeschränkt; Behebung = Ursache beseitigt.

## 3. In ALLEN Stufen enthalten

- Technisches Monitoring mit automatischer Alarmierung an uns: rund um die Uhr, unabhängig von den Servicezeiten
- Tägliche verschlüsselte Backups nach 3-2-1 (eine Kopie bei einem Zweitanbieter), periodisch getesteter Restore
- Sicherheitsupdates: kritische Lücken innert 48 Stunden behandelt
- Angekündigte Wartungsfenster (min. 3 Arbeitstage Vorlauf, ausserhalb Bürozeiten); zählen nicht als Ausfall
- Benannter Ansprechpartner + Stellvertretung; Eskalation direkt an die Geschäftsleitung (bei uns heisst das: an einen Gründer, und das ist keine Floskel, sondern die Struktur)

## 4. Verfügbarkeits-Mechanik (für Schmids Nachfragen)

- Gemessen wird die Erreichbarkeit der Plattform (HTTP-Healthcheck, extern), Monatsbasis; Wartungsfenster und Störungen ausserhalb unseres Verantwortungsbereichs (Kundennetz, Internetprovider vRv) zählen nicht.
- Unsere Zusage liegt bewusst **unter** der des Infrastrukturanbieters, damit wir nichts versprechen, was wir nur weiterreichen. **[Stand prüfen: exakte Anbieter-SLA (Exoscale/Infomaniak) nach Hosting-Entscheid 6.3 eintragen]**
- Verfehlung: Gutschrift von 5% der Monatspauschale je angefangene 0.5 Prozentpunkte unter dem Ziel, gedeckelt bei 50% der Monatspauschale. Bewusst moderat (Dossier E: keine existenzgefährdenden Pönalen, dafür realistische Zusagen).

## 5. Abgrenzung (Leistungsabgrenzung, wie die Ausschreibung sie verlangt)

Nicht Teil dieses SLA: Büronetz und Endgeräte von vRv (eigenes Los bzw. IT-Partner, je nach Scope-Entscheid E4/E2) · pebeFINANCE selbst (Wartungsvertrag pebe AG; unsere Schnittstellen-Anpassungen bei Formatänderungen sind abgedeckt) · M365-Tenant-Administration (sofern nicht als eigenes Los vereinbart) · Weiterentwicklungswünsche (laufen als Change Request, nicht als Störung).

## 6. Sprechfähige Kurzfassung für den 5.8.

"Wir bieten drei Servicestufen an. Empfehlung für Sie ist die mittlere: Support werktags acht bis siebzehn Uhr, auf kritische Störungen reagieren wir innert vier Arbeitsstunden, Verfügbarkeitsziel 99.5 Prozent, technische Überwachung läuft automatisiert rund um die Uhr. Was wir bewusst nicht versprechen: einen 24-Stunden-Pikettdienst als Beilage. Wenn Sie den brauchen, vereinbaren wir ihn ausdrücklich, mit ehrlichem Preis."
