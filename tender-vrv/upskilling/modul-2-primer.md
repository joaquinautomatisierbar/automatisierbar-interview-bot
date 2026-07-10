# Modul 2 · Cybersecurity + IT-Infrastruktur

> Session 3, Owner: **Joaquin** (unterrichtet die anderen drei). An dieselbe Session angehängt: **Scope-Entscheidungs-Session (45 min, Dossier E Matrix füllen)**. Lesezeit ~45 min.
> Grundlage: [research/dossier-d-security-compliance.md](../research/dossier-d-security-compliance.md) (Begriffskatalog mit fertigen sprechfähigen Antworten, Verweise als [D §n]) + [research/dossier-e-machbarkeit.md](../research/dossier-e-machbarkeit.md) (Teilbereichs-Analyse, Verweise als [E n]).
> Warum dieses Modul: Die Ausschreibung fragt wörtlich EndpointSecurity, Firewall, VPN, AlwaysOnVPN, Notfallkonzept, Berechtigungsstruktur ab. Ein Wirtschaftsprüfer merkt in einer Minute, ob jemand Begriffe aufsagt oder versteht. Und: Die grösste Team-Entscheidung des Projekts (E4) hängt an diesem Stoff.

## Lernziele

Nach der Session kann jeder von uns:

1. Jeden Sicherheitsbegriff der Ausschreibung in zwei Sätzen erklären UND in einem dritten sagen, wie WIR ihn beantworten.
2. Die Verantwortungsgrenze ziehen: was wir liefern (Applikationsschicht, Betrieb unserer Lösung), was beim Kunden/IT-Partner bleibt (Büronetz, Endgeräte), ohne dass es nach Ausrede klingt.
3. AlwaysOnVPN korrekt einordnen und den Zero-Trust-Reframe begründen.
4. Den E4-Entscheid (Endpoints selbst betreiben?) mit Zahlen führen: Lernstunden, Betriebsstunden, Marktpreis, Risiken.
5. Unser eigenes Sicherheits-Niveau ehrlich beschreiben (was steht, was fehlt), ohne uns kleiner oder grösser zu machen.

---

## 1. Das Prinzip zuerst: Verantwortungsschichten

Bevor Begriffe kommen, das Modell, das alle Antworten trägt [D §1]:

- **Physisch/Infrastruktur:** Rechenzentrum (Gebäude, Strom, Netz) → zertifizierter Anbieter (ISO 27001), wir mieten.
- **Plattform/Applikation:** Architektur, Code, Betrieb, Datenhaltung, Backups unserer Lösung → **wir, voll verantwortlich.**
- **Kundenumgebung:** Büronetz, Endgeräte, M365-Tenant von vRv → vRv bzw. deren IT-Partner (je nach Scope-Entscheid auch wir, siehe E4).

Diese Trennung ist keine Ausrede, sondern exakt die "Verantwortlichkeiten, Leistungsabgrenzungen", die die Ausschreibung verlangt. Wer alles verspricht, hat entweder ein 50-Personen-NOC oder lügt.

## 2. Die Begriffe der Ausschreibung (Erklärung → unsere Antwort)

Vollständige sprechfähige Antworten stehen fertig in [D §2 und §7]; hier die Kurzform zum Lernen.

**Endpoint Security / EDR** [D §2.1]. Schutz der Endgeräte: Verschlüsselung, Malware-Schutz, zentrale Verwaltung (MDM). EDR geht über Antivirus hinaus: beobachtet Verhalten (Prozesse, Verbindungen), erkennt Muster, kann reagieren (Gerät isolieren). KMU-Realität: Microsoft Defender for Business, in Business Premium enthalten, verwaltet über Intune. **Unsere Antwort:** eigene Geräte verschlüsselt + EDR + MFA; für vRv-Geräte bleibt es beim IT-Partner (oder bei uns, falls E4 = selbst); unsere Lösung braucht keinen Agent auf ihren Geräten, sie läuft über TLS im Browser.

