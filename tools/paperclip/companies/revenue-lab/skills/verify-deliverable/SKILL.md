---
name: verify-deliverable
description: >
  How the QA Reviewer actually verifies a deliverable — by RENDERING and OBSERVING it, never by
  assuming. Use before posting any REVIEW_PASS/REVIEW_FAIL. The core lesson: a deliverable you
  have not looked at is unreviewed.
---

# Verify Deliverable (observe it — don't assume)

The one rule that created this role: **a broken PDF reached the operator because no one looked
at it.** So: you do not judge a deliverable you have not rendered and seen. Evidence before verdict.

## Step 1 — Render / open the actual artifact

- **PDF:** `python3 ~/_context/tools/render_pdf.py <path-to.pdf>` → writes one PNG per page next
  to the PDF (e.g. `<name>.p1.png`, `.p2.png`…). Then use the **Read tool on each PNG** so you
  actually SEE the rendered pages. A PDF is not reviewed until you have viewed every page image.
- **Markdown / outreach / text:** Read the full file end-to-end (not the first lines).
- **SVG / image:** Read it directly.

## Step 2 — Run the hard checklist (every item, every time)

**A. Layout integrity** (the bug that started this):
- [ ] No overlapping text / elements stacked on each other
- [ ] Nothing runs off the page or is clipped
- [ ] Diagrams/images are legible at print size (not tiny/blurry)
- [ ] Consistent margins, spacing, page breaks; pages numbered correctly

**B. Brand compliance — ZERO Automatisierbar** (the separation rule):
- [ ] Uses ONLY the Revenue Lab brand (name, colors, type, logo) from the company brand guide
- [ ] NO Automatisierbar name, NO violet/blueprint "Theme 02", NO `@automatisierbar.ch`
- [ ] Contact = the approved Revenue Lab address/placeholder, nothing else
- [ ] No reuse of Automatisierbar scripts' styling (visual_process_diagram.py Theme 02, etc.)

**C. Content honesty**:
- [ ] Every CHF/time number is grounded in the input, not invented
- [ ] Human-residual time (Mensch-Restzeit) shown separately — no "100% automation" promise
- [ ] Claims are defensible to a skeptical buyer

**D. Offer correctness**:
- [ ] Price, scope, and CTA match the approved offer
- [ ] For outreach: the sending-gate checklist is present and unchecked (not sent)

## Step 3 — Post the verdict (handoff-protocol markers)

- **`REVIEW_PASS`** — only if you rendered/read it AND every box passes. State what you observed
  ("rendered 3 pages, viewed each; no overlap; brand = Revenue Lab only; numbers grounded").
- **`REVIEW_FAIL:`** — a numbered, specific, reproducible defect list, each tied to a location
  (`p2:`, `outreach Version A:`). Enough that Builder can fix without guessing.

## Anti-patterns (these are themselves review failures)

- Passing without rendering ("the description says it has 3 sections" ≠ you saw them).
- Vague fails ("looks off") — always say exactly what and where.
- Reviewing the Builder's *summary comment* instead of the *actual file*.
