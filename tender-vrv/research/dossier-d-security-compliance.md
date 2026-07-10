# Dossier D: Security- und Compliance-Antwortkatalog (vRv-Ausschreibung)

> Stand: 10.7.2026 · Erstellt für: Meeting-Vorbereitung 5.8.2026 (eidg. dipl. Wirtschaftsprüfer Rolf H. Schmid) + Rohmaterial für das Security-Antwortpaket an vR verwaltungen ag.
>
> **Legende Quellenlage:** `V(Qn)` = in dieser Recherche gegen Quelle n geprüft (Quellenverzeichnis am Ende). `INFERIERT` = fachliche Einschätzung oder gängiges Praxiswissen, in dieser Recherche nicht gegen eine Primärquelle geprüft. Alles ohne Markierung in den Antwort-Bausteinen ist unsere eigene, ehrliche Selbstbeschreibung.

---

## 1. Zusammenfassung (5 Bullets)

1. **Wir beantworten alle Sicherheitsfragen als Software- und Automationsanbieter, nicht als MSP.** Netzwerk, Endgeräte und O365-Tenant von vRv bleiben bei vRv bzw. deren IT-Partner; wir verantworten Applikationsschicht, Betrieb und Datenhaltung unserer Lösung. Diese saubere Leistungsabgrenzung ist genau das, was die Ausschreibung unter "Verantwortlichkeiten, Leistungsabgrenzungen" verlangt, und unser stärkstes Glaubwürdigkeitsargument.
2. **Rechenzentrum-Antwort: zertifizierte Schweizer Rechenzentren, gemietet statt selbst gebaut.** Infomaniak (Genf, eigene TIER-III-Rechenzentren, ISO 27001 seit 2018, V(Q13)) oder Exoscale (Genf/Zürich, ISO 27001/27017/27018, V(Q14)) sind für uns die glaubwürdigste Antwort; Azure Switzerland North nur, falls vRv maximale O365-Nähe will (teurer, US-Anbieter).
3. **nDSG: Wir sind Auftragsbearbeiter nach Art. 9 DSG.** Es braucht einen Auftragsbearbeitungsvertrag (AVV) mit vRv, dokumentierte technisch-organisatorische Massnahmen, und jede Unterauftragsbearbeitung (Hosting, AI-Dienste) muss offengelegt und vorgängig genehmigt werden (V(Q5)). Vorsorgedaten können besonders schützenswerte Personendaten enthalten (z.B. Gesundheitsdaten bei Invaliditätsfällen), das hebt die Sorgfaltslatte.
4. **FINMA-Abgrenzung, präzis: Die Vorsorgeeinrichtung von vRv untersteht der BVSA (BVG- und Stiftungsaufsicht Aargau, zuständig auch für Solothurn) und der Oberaufsicht der OAK BV, nicht der FINMA.** FINMA beaufsichtigt im BVG-Bereich nur die Lebensversicherer (V(Q8, Q9, Q10)). "BVG allenfalls FINMA" in der Ausschreibung lesen wir als: BVG-Anforderungen zwingend, FINMA-nahe Standards als freiwillige Referenz-Messlatte. Das am 5.8. korrekt einordnen zu können, ist eine Chance zu glänzen.
5. **BVG-Aufbewahrung (Art. 27i-k BVV 2) heisst technisch: revisionssichere Langzeit-Archivierung nach GeBüV-Massstab.** 10 Jahre nach Ende der Leistungspflicht bzw. bis zum 100. Altersjahr, jederzeit lesbar (V(Q1)). Umsetzung: WORM-/Object-Lock-Speicher, Integritätsnachweis (Hash/Zeitstempel), dokumentierte Migration (V(Q2)). Wichtigste Scope-Grenze: Unsere Order2Cash-Plattform muss nicht selbst das Vorsorge-Archiv sein; sie darf Vorsorgeunterlagen an ein dediziertes Archiv übergeben.

---

## 2. Begriffskatalog

Format je Begriff: **Erklärung** (Praxistiefe) → **Unsere sprechfähige Antwort** (so würden wir es am 5.8. sagen bzw. ins Antwortpaket schreiben).

### 2.1 Endpoint Security / EDR

**Erklärung:** Endpoint Security umfasst alle Schutzmassnahmen auf Endgeräten (Laptops, Smartphones): Malware-Schutz, Festplattenverschlüsselung, Gerätesperren, Gerätemanagement (MDM). EDR (Endpoint Detection and Response) geht über klassisches Antivirus hinaus: Es zeichnet Verhalten auf dem Gerät kontinuierlich auf (Prozesse, Netzverbindungen, Dateizugriffe), erkennt Angriffsmuster statt nur bekannte Signaturen und erlaubt Reaktion (Gerät isolieren, Prozess beenden). Für KMU ist die realistische EDR-Antwort heute Microsoft Defender for Business (in Microsoft 365 Business Premium enthalten), verwaltet über Intune; genau das passt in die O365-Welt von vRv (INFERIERT, Produktzuordnung allgemein bekannt). Das BACS-Merkblatt für KMU nennt aktuell gehaltenen Malware-Schutz auf jedem Gerät als organisatorische Grundmassnahme (V(Q11)).

**Unsere Antwort:** "Unsere Firmengeräte sind vollständig verschlüsselt, zentral verwaltet, mit aktivem Malware-/EDR-Schutz und Bildschirmsperre; Zugriff auf Kundensysteme nur mit MFA. Für Ihre Endgeräte bleibt Endpoint Security Sache Ihres IT-Partners; unsere Lösung setzt kein Agent-Deployment auf Ihren Geräten voraus, sie läuft im Browser bzw. als App über TLS."

### 2.2 Firewall (Perimeter vs. Host vs. Cloud Security Groups)

**Erklärung:** Eine Firewall filtert Netzwerkverkehr nach Regeln. Drei Ebenen: (1) Perimeter-Firewall am Netzrand eines Standorts (klassische Appliance, bei vRv Sache der eigenen IT), (2) Host-Firewall auf dem einzelnen Server (z.B. nftables/ufw unter Linux, Windows Defender Firewall), (3) Security Groups / Cloud-Firewalls beim Cloud-Anbieter: Regelwerke, die pro Server oder Gruppe definieren, welche Ports von welchen Quellen erreichbar sind. In Cloud-Setups ist die Kombination aus (2) und (3) der Standard: alles zu, nur 443/TCP öffentlich, Admin-Zugänge (SSH) nur von definierten IPs oder über VPN/Bastion (INFERIERT, Standard-Praxis).

