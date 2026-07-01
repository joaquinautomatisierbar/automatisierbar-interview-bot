# Specs-Check, zum Weiterleiten an Busslinger

Kurzer Text, den du Busslinger schicken kannst (WhatsApp / SMS / Mail). Dauert
30 Sekunden und sagt uns genau, welches Modell auf seinen PC passt.

---

Guten Tag Herr Busslinger, damit wir das Programm optimal für Ihren Computer
einstellen, bräuchten wir drei kleine Angaben. Bitte so vorgehen:

**1. Windows-Version**
Drücken Sie die Windows-Taste + R, tippen Sie `winver` ein und drücken Enter. Es
erscheint ein Fenster, schicken Sie uns einfach ein Foto davon.

**2. Arbeitsspeicher (RAM) und Prozessor**
Klicken Sie mit der rechten Maustaste auf **Dieser PC** (oder **Computer**) und
wählen Sie **Eigenschaften**. Schicken Sie uns ein Foto der Seite, dort stehen
«Installierter RAM» und «Prozessor».

Das war schon alles, vielen Dank.

---

## Was wir aus den Antworten ablesen

| Angabe | Warum sie zählt |
|--------|-----------------|
| Windows-Version (winver) | Bestätigt Windows 10 (nicht 7). Ändert die ganze Toolchain. |
| RAM (4 / 8 / 16 GB) | Bestimmt die Modellgrösse: 4 GB → 1.5B oder deterministisch, 8 GB → 7B. |
| Prozessor (CPU-Modell) | Alter/AVX2 → Geschwindigkeit der KI-Vorschläge. |

Trag die Antworten dann ins Memory / in den Plan nach, damit der finale Build das
richtige Modell bündelt.
