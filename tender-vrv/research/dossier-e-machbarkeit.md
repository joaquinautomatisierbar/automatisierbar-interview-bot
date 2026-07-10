# Dossier E: Teilbereichs-Machbarkeitsanalyse

> **Status: fertig zur Team-Entscheidung. Scope-Entscheidungs-Session: 21.7. (an S3).**
> Auftrag (Joaquin, 10.7.): Kein Teilbereich wird vorab ausgeschlossen. Für jeden Teilbereich: Was verlangt er konkret, ist er bis Projektstart (~Okt. 2026) erlernbar (Preis in Stunden), was heisst Betrieb, Haftung, Marge. DANN entscheidet das Team pro Teilbereich: **selbst / mit Partner / nicht anbieten.**
> Inputs: Dossiers A-D (research/), MSP-/Betriebs-Recherche 10.7. (Quellen unten), eigene Betriebserfahrung (VPS-Betrieb, verschlüsselte Backups + Restore-Runbook, Auth-Systeme, Deploys, Monitoring).
> Kennzeichnung: [V] = quellenbelegt, [G] = geschätzt mit Herleitung, [E] = eigene belegbare Erfahrung.

## Executive Summary

1. **Der Kern der Ausschreibung (Plattform, pebe-Integration, Hauswart-App, Datenmigration, Schulung, Projektleitung, KI, Datenschutz) ist vollständig selbst lieferbar**, grösstenteils heute schon belegbar durch gebaute Systeme.
2. **Ein Infra-Block passt echt zu uns: Managed Endpoints + Betriebssoftware** (E4/E5). Cloud-only, klarer Lernpfad (MD-102, 120h Stoff [V]), 25-40h/Monat Betrieb für ~28 Seats [G], Marktpreis CHF 50-120/User/Monat [V]. Einzige echte Hürde: Helpdesk-Verfügbarkeit im 4er-Team; Lösung ist ein definiertes Support-Fenster + Partner-Backstop für schwere Security-Incidents.
3. **Netzwerk vor Ort (E2/E6-Perimeter) ist ein Betriebsgeschäft, kein Wissensproblem**: Konfiguration in 100-200h lernbar [G], aber Vor-Ort-SLA, Pikett und Diagnose-Erfahrung amortisieren sich mit einem einzigen Kunden nie. Partner-Terrain, mit unseren Design-Vorgaben.
4. **Hardware (E3) ist Kommodität**: 86% der Reseller machen 1-10% Marge [V]. Als Koordinations- und Deployment-Leistung in Stunden anbieten, Einkauf via Partner oder Kunde direkt.
5. **AlwaysOnVPN (E7) nicht selbst betreiben**: dauerhafter RRAS/NPS/PKI-Betrieb ist teurer Legacy; Microsoft positioniert Entra Private Access (USD 5/User/Monat) als Nachfolger [V]. Anforderung am Termin reframen ("sicherer mobiler Zugriff"), Entra-Route offerieren, sonst Partner.
6. **Empfohlene Angebotsarchitektur: Modell "Wir orchestrieren, Partner betreibt die Vor-Ort-Schicht"** (Teillose mit getrennten Verträgen, wir als Gesamtkoordinator + Architekt). Kein aufgeblähter Durchlaufumsatz, keine Haftungsdurchreiche, und die Ausschreibungs-Rolle "Architektur und Projektleitung" ist exakt das.

---

## Bewertungsraster

Je Teilbereich: **Verlangt** (aus der Ausschreibung) · **Liefern/Betreiben** (einmalig vs. dauerhaft) · **Können wir heute?** · **Lernpfad + Stunden** · **Betrieb/Monat** · **Haftung** · **Marge** · **Optionen mit Pros/Cons** · **Empfehlung (Konfidenz)**. Entscheid trifft das Team am 21.7. (Matrix am Ende).

---

## E1 · Rechenzentrum/Hosting der Lösung

