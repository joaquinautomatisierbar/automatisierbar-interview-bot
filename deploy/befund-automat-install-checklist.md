# Befund-Automat — Install-Termin Checkliste (Praxis Dr. med. Tina Ulrich)

~2h vor Ort. Rollback jederzeit: Tray-Symbol → Beenden (nichts Destruktives:
keine Mail gelöscht/verschoben, keine Schreibzugriffe ausserhalb Hotfolder).

## Vorbereitung (vor dem Termin)

- [ ] Windows-Build-Smoke-Test grün (deploy/befund-automat-build.md)
- [ ] Setup.exe auf USB-Stick + Download-Link
- [ ] Kern-Concept-Antwort-Status geklärt (beide Zweige vorbereitet, s.u.)
- [ ] Datenschutz-Entscheid-Blatt gedruckt (tools/praxis_ulrich/DATENSCHUTZ-ENTSCHEID.md)
- [ ] Klientin gebrieft: HIN-Login bereithalten
- [ ] Falls Datenschutz-Option A (Azure): Azure-OpenAI-Ressource + Key vorab erstellt

## 0:00–0:15 — Maschine + Installation

- [ ] DIE Maschine bestimmen (genau EINE, sonst Doppelablage!) und notieren: ________
- [ ] Setup.exe installieren (SmartScreen: Weitere Informationen → Trotzdem ausführen)
- [ ] Tray-Symbol erscheint; Autostart-Verknüpfung in `shell:startup` vorhanden

## 0:15–0:35 — HIN Mail Token + Postfach

- [ ] Mit Dr. Ulrich auf apps.hin.ch einloggen → Mail Token Service → Token für
      "IMAP-Client" erzeugen (Runbook: Token = Passwort, HIN-ID = Benutzer)
- [ ] Token via doctor-Setup in den Credential Locker schreiben (nie in Dateien)
- [ ] `BefundAutomat\doctor` Selbsttest: IMAP-Login, UIDVALIDITY, 7-Tage-Zählung,
      Fähnchen-Roundtrip → alles ✅
- [ ] BESTÄTIGEN: Nutzt die Praxis rote Fähnchen heute schon für etwas anderes?
      (Wenn ja: Kollisionsregel besprechen, ggf. andere Markierung wählen)
- [ ] Titel-Vorlagenliste durchgehen: 3 normalisierte Schreibweisen bestätigen
      (Einwilligungserklärung / Ejakulatanalyse / Definitiver) + Dateiname MM-JJJJ ok?

## 0:35–0:50 — Ablageziel (zwei Zweige)

- [ ] **Zweig A (Kern-Concept-Antwort da):** echten Aeskulap-Import-Pfad/GDT
      konfigurieren (config.json: hotfolder_path, sink), Probe-Import verifizieren
- [ ] **Zweig B (keine Antwort):** Ordner "Befund-Ablage" in Dokumenten anlegen,
      als hotfolder_path setzen. Dr. Ulrich zieht Dateien selbst in Aeskulap
      (spart trotzdem Lesen/Benennen/Zusammenfassen). Umstellung später = 1 Pfad.
- [ ] doctor Hotfolder-Probe ✅

## 0:50–1:00 — Benachrichtigungen

- [ ] Toast-Probe sichtbar, Clipboard-Probe mit Ctrl+V in DigiSono getestet
- [ ] Datenschutz-Entscheid unterschrieben? → LLM-Key in Credential Locker,
      `llm_provider` setzen. (Ohne Unterschrift: nur Install + Smoke, KEIN Live-Lauf)

## 1:00–1:40 — Überwachter Live-Lauf (nur mit Datenschutz-Freigabe)

- [ ] `--once --max-per-run 3` auf den heutigen echten Mails
- [ ] Pro Dokument gemeinsam prüfen: Dateiname, Ablage in Aeskulap sichtbar,
      Fähnchen in Outlook, Toast-Inhalt, 4-Zeiler via Ctrl+V in DigiSono
- [ ] **ROI-Baseline: EINEN Befund von Hand stoppen** (Minuten notieren): ________
- [ ] Dauerbetrieb starten (Tray läuft weiter)

## 1:40–2:00 — Übergabe

- [ ] Fehler-Kontrakt erklären: "Kein rotes Fähnchen = wie bisher von Hand.
      Der Automat fasst diese Mail nie wieder an."
- [ ] Rollback zeigen: Tray → Beenden; Kill-Switch: Token auf apps.hin.ch widerrufen
- [ ] Gedruckte Anleitung übergeben
- [ ] Pilot-Erwartung: 2 Wochen jede Ablage kurz prüfen (L2); wir melden uns
      wöchentlich mit der Statistik; bei EINER falschen Patientenzuordnung
      stoppen wir die Auto-Ablage sofort

## Pilot-Gate (nach 2 Wochen, vor Phase 2)

- NULL falsche Patientenzuordnungen (rote Linie)
- ≥95% der Befund-PDFs korrekt erkannt + abgelegt (doctor --stats)
- Subjektives OK von Dr. Ulrich zum Umgang mit unmarkierten Mails
