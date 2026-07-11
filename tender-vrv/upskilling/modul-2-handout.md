# Modul 2 · Handout + Hausaufgabe: Sicherheits-Audit

> Session 3 (Modul 2, Cybersecurity + IT-Infrastruktur). **Abgabe: Mittwoch, 15. Juli 2026, 18:00** im Hub: Lernen → Modul 2 → "Abgaben ansehen" → hochladen (PDF, Fotos/Screenshots, Markdown oder Text). Aufwand: 60-90 Minuten, Extra-Aufgabe +30 Minuten.
> PDF-Fassung: im Hub neben dem Handout. (Intern: nach Änderungen an dieser Datei das PDF neu generieren.)

---

## Warum diese Aufgabe genau so (und warum ohne Claude)

Am 5.8. sagen wir einem Wirtschaftsprüfer Sätze wie "unsere Geräte sind verschlüsselt, MFA ist überall Pflicht, Zugriffe laufen über persönliche Konten". Diese Sätze stehen schon im Security-Antwortpaket. **Sie müssen für jeden von uns vier wirklich stimmen.** Genau das prüfst du jetzt: an deinem eigenen Gerät, an deinen eigenen Konten.

Claude kann diese Aufgabe nicht für dich machen, und zwar nicht aus Prinzip, sondern praktisch: Claude sieht weder deine Festplatten-Verschlüsselung noch deine Account-Einstellungen. Und der Lerneffekt ist der Punkt: Wer sein eigenes Setup einmal durchgeprüft hat, kann am 5.8. über EDR, MFA und Backups reden, ohne auswendig gelernt zu klingen.

> **WICHTIG, vor dem Hochladen:** Auf Screenshots NIEMALS Passwörter, Recovery-Codes, vollständige Kontonummern oder private Mails zeigen. Vorher schwärzen oder abschneiden. Die Abgaben liegen auf unserem VPS und sind für alle vier sichtbar. Es geht um den NACHWEIS der Einstellung (z.B. "FileVault: aktiviert"), nie um den Inhalt.

---

## Spickzettel: das Modell in 30 Sekunden

**Drei Verantwortungsschichten:** (1) Rechenzentrum = zertifizierter Anbieter, wir mieten. (2) Applikation + Betrieb + Daten unserer Lösung = **wir, voll verantwortlich**. (3) Büronetz, Endgeräte, M365 des Kunden = Kunde bzw. sein IT-Partner (je nach E4-Entscheid auch wir).

**Vier Schutzringe:** Identität (Passwort-Manager, MFA) → Gerät (Verschlüsselung, EDR, Updates) → Netz (Firewall, TLS, kein offener Admin-Zugang) → Daten (Rollen, Least Privilege, Audit-Log). Dahinter das Netz für den Ernstfall: Backup 3-2-1 mit getestetem Restore.

| Begriff | In einem Satz |
|---|---|
| MFA | Zweiter Faktor neben dem Passwort; gestohlene Passwörter allein werden wertlos |
| Passwort-Manager | Ein Tresor, überall einzigartige Passwörter; du merkst dir genau eins |
| Verschlüsselung at rest | Gespeicherte Daten sind ohne Schlüssel unlesbar (gestohlener Laptop = nutzlos) |
| TLS / in transit | Verschlüsselte Verbindung; das Schloss im Browser |
| EDR | Gerät wird auf verdächtiges VERHALTEN überwacht, nicht nur auf bekannte Viren gescannt |
| Firewall | Türsteher für Netzwerkverkehr; bei uns: nur HTTPS öffentlich offen |
| VPN / Always On VPN | Automatischer Tunnel ins Firmennetz (Windows-Technik); unsere Lösung braucht keins |
| Zero Trust | Nicht das Netz vertraut dir, sondern jede App prüft dich einzeln (Identität + Gerätezustand) |
| RBAC / Least Privilege | Rechte hängen an Rollen; jede Rolle bekommt nur das Minimum |
| Backup 3-2-1 | 3 Kopien, 2 Systeme, 1 extern; zählt erst mit GETESTETER Wiederherstellung |
| RTO / RPO | Wie schnell läuft es wieder / wie viel Datenverlust ist maximal drin |
| Patch-Management | Sicherheitsupdates zeitnah einspielen; kritische Lücken bei uns innert 48h |

---

## Aufgabe A · Sicherheits-Audit deines Setups (ca. 50-60 min)

Prüfe jeden Punkt an deinem Hauptgerät und deinen wichtigsten Konten. Trage pro Zeile ein: **Ampel** (GRÜN = passt · GELB = teilweise · ROT = fehlt), **Beleg** (Screenshot-Nr.), und bei GELB/ROT eine **Massnahme mit Datum**, bis wann du es fixst. Format frei: diese Tabelle ausgefüllt als PDF/Foto, oder ein eigenes Dokument mit denselben Punkten.

### Teil 1: Dein Gerät

