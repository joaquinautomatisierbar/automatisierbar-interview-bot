# CH-Hosting: Kostenblatt + Entscheidungsvorlage

> Task WS6.3 (J+C, Entscheid: **Joaquin**, Ziel bis 27.7.). Definiert den Schweizer Hosting-Standard für Kundenprojekte, zuerst für vRv. Der Entscheid fliesst in: Offerte Kap. 8.1 (Rechenzentrum), Security-Paket 3.4, SLA-Baukasten (Verfügbarkeits-Kopplung), AVV-Unterauftragsbearbeiter-Liste (6.5), Fragen-Bank Q28.
> Zertifikats- und Eignungsdaten aus Dossier D §6 (geprüft 10.7.). Preise: Exoscale-Zahlen aus Drittquelle (getdeploying.com, Stand 12.2.2026, **USD**; CHF-Listen im Portal ziehen); Infomaniak nur per Kalkulator abrufbar. **Vor Offertabgabe: exakte Preise 10 min im jeweiligen Kalkulator ziehen, Links unten.**

## 1. Referenz-Setup (was die vRv-Plattform konkret braucht)

| Komponente | Dimension (Start) | Wozu |
|---|---|---|
| App-Server (VM) | 2-4 vCPU, 4-8 GB RAM | Plattform + Integrationsdienst |
| Managed PostgreSQL | 4 GB RAM, 80 GB, mit Point-in-Time-Recovery | Prozessdaten; PITR trägt unsere RPO-Zusage im SLA |
| Objektspeicher | 100-500 GB im ersten Jahr, wachsend | **Hauswart-Fotos!** + Dokumente + Versionierung/Object Lock (Archiv-Weg B) |
| Offsite-Backup | Kopie bei ZWEITEM Anbieter, ~50-100 GB | 3-2-1-Pflicht aus dem Notfallkonzept |
| Staging (optional) | kleinste VM, nur bei Bedarf aktiv | Abnahmen ohne Produktionsrisiko |
| Egress | moderat (mobile Sync, Berichte) | bei beiden Anbietern grosszügige Freikontingente |

## 2. Anbieter-Vergleich

### Exoscale (Zonen Genf CH-GVA-2 / Zürich) — Empfehlung Standard

- **Zertifikate:** ISO 27001:2022, 27017, 27018 [D §6]. Security Groups, **Managed DBaaS (PostgreSQL, betrieben mit Aiven, Backups/PITR integriert)**.
- **Preise (Drittquelle 2/2026, USD, CHF-Liste im Portal ziehen):** VM 4 vCPU/8 GB ≈ **67/Mt.** · Managed PostgreSQL "Startup-4" (4 GB/80 GB) ≈ **98/Mt.** (Business-4 mit Replika: höher, **[Portal ziehen]**) · Objektspeicher ≈ **0.02/GB** (≈20/TB) · Egress: 1 TB frei je Instanz, dann 0.02/GB.
- **Referenz-Setup grob: CHF 170-260/Monat** (VM + Managed-PG Startup + Speicher + Reserve), Staging klein dazu bei Bedarf.
- **Pro:** Managed-DB nimmt uns Patching/Backup-Engineering ab (unsere Betriebsstunden sind der teuerste Posten); CH-Zonen; ISO-Trio deckt die Prüfer-Frage sauber. **Contra:** europäischer Anbieter (A1-Gruppe), nicht "100% Schweizer Firma".

### Infomaniak (Genf, eigene Rechenzentren) — Empfehlung Offsite-Backup + Alternative

