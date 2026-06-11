---
name: send-telegram-reply
description: >
  Send a reply via the Automatisierbar Operations Telegram bot back to the team member who started a Team Chat conversation. Use this at the end of EVERY heartbeat on a "Team Chat — {name}" issue, after you've written your response comment. Without this skill, the team member never sees your answer — the paperclip comment is invisible to them.
---

# Send Telegram Reply

When the CEO (or any agent) responds on a Team Chat issue, the response only lives in paperclip — the human on the other end of Telegram doesn't see it. This skill closes the loop by also pushing the response via the Bot API.

## When to use

**Always**, when:

1. The current Issue's title starts with `Team Chat —` (one of Joaquin / Patrik / Nicolas / Tej).
2. You just wrote a substantive comment in response to an incoming Telegram message.

Skip when:

- You're posting an internal note ("CEO reasoning: waiting for X" — not meant for the human).
- You're delegating to another agent and don't have an answer yet (post a holding message via this skill instead: "Lass mich kurz mit CTO checken, ich melde mich in 5–10 Min.").

## How to use

### 1. Read the chat_id from the issue description

Every Team Chat issue's description contains `**Telegram chat_id:** \`<chat_id>\``. Extract it.

### 2. Compose the reply

- **Match the user's language.** German default. If they wrote English, reply English. If they wrote Swiss German (Schwizerdütsch), reply Hochdeutsch (we don't write Schwizerdütsch — it parses weird in text).
- **Concise.** Telegram bubbles are read on phones — keep it to 1–4 paragraphs. If you need to share a long doc, point at a paperclip Issue / URL instead of pasting it inline.
- **Markdown OK** — Telegram supports `*bold*`, `_italic_`, `\`code\``, links `[text](url)`. Use sparingly.
- **No internal jargon** — Tej/Nico/Patrik don't know "paperclip" or "run IDs". Use their language: "der Build für Bieri" not "AUT-26".
- **Reference issues by what they mean to the user** — "die Bieri-Automation" beats "AUT-26", unless the user explicitly named the identifier.

### 3. Send via Bot API

Use Bash to call the Bot API:

```bash
BOT_TOKEN="$TEAM_TELEGRAM_BOT_TOKEN"
CHAT_ID="<the chat_id from issue description>"
TEXT="<your reply text>"

curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg cid "$CHAT_ID" --arg t "$TEXT" '{chat_id: $cid, text: $t, parse_mode: "Markdown", disable_web_page_preview: true}')"
```

If `TEAM_TELEGRAM_BOT_TOKEN` is not in the agent environment, the env var is in the project's `.env` at `/Users/sexyjoaquin/Desktop/Claude Code/n8n Workflow Interview/.env` — read it with `grep ^TEAM_TELEGRAM_BOT_TOKEN .env | cut -d= -f2`.

### 4. Verify

The response's `"ok": true` confirms the send. If `false`, the error message tells you why (bad chat_id, banned, etc.). Log a comment on the issue with the failure so future runs can see.

## Disambiguation patterns

If the user's message is ambiguous, **ask before assuming**. Common cases:

| User says | Without context, ambiguous because… | How you respond |
|---|---|---|
| "Wie läuft mein Projekt?" | Multiple projects could be theirs | "Du hast aktuell X laufen — meinst du A oder B?" |
| "Füge noch xyz hinzu" | To which build? | "Welcher Build — die [Bieri Slack-Notification](AUT-26) oder [Gränacher Belegerfassung](AUT-27)?" |
| "Cancel das" | Which "das"? | "Welche meinst du? Aktuell aktiv: [list]. Sag mir die Nummer (1, 2, 3) oder Titel." |
| "Wie weit ist der CTO?" | Which issue is the CTO on? | Look at CTO's active runs; if exactly one, answer it. If multiple, list with status. |

Don't guess. The cost of one extra round-trip is much lower than acting on the wrong issue.

## Multi-modal: photos / PDFs / voice

When the Telegram listener forwards an attachment, the paperclip comment contains a local file path like `/Users/sexyjoaquin/.paperclip/team-chat/files/<chat_id>/<update_id>_<name>`. Use the Read tool on it:

- **Image** (jpg/png) → use the Read tool directly; you can see images.
- **PDF** → use the Read tool's `pages` parameter for large PDFs. Or shell out: `python3 -c "import fitz; print(fitz.open('PATH').load_page(0).get_text())"` for raw text.
- **Excel / CSV** → don't try to read raw. Use `python3 /Users/sexyjoaquin/Desktop/Claude\\ Code/n8n\\ Workflow\\ Interview/tools/file_extract.py` (already exists from the interview bot — handles pandas head/tail/sample/outliers + type-anomaly detection).
- **Voice / audio (.ogg, .mp3, .m4a)** → transcribe via Gemini 2.5 Flash. The Cold Call pipeline (`workflows/audio_to_transcript.md` if present, otherwise Workflow C in n8n) has this pattern. For quick one-off transcripts, you can hit Gemini's API directly with the file uploaded via Files API.

Reference the content of the attachment in your reply — don't just acknowledge "ich sehe das PDF". Say what you found in it.

## Output discipline

- **One Bash call per response.** Don't fire multiple sends in sequence — Telegram has rate limits and it looks spammy. Compose one good reply.
- **Confirm action.** If you executed a command (cancelled an issue, reassigned, started a build), explicitly say so in the reply: "Erledigt — AUT-27 ist abgebrochen." Don't make the user check.
- **Log the bridge.** After sending, the curl response is in your shell output. If it failed, post a follow-up comment on the issue explaining the failure (so the listener can re-try or the operator can see).

## Anti-patterns

- ❌ Replying only in paperclip without the Bash call → user thinks you're ignoring them.
- ❌ Pasting a 2000-character monologue into Telegram → Telegram cuts it, looks terrible. Split or link.
- ❌ Replying in English to a German message (matches default voice failure).
- ❌ Using paperclip identifiers (AUT-26) when the user asked about "die Bieri-Sache". Translate.
- ❌ Sending without disambiguating an unclear request. Ask first.
