---
description: Pre-create the next LinkedIn weekly brief skeleton page in Notion. All properties auto-filled. Run this any time Mon–Thu to start collecting notes for the week.
---

# Create Next Week's LinkedIn Brief Skeleton

You're helping Joaquin pre-create the upcoming Friday's LinkedIn brief page in
the Notion DB so he can add mid-week notes (customer quotes, post-worthy
moments) without typing anything.

## What to do

1. **Read any `$1` argument** the user supplied with the slash command. If it
   looks like a YYYY-MM-DD date, use it as `--week-of`. If empty, the script
   defaults to the upcoming Friday relative to today.

2. **Run the create-page command:**
   ```bash
   .venv/bin/python tools/linkedin_brief.py --create-page [--week-of YYYY-MM-DD]
   ```

3. **Report back** with the Notion URL the script prints. Format:
   ```
   Skeleton bereit für KW-XX · YYYY-MM-DD:
   <notion-url>

   Schreib deine Notizen direkt rein (Paragraphs, Bullets, Callouts — alles native Notion).
   Freitag 16:00 hängt das Skript die Wochen-Auswertung als Markdown-Codeblock unten an.
   ```

## Failure modes you might hit

- **Page already exists for that week** → script exits 1 with the existing
  page's URL in the error. Surface that URL to Joaquin (he probably just wants
  to open the existing page).
- **`NOTION_BRIEFS_DB_ID` not set** → exit 2. Direct him to run
  `--bootstrap-db --parent-page-id <pid>` first.
- **Notion API error** → relay the message.

## Do NOT

- Don't run `--dry-run` (this command's job is to create a real page).
- Don't add `--force` (skeleton creation isn't a destructive op).
- Don't pollute the brief body with anything. The script's skeleton already
  has the right shape (callout + "Wochen-Notizen" heading + empty paragraph).
- Don't fire a Telegram ping manually — the script does it automatically
  unless `--no-telegram` is passed.