**Firewall, drei Ebenen** [D §2.2]. (1) Perimeter am Büro-Netzrand (Appliance), (2) Host-Firewall auf jedem Server, (3) Cloud Security Groups beim Anbieter. Cloud-Standard: alles zu, nur HTTPS (443) öffentlich, Admin-Zugänge nur per Schlüssel von definierten Quellen. **Unsere Antwort:** (2)+(3) machen wir heute schon; (1) bleibt beim IT-Betrieb von vRv, optional IP-Beschränkung auf deren Firmen-Adressen.

**VPN und Always On VPN** [D §2.3]. VPN = verschlüsselter Tunnel ins Firmennetz. **Always On VPN ist konkret Microsoft-Windows-Technik:** baut den Tunnel automatisch auf, zwei Typen: Device Tunnel (vor dem Login, nur IKEv2, domain-joined) und User Tunnel (nach Login). Nachfolger des abgekündigten DirectAccess. Dahinter hängt echter Serverbetrieb: RRAS, NPS/RADIUS, eigene PKI mit Zertifikats-Rollout [E7]. **Unsere Antwort:** Unsere Lösung braucht kein VPN (TLS + Entra-Login + MFA); läuft transparent DURCH ein bestehendes AOVPN; das AOVPN-Setup selbst betreiben wir nicht.

**Zero Trust / Entra Private Access** [D §2.3, E7]. Moderne Alternative zum Voll-VPN: Zugriff pro Applikation nach Identität, Gerätezustand und Richtlinie statt "ganzes Netz auf". Microsoft positioniert Entra Private Access (USD 5/User/Monat) explizit als VPN-Ablösung; Signal: SSTP-Retirement per 31.3.2026. **Verwendung am Termin:** Anforderung "AlwaysOnVPN" respektvoll reframen auf "sicherer mobiler Zugriff", Entra-Route als zeitgemässe Antwort einordnen (Tool-Frage g5 klärt, was vRv wirklich meint).

**MFA** [D §2.6]. Zweiter Faktor neben dem Passwort; wirksamste Einzelmassnahme gegen Kontoübernahme. Modern: phishing-resistent (FIDO2/Passkeys) statt SMS. In der M365-Welt zentral über Conditional Access erzwungen, gilt dann auch für angebundene Dritt-Apps. **Unsere Antwort:** intern Pflicht überall; für vRv-Nutzer erbt unsere Lösung die Tenant-Policy via SSO.

**Berechtigungsstruktur / RBAC / Least Privilege** [D §2.4]. Rechte hängen an Rollen, Personen bekommen Rollen; jede Rolle nur das Minimum; Admin getrennt vom Alltagskonto; keine Sammel-Logins; Offboarding entzieht Rechte. Plus Mandanten-/Objekttrennung (Hauswart sieht nur seine Liegenschaften). **Unsere Antwort:** Rollenmodell Administration / Sachbearbeitung / Hauswart / Read-only-Revision, Audit-Log, Login über vRv-Konten (Join/Leave wirkt automatisch).

**Notfallkonzept: BCP/DR, RTO/RPO** [D §2.5]. RTO = wie schnell läuft es wieder. RPO = wie viel Datenverlust ist maximal tolerierbar. BCP = organisatorisch weiterarbeiten, DR = technisch wiederherstellen. **Unsere ehrlichen Zielwerte:** RPO max. 24h (Datenbank mit Point-in-Time besser), RTO wenige Stunden zu Servicezeiten; Monitoring + Alarmierung automatisiert rund um die Uhr, personelle Reaktion zu vereinbarten Zeiten, **kein 24/7-Pikett als Standardversprechen** (bei 4 Personen wäre alles andere gelogen; separat vereinbar).

**Backup 3-2-1** [D §2.5]. 3 Kopien, 2 Systeme, 1 davon extern, idealerweise unveränderbar (Ransomware). Entscheidend ist der **getestete Restore**, nicht das Backup. **Unsere Antwort:** täglich, verschlüsselt, Zweitanbieter-Kopie, Restore-Runbook existiert und wird geprobt (machen wir für die eigenen Produktionssysteme bereits).

