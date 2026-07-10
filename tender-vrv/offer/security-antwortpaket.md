# Security-Antwortpaket: Sicherheit, Datenschutz und Betrieb

> Task WS3.4. Kundendokument: füllt die Offerten-Kapitel 8 (Sicherheit) und dient als eigenständiges Handout, falls vRv Sicherheitsfragen vor der Offerte schriftlich beantwortet haben will. Gliederung folgt exakt den "Gewünschten Informationen" der Ausschreibung. Quellen: Dossier D §7/§8 (quellenbelegt), hosting-kostenblatt.md, sla-baukasten.md, datenschutz-statement.md.
> **ENTWURF.** Vor jedem Aussen-Einsatz: (1) alle **[6.3]**-Marker nach dem Hosting-Entscheid definitiv setzen ("vorgesehen" raus), (2) Versicherungs-Satz in §1 nach Stand 6.1 aktualisieren, (3) Joaquin-Review, (4) Konsistenz-Check: 24h-Meldefrist (AVV Ziff. 9), RPO/RTO (SLA-Baukasten), 48h-Patch-Frist (Modul 2) müssen überall identisch sein.

---

## 1. Unser Verantwortungsmodell (die Klammer vor allen Detailantworten)

Wir beantworten Ihre Sicherheitsfragen als Software- und Automationsanbieter, nicht als klassisches Systemhaus, und grenzen die Verantwortung bewusst sauber ab:

| Schicht | Verantwortlich | Nachweis |
|---|---|---|
| Rechenzentrum: Gebäude, Strom, Netz, physische Sicherheit | zertifizierter Schweizer Infrastruktur-Anbieter | ISO-27001-Zertifikate des Anbieters |
| Applikation, Betrieb, Datenhaltung, Backups der Lösung | **wir** | dieses Dokument, AVV mit TOMs, Audit-Log |
| Büronetzwerk, Endgeräte, Microsoft-365-Tenant von vRv | vRv bzw. Ihr IT-Partner | bestehende Betriebsverträge |

Diese Abgrenzung steht als Verantwortungstabelle (RACI) in der Offerte und wird Vertragsbestandteil. Hinter unserer Verantwortung stehen eine Berufshaftpflicht- und eine Cyber-Versicherung [6.1: Stand einsetzen; bis Abschluss: "in Abschluss, Deckungssummen legen wir in der Offerte offen"].

## 2. Rechenzentrum: Ort, Umfang und Art

Wir betreiben kein eigenes Rechenzentrum und behaupten das auch nicht. Die Lösung wird in zertifizierten **Schweizer Rechenzentren** betrieben [6.3: vorgesehen Exoscale, Zone Genf/Zürich, ISO 27001/27017/27018; Sicherungskopie bei Infomaniak, Genf, ISO 27001; nach Entscheid definitiv formulieren]. Der Rechenzentrumsbetreiber verantwortet Gebäude, Strom, Netz und physische Sicherheit; wir verantworten Systemarchitektur, Applikationsbetrieb, Datenhaltung und Backups. Alle produktiven Daten des Projekts verbleiben in der Schweiz.

## 3. Datensicherheit: Organisation

Wir sind ein Team von vier Gründern; die Sicherheitsverantwortung ist bei einer benannten Person gebündelt, mit geregelter Stellvertretung, nicht anonym verteilt. Es gelten dokumentierte Grundregeln: persönliche Konten statt Sammel-Logins, Multi-Faktor-Authentifizierung auf allen Systemen, Passwort-Manager, Least-Privilege-Zugriffe, verschlüsselte Firmengeräte, dokumentiertes On- und Offboarding.

Wir orientieren uns am Merkblatt Informationssicherheit für KMU des Bundesamts für Cybersicherheit (BACS) und, als Referenzrahmen, am IKT-Minimalstandard des Bundes. Eine ISO-27001-Zertifizierung unseres Unternehmens besteht nicht; zertifiziert sind die eingesetzten Infrastrukturanbieter. Sollte Ihnen eine Zertifizierung wichtig sein, sprechen wir offen über den Weg dahin.

## 4. Notfallkonzept

Tägliche automatisierte, verschlüsselte Backups (Datenbank mit Point-in-Time-Recovery, Objektspeicher-Versionierung), Kopien nach dem 3-2-1-Prinzip inklusive einer Kopie bei einem zweiten Anbieter [6.3: Offsite-Ziel einsetzen]. Die Wiederherstellung ist dokumentiert und wird periodisch getestet; das haben wir für unsere eigenen Produktionssysteme eingerichtet und geprobt.