| # | Prüfpunkt | Wo nachschauen (Mac / Windows) | Ampel | Beleg | Massnahme + bis wann |
|---|---|---|---|---|---|
| 1 | Festplatte verschlüsselt (FileVault / BitLocker) | Systemeinstellungen → Datenschutz & Sicherheit → FileVault · Einstellungen → Datenschutz → BitLocker | | | |
| 2 | Bildschirmsperre automatisch, Passwort sofort nötig | Sperrbildschirm-Einstellungen (max. 5 min) | | | |
| 3 | Betriebssystem aktuell, automatische Updates AN | Softwareupdate / Windows Update | | | |
| 4 | Malware-Schutz aktiv (XProtect/Gatekeeper läuft ab Werk · Defender AN?) | Windows: Sicherheit auf einen Blick | | | |
| 5 | Separater Admin: arbeitest du im Alltag als Administrator? (Least Privilege am eigenen Gerät) | Benutzerkonten anschauen | | | |
| 6 | Findet mein Gerät: "Wo ist?" / "Mein Gerät suchen" aktiviert (Remote-Sperre möglich) | Apple-ID / Microsoft-Konto | | | |

### Teil 2: Deine Konten (MFA-Inventar)

Geh deine 6 wichtigsten Konten durch, MINDESTENS: privates E-Mail-Konto (das ist der Generalschlüssel, darüber läuft jedes "Passwort vergessen"), Google/Apple-ID, GitHub, Microsoft 365 (automatisierbar), E-Banking, 1 weiteres nach Wahl (LinkedIn, Hosting, Telegram).

| # | Konto | MFA an? Welche Art (App/SMS/Passkey)? | Passwort einzigartig + aus dem Manager? | Recovery-Codes gesichert (wo)? | Ampel | Massnahme + bis wann |
|---|---|---|---|---|---|---|
| 1 | Privates E-Mail | | | | | |
| 2 | Google / Apple-ID | | | | | |
| 3 | GitHub | | | | | |
| 4 | Microsoft 365 | | | | | |
| 5 | E-Banking | | | | | |
| 6 | (eigene Wahl) | | | | | |

Hinweise: SMS-MFA zählt als GELB (besser als nichts, aber abfangbar; App oder Passkey = GRÜN). "Passwort im Browser gespeichert" ist kein Passwort-Manager (GELB): Browser-Speicher hängt am Geräte-Login und hat keine einzigartigen Passwörter erzwungen.

### Teil 3: Zugriffs-Landkarte (10 min)

Beantworte in 5-8 Sätzen: **Wer könnte heute auf was zugreifen, wenn dein Laptop JETZT gestohlen würde?** Geh die Kette durch: Kommt der Dieb rein (Sperre? Verschlüsselung?)? Was ist im Browser eingeloggt? Wo führt dein E-Mail-Konto hin? Was davon betrifft nicht dich, sondern Automatisierbar-Kunden?

---

## Aufgabe B · 5 Begriffe an DEINEM Beispiel (ca. 20-25 min)

Erkläre die folgenden 5 Begriffe in je 2-3 Sätzen, **zwingend am Beispiel aus deinem eigenen Audit** (nicht abstrakt, nicht aus dem Primer kopiert). So klingst du am 5.8. nach Erfahrung statt nach Auswendiglernen.

1. **MFA**: Erkläre am Beispiel eines deiner Konten aus Teil 2 (welche Art, was sie stoppt).
2. **Verschlüsselung at rest**: am Beispiel deines Laptops aus Teil 1 (was passiert beim Diebstahl mit/ohne).
3. **Least Privilege**: am Beispiel deines Admin-Kontos (Punkt 5) oder eines Kontos, das mehr darf als nötig.
4. **Recovery / RPO**: Wenn dein Laptop heute stirbt: was wäre weg, seit wann ist die letzte Kopie? Das IST dein persönliches RPO.
5. **Phishing-Kette**: Beschreibe, wie ein Angreifer mit DEINEM E-Mail-Konto (Teil 2, Zeile 1) an ein zweites Konto käme, und welcher deiner Häkchen aus dem Audit die Kette wo bricht.

---

## Extra-Aufgabe (freiwillig, +30 min) · Angriffs-Drehbuch auf Automatisierbar

Wechsle die Seite: Du bist ein Angreifer und willst an Automatisierbar-Kundendaten. Schreibe ein konkretes Drehbuch (halbe Seite): **(1)** Wen von uns vier greifst du an und warum ausgerechnet ihn? **(2)** Mit welcher Mail/Nachricht (Vorwand, Absender, Zeitpunkt, gerne den Text ausformulieren)? **(3)** Was willst du erbeuten? **(4)** An welcher unserer heutigen Massnahmen scheiterst du, und wo kämst du durch? Nutze dein Insider-Wissen (unsere Tools, Kunden, Abläufe, Gewohnheiten), genau das macht echte Angriffe gefährlich und diese Übung wertvoll. Beste Einreichung wird am 5.8.-Vorbereitungsstand Anschauungsmaterial.

---

## Abgabe

1. Alles in EINE Datei packen, wenn möglich (PDF am einfachsten: Fotos der ausgefüllten Tabellen + Text). Mehrere Dateien gehen auch.
2. Hub öffnen: cockpit.automatisierbar.ch/vrv → **Lernen** → Karte **Modul 2** → **Abgaben ansehen** → Name wählen, Datei hochladen, kurzer Kommentar.
3. **Frist: Mittwoch, 15. Juli 2026, 18:00.** Die Abgaben sind für alle vier sichtbar; wir besprechen die Ampeln (nicht die Details) kurz in der nächsten Session.
4. ROTE Punkte müssen nicht vor der Abgabe gefixt sein. Ehrliche Rots mit Massnahme sind der Sinn der Übung; ein geschöntes Audit ist wertlos.