**Patch-Management** [D §2.7]. Geordnetes, zeitnahes Einspielen von Updates: OS automatisch, Abhängigkeiten per Tooling überwacht, kritische Lücken innert 48h, Managed-Dienste patcht der Anbieter.

**Verschlüsselung** [D §2.8]. In transit: alles TLS, ohne Ausnahme. At rest: Datenspeicher + Backups verschlüsselt (AES-256). Geheimnisse nie im Code, sondern im Secrets-Management. Auf Wunsch feldweise Zusatzverschlüsselung.

**Referenzrahmen, die wir nennen können** [D §7]: BACS-Merkblatt Informationssicherheit für KMU (unsere Grundmassnahmen-Checkliste) und IKT-Minimalstandard des Bundes (NIST-basiert: Identify/Protect/Detect/Respond/Recover). Wichtig: **Wir sind NICHT ISO-27001-zertifiziert und sagen das offen**; zertifiziert sind die Infrastrukturanbieter.

## 3. Unser eigenes Haus, ehrlich (Selbstauskunft für Rückfragen)

Steht: MFA auf allen Systemen, Passwort-Manager, verschlüsselte Geräte, persönliche Konten, Least-Privilege-Zugriffe, tägliche verschlüsselte Backups mit getestetem Restore-Runbook, automatisiertes Monitoring mit Alarmierung, dokumentierte Deploys.
Fehlt (und wird nicht vorgetäuscht): ISO-Zertifizierung des Unternehmens, 24/7-Pikett mit Menschen, dediziertes SOC. Ehrlichkeit hier ist Positionierung: Der Prüfer testet nicht das Niveau, sondern ob wir flunkern.

## 4. Die Scope-Entscheidung E4 (der eigentliche Grund, warum diese Session zählt)

An S3 entscheidet das Team pro Teilbereich: selbst / Partner / nicht anbieten. Fast alles ist nach Datenlage klar [E, Matrix]. **Die eine echte Debatte ist E4: Endpoints/Betriebssoftware selbst betreiben?**

**Was "selbst" konkret heisst** [E4]: Intune-Enrollment via Autopilot, Compliance-Policies, Update-Rings, App-Deployment, Defender-Alert-Triage, On-/Offboarding-Runbooks, Reporting, Helpdesk-Fenster für ~28 Seats.

**Die Zahlen für die Debatte** (alle [E4], dort quellenbelegt):

| Grösse | Wert |
|---|---|
| Lernpfad | MD-102 (120h Stoff) + Conditional-Access-Teile SC-300: **150-250h** für eine Person bis Oktober (12-20h/Woche) |
| Betrieb | Benchmarks ~1h/User/Monat → **25-40h/Monat all-in** inkl. Helpdesk; reine Policy-/Patch-Pflege 8-15h |
| Marktpreis | CHF 50-120/User/Monat Managed Workplace → 28 Seats ≈ **CHF 2'520/Monat** wiederkehrend |
| Effektiver Stundensatz | CHF 63-100/h, mit Automatisierungs-Disziplin eher oben |
| Lizenzbasis | Business Premium (CHF 17.80/User/Mt. Stand alt; **Preiserhöhung 1.7.2026, neu ziehen**) enthält Intune + Defender + Entra P1 |
| Versicherung | Managed-(Security-)Services müssen in der Berufshaftpflicht **explizit** vereinbart sein → Anfrage 6.1 erweitern |

**Pro selbst:** einziger Infra-Block, der zu uns passt (cloud-only, Runbook-Disziplin ist unsere Stärke); wiederkehrender Umsatz; macht "alles aus einer Hand mit einem Vor-Ort-Partner" glaubwürdig.
**Contra selbst:** Helpdesk-Bindung + Ferienabdeckung im 4er-Team; souverän erst nach 6-12 Monaten Praxis; Haftungsfolgen.
**Der Mittelweg (Empfehlung Dossier E):** selbst mit definiertem Support-Fenster (Mo-Fr 08-17, Reaktion 4h) + vertraglichem Partner-Backstop für schwere Security-Incidents. Konfidenz mittel-hoch; genau darüber stimmen wir ab.