**Unsere Antwort:** "Unsere Systeme stehen hinter Cloud-Firewalls (Security Groups) plus Host-Firewalls: öffentlich erreichbar ist ausschliesslich HTTPS (Port 443) mit TLS; Administrationszugänge sind nicht öffentlich, sondern nur per Schlüssel-Authentifizierung von definierten Quellen. Eine Perimeter-Firewall für Ihr Büronetz liefern wir nicht; das bleibt bewusst bei Ihrem bestehenden IT-Betrieb."

### 2.3 VPN und Always On VPN (und die moderne Alternative)

**Erklärung:** Ein VPN baut einen verschlüsselten Tunnel zwischen Gerät und Netzwerk. **Always On VPN** ist konkret eine Microsoft-Technologie in Windows: Die VPN-Verbindung wird automatisch aufgebaut, ohne dass Nutzer klicken müssen; es gibt zwei Tunnel-Typen: den **Device Tunnel** (verbindet schon vor dem Login, nur IKEv2, nur domain-joined Geräte) und den **User Tunnel** (nach dem Login, IKEv2 oder SSTP als Fallback) (V(Q6)). Always On VPN ist Microsofts Nachfolger des abgekündigten DirectAccess (V(Q7)) und integriert mit Entra ID Conditional Access und MFA (V(Q6)). Die moderne Weiterentwicklung ist Zero Trust Network Access (ZTNA): Statt das ganze Netz zu öffnen, gewährt z.B. **Microsoft Entra Private Access** (Teil von Global Secure Access) pro Applikation Zugriff auf Basis von Identität, Gerätezustand und Conditional-Access-Regeln; Microsoft positioniert es explizit als Ablösung von Legacy-VPNs (V(Q12)).

**Unsere Antwort:** "Unsere Lösung ist cloudbasiert und wird über HTTPS/TLS mit Login über Ihren Microsoft-Tenant (Entra ID SSO, MFA, Conditional Access) genutzt. Sie benötigt kein VPN. Wenn Ihre Geräte per Always On VPN ins Firmennetz eingebunden sind, funktioniert unsere Lösung transparent darüber; das Always-On-VPN-Setup selbst (Windows-Clients, Gateway, Zertifikate) betreibt Ihr IT-Partner. Auf Wunsch schränken wir den Zugriff zusätzlich auf Ihre festen Firmen-IP-Adressen ein. Perspektivisch ist für den mobilen Zugriff der Zero-Trust-Ansatz (Entra Conditional Access, gerätebasierte Policies) die zeitgemässere Antwort als ein Voll-VPN; das können wir am Termin gerne einordnen."

### 2.4 Berechtigungsstruktur / RBAC / Least Privilege

**Erklärung:** Eine Berechtigungsstruktur legt fest, wer was sehen und tun darf. Standardmodell ist RBAC (Role-Based Access Control): Rechte hängen an Rollen (z.B. Admin, Sachbearbeitung, Hauswart, Nur-Lesen), Personen bekommen Rollen, nie Einzelrechte. **Least Privilege** heisst: jede Rolle erhält nur die minimal nötigen Rechte, Admin-Rechte sind auf wenige Personen beschränkt und getrennt vom Alltagskonto. Dazu gehören nachvollziehbare Vergabe (wer hat wann wem welche Rolle gegeben), keine geteilten Konten und ein Offboarding-Prozess (Rechteentzug bei Austritt). In der App-Praxis kommt Mandanten-/Objekttrennung dazu: ein Hauswart sieht nur seine Liegenschaften (INFERIERT, Standard-Praxis; Grundgedanke auch im BACS-KMU-Merkblatt, V(Q11)).

**Unsere Antwort:** "Die Plattform erhält ein Rollenmodell nach Least-Privilege-Prinzip: z.B. Administration (vRv-Leitung), Sachbearbeitung, Hauswart (mobil, nur zugewiesene Objekte und Aufträge), Read-only für Revision. Jede Aktion ist einem persönlichen Konto zugeordnet, es gibt keine Sammel-Logins, und sicherheitsrelevante Aktionen werden protokolliert (Audit-Log). Authentisierung läuft über Ihre bestehenden Microsoft-Konten, damit greift Ihr zentrales Join/Leave-Management automatisch auch für unsere Lösung."

### 2.5 Notfallkonzept (BCP/DR, RTO/RPO, Backup 3-2-1)

**Erklärung:** Ein Notfallkonzept beantwortet: Was passiert bei Ausfall, Datenverlust, Ransomware, Anbieterausfall? Kernbegriffe: **RTO** (Recovery Time Objective) = wie schnell muss der Dienst wieder laufen; **RPO** (Recovery Point Objective) = wie viel Datenverlust ist maximal tolerierbar (Zeit seit letztem Backup). **BCP** (Business Continuity) beschreibt organisatorische Weiterarbeit, **DR** (Disaster Recovery) die technische Wiederherstellung. Die **3-2-1-Regel** ist der Backup-Grundstandard: 3 Kopien der Daten, auf 2 verschiedenen Medien/Systemen, davon 1 an einem anderen Ort (offsite), idealerweise unveränderbar (Schutz gegen Ransomware). Entscheidend ist nicht das Backup, sondern der **getestete Restore** mit dokumentiertem Ablauf (INFERIERT, etablierter Industriestandard; BACS empfiehlt regelmässige, getrennte Datensicherungen, V(Q11)).

**Unsere Antwort:** "Unser Notfallkonzept für die Lösung: tägliche automatisierte, verschlüsselte Backups der Datenbank plus Objektspeicher-Snapshots, eine Kopie bei einem zweiten Anbieter bzw. an einem zweiten Standort (3-2-1), dokumentierte und getestete Restore-Prozedur. Realistische Zielwerte für eine Lösung unserer Grösse: RPO 24 Stunden (mit Point-in-Time-Recovery der Managed-Datenbank besser), RTO im Bereich weniger Stunden an Werktagen. Wir betreiben kein 24/7-Operations-Center und sagen das offen; dafür ist die Überwachung (Healthchecks, Alarmierung auf unsere Telefone) rund um die Uhr automatisiert."