Zielwerte: maximal 24 Stunden Datenverlust im schlimmsten Fall (Datenbank durch Point-in-Time-Recovery deutlich besser), Wiederanlauf innerhalb weniger Stunden zu den vereinbarten Servicezeiten. Die Störungsüberwachung läuft automatisiert rund um die Uhr mit Alarmierung an das Team; die personelle Reaktion erfolgt zu den Servicezeiten gemäss SLA (Stufen in der Offerte). Ein 24/7-Pikettdienst gehört bei unserer Unternehmensgrösse bewusst nicht zum Standardangebot; wenn Sie ihn brauchen, vereinbaren wir ihn ausdrücklich und ehrlich bepreist.

## 5. Firewalls

Mehrstufig: Cloud-Firewalls (Security Groups) vor jedem System plus Host-Firewalls auf jedem Server. Öffentlich erreichbar ist ausschliesslich HTTPS (Port 443) mit TLS; Administrationszugänge sind nicht öffentlich exponiert und nur mit Schlüssel-Authentifizierung von definierten Quellen möglich. Die Perimeter-Firewall Ihres Büronetzes bleibt in der Verantwortung Ihres IT-Betriebs; auf Wunsch beschränken wir den Zugriff auf die Plattform zusätzlich auf Ihre Firmen-IP-Adressen.

## 6. Berechtigungsstruktur

Rollenbasiertes Berechtigungsmodell (RBAC) nach dem Least-Privilege-Prinzip, zum Beispiel: Administration (vRv-Leitung), Sachbearbeitung, Hauswart (mobil, nur zugewiesene Objekte und Aufträge), Nur-Lesen für die Revision. Jede Aktion ist einem persönlichen Konto zugeordnet, es gibt keine Sammel-Logins, und sicherheitsrelevante Aktionen werden in einem Audit-Log festgehalten.

Der Login läuft über Ihre bestehenden Microsoft-365-Konten (Entra ID Single Sign-on), damit gelten Ihre MFA- und Zugriffsrichtlinien automatisch auch für unsere Lösung, und Ein- wie Austritte wirken über Ihr zentrales Benutzer-Management sofort.

## 7. Sicherheitsstandards: Endpoint Security, VPN, BVG und FINMA

**Endpoint Security:** Für unsere eigenen Geräte betreiben wir Verschlüsselung, EDR-Schutz und zentrale Verwaltung; Zugriff auf Kundensysteme nur mit MFA. Für Ihre Endgeräte bleibt Endpoint Security bei Ihrem IT-Partner; unsere Lösung benötigt dort keine Sonderrechte und kein Agent-Deployment, sie läuft im Browser bzw. als App über TLS.

**Patch-Management:** Server erhalten automatische Sicherheitsupdates, Software-Abhängigkeiten werden kontinuierlich per Tooling überwacht, kritische Schwachstellen behandeln wir prioritär innert 48 Stunden. Wo möglich setzen wir Managed-Datenbanken ein; dort patcht der zertifizierte Anbieter die Engine.

**Verschlüsselung:** Sämtliche Verbindungen ausschliesslich über TLS (in transit); alle Datenspeicher und Backups verschlüsselt (at rest). Zugangsdaten liegen in einem Secrets-Management, nie im Code.

**Regulatorischer Rahmen:** Massgebend für die Vorsorgeeinrichtung sind BVG/BVV 2 (insbesondere die Aufbewahrungspflichten nach Art. 27i-k BVV 2) und das Datenschutzgesetz; die direkte Aufsicht liegt bei der BVSA (BVG- und Stiftungsaufsicht Aargau, zuständig auch für Solothurn) und der Oberaufsicht OAK BV, nicht bei der FINMA; die FINMA beaufsichtigt in der zweiten Säule nur die Lebensversicherer. Wo Sie FINMA-Niveau als Messlatte wünschen, orientieren wir uns freiwillig an den Grundsätzen des FINMA-Rundschreibens 2023/1: klare Verantwortlichkeiten, Auditierbarkeit, Datenstandort Schweiz.

**BVG-Aufbewahrung, konkret:** Die Aufgaben-Plattform ist ein operatives System, kein 70-Jahre-Archiv, und muss es auch nicht sein. Dokumente mit Vorsorge-Charakter übergibt sie an ein dediziertes, revisionssicheres Archiv: entweder Ihre bestehende Microsoft-Umgebung mit Aufbewahrungsrichtlinien oder ein von uns eingerichteter Schweizer Objektspeicher mit Schreibschutz (WORM), Integritätsnachweis über Prüfsummen und Zeitstempel und protokollierter Format-Migration. "Jederzeit lesbar" über Jahrzehnte heisst dokumentierte Migration, nicht ewige Dateiformate; das Migrationskonzept gehört zum Archiv-Baustein der Offerte.