- **Zertifikate/Story:** ISO 27001 (seit 2018), 9001, 14001, 50001; **Schweizer Firma, eigene RZ, ausschliesslich Schweiz** [D §6]. Stärkste "alles Schweiz"-Erzählung, dazu Ökostrom-Positionierung.
- **Preise:** VPS/Public Cloud in CHF, stundengenau abgerechnet, tief; Managed-DB-Palette schmaler als Exoscale → PostgreSQL hiesse weitgehend **Eigenbetrieb** (Patching, Backups, Monitoring durch uns). **[Kalkulator ziehen: infomaniak.com/de/hosting/public-cloud/prices bzw. /vps-cloud/prices]**
- **Rechnung ehrlich:** Der VPS ist vielleicht CHF 60-120/Mt. günstiger, aber 2-4 h/Mt. DB-Eigenbetrieb fressen die Ersparnis bei jedem realistischen Stundensatz auf. Darum: erste Wahl fürs **Offsite-Backup** (billig, unabhängig, zweiter Schweizer Anbieter = 3-2-1 erfüllt UND die "beide Anbieter Schweiz"-Story) und Plan B fürs Ganze, falls die 100%-Schweiz-Story am Termin überraschend hoch gewichtet wird.

### Azure Switzerland North (Zürich) — nur auf Kundenwunsch

- **Zertifikate:** breitestes Portfolio inkl. dokumentiertem FINMA-Compliance-Mapping [D §6]. Maximale O365-/Entra-Nähe.
- **Contra:** teuerste Klasse (grob 2-4× Exoscale für dasselbe Setup, erst kalkulieren, wenn gefordert), US-Anbieter (CLOUD-Act-Diskussion beim Prüfer möglich), für unseren Stack Overkill. Position: "können wir, empfehlen wir für diese Lösung nicht; Ihre M365-Daten liegen ohnehin dort."

## 3. Empfehlung (zur Bestätigung durch Joaquin)

1. **Standard für Kundenprojekte: Exoscale, Zone Genf oder Zürich** (Managed PostgreSQL mit PITR ist das Argument; er trägt direkt RPO/RTO im SLA-Baukasten).
2. **Offsite-Backup-Kopie: Infomaniak** (Objektspeicher; erfüllt 3-2-1 mit zweitem Schweizer Anbieter).
3. **Azure CH: nur wenn vRv es explizit will**; dann Aufpreis transparent ausweisen.
4. Sprechsatz (ersetzt "vorgesehen" in Fragen-Bank Q28 + Offerte 8.1): "Wir betreiben in zertifizierten Schweizer Rechenzentren: Exoscale in Genf/Zürich für den Betrieb, Infomaniak in Genf für die unabhängige Sicherungskopie. Beide ISO-27001-zertifiziert, alle Produktivdaten in der Schweiz."

## 4. Entscheid-Checkliste (10 Minuten, Joaquin)

- [ ] Empfehlung 1-3 so bestätigen oder kippen (einzige echte Alternative: alles Infomaniak für die 100%-Schweiz-Story, Preis: DB-Eigenbetrieb)
- [ ] Exoscale-Konto erstellen (Firmen-Account, 2FA, Rechnungsadresse) + Zone wählen
- [ ] CHF-Preise im Portal ziehen und HIER eintragen: VM ______ · PG Startup-4 ______ · PG Business-4 ______ · SOS/GB ______ (Quelle: exoscale.com/pricing, Datum: ______)
- [ ] Infomaniak-Objektspeicher-Preis ziehen: ______ /GB (Datum: ______)
- [ ] Anbieter-SLA-Prozente notieren (für SLA-Baukasten §4): Exoscale Compute ______ % · DBaaS ______ %
- [ ] Danach: Baustein 8.1 finalisieren (C), AVV-Unterauftragsbearbeiter-Liste ergänzen (C), E1-Referenz-Setup 20-40h einplanen [E1]

## 5. Was bewusst NICHT Teil dieses Blatts ist

Eigene Hardware/eigenes RZ (behaupten wir nie); Hosting der M365-Welt (liegt bei Microsoft, Schweizer Tenant); Kosten des Archiv-Wegs SharePoint+Purview (steht im Lizenzteil von Dossier C bzw. Offerte Kap. 13.3).