### 2.6 MFA (Multi-Faktor-Authentifizierung)

**Erklärung:** MFA verlangt neben dem Passwort einen zweiten Faktor (App-Bestätigung, FIDO2-Schlüssel, Passkey). Sie ist die wirksamste Einzelmassnahme gegen Kontoübernahmen, weil gestohlene Passwörter allein wertlos werden. Moderne Umsetzung: Phishing-resistente Verfahren (FIDO2/Passkeys, Windows Hello) statt SMS. In der O365-Welt wird MFA zentral über Entra ID Conditional Access erzwungen; damit gilt sie automatisch auch für angebundene Dritt-Apps (V(Q6) für die Conditional-Access-Mechanik; Rest INFERIERT, Standard-Praxis).

**Unsere Antwort:** "MFA ist bei uns intern Pflicht auf allen Systemen (Code-Repository, Cloud-Konsolen, E-Mail). Für Ihre Nutzer übernimmt unsere Lösung die MFA-Policy Ihres Microsoft-Tenants über SSO; wir bauen keine eigene, schwächere Passwort-Welt daneben auf."

### 2.7 Patch-Management

**Erklärung:** Patch-Management ist der geordnete Prozess, Sicherheitsupdates zeitnah einzuspielen: Betriebssystem, Laufzeitumgebungen, Applikationsabhängigkeiten (Libraries) und die eigene Software. Gute Praxis für einen kleinen Anbieter: automatische Sicherheitsupdates auf Servern, wöchentlicher Abhängigkeits-Check über die CI-Pipeline (z.B. Dependabot), definierte Frist für kritische Lücken (Stunden bis wenige Tage, nicht Wochen) und Nutzung von Managed-Diensten, bei denen der Cloud-Anbieter Infrastruktur und Datenbank-Engine patcht (INFERIERT, Standard-Praxis; BACS nennt konsequentes Updaten als Grundmassnahme, V(Q11)).

**Unsere Antwort:** "Server erhalten automatische Sicherheitsupdates, Abhängigkeiten unserer Software werden kontinuierlich per Tooling überwacht und aktualisiert, kritische Schwachstellen behandeln wir prioritär innert 48 Stunden. Wo möglich setzen wir Managed-Datenbanken ein, dort patcht der zertifizierte Anbieter die Engine."

### 2.8 Verschlüsselung (at rest / in transit)

**Erklärung:** **In transit** heisst: alle Datenübertragungen laufen über TLS 1.2/1.3 (HTTPS), auch intern zwischen Diensten; unverschlüsseltes HTTP existiert nicht. **At rest** heisst: gespeicherte Daten (Datenbank, Objektspeicher, Backups) liegen verschlüsselt auf den Datenträgern (üblich AES-256), sodass ein entwendeter Datenträger nutzlos ist. Dazu gehört Schlüssel- und Geheimnisverwaltung: Zugangsdaten und API-Keys liegen nie im Quellcode, sondern in geschützten Umgebungsvariablen bzw. einem Secrets-Store. Für besonders sensible Felder ist zusätzlich Verschlüsselung auf Applikationsebene möglich (INFERIERT, Standard-Praxis).

**Unsere Antwort:** "Sämtliche Verbindungen laufen ausschliesslich über TLS (in transit), alle Datenspeicher und Backups sind at rest verschlüsselt (AES-256 auf Anbieterebene, verschlüsselte Backups). Zugangsdaten werden in einem Secrets-Management gehalten, nie im Code. Auf Wunsch verschlüsseln wir besonders sensible Felder zusätzlich applikationsseitig."

---

## 3. nDSG-Pflichten als Anbieter (konkret, nicht akademisch)

Rechtsgrundlage: Bundesgesetz über den Datenschutz (DSG, SR 235.1, in Kraft seit 1.9.2023) und Datenschutzverordnung (DSV, SR 235.11) (V(Q3, Q4)).

**Rollen:** vRv ist Verantwortlicher (bestimmt Zweck und Mittel), wir sind **Auftragsbearbeiter** nach Art. 9 DSG, sobald wir Personendaten von Mietern, Eigentümern, Versicherten oder Mitarbeitenden in unserer Lösung bearbeiten.

**Was Art. 9 DSG konkret verlangt (V(Q5)):**
- Bearbeitung nur so, wie es der Verantwortliche selbst dürfte; keine gesetzliche oder vertragliche Geheimhaltungspflicht darf entgegenstehen.
- Der Verantwortliche muss sich vergewissern, dass der Auftragsbearbeiter die **Datensicherheit gewährleisten** kann; praktisch heisst das: wir müssen unsere technisch-organisatorischen Massnahmen (TOMs) dokumentiert vorlegen können (Anforderungen an die Datensicherheit: Art. 8 DSG i.V.m. Art. 1 bis 6 DSV).
- **Unterauftragsbearbeiter nur mit vorgängiger Genehmigung** des Verantwortlichen (Art. 9 Abs. 3). Für uns sind das typischerweise: der Hosting-Anbieter (z.B. Infomaniak/Exoscale), E-Mail-Dienste und allfällige AI-Anbieter. Diese Liste gehört transparent in den AVV.

**AVV (Auftragsbearbeitungsvertrag), Mindestinhalt in der Praxis:** Gegenstand und Dauer, Art der Daten und betroffene Personen, Weisungsrecht, Vertraulichkeitspflicht der Mitarbeitenden, TOMs als Anhang, Regelung der Unterauftragsbearbeiter, Unterstützungspflichten (Auskunftsbegehren), Meldung von Datensicherheitsverletzungen an den Verantwortlichen, Löschung/Rückgabe bei Vertragsende, Audit-/Nachweisrechte (V(Q5), Detailkatalog teils INFERIERT aus gängigen AVV-Vorlagen).

