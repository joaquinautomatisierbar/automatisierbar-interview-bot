# E-Mail-Entwurf: Kern Concept AG (Aeskulap-Schnittstelle)

> Status: ENTWURF, noch nicht versendet. Operator prüft und versendet
> (oder pusht via `tools/walkin/infomaniak_draft.py`-Flow als Infomaniak-Draft).
> Blockiert: die finale Ablage-Implementierung (Sink) hängt an dieser Antwort.
> MVP-Fallback ohne Antwort: manueller Ablage-Ordner, siehe Install-Checkliste.

**An:** carl-ulrich.schneider@kernconcept.ch
**Betreff:** Aeskulap 3.10.0.124: Automatischer Dokumentenimport für Praxis Dr. med. Tina Ulrich, Zürich

---

Sehr geehrter Herr Schneider

Wir betreuen die Praxis von Dr. med. Tina Ulrich (Gynäkologie und Geburtshilfe, Badenerstrasse 681, 8048 Zürich) beim Aufbau einer Automatisierung für eingehende Befundberichte. Frau Dr. Ulrich hat uns gebeten, uns direkt an Sie zu wenden.

Konkret geht es darum, per E-Mail eintreffende Befund-PDFs automatisch, mit korrektem Dokumenttitel und der richtigen Patientenzuordnung, in Aeskulap (Version 3.10.0.124, lokale Installation auf Windows) abzulegen. Dazu hätten wir folgende Fragen:

1. **Import-Ordner (Hotfolder):** Unterstützt Aeskulap einen überwachten Import-Ordner für externe PDF-Dokumente? Falls ja: Wo wird der Pfad konfiguriert, und welche Anforderungen gelten an die Dateinamen?

2. **GDT-Schnittstelle:** Auf Ihrer Website ist die GDT-Anbindung für Geräte dokumentiert. Lässt sich über GDT auch ein PDF-Dokumentenimport mit Patientenzuordnung realisieren? Falls ja: Welche GDT-Version (2.1 oder 3.0) und welche Satzart erwartet Aeskulap, und in welches Verzeichnis werden die Dateien gelegt?

3. **Patientenzuordnung:** Erfolgt die Zuordnung beim Import über Name und Geburtsdatum, oder ist eine interne Patienten-ID zwingend? Was geschieht, wenn keine eindeutige Zuordnung möglich ist?

4. **Begleitdaten:** Erwartet der Import eine Begleitdatei (Sidecar, z.B. XML oder GDT-Datei) mit Metadaten wie Dokumenttitel und Berichtsdatum, oder genügt das PDF selbst?

5. **API oder Modul:** Gibt es alternativ eine dokumentierte Import-API oder ein Zusatzmodul für den Dokumentenimport, und falls ja, wie sieht die Lizenzierung aus?

Falls es eine technische Dokumentation zu diesen Schnittstellen gibt, wären wir um eine Kopie sehr froh. Gerne stehen wir auch für ein kurzes Telefonat zur Verfügung.

Besten Dank im Voraus und freundliche Grüsse

Joaquin Bremermann
Automatisierbar
joaquin@automatisierbar.ch
