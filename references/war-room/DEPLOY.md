# War Room Scoreboard — Deploy & Aktivierung

> Für Joaquin. Das Tool ist gebaut + gegen Live-Notion verifiziert (Read **und** Write ✓, Pace-Mathematik-Selftest ✓). Offen ist nur die **Aktivierung des täglichen Telegram-Team-Posts** — bewusst NICHT scharf geschaltet (Halt-vor-Acting-Policy: erster echter Outbound-Post in die Team-Gruppe).

## Was schon läuft

- Notion-Hub + Daily-100-DB + Pace-State-DB + Views + Lead-`War-Room Status` → live.
- `tools/war_room_scoreboard.py` liest Daily-100, rechnet IST/SOLL/SALDO, schreibt Pace-State. **Getestet, funktioniert.**
- Selftest grün: `python3 tools/war_room_scoreboard.py --selftest`
- Dry-Run (liest live, postet nicht): `python3 tools/war_room_scoreboard.py --dry-run`

## Schritt 1 — Bot in der Team-Gruppe prüfen (einziger Blocker)

Der Reveal postet in Chat `-5026363666` (Team-Gruppe). Default-Bot = `OPERATOR_TELEGRAM_BOT_TOKEN` (postet laut Workflow F bereits in diese Gruppe). Willst du den dedizierten Team-Bot, setz in `.env`:

```
WAR_ROOM_BOT_TOKEN = <token des Bots der in -5026363666 Mitglied ist>
WAR_ROOM_CHAT_ID = -5026363666
```

**Einmaliger Verifikations-Post** (das ist der erste echte Team-Post — bewusst manuell):

```
python3 tools/war_room_scoreboard.py --mode kickoff
```

→ Kommt die Nachricht in der Gruppe an, ist der Telegram-Pfad bestätigt.

## Schritt 2 — Scheduling scharf schalten (launchd, wie LinkedIn-Brief)

```bash
cp "tools/scheduled/launchd/com.automatisierbar.war-room-reveal.plist"  ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.automatisierbar.war-room-reveal.plist     # PM 20:00

# Optional — AM-Kickoff 08:30 ("in Film kommen"):
cp "tools/scheduled/launchd/com.automatisierbar.war-room-kickoff.plist" ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.automatisierbar.war-room-kickoff.plist
```

Deaktivieren: `launchctl unload ~/Library/LaunchAgents/com.automatisierbar.war-room-reveal.plist`.

**Caveat:** launchd feuert nur, wenn der Mac um 20:00 wach ist (wie der LinkedIn-Brief). Für Always-On lieber als **Render Cron Job** (`python3 tools/war_room_scoreboard.py`) — dann `WAR_ROOM_BOT_TOKEN` + `WAR_ROOM_CHAT_ID` im Render-Dashboard setzen (NOTION_API_KEY ist dort schon).

## Tuning (eine Konstante, falls nötig)

In `tools/war_room_scoreboard.py` oder per `.env`:

| Konstante / Env | Default | Bedeutung |
|---|---|---|
| `WAR_ROOM_TARGET_TOTAL` | 4000 | Team-Gesamtziel über das Fenster. **Für Rule-of-100 als Floor → 16000.** |
| `WAR_ROOM_DAILY_PACE` | 100 | Team-Pace/Tag (SOLL-Steigung). Verpasster Tag = −diese Zahl. |
| `WAR_ROOM_DAILY_PACE_PERSON` | 100 | Pro-Person ✓-Schwelle im Reveal. |
| `WAR_ROOM_WORKING_DAYS` | 40 | Arbeitstage im Fenster (8 Wochen × 5). |
| `WAR_ROOM_WINDOW_START` | 2026-06-22 | Erster Zähltag (Montag W1 Remote). |

> Annahme: 4000 = Team-Total über 8 Wochen (deckt deine „−100 pro verpasstem Tag"-Logik). Pro-Person-Rule-of-100 (16000) sitzt als Aspiration darüber.

→ Team-Doku: [README.md](README.md)
