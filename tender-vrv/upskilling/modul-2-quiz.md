# Modul 2 · Quiz + Drill

> 15 min in Session 3, ohne Primer offen. Lösungen zuunterst. Bestehensgrenze fürs Selbstvertrauen: 10 von 12. Danach direkt in die Scope-Entscheidungs-Session (Dossier E Matrix).

## Quiz (12 Fragen)

1. Nenne die drei Verantwortungsschichten unseres Sicherheitsmodells und wer je verantwortlich ist.
2. Was unterscheidet EDR von klassischem Antivirus, und welches Produkt ist die KMU-Realität in der M365-Welt?
3. Die drei Firewall-Ebenen: welche betreiben wir selbst, welche nicht?
4. Was ist Always On VPN technisch (Hersteller, zwei Tunnel-Typen), und welchen Serverbetrieb zieht es nach sich?
5. Wie lautet unser Reframe der AlwaysOnVPN-Anforderung, und mit welchen zwei Microsoft-Fakten begründen wir ihn?
6. Definiere RTO und RPO und nenne unsere ehrlichen Zielwerte.
7. Was bedeutet 3-2-1 beim Backup, und was ist wichtiger als das Backup selbst?
8. Vier Elemente einer sauberen Berechtigungsstruktur (RBAC) für die vRv-Plattform.
9. Sind wir ISO-27001-zertifiziert? Wie lautet die vollständige, ehrliche Antwort?
10. E4-Entscheid: Nenne Lernaufwand, monatlichen Betriebsaufwand für 28 Seats und den Marktpreis pro User/Monat.
11. Welche Versicherungs-Konsequenz hat E4 = selbst, und in welchen Task fliesst sie?
12. Innert 48 Stunden: was passiert bei uns in dieser Frist in zwei verschiedenen Kontexten? (Tipp: Patch + Datenschutz)

## Drill (offene Transfer-Fragen, je 2 min)

D1. Schmid: "Wer garantiert mir, dass nicht einer Ihrer Praktikanten unsere Daten absaugt?" (Es gibt keine Praktikanten. Antworte trotzdem souverän.)
D2. Guldimann: "Unser IT-Partner sagt, ohne VPN ist nichts sicher." Antworte, ohne den Partner zu diskreditieren.
D3. Böni: "Was passiert konkret am Montagmorgen, wenn Ihr Server am Sonntag abbrennt?" Erzähle die Wiederherstellung als Geschichte mit Zeiten.
D4. Kunz: "Meine Hauswarte haben ihre privaten Handys. Ist das nicht unsicher?" Antworte mit dem Unterschied App-Daten vs. Geräteverwaltung (und was davon wessen Entscheid ist).
D5. Schmid: "Bieten Sie uns den IT-Betrieb gleich mit an?" Antworte VOR dem 21.7. (Entscheid offen), ohne etwas zu versprechen und ohne schwach zu wirken.

---

## Lösungen