**Weitere Pflichten, kurz:**
- **Verzeichnis der Bearbeitungstätigkeiten** (Art. 12 DSG): Ausnahme für Unternehmen unter 250 Mitarbeitenden, sofern kein hohes Risiko (Art. 24 DSV); trotzdem empfehlenswert, ein schlankes Verzeichnis zu führen, weil es die Fragen des Wirtschaftsprüfers direkt beantwortet (Gesetzesinhalt: V über Fedlex Q3/Q4; Empfehlung: INFERIERT).
- **Datenschutz-Folgenabschätzung (DSFA, Art. 22 DSG):** nötig, wenn eine Bearbeitung ein hohes Risiko mit sich bringen kann, insbesondere bei umfangreicher Bearbeitung besonders schützenswerter Personendaten. Im Vorsorgekontext (Gesundheitsdaten bei Invaliditätsfällen, umfassende Finanz-/Sozialversicherungsdaten) ist eine DSFA vor Produktivsetzung die saubere Antwort; sie ist bei uns ein zweiseitiges, ehrliches Dokument, kein 40-Seiten-Gutachten (Pflichtenlage: V(Q3); Einstufung Vorsorgedaten: INFERIERT, aber Gesundheitsdaten sind in Art. 5 lit. c DSG explizit besonders schützenswert).
- **Meldung von Datensicherheitsverletzungen (Art. 24 DSG):** der Verantwortliche meldet dem EDÖB so rasch als möglich, wenn ein hohes Risiko für die betroffenen Personen resultiert; als Auftragsbearbeiter melden wir jede Verletzung unverzüglich an vRv. Unsere interne Frist: Erstmeldung an den Kunden innert 24 Stunden nach Feststellung (Gesetzesinhalt V(Q3); interne Frist = unsere Zusage).
- **Bekanntgabe ins Ausland (Art. 16/17 DSG):** zulässig ohne Weiteres nur in Staaten mit angemessenem Schutzniveau gemäss Staatenliste in Anhang 1 DSV; sonst braucht es Garantien wie die vom EDÖB anerkannten EU-Standarddatenschutzklauseln. Für die USA gilt seit 15.9.2024 der Angemessenheitsbeschluss für nach dem **Swiss-U.S. Data Privacy Framework** zertifizierte Unternehmen (V(Q4)).

**Data-Residency-Argument, sprechfähig:** "Wir halten die produktiven Daten des Projekts in der Schweiz. Damit entfällt die ganze Auslandsbekanntgabe-Prüfung für das Hosting. Wo einzelne Hilfsdienste Daten im Ausland bearbeiten (z.B. ein AI-Dienst in der EU oder ein DPF-zertifizierter US-Anbieter), weisen wir das im AVV explizit aus, inklusive Rechtsgrundlage nach Art. 16 DSG."

---

## 4. BVG/GeBüV-Archivierung, technisch übersetzt

**Was Art. 27i-k BVV 2 verlangt (SR 831.441.1, V(Q1); Volltext liegt der Ausschreibung bei):**
- **Art. 27i:** Vorsorgeeinrichtungen (und Freizügigkeitseinrichtungen) müssen alle Vorsorgeunterlagen aufbewahren, die wesentliche Angaben zur Geltendmachung von Vorsorgeansprüchen enthalten: Guthaben- und Kontounterlagen, relevante Vorgänge (Einkäufe, WEF-Vorbezüge, Scheidungsauszahlungen), Anschlussverträge, Reglemente, wichtige Geschäftskorrespondenz, Identifikationsunterlagen. Aufbewahrung auf anderen Trägern als Papier ist zulässig, **sofern die Unterlagen jederzeit lesbar gemacht werden können**.
- **Art. 27j:** Frist bei ausgerichteten Leistungen: **10 Jahre nach Beendigung der Leistungspflicht**. Wurden keine Leistungen geltend gemacht: **bis zum vollendeten bzw. hypothetischen 100. Altersjahr** der versicherten Person. Freizügigkeitsfall: 10 Jahre nach Überweisung der Austrittsleistung.
- **Art. 27k:** Bei Liquidation sorgen die Liquidatoren für die Aufbewahrung.

**Praktische Konsequenz:** Der Planungshorizont ist nicht 10 Jahre, sondern potenziell **70+ Jahre** (eine heute 25-jährige versicherte Person). Kein Dateiformat und kein Speichersystem lebt so lange; die Anforderung "jederzeit lesbar" ist deshalb in Wahrheit eine **Migrations-Anforderung**.

**Was "revisionssicher" heisst: der GeBüV-Massstab (SR 221.431, V(Q2)):** Die Geschäftsbücherverordnung konkretisiert die kaufmännische Aufbewahrung (Art. 957 ff. OR, Frist 10 Jahre nach Art. 958f OR) und ist der etablierte Referenzstandard dafür, wie elektronische Archive beschaffen sein müssen:
- **Integrität:** Informationen so speichern, dass sie nicht geändert werden können, ohne dass dies feststellbar ist.
- **Informationsträger:** Unveränderbare Träger sind ohne Weiteres zulässig; **veränderbare Träger (Disk, Cloud-Storage) nur, wenn** technische Verfahren die Integrität gewährleisten (z.B. digitale Signatur), der **Speicherzeitpunkt unverfälschbar nachweisbar** ist (z.B. Zeitstempel) und die Abläufe **dokumentiert** sind (inkl. Protokoll-/Logdateien).
- **Migration:** Übertragung auf neue Formate/Träger ist erlaubt, wenn Vollständigkeit und Korrektheit sichergestellt und die Migration **protokolliert** wird; Verfügbarkeit und Lesbarkeit müssen gewahrt bleiben.

**Technische Umsetzung, die wir vertreten können (INFERIERT als Architekturempfehlung, Bausteine einzeln Standard):**
1. Dokumente als **PDF/A** ablegen (Langzeitformat), Metadaten daneben strukturiert.
2. Speicherung in einem Objektspeicher mit **Versionierung und Object Lock (WORM)**: Objekte können während der Retention-Frist weder geändert noch gelöscht werden.
3. **SHA-256-Hash pro Dokument** plus signierte bzw. zeitgestempelte Hash-Listen: Integrität und Speicherzeitpunkt jederzeit nachweisbar.
4. **Retention-Policy pro Dossier** statt pauschal: Fristende hängt am Ereignis (Ende Leistungspflicht, 100. Altersjahr), also braucht das Archiv ein Fristen-Feld und einen jährlichen Prüfjob.
5. **Migrationskonzept:** dokumentierter Export (offene Formate), Migrationsprotokolle, Restore-Tests. Das erfüllt genau die GeBüV-Migrationsregel.

