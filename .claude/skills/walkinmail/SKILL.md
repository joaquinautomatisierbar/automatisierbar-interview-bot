---
name: walkinmail
description: Use when the operator types /walkinmail or asks to "draft the walk-in mails", "do the walk-in follow-ups", "schreib die Walk-in Mails" — typically after a day of door-to-door walk-ins. Reads the new walk-in entries from the 💡-callout on the Operations Cockpit, finds each company's website + contact email, picks the matching industry pain-hypothesis from the Follow-Up Email Script, and drafts one send-ready German (Hochdeutsch, Sie) follow-up email per company as an openable draft directly in the operator's Infomaniak mailbox (Drafts folder, via IMAP — never sent), with a Notion archive copy on the "📧 Walk-in Mail Drafts" page, then marks each processed callout line ✅ + date. Drafts only — never sends.
---

# /walkinmail — Walk-in follow-up email drafter

After a walk-in where the prospect said *"schicken Sie mir ein Mail"*, turn each callout
entry into a finished, send-ready email. One run = N openable drafts in the Infomaniak mailbox
(`Drafts`), a Notion archive copy, + the callout marked done.

**The operator sends from `joaquin@automatisierbar.ch` via Infomaniak (not Gmail).** This skill
deposits each finished mail as an **openable draft directly in the Infomaniak mailbox** (IMAP
APPEND into `Drafts`, never SMTP, so nothing is ever sent) **and** archives a copy to
Notion. The operator just opens the draft and hits send. Bike Method Phase 1: operator reviews + sends.

## Config — the only thing to edit when details change

```
SENDER     = Joaquin Gamonal
FROM       = joaquin@automatisierbar.ch   # operator copies + sends from Infomaniak webmail
BOOKING    = https://calendar.app.google/mWy2heiDmRFcgFKA7   # ⚠️ Google booking link, being replaced — update here
PHONE      = +41 76 477 11 07
ORT        = Baden
```

### Notion IDs (single source of truth)
- **Operations Cockpit** page: `311bebb0c2f980de89a0f3d463a0fbce`
- **💡 walk-in callout** lives on that page (gray callout, lines like `Firma → Notiz`). Block: `389bebb0c2f9804eb2bef28e599c0a68`
- **Follow-Up Email Script** (template + Pitch-Bibliothek): `388bebb0c2f98088991deea070765a37`
- **📧 Walk-in Mail Drafts** archive page: `38abebb0c2f98179b9b7cadc7c3e9e47`

### Infomaniak draft delivery (primary output)
- Tool: `tools/walkin/infomaniak_draft.py` — appends each mail as a `\Draft` into `Drafts`
  via IMAP (imaplib only, **never SMTP** → cannot send). Mail-side defaults (host/port/subfolder)
  live in `tools/walkin/walkin_config.json`.
- Auth in `.env`: `INFOMANIAK_IMAP_USER`, `INFOMANIAK_IMAP_PASSWORD` (an Infomaniak **application
  password**, generated in the Infomaniak Manager → Mail → security).
- **Creds-missing / IMAP error is non-fatal:** the tool prints `creds fehlen` or a login error and
  exits 2; the skill then proceeds Notion-only and reports it. Never hard-fail the run.

## Procedure

### 1. Read the inputs
- `notion-fetch` the **Follow-Up Email Script** page → use its *Final Script* as the template and
  its *Branchenspezifische Pitch-Bibliothek* as the hypothesis library. Notion is the source of
  truth — never hardcode the template here; re-read it each run so script edits flow through.
- `notion-fetch` the **Operations Cockpit** page → read the 💡-callout. Parse each line as
  `Company → notes` (separators seen: `→`, `->`, `-`). **Skip any line already containing `✅`.**
- If the operator passed company names as args (e.g. `/walkinmail Codes SA, Avantec`), process
  only those lines instead of the whole callout.
- If there are no unprocessed lines, say so and stop.