1. Physisch/Infrastruktur = zertifizierter RZ-Anbieter (ISO 27001, gemietet); Plattform/Applikation = wir, voll verantwortlich (Architektur, Betrieb, Daten, Backups); Kundenumgebung (Büronetz, Endgeräte, M365-Tenant) = vRv bzw. ihr IT-Partner, je nach E4-Entscheid teilweise wir.
2. Antivirus erkennt bekannte Signaturen; EDR zeichnet Verhalten kontinuierlich auf (Prozesse, Verbindungen, Dateizugriffe), erkennt Angriffsmuster und erlaubt Reaktion (Gerät isolieren, Prozess beenden). KMU-Realität: Microsoft Defender for Business, in Business Premium enthalten, verwaltet über Intune.
3. (1) Perimeter-Firewall am Büro-Netzrand: nicht wir (IT-Betrieb vRv bzw. E2-Partner). (2) Host-Firewall auf jedem Server: wir. (3) Cloud Security Groups: wir. Öffentlich nur 443/HTTPS, Admin nur per Schlüssel von definierten Quellen.
4. Microsoft-Windows-Technologie, Nachfolger von DirectAccess. Device Tunnel (verbindet vor dem Login, nur IKEv2, domain-joined Geräte) und User Tunnel (nach dem Login). Dahinter: RRAS-VPN-Server, NPS/RADIUS mit EAP-TLS und eine eigene PKI mit Zertifikats-Rollout, dauerhaft zu betreiben; typische Störungen (CRL, Zertifikats-Mismatch) sind sofort P1.
5. Reframe: "sicherer mobiler Zugriff" statt wörtlich AOVPN. Begründung: (a) Microsoft positioniert Entra Private Access (USD 5/User/Monat) explizit als Nachfolger klassischer VPNs, (b) SSTP-Retirement per 31.3.2026 als Signal, dass die Legacy-Schiene ausläuft. Unsere Lösung selbst braucht ohnehin kein VPN (TLS + Entra SSO + MFA); Tool-Frage g5 klärt, was vRv wirklich meint.
6. RTO = maximale Zeit bis der Dienst wieder läuft; RPO = maximal tolerierter Datenverlust (Zeit seit letzter Sicherung). Unsere Zielwerte: RPO max. 24h (mit Point-in-Time-Recovery der Datenbank besser), RTO wenige Stunden zu Servicezeiten; Monitoring/Alarmierung automatisiert 24/7, personelle Reaktion zu vereinbarten Zeiten, kein 24/7-Pikett als Standard.
7. 3 Kopien der Daten, auf 2 verschiedenen Systemen/Medien, 1 davon an einem anderen Ort/Anbieter, idealerweise unveränderbar (Ransomware-Schutz). Wichtiger als das Backup: der getestete, dokumentierte Restore.
8. Rollen statt Einzelrechte (Administration, Sachbearbeitung, Hauswart, Read-only-Revision) · Least Privilege (Minimum je Rolle, Admin getrennt) · persönliche Konten, keine Sammel-Logins, Audit-Log · Objektbindung (Hauswart sieht nur zugewiesene Liegenschaften/Aufträge) · Join/Leave wirkt automatisch via Entra-SSO. (Vier davon.)
9. Nein. Vollständig: "Nein, und bei vier Personen wäre die Behauptung unglaubwürdig. Zertifiziert sind die Schweizer Infrastrukturanbieter, auf denen wir betreiben. Wir arbeiten nach dem BACS-KMU-Merkblatt, orientieren uns am IKT-Minimalstandard des Bundes und legen unsere technisch-organisatorischen Massnahmen dokumentiert vor."
10. Lernpfad 150-250 Stunden (MD-102, 120h Stoff, plus Conditional-Access-Teile aus SC-300) für eine Person bis Oktober. Betrieb 25-40 Stunden/Monat all-in für ~28 Seats (reine Policy-/Patch-Pflege 8-15h). Marktpreis CHF 50-120 pro User/Monat, bei 28 Seats rund CHF 2'520/Monat.
11. Managed-(Security-)Services müssen in der Berufshaftpflicht ausdrücklich eingeschlossen sein; sonst Deckungslücke bei Patch-/Konfigurationsfehlern mit Drittschaden. Fliesst in die Versicherungsanfrage Task 6.1 (Template wird um "Managed Endpoint/Workplace Services" erweitert).
12. (a) Kritische Sicherheitslücken in unseren Systemen werden innert 48h behandelt (Patch-Management). (b) Nicht verwechseln: Datenschutzverletzungen melden wir dem Kunden innert 24h nach Feststellung (nDSG-Zusage, Modul 3).

### Drill-Leitplanken (Elemente, die vorkommen müssen)

D1: Ruhig bleiben, nicht beleidigt → Zugriffe laufen über persönliche Konten mit minimalen Rechten, produktiver Datenzugriff nur wer ihn für Betrieb/Support braucht, alles protokolliert → AVV mit Vertraulichkeitspflicht → und ehrlich: bei vier benannten Personen wissen Sie genauer als bei jedem Grossanbieter, wer Zugriff hat.
D2: Zustimmen im Kern (Tunnel schützt Alt-Systeme im Firmennetz) → unsere Lösung ist kein Alt-System: TLS + Entra-Login + MFA + Conditional Access, das ist das Modell, zu dem Microsoft selbst rät → beides koexistiert problemlos; gerne stimmen wir uns mit dem Partner ab (Split-Tunnel-Ausnahme).
D3: Konkrete Kette: Alarm schlägt automatisch an → wir werden benachrichtigt, Sie innert definierter Frist informiert → neuer Server aus Infrastruktur-Vorlage, Restore aus verschlüsseltem Backup beim Zweitanbieter (getesteter Ablauf) → Datenverlust maximal seit letzter Sicherung (RPO ≤ 24h, DB besser) → Ziel: mittags läuft es wieder; ehrlich: Werktag-Zeiten, kein Sonntagspikett im Standard.
D4: Trennen: Die App speichert lokal nur verschlüsselt Zwischenstände und synchronisiert; Login über Firmenkonto mit MFA, Zugriff entziehbar → Geräteverwaltung (MDM) privater Handys ist eine Firmen-Policy-Frage von vRv (BYOD vs. Firmengeräte), die wir neutral aufnehmen (Tool e-Kapitel) → keine Panikmache, keine Verharmlosung.
D5: Nicht zusagen, nicht kneifen: "Wir prüfen das gerade seriös, inklusive dessen, was es an Bereitschaft wirklich braucht; unsere Antwort steht in der Offerte als eigenes Los mit klaren Servicezeiten. Was wir sicher nicht tun: Ihnen heute einen 24/7-Betrieb versprechen, den ein Vier-Personen-Team nicht ehrlich leisten kann."