**Die ehrliche Scope-Grenze (wichtig für Offerte und Meeting):** Die Order2Cash-/Aufgabenplattform, die vRv ausschreibt, ist primär ein **operatives System** (Aufträge, Checklisten, Fotos, Leistungserfassung, Verrechnung). Sie wird erst dann zum BVG-Archiv-Thema, wenn **Vorsorgeunterlagen im Sinne von Art. 27i** darin erzeugt oder gespeichert werden (z.B. Korrespondenz der Personalvorsorgeverwaltung, Austrittsabrechnungen). Unsere Position: Die Plattform hält operative Daten; Dokumente mit Vorsorge-Charakter werden **an ein dediziertes, revisionssicheres Archiv übergeben** (bestehendes DMS von vRv oder ein von uns eingerichteter WORM-Speicher mit obigen Eigenschaften). So bleibt die Verantwortlichkeit sauber und wir versprechen kein 70-Jahre-Archiv als Nebenprodukt einer Task-App.

---

## 5. FINMA-Abgrenzung (präzis, mit Quellen)

Die Ausschreibung schreibt "Sicherheitsstandards: ... BVG allenfalls FINMA". Die Aufsichtslage ist klar und wir sollten sie am 5.8. exakt wiedergeben können:

1. **Vorsorgeeinrichtungen (Pensionskassen, Sammel-/Gemeinschaftsstiftungen) werden NICHT von der FINMA beaufsichtigt.** Direkte Aufsicht führen die kantonalen bzw. regionalen **BVG- und Stiftungsaufsichtsbehörden** nach Art. 61 BVG; darüber wacht die **Oberaufsichtskommission Berufliche Vorsorge (OAK BV)**, die die sieben regionalen Behörden beaufsichtigt und für einheitliche Aufsichtspraxis sorgt; direkt beaufsichtigt die OAK BV nur Anlagestiftungen, den Sicherheitsfonds und die Auffangeinrichtung (V(Q8)).
2. **Zuständig für eine Stiftung mit Sitz im Kanton Solothurn ist die BVSA** (BVG- und Stiftungsaufsicht Aargau): Aargau und Solothurn haben die BVG-Aufsicht per Vereinbarung zusammengelegt (BGS 212.15; die BVSA nimmt die Aufsicht über Vorsorgeeinrichtungen mit Sitz im Kanton Solothurn wahr) (V(Q9)).
3. **Wo FINMA im BVG-Kontext tatsächlich vorkommt:** Sie beaufsichtigt die **Lebensversicherer**, die berufliche Vorsorge anbieten (z.B. Vollversicherungslösungen): getrenntes gebundenes Vermögen, jährliche Betriebsrechnung berufliche Vorsorge, **Tarifgenehmigungspflicht** für BVG-Tarife (V(Q10)). Eine Vorsorgeeinrichtung ist also nur dann indirekt FINMA-berührt, wenn sie Risiken bei einem Lebensversicherer rückgedeckt hat.
4. **Lesart der Ausschreibungsformulierung:** "BVG allenfalls FINMA" heisst sinnvollerweise: Die Lösung muss den BVG-Pflichten genügen (v.a. Aufbewahrung Art. 27i-k BVV 2, Datenschutz); FINMA-nahe Standards (z.B. FINMA-Rundschreiben 2023/1 "Operationelle Risiken und Resilienz", das die Outsourcing-Anforderungen für Banken/Versicherer enthält) dienen **allenfalls als freiwillige Referenz-Messlatte**, etwa wenn ein Lebensversicherer als Partner der Stiftung involviert ist (Existenz und Rolle des RS 2023/1: V(Q15); Lesart: INFERIERT, aber die einzig kohärente).

**Sprechfähige Meeting-Formulierung:** "Ihre Vorsorgeeinrichtung untersteht der BVSA als Direktaufsicht und der OAK BV als Oberaufsicht; die FINMA beaufsichtigt in der zweiten Säule nur die Lebensversicherer. Für unser Projekt heisst das: massgebend sind BVG/BVV 2, Datenschutzgesetz und die kaufmännischen Aufbewahrungsregeln. Wo Sie FINMA-Niveau als Messlatte wünschen, orientieren wir uns freiwillig an den Outsourcing-Grundsätzen des FINMA-RS 2023/1: klare Verantwortlichkeiten, Auditierbarkeit, Datenstandort Schweiz."

---

## 6. CH-Hosting-Vergleich

| Anbieter | Standort RZ | Zertifizierungen (Quelle) | Managed DB / Backup | Kostenklasse | Einordnung für uns |
|---|---|---|---|---|---|
| **Infomaniak** | Genf (eigene TIER-III+ RZ, ausschliesslich Schweiz) | ISO 27001 (seit 2018), ISO 9001, 14001, 50001 (V(Q13)) | VPS/Public Cloud (OpenStack), Backups inklusive; dedizierte DBaaS-Palette schmaler als Exoscale (INFERIERT) | tief | Stärkste "alles Schweiz"-Story: Schweizer Firma, eigene RZ, günstig. Sehr glaubwürdige Erstantwort. |
| **Exoscale** | Genf + Zürich (weitere Zonen EU) | ISO 27001:2022, ISO 27017, ISO 27018, DSG-/GDPR-konform (V(Q14)) | **DBaaS** (PostgreSQL/MySQL/OpenSearch u.a., betrieben mit Aiven, Backups/PITR integriert) (V(Q14)) | mittel | Beste technische Wahl für uns: Security Groups, Managed DB mit Backups, CH-Zonen wählbar. |
| **Azure Switzerland North** | Zürich (Paar-Region: Switzerland West, Genf) | ISO 27001, ISO 22301, SOC 1-3, PCI DSS u.a.; Microsoft dokumentiert FINMA-Compliance-Mapping (V(Q15)) | Voll (Managed SQL/PostgreSQL, Backup Vaults) | hoch | Sinnvoll bei maximaler O365/Entra-Integration; Gegenargumente: Kosten, US-Anbieter (CLOUD-Act-Diskussion, INFERIERT), Modellverfügbarkeit für Azure OpenAI in CH eingeschränkt (V(Q18)). |
| **cloudscale.ch** | Rümlang ZH + Lupfig AG | ISO 27001 (V(Q16)) | IaaS + Objektspeicher, keine Managed-DB (INFERIERT) | mittel | Solide Schweizer IaaS-Alternative, aber mehr Eigenbetrieb für uns. |
| **Nine** | Zürich (CH-RZ) | ISO 27001, positioniert für Finanzkunden (INFERIERT, in dieser Recherche nicht einzeln geprüft) | Managed Services breit | mittel-hoch | Managed-Ansatz, eher für grössere Setups. |
| **Hostpoint** | CH (Managed Server in FINMA-/ISO-zertifizierten RZ, gem. Support-Doku) (V(Q17)) | RZ-seitig ISO 27001 | Webhosting/Managed Server, kein Cloud-Baukasten | tief | Für Web-Workloads ok, für unsere Plattform zu wenig Cloud-Primitives. |

