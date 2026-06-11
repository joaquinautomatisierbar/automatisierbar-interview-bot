---
name: build-visual-process-diagram
description: >
  Produce a brand-aligned A4-landscape SVG showing before/after of a customer's
  process (VORHER manual | NACHHER automated columns). Deterministic — invokes
  tools/visual_process_diagram.py, NOT an LLM. Use when the Presentation Designer
  agent needs the visual artifact for the customer's table.
---

# Build Visual Process Diagram

The customer's process described in the brief becomes a printable visual. This skill calls a deterministic Python generator — you don't render SVG yourself.

## Required input

Build a JSON object matching this schema:

```json
{
  "title": "string — customer name + automation name, e.g. 'Priority Inbox · Anwaltskanzlei Müller'",
  "customer_quote": "string — one sentence from the brief, ideally the desired_outcome verbatim",
  "hourly_rate_chf": 70,
  "cycles_per_week": 5,
  "steps": [
    {
      "who": "string — Mitarbeiter / n8n Workflow / Claude API / Slack-Bot etc.",
      "action": "string — short verb phrase, e.g. 'Posteingang prüfen'",
      "tool": "string — Outlook / Notion / Winjur / Slack / Gmail / Custom-CRM",
      "data_in": "string — e.g. '100+ Mails / Tag'",
      "data_out": "string — e.g. '5 wichtige markiert'",
      "time_minutes_before": 25,
      "time_minutes_after": 2
    }
  ]
}
```

**Critical:** every step needs BOTH `time_minutes_before` and `time_minutes_after`. If a step is fully automated, `time_minutes_after` is 0 (but the upstream human time to TRIGGER may not be — surface that in the previous step). See `compute-honest-roi` skill for the heuristics.

## How to invoke

Write the JSON to a file in your workspace, then run:

```bash
python3 /path/to/tools/visual_process_diagram.py \
  --input ./diagram-input.json \
  --output ./process-diagram.svg
```

The generator is at `tools/visual_process_diagram.py` relative to the project root. On VPS this is `/home/paperclip/<project>/tools/visual_process_diagram.py`. You can find it in `~/_context/` mount path conventions OR just install it once at `/home/paperclip/tools/visual_process_diagram.py` and reference it from there.

If the generator fails (invalid JSON, missing field), it exits with code 2 and prints the error to stderr — read it, fix the JSON, re-run.

## Output

A self-contained SVG file. Embed it in `roi-page.html` via:

```html
<div class="diagram">
  <!-- inline the SVG contents directly -->
</div>
```

OR reference it as an `<img src="process-diagram.svg">` if you keep it as a separate file alongside the HTML.

## Layout reference

The generator produces:

- A4-landscape (842 × 595 pt)
- Top header bar with title (Primary Deep #063D25) + customer quote (Primary Light)
- Two columns: VORHER (Mid Gray) | NACHHER (Primary Dark)
- Step cards with: who → action / tool · data_in → data_out / time badge
- Footer with totals: minutes saved per cycle, CHF saved per week/month/year, Mensch-Restzeit honesty note

Brand palette is hardcoded from `Automatisierbar_Brand_Guide EXTERN copy.pdf` v1.0. You don't override colors.

## What this skill does NOT do

- It does NOT estimate `time_minutes_before` / `time_minutes_after` — that's the `compute-honest-roi` skill's job.
- It does NOT generate the `roi-page.html` wrapper — you write that yourself, embedding the SVG.
- It does NOT write the `live-demo-script.md` — separate Presentation Designer artifact.
- It does NOT pick brand colors or fonts — they're locked from the brand guide.

## Failure modes

- **`time_minutes_*` missing**: fill with 0 if truly automated, otherwise revisit the step.
- **Long action/tool strings get truncated**: keep `action` under 30 chars, `tool` under 20.
- **Customer quote too long**: max 2 wrapped lines in the header. Keep quote under 200 chars.
- **More than ~9 steps**: rows get cramped. Split into 2 diagrams (Phase A / Phase B) OR combine adjacent micro-steps into one row.