**Verlangt:** "Rechenzentrum: Ort, Umfang und Art". **Liefern:** Betrieb unserer Plattform in zertifizierter CH-Infrastruktur; wir verantworten Architektur, Applikationsbetrieb, Datenhaltung, Backups, der RZ-Betreiber Gebäude/Strom/Netz. **Heute:** [E] Wir betreiben produktive Systeme selbst (VPS, TLS, verschlüsselte Backups, getestete Restores, Monitoring + Alarmierung); es fehlt nur der Schweizer Standort als Standard. **Lernpfad:** Exoscale/Infomaniak-Migration ist Routinearbeit, 20-40h für Referenz-Setup inkl. Managed DB + Object Storage [G]. **Betrieb:** 2-6h/Monat pro Kundensystem [E/G]. **Haftung:** Applikationsverfügbarkeit gemäss SLA; RZ-Risiken beim zertifizierten Anbieter (ISO 27001/27017/27018 bei Exoscale, ISO 27001 bei Infomaniak [V, Dossier D]). **Marge:** gesund; Hosting-Einkauf tief, Wert liegt im Betrieb. **Optionen:** selbst (pro: Kernkompetenz, glaubwürdig; contra: keiner) / Partner (unnötig). **Empfehlung: SELBST (hoch).** Standard-Antwort: "Exoscale Genf/Zürich, alternativ Infomaniak; alle Produktivdaten in der Schweiz."

## E2 · Netzwerk-Bereitstellung beim Kunden (LAN/WLAN/Firewall vor Ort)

**Verlangt:** "Bereitstellung Netzwerk (Initial- und laufende Kosten, Umfang Managed Services)". **Liefern:** Site Survey, Verkabelung prüfen, Firewall/Switches/APs, VLANs, Doku; danach Managed Network (Monitoring, Firmware, Regeln, Vor-Ort-Störungsdienst). Kostenrahmen 1 Standort/28 MA: CHF 15'000-35'000 initial [G aus V-Komponentenpreisen: WLAN 200m² CHF 4-8k, Firewall-Klasse KMU]. **Heute:** Konzepte ja (VLAN/Zero-Trust-Verständnis), Praxis vor Ort nein. **Lernpfad:** FortiGate-Kurs ~40h [V] bzw. UniFi flacher; bis "kann einen KMU-Standort sauber bauen" 100-200h [G]. Ehrliche Grenze: Kurse lehren Konfiguration, nicht Diagnose unter Zeitdruck; genau dafür bezahlt man Managed-Network. **Betrieb:** Routine 4-8h/Monat, aber der eigentliche Preis ist die Störungsbereitschaft: Netz down = 28 Leute stehen, Erwartung Techniker vor Ort in Stunden. **Haftung:** höchste operative Sichtbarkeit; Netzausfall = Betriebsunterbruch = klassischer Vermögensschaden-Drittanspruch [V]. **Marge:** Service ordentlich, setzt aber NOC-Tooling + Pikett voraus, amortisiert sich mit 1 Kunden nicht [G]. **Optionen:** selbst (pro: Lernwert, voller Scope; contra: unfair gegenüber Kunde bei Störung, Pikett unmöglich im 4er-Team neben Produktgeschäft) / **Partner mit unseren Design-Vorgaben** (pro: voller Scope ohne Überdehnung, wir schreiben VLAN-/Security-Anforderungen ins Pflichtenheft; contra: Koordination, Margenteilung) / nicht anbieten (contra: reisst Loch in "alles aus einer Hand"). **Empfehlung: PARTNER (hoch).**

## E3 · Hardware-Infrastruktur (Arbeitsplätze, Mobile, Server-Verzicht)