**Nicht zur Debatte (Empfehlungen hoch, nur bestätigen):** E1 Hosting selbst · E2 Netzwerk vor Ort Partner (mit unserem Pflichtenheft) · E3 Hardware als Koordination, Einkauf Partner/Kunde · E7 AOVPN reframen, sonst Partner · E8-E17 selbst.

**Vorbereitung für alle vier:** Vor S3 die Executive Summary + E4 in Dossier E lesen (15 min). Wer dagegen stimmen will, bringt eine Zahl mit, kein Bauchgefühl.

## 5. Verbindung zur Aufsichts-Frage (Vorgriff auf Modul 3)

Ein Satz reicht hier, Details in Modul 3 und [D §5]: Die Vorsorgeeinrichtung untersteht **BVSA (Direktaufsicht) + OAK BV (Oberaufsicht), nicht der FINMA** (die beaufsichtigt in der 2. Säule nur Lebensversicherer). "BVG allenfalls FINMA" in der Ausschreibung lesen wir als: BVG zwingend, FINMA-Niveau freiwillige Messlatte (RS 2023/1: Verantwortlichkeiten, Auditierbarkeit, Datenstandort).

---

## 6. Zehn sprechfähige Sätze (auswendig können)

1. "Wir beantworten Ihre Sicherheitsfragen als Software- und Betriebsanbieter unserer Lösung; Büronetz und Endgeräte bleiben sauber abgegrenzt bei Ihrem IT-Betrieb." (Variante, falls E4 = selbst: "... können wir auf Wunsch als eigenes Los übernehmen.")
2. "Öffentlich erreichbar ist bei uns genau ein Port: HTTPS. Administration läuft nur mit Schlüssel-Authentifizierung von definierten Quellen."
3. "EDR heisst: Das Gerät wird beobachtet, nicht nur gescannt. Auffälliges Verhalten wird erkannt und das Gerät kann isoliert werden."
4. "Unsere Lösung braucht kein VPN: verschlüsselte Verbindung, Anmeldung über Ihre Microsoft-Konten, Ihre MFA-Regeln gelten automatisch."
5. "Wenn Ihre Geräte Always On VPN fahren, läuft unsere Lösung transparent hindurch; das VPN-Setup selbst bleibt bei Ihrem IT-Partner."
6. "Für den mobilen Zugriff positioniert Microsoft heute Zero Trust über Entra als Nachfolger des Voll-VPN; das ordnen wir gerne ein, bevor jemand teuren Legacy-Betrieb offeriert."
7. "Backup heisst bei uns 3-2-1 mit einer Kopie beim Zweitanbieter, und wir testen die Wiederherstellung, statt sie zu behaupten."
8. "Unsere ehrlichen Zielwerte: maximal 24 Stunden Datenverlust im schlimmsten Fall, Wiederanlauf in Stunden zu Servicezeiten, Überwachung automatisiert rund um die Uhr."
9. "Jede Aktion in der Plattform ist einem persönlichen Konto zugeordnet, sicherheitsrelevante Schritte stehen im Audit-Log; für die Revision gibt es eine Nur-Lese-Rolle."
10. "Wir sind nicht ISO-zertifiziert und behaupten das auch nicht; zertifiziert sind die Schweizer Rechenzentren, auf denen wir betreiben, und wir arbeiten nach dem KMU-Merkblatt des Bundesamts für Cybersicherheit."

## 7. Verbindung zu den anderen Modulen

- **Modul 1 (S2):** Entra ID/Conditional Access als Identitäts-Sockel; Business-Premium-Inhalt (Intune/Defender/Purview).
- **Modul 3 (S4):** nDSG/AVV, BVG-Archivierung, Aufsichts-Landkarte im Detail.
- **Modul 6 (S5):** Entra-Private-Access-Argumentation technisch, Integrations-Sicherheit (Secrets, Validierung).
- **Offerte:** Dieses Modul + [D §7] füllen die Kapitel 8.1 bis 8.4; der E4-Entscheid bestimmt Kapitel 10.3.