### 2. For each company
1. **Resolve the recipient email.**
   - Use any email already in the line (e.g. `Mail@stephan-hatt.ch`).
   - Otherwise `WebSearch` the company + "Schweiz Kontakt", open the official site, read the
     Impressum/Kontakt page (`WebFetch`) and extract the contact email (prefer a real inbox like
     `info@`, `welcome@`, `kontakt@`, or a named person).
   - **Never invent an address.** If none is found, or the note says a non-email channel only
     (e.g. just "LinkedIn") and no email surfaces → flag the company, skip drafting it.
   - **Confidence flag (drives the An-field):** mark the address `confident: true` when it came
     verbatim from the callout line or a verified Impressum/Kontakt page. Mark `confident: false`
     for a best-guess/ambiguous address (several plausible inboxes, or the generic HQ inbox of a
     large org) — the draft then ships with an empty An-field so the operator fills it consciously.
2. **Classify the sector** from the website → pick the closest hypothesis from the Pitch-Bibliothek
   (Treuhand · Immobilien · Anwalt · Steuerberatung · Beratung/Agentur · Fiduciaire). If the sector
   is outside those six but still office/back-office (agency, IT reseller, etc.), pick the nearest
   analog (agencies → Beratung) and add a ⚠️ note that the hypothesis is a best-guess.
   - **ICP filter:** if the company is clearly non-back-office (Coiffeur, Restaurant, Bäckerei,
     trades) → flag it, don't draft. There's no automation pain to pitch.
3. **Fill the Final Script** (Hochdeutsch, **siezen**):
   - Subject: `Unser Besuch bei Ihnen, kurzer nächster Schritt` (or a script variant).
   - Warm anchor: `wie besprochen, wir waren diese Woche kurz bei Ihnen im Büro. Sie haben uns
     empfohlen, Ihnen eine kurze Nachricht zu schicken …` (use the actual weekday if known).
   - Pain hook (1 sentence): the sector hypothesis framed as the weekly time it costs them
     (**the pain is the pitch**), **no jargon** (never "API", "n8n", "Automatisierung" in the
     tech sense), **no prices**.
   - The offer = our **Grand Slam Offer**, used close to verbatim (it sits at the top of the
     Notion Final Script + as the red callout on the Operations Cockpit):
     *„Wir schauen uns Ihren Betrieb und Ihre Prozesse genau an, von A bis Z. Dann optimieren wir
     den Prozess, der am meisten Zeit kostet, und kommen mit etwas zurück, das Sie in Ruhe testen
     können. Bis dahin kostet es Sie nichts, und erst wenn es Sie überzeugt, sprechen wir über
     alles Weitere."* This is the confident risk-reversal: say it once, do not pile on.
   - **Sell the value, never sound cheap.** State that it costs nothing **exactly once**, inside
     the offer above. **Never** write "gratis"/"kostenlos" repeatedly, "kostet keinen Rappen", or
     self-deprecating lines like "Bringt's nichts, ist auch gut". Confident, not billig.
   - CTA (two options): the `BOOKING` link **or** a quick reply.
   - Sign-off: `Freundliche Grüsse aus {ORT}, / {SENDER} / Automatisierbar / {PHONE}`.
   - **Honor the per-line note:** if it says the contact forwards to the team (e.g. Q27, Avantec),
     add a forward-invite line: *„Falls jemand anderes bei Ihnen dafür zuständig ist, leiten Sie
     die Nachricht gerne weiter."* Address a known person by name (`Guten Tag Herr/Frau X`),
     otherwise `Guten Tag`.

### 3. Write the drafts to Notion (archive copy)
The Notion page is now a silent archive/searchable log — the operator works from the mailbox, not
Notion, but keep writing here every run for traceability and so `/walkinleadsconvert` has a record.
- `notion-update-page` (command `insert_content`, position end) on the **Walk-in Mail Drafts** page.
- **Use real line breaks in the content string, not `\n` escape sequences.** `notion-update-page`
  writes `\n` literally and mangles the whole layout (create-pages tolerates `\n`, update-page does
  not). One plain ` ``` ` code fence per email for one-click copy.
- Append a dated section: `## {YYYY-MM-DD} — N Entwürfe`, then per company:
  - `### {n}. {Firma} · {email}`
  - `**An:** {email}` and a `**Branche:**` line (with ⚠️ if best-guess / non-core ICP).
  - A fenced code block containing the full email (`Betreff:` line + body) for one-click copy.
  - A `---` divider between companies.

