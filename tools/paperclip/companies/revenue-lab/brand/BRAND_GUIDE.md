# Revenue Lab — Brand Guide (SOURCE OF TRUTH)

> **STATUS: NOT YET DEFINED.** The brand-proposal cycle must fill this in (CEO proposes → QA
> checks → operator approves) BEFORE any customer-facing artifact is generated. Until the fields
> below are filled and operator-approved, no PDF/outreach may be produced.

This file is the ONLY brand source for Revenue Lab deliverables. Every customer-facing artifact
(reports, outreach, landing copy) must match this and nothing else.

## HARD CONSTRAINTS (non-negotiable — QA fails any violation)

- **Zero Automatisierbar.** Revenue Lab is a completely separate business. NO Automatisierbar
  name, logo, colors, the violet/blueprint "Theme 02", the `automatisierbar.ch` domain, or the
  `@automatisierbar.ch` email may appear anywhere. Do NOT reuse Automatisierbar's brand assets
  or the styling baked into its scripts (`visual_process_diagram.py` Theme 02, its PDF themes).
- **Own identity.** Distinct name, palette, and typography that are Revenue Lab's own.
- **Contact = the approved address only.** Until a real domain/email is provisioned, use the
  placeholder `[KONTAKT-EMAIL]` literally — never substitute an Automatisierbar address.
- **Honest by default** (carries into copy): no "100% automation" claims; human-residual time
  shown separately; every number grounded.

## FIELDS TO DEFINE (the brand-proposal cycle fills these)

- **Business name:** _TBD_
- **One-line positioning / tagline:** _TBD_
- **Primary color (hex):** _TBD_  ·  **Secondary:** _TBD_  ·  **Accent:** _TBD_
  - (Must NOT be Automatisierbar's violet/blueprint or green.)
- **Typography:** heading font _TBD_, body font _TBD_ (system/open fonts only).
- **Logo / wordmark approach:** _TBD_ (text wordmark is fine for v1).
- **Tone of voice:** _TBD_ (e.g. direct, sachlich, Hochdeutsch for the Swiss SME ICP).
- **Contact:** `[KONTAKT-EMAIL]` (placeholder until operator provisions a real one).
- **Footer / legal line:** _TBD_ (Revenue Lab brand only).

## How deliverables consume this

The Builder's PDF/outreach generator must read these values from this file (or a small
`brand.json` it derives from this) and apply them — it must NOT hardcode any Automatisierbar
styling. QA verifies the rendered output matches this guide and contains zero Automatisierbar
references (see the `verify-deliverable` skill, checklist section B).