## 8. Mobile Nutzung und Always On VPN

Die mobile Nutzung (Hauswarte: Checklisten, Fotos, Zeiterfassung) erfolgt über die Web-App per TLS mit Microsoft-Anmeldung und MFA; ein VPN ist dafür nicht erforderlich. Betreiben Sie auf Ihren Windows-Geräten Microsoft Always On VPN, funktioniert die Lösung transparent durch den Tunnel; das Always-On-VPN-Setup selbst (Geräteprofile, Gateway, Zertifikate) liegt bei Ihrem IT-Partner, mit dem wir uns bei Bedarf abstimmen (z.B. Split-Tunnel-Ausnahmen). Perspektivisch empfehlen wir für mobile Szenarien den Zero-Trust-Ansatz über Entra Conditional Access, den Microsoft selbst als Nachfolger klassischer VPN-Vollzugriffe positioniert; das ordnen wir Ihnen auf Wunsch gerne ein.

## 9. Datenschutz (nDSG)

Wir agieren als Auftragsbearbeiter nach Art. 9 DSG und schliessen mit Ihnen einen Auftragsbearbeitungsvertrag mit dokumentierten technisch-organisatorischen Massnahmen. Alle Unterauftragsbearbeiter (Hosting, allfällige KI-Dienste) werden offengelegt und bedürfen Ihrer vorgängigen Genehmigung. Produktivdaten werden in der Schweiz gehalten. Verletzungen der Datensicherheit melden wir Ihnen innert 24 Stunden nach Feststellung. Vor der Produktivsetzung erstellen wir gemeinsam eine kurze Datenschutz-Folgenabschätzung, da im Vorsorgeumfeld besonders schützenswerte Personendaten betroffen sein können.

Details: Datenschutz-Statement (Anhang zur Offerte, Kap. 8.6) und AVV-Entwurf (Anhang B).

## 10. KI- und Sicherheitsstrategie

Unsere KI- und Sicherheitsstrategie folgt vier Regeln:

1. **Datenklassifizierung:** Wir definieren pro Anwendungsfall, welche Daten ein KI-Modell sehen darf. Besonders schützenswerte Personendaten werden KI-Diensten nicht oder nur pseudonymisiert übergeben; wo Metadaten genügen, gehen keine ganzen Dossiers an ein Modell (Datenminimierung).
2. **Kontrollierte Anbieter und Verarbeitungsorte:** ausschliesslich Geschäftskunden-Schnittstellen, bei denen Kundendaten vertraglich nicht für das Training der Modelle verwendet werden, mit definierten Löschfristen. Die Verarbeitungsorte weisen wir im Auftragsbearbeitungsvertrag aus, ehrlich: Ihre Daten liegen in der Schweiz, die KI-Verarbeitung läuft wahlweise in der EU oder in den USA unter dem Swiss-U.S. Data Privacy Framework. Wer Ihnen "alles inklusive KI in der Schweiz" verspricht, ist Stand heute nicht ehrlich.
3. **Mensch entscheidet:** KI entwirft, Menschen geben frei. Automatisierungen mit Aussenwirkung (E-Mails, Verrechnung, Dokumente) durchlaufen eine Freigabestufe, bis ihre Zuverlässigkeit über einen definierten Zeitraum nachgewiesen ist; erst dann wird der Autonomiegrad schrittweise erhöht.
4. **Nachvollziehbarkeit:** KI-Aufrufe werden protokolliert (wer, wann, welcher Datenumfang), und der Einsatz von KI-Diensten ist Ihnen gegenüber transparent als Unterauftragsbearbeitung deklariert.

---

## Interne Checkliste vor Versand (nicht Teil des Kundendokuments)

- [ ] Alle [6.3]-Marker ersetzt (Anbieter, Zone, Zertifikate, Offsite-Ziel) nach Joaquins Hosting-Entscheid
- [ ] §1 Versicherungs-Satz nach Stand 6.1 (nach Abschluss: konkrete Deckungssummen)
- [ ] Konsistenz: 24h-Meldung = AVV Ziff. 9 · RPO/RTO = SLA-Baukasten §3 · 48h-Patch = Modul 2 · Archiv-Aussage = Architektur-Papier §0
- [ ] Joaquin-Review (fachlich + Ton)
- [ ] Zero-Context-Test: versteht Schmid jedes Kapitel ohne uns im Raum?