**Empfehlung als "Rechenzentrum Schweiz"-Antwort:** Primär **Exoscale (Zone Genf oder Zürich)** für die Plattform (Managed DB, Security Groups, ISO 27001/27017/27018), alternativ **Infomaniak** wenn vRv die "100% Schweizer Anbieter"-Story höher gewichtet als Managed-DB-Komfort. Azure Switzerland nur bei explizitem Wunsch nach Microsoft-Ökosystem-Hosting. Wichtig für die Ehrlichkeit: **Wir besitzen kein eigenes Rechenzentrum und behaupten das auch nicht**; wir mieten zertifizierte Schweizer Infrastruktur und verantworten darauf Architektur, Betrieb und Sicherheit der Applikation.

---

## 7. Bausteine für unser Security-Antwortpaket (Rohtext)

Ehrlich für ein 4-Personen-Unternehmen formuliert; keine erfundenen SOCs, kein 24/7-NOC. Direkt in das Kundendokument übernehmbar, Reihenfolge folgt der Ausschreibung.

**Rechenzentrum (Ort, Umfang, Art):**
"Wir betreiben kein eigenes Rechenzentrum. Die Lösung wird in zertifizierten Schweizer Rechenzentren betrieben (vorgesehen: Exoscale, Zone Genf/Zürich, ISO 27001/27017/27018, oder Infomaniak, Genf, ISO 27001). Der Rechenzentrumsbetreiber verantwortet Gebäude, Strom, Netz und physische Sicherheit; wir verantworten Systemarchitektur, Applikationsbetrieb, Datenhaltung und Backups. Alle produktiven Daten des Projekts verbleiben in der Schweiz."

**Datensicherheit, Organisation:**
"Wir sind ein Team von vier Gründern; Sicherheitsverantwortung ist bei einer benannten Person gebündelt (Stellvertretung geregelt), nicht anonym verteilt. Es gelten dokumentierte Grundregeln: persönliche Konten statt Sammel-Logins, MFA auf allen Systemen, Passwort-Manager, Least-Privilege-Zugriffe, verschlüsselte Firmengeräte, dokumentiertes On-/Offboarding. Wir orientieren uns am Merkblatt Informationssicherheit für KMU des Bundesamts für Cybersicherheit (BACS) und, als Referenzrahmen, am IKT-Minimalstandard des Bundes (NIST-CSF-basiert: Identify, Protect, Detect, Respond, Recover). Eine ISO-27001-Zertifizierung unseres Unternehmens besteht nicht; zertifiziert sind die eingesetzten Infrastrukturanbieter."

**Notfallkonzept:**
"Tägliche automatisierte, verschlüsselte Backups (Datenbank mit Point-in-Time-Recovery, Objektspeicher-Versionierung), Kopien nach dem 3-2-1-Prinzip inklusive einer Kopie bei einem zweiten Anbieter. Wiederherstellung ist dokumentiert und wird periodisch getestet. Zielwerte: RPO maximal 24 Stunden (Datenbank besser), RTO wenige Stunden innerhalb der Supportzeiten. Störungsüberwachung läuft automatisiert rund um die Uhr mit Alarmierung an das Team; personelle Reaktion erfolgt zu den vereinbarten Servicezeiten (SLA-Vorschlag in der Offerte). Ein 24/7-Pikettdienst gehört bei unserer Unternehmensgrösse bewusst nicht zum Standardangebot und würde separat vereinbart."

**Firewalls:**
"Mehrstufig: Cloud-Firewalls (Security Groups) vor jedem System plus Host-Firewalls auf jedem Server. Öffentlich erreichbar ist nur HTTPS; Administrationszugänge sind nicht öffentlich exponiert und nur mit Schlüssel-Authentifizierung von definierten Quellen möglich. Die Perimeter-Firewall Ihres Büronetzes bleibt in der Verantwortung Ihres IT-Betriebs; auf Wunsch beschränken wir den Zugriff auf die Plattform zusätzlich auf Ihre Firmen-IP-Adressen."

**Berechtigungsstruktur:**
"Rollenbasiertes Berechtigungsmodell (RBAC) nach Least-Privilege-Prinzip mit Rollen wie Administration, Sachbearbeitung, Hauswart (nur zugewiesene Objekte/Aufträge, mobil) und Read-only für Revision. Login über Ihre bestehenden Microsoft-365-Konten (Entra ID SSO inkl. Ihrer MFA- und Conditional-Access-Richtlinien). Sicherheitsrelevante Aktionen werden in einem Audit-Log festgehalten. Eintritte und Austritte wirken über Ihr zentrales Benutzer-Management automatisch auch auf unsere Lösung."