### 3b. Push the drafts into the Infomaniak mailbox (primary output)
Build a JSON payload of the mails you just composed and run the tool so each lands as an openable
draft in `Drafts`:
- Payload shape: `{"from": FROM, "drafts": [{"company","to","subject","body","confident"}, …]}`.
  - `confident: true` → put the resolved address in `to` (An: pre-filled, one-click send).
  - `confident: false` → set `to: ""` (An-field stays empty); carry the best-guess address + the
    ambiguity into the chat report so the operator fills it in deliberately.
  - `subject` = the Betreff text **without** the `Betreff:` prefix. `body` = the full mail body
    (real line breaks; the JSON encodes them, the tool keeps UTF-8 umlauts + the 👉 emoji).
- Write the payload to the scratchpad, then run:
  `python3 tools/walkin/infomaniak_draft.py --payload <scratchpad>/walkin_<YYYY-MM-DD>.json`
- Read the tool output: `[OK  ] <company> → Drafts` per success (`(An: leer)` for
  best-guess ones). If it prints `creds fehlen` or an IMAP login error, note it in the report and
  continue — the Notion archive (step 3) still holds every draft. Use `--list-folders` once if you
  need to debug folder detection, `--dry-run` to preview MIME without touching the mailbox.
- **First real run is supervised** (Bike Method Phase 1): tell the operator to open one draft and
  confirm it renders right before trusting the routine.

### 4. Mark the callout done
- `notion-update-page` (command `update_content`) on the **Operations Cockpit** page. For each
  processed line, append ` ✅ {YYYY-MM-DD}` using a unique trailing substring of the line as
  `old_str` (avoid the `→`/`->` arrows — they're markdown-escaped; match text after the arrow).

### 5. Report
One line per company: `✅ draft in Mailbox ({email}, {sector})`, `✅ draft, An: leer — best-guess
{email}` (operator fills the address), or `⚠️ flagged — {reason}`. Then tell the operator the drafts
are in **`Drafts`** (open + send), list any best-guess addresses to fill in, and link the
Notion archive page. If the Infomaniak push failed (creds/IMAP), say so plainly and point to the
Notion archive as the fallback.

## Guardrails
- **Drafts only — never send.** Output is an openable IMAP draft in `Drafts` (+ Notion
  archive); the operator opens + sends manually. The tool imports `imaplib` only, never `smtplib`,
  so it physically cannot send.
- **Creds-missing / IMAP failure is non-fatal** — fall back to the Notion archive, report it, keep going.
- **Best-guess address → empty An-field**, never a guessed recipient pre-filled for one-click send.
- **Never fabricate** an email address or a sector — flag instead.
- **Sell value, not cheap.** The Grand Slam Offer is the pitch; mention that it costs nothing
  **once**, confidently. Banned phrasings: repeated "gratis"/"kostenlos", "kostet keinen Rappen",
  "Bringt's nichts, ist auch gut" — they make us look billig.
- **Siezen, no tech jargon, no prices** — enforce the script's rules.
- **Keine Gedankenstriche (—/–) im E-Mail-Text.** Stattdessen Komma / Doppelpunkt / Punkt.
  Bindestriche in zusammengesetzten Wörtern (z. B. `30-Minuten-Termin`,
  `Lizenz- und Vertragsverlängerungen`) bleiben — die sind grammatikalisch korrekt.
- **Don't re-draft** lines already marked `✅`.
- The drafts page is an internal ops note (not a live leads DB), so writing to it + marking the
  callout is fine without a halt. Sending is the human's step.

## Reference
- Tone: `references/war-room/walkin_opener.md` (seriös, lokal, geduldig; kein Druck) +
  `references/business-context.md` (offer, ICP, free 2-week pilot, no pricing talk yet).
- Script + Pitch-Bibliothek live in Notion (`388bebb0…`) — that's the canonical copy.
- 48h no-answer follow-up (#2) also lives on the script page; this skill drafts #1 only.