**Verlangt:** "Bereitstellung Hardware-Infrastruktur (on-premise, Cloud, Umfang Managed Services)". **Liefern:** Beschaffung, Autopilot-Zero-Touch-Rollout, Garantie/RMA, Refresh-Zyklus 3-4 Jahre; bei Cloud-first-Angebot bewusst ohne neue On-prem-Server. **Heute:** Autopilot-Wissen fehlt, ist aber Teil des MD-102-Stoffs (E4). **Lernpfad:** in E4 enthalten + 10-20h Prozessaufbau (Bestell-Runbook, Inventar, RMA) [G]. **Betrieb:** Initial-Rollout ~30 Geräte 3-5 Arbeitstage; laufend 2-5h/Monat [G]. **Haftung:** tief (Herstellergarantie; Restrisiko Logistik/Termine). **Marge:** [V] 86% der Reseller: 1-10% auf PCs/Notebooks; bei 30 Geräten à CHF 1'500 einmalig CHF 450-4'500. Handel lohnt nicht. **Optionen:** Handel selbst (contra: Kapitalbindung, Margenwitz) / **Koordination + Deployment selbst, Einkauf via Partner oder Kunde direkt** (pro: wertvolle Arbeit in Stunden verrechnet, kein Lager; contra: keiner ernsthaft) / komplett Partner. **Empfehlung: SELBST als Koordination + Deployment, Einkauf Partner/Kunde (hoch).**

## E4 · Betriebssoftware + Endpoint-Management (OS, Patching, Intune)

**Verlangt:** "Bereitstellung Betriebssoftware (Operatingsysteme, Sicherheits-SW, Umfang Managed Services)". **Liefern:** Im Microsoft-Cloud-Modell fällt dieser Block fast vollständig in Business Premium: Windows-Upgrade-Rechte, Intune Plan 1, Defender for Business, Entra ID P1, Purview-Basis [V]. CH-Preis CHF 17.80/User/Monat Jahresabo [V]; **Achtung: Microsoft-Preiserhöhung per 1.7.2026 angekündigt (bis zu 33% je nach Plan), CHF-Preise vor Offertabgabe zwingend neu ziehen [V]**. Betrieb: Autopilot-Enrollment, Compliance-Policies, Update-Rings, App-Deployment, Defender-Alert-Triage, On-/Offboarding-Runbooks, Reporting, Helpdesk-Fenster. **Heute:** SaaS-Betrieb, Scripting, Runbook-Disziplin [E]; Intune/Defender-Praxis fehlt. **Lernpfad:** [V] MD-102 "Endpoint Administrator" (120h Stoffumfang) + Conditional-Access-Teile aus SC-300 (+30-60h); gesamt **150-250h für einen starken Generalisten bis kompetenter Operator** [G]. Bei Start jetzt: 1 Person × 12-20h/Woche bis Oktober, machbar. Zertifikat optional, als Offerten-Nachweis wertvoll. **Betrieb:** [V/G] Benchmarks 0.96-1.34 h/User/Monat bzw. ~1 Ticket/Endpoint/Monat → 28 Seats: **25-40h/Monat all-in inkl. Helpdesk**, reine Policy-/Patch-Pflege 8-15h. **Haftung:** verpasster Patch/Fehlkonfiguration = Drittschaden; Managed-(Security-)Services müssen in der Berufshaftpflicht **explizit** vereinbart sein [V] → in die Versicherungsanfrage (WS6.1) aufnehmen (Template wird ergänzt). **Marge:** [V] Markt CHF 50-120/User/Monat Managed Workplace → 28 × CHF 90 ≈ CHF 2'520/Monat; bei 25-40h effektiv CHF 63-100/h, mit unserer Automatisierungs-Disziplin eher oben [G]. Lizenz-Reselling (CSP) dagegen 10-20%, Durchlaufposten. **Optionen:** selbst mit Support-Fenster + Partner-Backstop (pro: passt zu Stärken, wiederkehrender Umsatz, macht "alles aus einer Hand" glaubwürdig; contra: Helpdesk-Bindung, Ferienabdeckung im 4er-Team, souveräner Betrieb erst nach 6-12 Monaten Praxis) / Partner (pro: null Risiko; contra: wir verschenken den einzigen gut passenden Infra-Block) / nicht anbieten. **Empfehlung: SELBST mit definiertem Support-Fenster (Mo-Fr 08-17, Reaktion 4h) + vertraglichem Partner-Backstop für schwere Security-Incidents (mittel-hoch). Dies ist die eigentliche Team-Entscheidung am 21.7., denn sie kostet 150-250 Lernstunden + dauerhafte Betriebsbindung.**

