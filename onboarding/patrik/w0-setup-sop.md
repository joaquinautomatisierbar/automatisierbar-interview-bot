# W0 — Setup SOP (für Patrik)

*Ziel: dis Repo lauft, dini Sandbox isch parat, ei Befehl antwortet. ~30 Minute. Folg de Schritt eis für eis. Wenn öppis hakt → [escape-hatch.md](escape-hatch.md).*

**De einzig Regel wo du hüt muesch verinnerliche: 🚫 Nüt gaat live ohni Review.** Du hesch volle Lesezugriff und chasch i dinere Sandbox alles usprobiere — aber nüt wird gmerged / deployed / würkli gschickt, bis en Gründer de PR reviewed hät. Genau wie mir eusi AI-Agente laufe lönd: read-only by default, de letscht Klick erscht nach Review.

---

## Was du vorher überchunnsch (vom Joaquin)

- **Link zu dim eigene Fork** vom Repo (s `.env` isch scho use gnah — kei Sorge, das isch Absicht).
- **`.env.sandbox`** — dini Test-Zuegangsdate: es Scratch-n8n, e Wegwerf-Notion-**Test**-DB, en budget-limitierte Haiku-Key, en Test-Telegram-Bot. **Nie mit eusne echte Systeme.**

---

## Die 6 Schritt

**1. Fork clone.**
```bash
git clone <DIN-FORK-URL> patrik-repo
cd patrik-repo
```

**2. Mach din eigene Branch** (nie direkt uf `main` schaffe):
```bash
git checkout -b patrik/w0-setup
```

**3. Python-Umgäbig ufsetze** (isoliert, macht nüt am System kaputt):
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
*(Wenn's kei `requirements.txt` het: frog de Joaquin welle Befehl — nöd rate.)*

**4. Dini Sandbox-`.env` iileere.** Kopier die Date wo du überchoo hesch:
```bash
cp .env.sandbox .env
```
Öffne si churz und lueg, dass die Zeile gfüllt sind (n8n, Notion-Test, Haiku-Key, Telegram-Test). **Falls öppis fählt: nöd echti Keys sueche — ping de Joaquin.**

**5. Ei trivial Befehl laufe la** (bewiist, dass alles staat). Z.B. en Selftest vom ene deterministische Tool:
```bash
python tools/war_room_scoreboard.py --selftest
```
*(Oder welle Befehl de Joaquin dir seit. Ziel: es lauft grüen dure, kei Absturz.)*

**6. Screenshot + commit.**
```bash
git add -A
git commit -m "W0: setup runs green"
git push -u origin patrik/w0-setup
```
Mach en Screenshot vom grüene Lauf und häng en is W0-Issue.

---

## Fertig heisst (dini Checkliste)

- [ ] Fork clonet, eigne Branch `patrik/w0-setup` aktiv.
- [ ] `.venv` lauft, `pip install` dure.
- [ ] `.env` gfüllt us `.env.sandbox`.
- [ ] Ei Befehl lauft grüen dure — Screenshot gmacht.
- [ ] Commit + push + Screenshot im Issue.
- [ ] Du hesch die eint Regel gläse und verstande: **nüt gaat live ohni Review.**

Wenn alli sächs Häkli stönd: schriib im Issue *"W0 dure ✅"* und du bisch parat für W1. 🎉

> **Falls du >20 Min a irgend eim Schritt häntsch:** das isch normal bim Ufsetze. Screenshot + ei Zile was du probiert hesch → ping. Kei Formular. (→ Escape-Hatch.)