**Sicherheitsstandards (EndpointSecurity, Firewall, VPN; BVG allenfalls FINMA):**
"Endpoint Security betreiben wir für unsere eigenen Geräte (Verschlüsselung, EDR-Schutz, zentrale Verwaltung); für Ihre Endgeräte bleibt sie bei Ihrem IT-Partner, unsere Lösung benötigt dort keine Sonderrechte. Firewall- und VPN-Standards: siehe oben; die Lösung ist über TLS und Entra-ID-Anmeldung nutzbar, mit oder ohne Ihr VPN. Regulatorisch massgebend sind für die Vorsorgeeinrichtung BVG/BVV 2 (insbesondere die Aufbewahrungspflichten nach Art. 27i-k BVV 2) und das DSG; die direkte Aufsicht liegt bei der BVSA und der OAK BV, nicht bei der FINMA. Wo FINMA-Niveau als Messlatte gewünscht ist, orientieren wir uns freiwillig an den Grundsätzen des FINMA-RS 2023/1 (klare Verantwortlichkeiten, Auditierbarkeit, Datenstandort Schweiz)."

**Mobile Anbindung (AlwaysOnVPN):**
"Die mobile Nutzung (Hauswarte: Checklisten, Fotos, Zeiterfassung) erfolgt über die Web-App/PWA per TLS mit Microsoft-Anmeldung und MFA. Ein VPN ist dafür nicht erforderlich. Betreiben Sie auf Ihren Windows-Geräten Microsoft Always On VPN, funktioniert die Lösung transparent durch den Tunnel; das Always-On-VPN-Setup selbst (Geräteprofile, Gateway, Zertifikate) liegt bei Ihrem IT-Partner, wir stimmen uns bei Bedarf mit ihm ab (z.B. Split-Tunnel-Ausnahmen). Perspektivisch empfehlen wir für mobile Szenarien den Zero-Trust-Ansatz über Entra Conditional Access, den Microsoft als Nachfolger klassischer VPN-Vollzugriffe positioniert."

**Datenschutz:**
"Wir agieren als Auftragsbearbeiter nach Art. 9 DSG und schliessen mit Ihnen einen Auftragsbearbeitungsvertrag mit dokumentierten technisch-organisatorischen Massnahmen. Alle Unterauftragsbearbeiter (Hosting, allfällige KI-Dienste) werden offengelegt und bedürfen Ihrer vorgängigen Genehmigung. Produktivdaten werden in der Schweiz gehalten. Verletzungen der Datensicherheit melden wir Ihnen innert 24 Stunden nach Feststellung. Vor Produktivsetzung erstellen wir gemeinsam eine kurze Datenschutz-Folgenabschätzung, da im Vorsorgeumfeld besonders schützenswerte Personendaten betroffen sein können."

---

## 8. KI-Strategie-Baustein

Verteidigungsfähige Position für ein Unternehmen, dessen Kern Automatisierung mit KI ist; jede Zeile muss der Wirtschaftsprüfer-Nachfrage standhalten.

**Rohtext:**
"Unsere KI- und Sicherheitsstrategie folgt vier Regeln. **Erstens Datenklassifizierung:** Wir definieren pro Anwendungsfall, welche Daten ein KI-Modell sehen darf. Besonders schützenswerte Personendaten (z.B. Gesundheitsangaben) werden KI-Diensten nicht oder nur pseudonymisiert übergeben; für Textbausteine genügen in der Regel Metadaten statt ganzer Dossiers (Datenminimierung). **Zweitens kontrollierte Anbieter und Verarbeitungsorte:** Wir setzen ausschliesslich Geschäftskunden-APIs ein, bei denen Kundendaten vertraglich nicht für das Training der Modelle verwendet werden: Anthropic Claude (Commercial Terms: kein Training auf API-Daten, Löschung der API-Daten standardmässig innert 30 Tagen, Zero-Data-Retention vereinbar) und/oder OpenAI API (kein Training by default, EU-Datenresidenz-Option) bzw. Azure OpenAI (kein Training, Verarbeitung in der gewählten Azure-Region, Region Switzerland North verfügbar). Wo europäische Verarbeitung gefordert ist, nutzen wir die EU-Optionen (z.B. Claude über AWS Bedrock Frankfurt oder OpenAI mit EU-Residenz); die Verarbeitungsorte werden im Auftragsbearbeitungsvertrag ausgewiesen. **Drittens Human-in-the-loop:** KI entwirft, Menschen entscheiden. Automatisierungen mit Aussenwirkung (E-Mails, Verrechnung, Dokumente) durchlaufen eine Freigabestufe, bis ihre Zuverlässigkeit über einen definierten Zeitraum nachgewiesen ist; erst dann wird der Autonomiegrad schrittweise erhöht. **Viertens Nachvollziehbarkeit:** KI-Aufrufe werden protokolliert (wer, wann, welcher Datenumfang), und der Einsatz von KI-Diensten ist gegenüber Ihnen transparent als Unterauftragsbearbeitung deklariert."

**Faktenbasis dazu:** Anthropic-Kommerzbedingungen und API-Datenaufbewahrung (kein Training, 30 Tage, ZDR): V(Q19). OpenAI (kein Training by default, EU-Datenresidenz für API): V(Q20). Azure OpenAI in Switzerland North verfügbar, aber Modellpalette dort eingeschränkt (Stand Mitte 2026 im Wesentlichen GPT-4o für Standard-Deployments, neuere Modelle über EU Data Zones): V(Q18); Anthropic direkt-API verarbeitet in den USA, EU-Verarbeitung läuft über Bedrock/Vertex: V(Q21). Diese Nuancen nicht überverkaufen: wer "alles in der Schweiz, auch die KI" verspricht, ist Stand heute unglaubwürdig; ehrlich ist "Daten in der Schweiz, KI-Verarbeitung wahlweise EU oder USA (DPF-zertifiziert), vertraglich ohne Training".

---

## 9. Quellenverzeichnis

Primär- und Herstellerquellen, in dieser Recherche (10.7.2026) konsultiert:

- **Q1** Fedlex, BVV 2 (SR 831.441.1), Art. 27i-k: https://www.fedlex.admin.ch/eli/cc/1984/543_543_543/de (PDF-Fassung: fedlex.data.admin.ch, eli/cc/1984/543_543_543); Inhalt zusätzlich durch die der Ausschreibung beigelegte Volltext-Beilage bestätigt.
- **Q2** Fedlex, GeBüV (SR 221.431): https://www.fedlex.admin.ch/eli/cc/2002/216/de (Integrität, zulässige Informationsträger, Zeitstempel/Signatur, Dokumentation, Migration).
- **Q3** Fedlex, DSG (SR 235.1): https://www.fedlex.admin.ch/eli/cc/2022/491/de (Art. 5, 8, 9, 12, 16/17, 22, 24).
- **Q4** EDÖB, Bekanntgabe von Personendaten ins Ausland (inkl. Staatenliste Anhang 1 DSV, EU-Standardklauseln, Swiss-U.S. DPF seit 15.9.2024): https://www.edoeb.admin.ch/de/bekanntgabe-von-personendaten-ins-ausland
- **Q5** Art. 9 DSG Auftragsbearbeitung, Anforderungen und Unterauftrags-Genehmigung (Gesetzestext via Q3; Praxis-Kommentare: datenschutzpartner.ch/dsg/dsg-9, activemind.ch/gesetze/dsg/artikel-9).
- **Q6** Microsoft Learn, About Always On VPN (Device/User Tunnel, IKEv2/SSTP, Entra Conditional Access, MFA): https://learn.microsoft.com/en-us/windows-server/remote/remote-access/overview-always-on-vpn
- **Q7** Microsoft Learn, DirectAccess-zu-Always-On-VPN-Migration (DirectAccess-Nachfolge): https://learn.microsoft.com/en-us/windows-server/remote/remote-access/da-always-on-vpn-migration/da-always-on-migration-overview
- **Q8** OAK BV, Aufsichtsbehörden (Oberaufsicht über die sieben regionalen Behörden; Direktaufsicht Anlagestiftungen/Sicherheitsfonds/Auffangeinrichtung): https://www.oak-bv.admin.ch/de/beaufsichtigte/aufsichtsbehoerden
- **Q9** BVSA (Aufsichtsbehörde nach Art. 61 BVG für AG und SO): https://www.bvsa.ch/ ; Vereinbarung der Kantone Aargau und Solothurn über die BVG-Aufsicht, BGS 212.15: https://bgs.so.ch/app/de/texts_of_law/212.15
- **Q10** FINMA, Occupational pension schemes (FINMA beaufsichtigt Lebensversicherer im BVG-Geschäft; Tarifgenehmigung, Transparenzpflichten): https://www.finma.ch/en/supervision/insurers/sector-specific-tools/occupational-pension-schemes/
- **Q11** BACS/NCSC, Merkblatt Informationssicherheit für KMU: https://www.ncsc.admin.ch/dam/ncsc/de/dokumente/infos-unternehmen/ncsc-merkblatt-kmu-sicherheit.pdf.download.pdf/ncsc-merkblatt-kmu-sicherheit_de.pdf
- **Q12** Microsoft, Entra Private Access / Global Secure Access (identitätszentriertes ZTNA als VPN-Ablösung): https://www.microsoft.com/en-us/security/business/identity-access/microsoft-entra-private-access und https://learn.microsoft.com/en-us/entra/global-secure-access/overview-what-is-global-secure-access
- **Q13** Infomaniak, Zertifizierungen (ISO 27001 seit 2018; ISO 9001/14001/50001; eigene RZ in Genf): https://www.infomaniak.com/en/certifications und https://www.infomaniak.com/en/trust-center
- **Q14** Exoscale, Compliance (ISO 27001:2022, 27017, 27018; Zonen Genf/Zürich; DBaaS mit Aiven): https://www.exoscale.com/compliance/ und https://www.exoscale.com/datacenters/switzerland/
- **Q15** Microsoft Learn, FINMA Switzerland Compliance Offering (u.a. FINMA-RS 2023/1 Operationelle Risiken und Resilienz) und Azure Switzerland (Regionen, Zertifikate): https://learn.microsoft.com/en-us/compliance/regulatory/offering-finma-switzerland und https://azure.microsoft.com/en-ca/global-infrastructure/switzerland/
- **Q16** cloudscale.ch, News/Unternehmensangaben (ISO 27001; Regionen Rümlang und Lupfig): https://www.cloudscale.ch/en/news
- **Q17** Hostpoint Support, Standort/Sicherung Managed Server (FINMA-/ISO-zertifizierte RZ): https://support.hostpoint.ch/de/01-Produkte/Managed_Server/Wo_steht_der_Managed_Server_und_wo_werden_die_Daten_gesichert
- **Q18** Microsoft Q&A zu Azure OpenAI in Switzerland North (GPT-4o als einziges fortgeschrittenes Standard-Modell, Stand Mitte 2026; EU Data Zones als Ausweichoption): https://learn.microsoft.com/en-gb/answers/questions/4376981/ und https://learn.microsoft.com/en-us/answers/questions/5898946/
- **Q19** Anthropic, API and data retention (kein Training unter Commercial Terms, 30-Tage-Standardlöschung, Zero Data Retention): https://platform.claude.com/docs/en/manage-claude/api-and-data-retention
- **Q20** OpenAI, Data residency in Europe + Data controls (kein Training by default für API/Business): https://openai.com/index/introducing-data-residency-in-europe/ und https://help.openai.com/en/articles/10503543-data-residency-for-the-openai-api
- **Q21** Anthropic, Regional Compliance (EU-Verarbeitung via Bedrock/Vertex; Foundry EU "coming"): https://claude.com/regional-compliance
- **Q22** BWL/BACS, IKT-Minimalstandard 2023 (NIST-CSF-basiert; Identify/Protect/Detect/Respond/Recover): https://www.ncsc.admin.ch/dam/ncsc/de/dokumente/infos-unternehmen/ikt-minimalstandards/IKT-Minimalstandard-2023-DE.pdf.download.pdf/IKT-Minimalstandard-2023-DE.pdf

**Offene Verifikationspunkte (bewusst als INFERIERT markiert):** Nine-Zertifizierungslage im Detail; Infomaniak Managed-DB-Tiefe; CLOUD-Act-Bewertung für Azure CH (juristische Literatur, nicht Teil dieser Recherche); Kostenklassen (Erfahrungswerte, keine tagesaktuellen Preislisten gezogen).