## E5 · EndpointSecurity/EDR-Konzept

**Verlangt:** "Sicherheitsstandards: EndpointSecurity". **Liefern:** sprechfähiges Konzept + (falls E4=selbst) Betrieb Defender for Business. **Heute:** Konzeptwissen über Dossier D vorhanden (EDR vs. AV, BACS-Grundschutz). **Lernpfad:** in E4 enthalten; als reines Konzept 10-20h Vertiefung [G]. **Haftung/Marge:** folgt E4. **Empfehlung: Wissen SELBST (Modul 2), Betrieb folgt dem E4-Entscheid (hoch).**

## E6 · Firewall

**Verlangt:** "Datensicherheit: Firewalls". **Zweiteilen:** (a) **Cloud-seitig** (Security Groups, Host-Firewalls, WAF vor unserer Plattform): [E] machen wir heute schon, Antwortbaustein in Dossier D fertig. (b) **Perimeter vor Ort**: Teil von E2. **Empfehlung: (a) SELBST (hoch), (b) folgt E2 = Partner.**

## E7 · VPN / AlwaysOnVPN

**Verlangt:** "Mobile Anbindung: AlwaysOnVPN". **Liefern (wörtlich genommen):** dauerhafter Betrieb von RRAS-VPN-Server, NPS/RADIUS mit EAP-TLS, interner PKI mit Auto-Enrollment, Intune-Profilen [V]. Typische Störungen: CRL nicht erreichbar, Zertifikats-Mismatch, NPS-Policy [V]; jede Störung ist P1 (Aussendienst steht). **Lernpfad:** kein passendes Zertifikat; Erstumsetzung für Erfahrene 40-80h, für Erstlinge 100-200h mit leisen PKI-Fehlerrisiken [G]. **Betrieb:** 4-8h/Monat + Incident-Spitzen; man betreibt dafür dauerhaft 1-2 Windows-Server [G]. **Einordnung:** Für eine 28-MA-Firma ohne On-prem-Serverlandschaft ein teurer Anachronismus. Unsere Lösung braucht kein VPN (TLS + Entra SSO + MFA/Conditional Access, Baustein in Dossier D); Microsoft positioniert **Entra Private Access (USD 5/User/Monat, in Entra Suite USD 12)** explizit als VPN-Nachfolger [V], Signal: SSTP-Retirement 31.3.2026 [V]. Betrieb Private Access: Connector-VM + Policies, 1-3h/Monat [G]. **Optionen:** AOVPN selbst (contra: Legacy-Dauerbetrieb, P1-Risiko, PKI-Lernkurve) / AOVPN via Partner (falls vRv wegen einer On-prem-Fachapplikation darauf besteht) / **Reframe: "sicherer mobiler Zugriff" mit Entra-Route offerieren** (pro: moderner, billiger, wir kompetent; contra: erklärungsbedürftig gegenüber der wörtlichen Anforderung). **Empfehlung: REFRAME + Entra-Route SELBST; falls AOVPN zwingend: PARTNER (hoch).** Frage g5 im Discovery-Tool klärt zuerst, was vRv wirklich meint.

## E8 · Managed Services / SLA-Betrieb unserer Lösung

**Verlangt:** "SLAs: Reaktionszeiten, Lösungszeiten, Verfügbarkeiten". **Liefern:** SLA-Stufen für UNSERE Plattform. **Heute:** [E] Monitoring, Healthchecks, Alarmierung rund um die Uhr automatisiert; personelle Reaktion zu Bürozeiten; ehrlicher Baustein in Dossier D formuliert ("kein 24/7-Pikett als Standard, separat vereinbar"). **Lernpfad:** keiner nötig; SLA-Baukasten (WS5.5) definiert Bronze/Silber/Gold. **Haftung:** SLA-Pönalen bewusst moderat gestalten; Verfügbarkeitszusagen an Managed-DB/Hosting-SLAs des Anbieters koppeln. **Empfehlung: SELBST (hoch).**

## E9 · Datenmigration

