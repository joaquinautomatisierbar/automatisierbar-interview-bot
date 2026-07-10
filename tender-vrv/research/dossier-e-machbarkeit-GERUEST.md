# Dossier E: Teilbereichs-Machbarkeitsanalyse (GERÜST)

> **Status: Gerüst, in Arbeit. Fällig: 18.7.2026. Entscheidungs-Session: 21.7. (an S3).**
> Auftrag (Joaquin, 10.7.): Kein Teilbereich wird vorab ausgeschlossen. Für jeden abgefragten Teilbereich beantworten wir erst, was er konkret verlangt und ob er bis Projektstart erlernbar ist (egal was es kostet, der Preis wird in Stunden beziffert). DANN entscheidet das Team objektiv mit Pros und Cons: selbst anbieten / mit Partner / nicht anbieten.
> Inputs: Dossiers A-D (laufen), eigene Betriebserfahrung (VPS, Backups, Auth, Deploys), Web-Recherche je Teilbereich.

## Bewertungsraster (für jeden Teilbereich identisch)

1. **Was verlangt der Kunde konkret?** (Zitat/Ableitung aus der Ausschreibung)
2. **Was muss geliefert und was dauerhaft betrieben werden?** (Einmal-Leistung vs. Betriebsverantwortung)
3. **Können wir das heute schon?** (ehrliche Selbsteinschätzung, mit Beleg aus bestehenden Systemen)
4. **Erlernbar bis Projektstart (~Sept/Okt 2026)?** Lernpfad, Ressourcen, Übungsumgebung, geschätzte Stunden pro Person
5. **Laufender Betriebsaufwand** (Stunden/Monat, Pikett-Frage, Werkzeuge)
6. **Haftung + Versicherung** (was passiert bei Fehler/Ausfall, deckt die geplante Police das)
7. **Marge/Kommodität** (verdient man daran, oder ist es Durchlaufposten mit Preisvergleich)
8. **Optionen mit Pros/Cons:** selbst / mit Partner (wer käme in Frage) / nicht anbieten (wie begründen wir das elegant)
9. **Empfehlung + Konfidenz** (die Entscheidung trifft das Team am 21.7.)

## Teilbereiche (aus "Gewünschte Informationen" + Umsetzung der Ausschreibung)

| # | Teilbereich | Ausschreibungs-Bezug | Vorbefund (10.7., zu verifizieren) |
|---|---|---|---|
| E1 | Rechenzentrum/Hosting der Lösung | "Rechenzentrum: Ort, Umfang, Art" | Können wir: betreiben heute selbst VPS + Backups + TLS. Zu klären: CH-Rechenzentrum-Story (Infomaniak/Exoscale/Azure CH) statt Hostinger |
| E2 | Netzwerk-Bereitstellung beim Kunden (LAN/WLAN/Firewall-Hardware) | "Bereitstellung Netzwerk (Initial/laufend, Managed Services)" | Klassisches Systemhaus-Terrain, physische Präsenz + Hardware-Logistik. Partner-Kandidat |
| E3 | Hardware-Infrastruktur (Arbeitsplätze, Server, Mobile) | "Bereitstellung Hardware (on-premise, Cloud, Managed)" | Einkauf/Rollout/Lifecycle = Betriebsgeschäft. Partner-Kandidat; Mobile-Geräte evtl. Teilscope (MDM?) |
| E4 | Betriebssoftware + Endpoint-Management (OS, Patching, EDR) | "Betriebssoftware (OS, Sicherheits-SW, Managed)" | Erlernbar (Intune/Defender-Stack), aber dauerhafte Betriebsverantwortung + Pikett. Genau rechnen |
| E5 | EndpointSecurity/EDR-Konzept | "Sicherheitsstandards: EndpointSecurity" | Konzept-Wissen erlernbar in Tagen (Dossier D); Betrieb siehe E4 |
| E6 | Firewall (Perimeter + Cloud) | "Firewalls" | Cloud-seitig (Security Groups, WAF) können wir; On-prem-Perimeter siehe E2 |
| E7 | VPN/AlwaysOnVPN | "Mobile Anbindung: AlwaysOnVPN" | Begriff + moderne Alternativen (Zero Trust/Conditional Access) erlernbar in Tagen; On-prem-VPN-Betrieb eher Partner. Klären was vRv wirklich meint (Frage g5) |
| E8 | Managed Services/SLA-Betrieb unserer Lösung | "SLAs: Reaktions-/Lösungszeiten, Verfügbarkeiten" | Für UNSERE Plattform machbar (Monitoring, Alerting existiert); 24/7 vs. Bürozeiten ehrlich definieren. SLA-Baukasten WS5.5 |
| E9 | Datenmigration | "Zusatzkosten: Datenmigration" | Kernkompetenz (Skripte, Mapping, Validierung). Selbst |
| E10 | Schulung | "Zusatzkosten: Schulung" | Können wir (Key-User-Prinzip, Videos, Doku). Selbst |
| E11 | Projektleitung + Architektur | "Rolle Lösungsanbieter: Architektur und Projektleitung" | Methodik erlernbar + bereits praktiziert (Multi-Track-Builds); Gegenpart bei vRv nötig (Frage h5). Selbst, Vorgehen sauber dokumentieren |
| E12 | Plattform-Bau (Kern) | "Zentralisierte Plattform, Workflow-Automatisierung" | Kernkompetenz, mehrfach belegt (Hub, Cockpit, PWAs). Selbst |
| E13 | pebeFinance-Integration | "Integration pebeFinance in O365-Welt" | Machbar via belegte Flächen (CSV-Import); Detailtiefe hängt an Dossier A + Freigabe für pebe-Kontakt (Frage c5) |
| E14 | Mobile Hauswart-App | "Apps mit Checklisten, Foto-Funktion, GPS" | Kernkompetenz (Walk-in PWA, Ausgaben-PWA beweisen das Muster). Offline-Frage e6 beachten |
| E15 | KI-Strategie (Dokument + Umsetzung) | "KI- und Sicherheitsstrategie sicherstellen" | Können wir glaubwürdig (tägliche Praxis); Strategie-Dokument = Dossier D Baustein. Selbst |
| E16 | Datenschutz/nDSG + AVV | "Datenschutz sicherzustellen" | Erlernbar + teils vorhanden; AVV-Template = WS6.5. Selbst, ggf. Anwalts-Review als Zusatz |
| E17 | BVG-/GeBüV-konforme Archivierung | Beilage Art. 27i-k BVV 2 | Anforderung verstehen (Dossier D); Architektur-Frage: eigenes Archiv-Modul vs. Anbindung bestehendes DMS/SharePoint-Retention (Frage g7) |

## Entscheidungsmatrix (am 21.7. ausfüllen)

| Teilbereich | Entscheid (selbst/Partner/nicht) | Begründung (1 Satz) | Konsequenz für Offerte + Upskilling |
|---|---|---|---|
| E1 | | | |
| E2 | | | |
| ... | | | |

## Partner-Longlist (falls Modell "mit Partner" gewählt wird)

Zu recherchieren bis 18.7.: 2-3 Systemhäuser Region Solothurn/Mittelland mit M365-Fokus (für E2-E4), Kriterien: KMU-Fokus, Subunternehmer-Bereitschaft, kein Eigeninteresse an der Plattform-Schicht. Kandidaten aus Dossier B/D ableiten.