**Verlangt:** "Zusatzkosten: Datenmigration". **Liefern:** Stammdaten (Objekte, Mieter, Verträge) + Alt-Dokumente in die Plattform; Skripte, Mapping, Validierung, Testläufe, Abnahme. **Heute:** [E] Kernkompetenz (mehrfach gebaut: Notion-Migrationen, Lead-Archivierung 2'079 Datensätze, CSV-Pipelines). **Empfehlung: SELBST (hoch).** Transparent als Position ausweisen (die Ausschreibung fragt explizit danach).

## E10 · Schulung

**Verlangt:** "Zusatzkosten: Schulung". **Liefern:** Key-User-Schulung, Hauswart-Einführung vor Ort (kurz, gerätenah), Video-Snippets, Doku. **Heute:** [E] machbar; Kurzvideo/Loom-Disziplin vorhanden. **Empfehlung: SELBST (hoch).** Hauswarte gesondert schulen (Frage h7).

## E11 · Projektleitung + Architektur

**Verlangt:** "Rolle Lösungsanbieter: erstellen Architektur und Projektleitung; Mitarbeit vRv". **Liefern:** Architektur-Dokument, Projektplan mit Meilensteinen, Statusrhythmus, Entscheidungs-Log, Abnahmen, Change-Requests, Koordination allfälliger Partner (E2/E3). **Heute:** [E] praktiziert (Multi-Track-Builds mit Integrations-Gates, dokumentierte Runbooks/Decision-Logs), aber noch nie als formales Kundenmandat verkauft. **Lernpfad:** 20-40h Formalisierung (Vorlagen: Projekthandbuch, RACI, Statusreport, CR-Formular) [G]; Modul 5 (S6) übt genau das. **Haftung:** Projektleitungs-Fehler = Vermögensschaden → Berufshaftpflicht deckt Kernrisiko (WS6.1). **Empfehlung: SELBST (hoch), mit ehrlichem Junior-Bonus:** kleine Struktur heisst direkte Verantwortung der Gründer statt wechselnder PL-Junioren; genau das als Stärke verkaufen (Kriterium "Flexibilität, Transparenz").

## E12 · Plattform-Bau (zentrale Auftrags-/Workflow-Plattform)

**Verlangt:** "Zentralisierte Plattform für Erfassung, Abwicklung und Nachverfolgung von Aufgaben/Aufträgen; Workflow-Automatisierung". **Heute:** [E] Kernkompetenz, belegt: Hub (Work-OS mit Boards, Echtzeit, Mobile-PWA), Cockpit-Suite, mehrere Kunden-Tools. Dossier B bestätigt die Marktlücke: keine Standard-Suite bildet vRvs Drei-Geschäftsfelder-Order2Cash ab. **Empfehlung: SELBST (hoch). Das ist das Herz des Angebots.**

## E13 · pebeFinance-Integration

**Verlangt:** "Integration der heutigen Lösung pebeFinance in die O365-Welt" (Primär-Anforderung!). **Liefern:** Integrationsdienst auf den belegten Flächen: CSV/Excel-Buchungsimport (Lizenz "Schnittstellen" nötig! [V, Dossier A]), evtl. Fakturapositions-Import (Umfang unklar, Frage P3 an pebe), QR-Rechnung raus + camt.053/054-Zahlungsabgleich rein [V]. Letzter Meter bleibt zunächst ein menschlicher Import-Klick in pebe (bewusst als Kontrollpunkt verkaufen). **Heute:** [E] CSV-Pipelines, Validierungs-Disziplin, n8n; QR-Bill ist offener Standard. **Lernpfad:** Formatspezifikation von pebe abhängig (Fragen P1-P8 aus Dossier A); 20-40h Aufbau Integrationsdienst nach Spezifikation [G]. **Haftung:** Falschbuchungen → Vorvalidierung gegen Kontenplan/MWST-Regeln (spiegelt pebe-Prüfungen [V]) + Vier-Augen-Import. **Marge:** hoch, weil genau hier kein Wettbewerber antritt (Dossier B: keine Suite dokumentiert pebe-Schnittstelle). **Empfehlung: SELBST (hoch), mit früher pebe-Kontaktaufnahme als Projektbedingung (Frage c5: Freigabe am 5.8. einholen).**

## E14 · Mobile Hauswart-App

**Verlangt:** "Mobile Nutzung für Hauswarte (Apps mit Checklisten, Foto-Funktion), Echtzeit-Kommunikation, GPS". **Heute:** [E] Muster mehrfach gebaut (Walk-in PWA mit Foto/Sprache, Ausgaben-PWA mit Beleg-OCR, Hub mobile). Offline-Frage (e6) und GPS-Zweck (e4, nDSG-Verhältnismässigkeit!) klärt das Discovery-Tool. **Lernpfad:** Offline-First-Vertiefung 20-40h falls e6="zwingend" [G]. **Empfehlung: SELBST (hoch). Gegen AbaSmart (Dossier B) und pebe mobile (Dossier A) über vRv-exakte Prozesse + pebe-Erhalt differenzieren.**

## E15 · KI-Strategie

**Verlangt:** "Dabei ist ... eine KI- und Sicherheitsstrategie sicherzustellen". **Liefern:** Strategie-Dokument (Datenklassifizierung, Anbieter/Verarbeitungsorte, kein Training auf Kundendaten, Human-in-the-loop, Protokollierung) + Umsetzung in der Plattform. **Heute:** [E] tägliche Praxis; Baustein fertig formuliert in Dossier D (inkl. EU/CH-Verarbeitungsoptionen, ehrlich: "alles in der Schweiz auch für KI" verspricht heute niemand glaubwürdig). **Empfehlung: SELBST (hoch), als Differenzierer prominent führen.**

## E16 · Datenschutz/nDSG + AVV

**Verlangt:** "Datenschutz sicherzustellen". **Liefern:** AVV mit TOMs-Anhang, Unterauftragsverarbeiter-Liste, DSFA vor Produktivsetzung (Vorsorge-Nähe!), Meldeprozess 24h. **Heute:** Wissensbasis in Dossier D [V-fundiert]; AVV-Template = WS6.5. **Lernpfad:** 10-20h + optional Anwalts-Review des AVV (CHF 500-1'500 gut investiert) [G]. **Empfehlung: SELBST mit punktuellem Anwalts-Review (hoch).**

## E17 · BVG-/GeBüV-konforme Archivierung

**Verlangt:** BVG-Beilage Art. 27i-k (10 Jahre bis 100. Altersjahr, jederzeit lesbar). **Liefern:** NICHT zwingend ein eigenes 70-Jahre-Archiv. Ehrliche Architektur (Dossier D): Plattform = operatives System; Dokumente mit Vorsorge-Charakter werden an ein dediziertes revisionssicheres Archiv übergeben; Optionen: bestehendes DMS von vRv, SharePoint + Purview Retention (in Business Premium enthalten, CH-Datenhaltung, Stärke der Variante Microsoft [V, Dossier C]) oder von uns eingerichteter WORM-Objektspeicher (PDF/A, Object Lock, Hash/Zeitstempel, protokollierte Migration [V, GeBüV]). **Lernpfad:** 20-40h Purview-Retention-Praxis bzw. Object-Lock-Setup [G]. **Empfehlung: SELBST als Architektur + Anbindung; Archiv-Ablageort nach Kundenpräferenz (Frage g7) (hoch).**

---

## Entscheidungsmatrix (am 21.7. ausfüllen)

| # | Teilbereich | Empfehlung (Konfidenz) | Team-Entscheid | Konsequenz Offerte/Upskilling |
|---|---|---|---|---|
| E1 | Hosting/RZ | Selbst (hoch) | | CH-Hosting-Standard definieren (WS6.3) |
| E2 | Netzwerk vor Ort | Partner, Design von uns (hoch) | | Partner-Shortlist + Pflichtenheft |
| E3 | Hardware | Selbst als Koordination, Einkauf Partner/Kunde (hoch) | | Deployment in Stunden bepreisen |
| E4 | Endpoints/Betriebssoftware | Selbst + Support-Fenster + Backstop (mittel-hoch) | | **150-250 Lernstunden ab sofort (MD-102); Modul 2/6 vertiefen; Versicherung erweitern** |
| E5 | EDR-Konzept | Wissen selbst; Betrieb folgt E4 (hoch) | | Modul 2 |
| E6 | Firewall | Cloud selbst; Perimeter folgt E2 (hoch) | | Antwortpaket fertig |
| E7 | AlwaysOnVPN | Reframe auf Entra-Route; sonst Partner (hoch) | | Gesprächsleitfaden g5 |
| E8 | SLA-Betrieb Plattform | Selbst (hoch) | | SLA-Baukasten WS5.5 |
| E9 | Datenmigration | Selbst (hoch) | | Position in Offerte |
| E10 | Schulung | Selbst (hoch) | | Position in Offerte |
| E11 | PL + Architektur | Selbst (hoch) | | PL-Vorlagen bauen; Modul 5 |
| E12 | Plattform-Bau | Selbst (hoch) | | Herz des Angebots |
| E13 | pebe-Integration | Selbst, pebe-Kontakt früh (hoch) | | Freigabe-Frage c5 am 5.8.; Fragen P1-P8 an pebe |
| E14 | Hauswart-App | Selbst (hoch) | | Offline-Entscheid nach e6 |
| E15 | KI-Strategie | Selbst (hoch) | | Baustein aus Dossier D |
| E16 | nDSG/AVV | Selbst + Anwalts-Review (hoch) | | WS6.5 |
| E17 | BVG-Archivierung | Selbst als Architektur + Anbindung (hoch) | | Ablageort nach g7 |

**Die eine echte Debatte am 21.7. ist E4** (Endpoints selbst vs. Partner): Sie kostet 150-250 Lernstunden einer Person bis Oktober plus dauerhafte Helpdesk-Bindung, bringt aber wiederkehrenden Umsatz (~CHF 2'500/Monat bei 28 Seats zu Marktpreisen), den einzigen zu uns passenden Infra-Block und die glaubwürdige "alles aus einer Hand mit einem Vor-Ort-Partner"-Story. Alles andere ist nach Datenlage klar.

## Partner-Modell + fairer Deal (falls E2/E3/E7-Partner)

Drei Muster [V/G]: (1) **Referral** (Partner kontrahiert direkt, 5-10% Vermittlungsprovision üblich), (2) **Subunternehmer** (wir Prime mit Back-to-back-SLAs, Aufschlag 10-30%; Achtung: wir haften voll für Partner-Fehler, muss die Berufshaftpflicht explizit tragen), (3) **Teillose/Konsortium** (getrennte Verträge je Block, wir als Gesamtkoordinator mit ausgewiesenem Koordinationsmandat). **Empfehlung: Muster 3** — sauberste Haftung, volle Transparenz (Evaluationskriterium!), kein Durchlaufumsatz, und exakt die ausgeschriebene Rolle.

**Partner-Checkliste:** Microsoft Solutions Partner Designation (nicht nur Logo) · KMU-Referenzen 20-50 MA, ideal Immobilien/Treuhand · Vor-Ort-Radius Solothurn <30-45 min · reale Helpdesk-Zeiten/Ferienabdeckung · RMM/EDR/Monitoring-Stack + Runbooks · eigene Berufshaftpflicht + Cyber nachweisen · Back-to-back-SLA-Bereitschaft · Exit-Regelung (Tenant + Doku gehören dem Kunden) · **kein Eigeninteresse an konkurrenzierender Plattform**.

**Longlist Region (Websites geprüft 10.7.; Grössen via HR/LinkedIn vor Shortlist verifizieren):**

| Firma | Ort | Profil | Vorbehalt |
|---|---|---|---|
| headware informatik ag | **Solothurn** | Managed Workplace + Infrastructure, eigene Private Cloud im Solothurner RZ | Grösse/MS-Partnerstatus prüfen |
| MBB MOSER AG | Recherswil SO | ICT-Infrastruktur, Netzwerk, Managed, 35+ Jahre | Intune-/M365-Tiefe prüfen |
| AWeb Informatik | Olten SO | Netzwerk + Security, M365, Intune, MDR | Grösse prüfen |
| Support-4-IT AG | Burgdorf BE | KMU-IT, M365, Windows 365, Dell-Hardware | Firewall-Betriebs-Tiefe prüfen |
| IN4OUT AG | Aarau AG | Zertifizierter MS-Partner, Managed Workplace/Security | ~40 min Distanz, Vor-Ort-SLA klären |
| Boss Info AG | Langenthal BE | Stärkste MS-Designationen der Liste | Gross + eigene Produkte (bossERP/DMS): Kanalkonflikt aktiv prüfen; Plan B |

**Achtung Wettbewerbs-Doppelrolle:** Jeder dieser Partner ist potenziell selbst Mitbieter (Dossier B nennt den bestehenden IT-Dienstleister von vRv als wahrscheinlichsten Microsoft-Lager-Bieter). Partner-Ansprache erst NACH dem 5.8., wenn klar ist, wer der heutige IT-Partner ist (Frage g1) und ob er mitbietet.

## Konsequenzen fürs Upskilling (nach Scope-Entscheid)

- **E4 = selbst:** Modul 2 wird um Intune/Defender-Praxis erweitert; eine Person (Vorschlag: Joaquin oder Tej) startet den MD-102-Pfad sofort (12-20h/Woche bis Oktober); Test-Tenant + 3-5 Pilotgeräte aufsetzen; Versicherungsanfrage um "Managed Endpoint/Workplace Services" erweitern.
- **E4 = Partner:** Modul 2 bleibt konzeptionell (sprechfähig, nicht betreibend); dafür Partner-Evaluation als neue Task (nach 5.8.).
- **In beiden Fällen:** Modul 6 übernimmt die Entra-/Conditional-Access-Argumentation (E7-Reframe) und die pebe-Integrationsmuster (E13).

## Quellen (zusätzlich zu Dossiers A-D)

MD-102/SC-300: learn.microsoft.com/en-us/training/courses/md-102t00, /sc-300t00 · Business Premium Inhalt/Preis: learn.microsoft.com (m365bp-security-faq, mdb-overview), microsoft.com/de-ch (Pläne), computech.ch/microsoft-365/articles/preise · Preiserhöhung 1.7.2026: itreseller.ch/Artikel/104527 · MSP-Benchmarks: superops.com (0.96-1.34 h/User/Mt), auvik.com (Endpoints/Techniker), kaseya.com (US-Preise), kpx-it.ch + it-provider.ch (CH-Preise, WLAN-Kosten) · Hardware-Margen: channelpartner.de/a/das-geheimnis-hoher-hardware-margen,3041207 (COMPRiS, n=353) · Autopilot: learn.microsoft.com/en-us/autopilot/add-devices · AOVPN: learn.microsoft.com (tutorial-aovpn-deploy-create-certificates), directaccess.richardhicks.com · Entra Private Access Preis: microsoft.com/en-us/security/business/microsoft-entra-pricing · Versicherung: zurich.ch (IT-Dienstleister), exali.ch, swissICT-Warnung · Partner-Deals: sakasandcompany.com (Referral 5-10%), knowbe4.com/legal (SLA-Flow-down) · Firewall-Betrieb: emasi.ch (FortiGate-aaS ab CHF 390/Mt), care4it.ch · Longlist: headware.ch, mbbmoser.ch, aweb.ch, support-4-it.ch, in4out.ch, bossinfo.com.

---

*Dossier E, erstellt 10.7.2026 (8 Tage vor Soll-Termin 18.7.). Nächster Schritt: Team liest Executive Summary + E4 vor der Session am 21.7.; Entscheid-Spalte wird in der Session gefüllt; Ergebnis fliesst in Deck (WS3.1), Architektur-Papier (WS5.2), Offerten-Skelett (WS5.1) und Upskilling-Vertiefung (WS2).*
