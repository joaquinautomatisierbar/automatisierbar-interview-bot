---
name: pick-fast-revenue-offer
description: >
  Choose ONE fast-to-revenue productized digital service for Revenue Lab, grounded in the
  distilled library + the real ICP, optimized for the shortest path to a first cleared payment.
  Use when the CEO is selecting what the company will sell.
---

# Pick a Fast-Revenue Offer

The goal is the SHORTEST honest path to one cleared payment — not the biggest TAM. Pick a
fixed-scope, fixed-price digital deliverable an ICP buyer can purchase via a payment link.

## Constraints (from COMPANY.md)

- **Digital service only.** Productized: same scope every time, deliverable by the Builder + the
  existing n8n/Notion infra. No physical goods, no bespoke consulting that needs the operator's
  hours per sale.
- **ICP fit (hard filter):** backoffice-heavy Swiss SMEs — Immobilien / Treuhand / Anwalt /
  Steuerberater. They have real backoffice pain and budget. Exclude Coiffeur / Restaurant /
  Bäckerei / trades (no backoffice = no automation pain).
- **Time-to-revenue first.** Prefer offers where the asset already half-exists in this repo
  (lead enrichment, a Notion/n8n micro-automation, a templated deliverable) over greenfield.

## Ground every choice in the library

Read `references/library/INDEX.md` and apply:
- **Value Equation** (dream outcome × perceived likelihood ÷ time delay ÷ effort): pick an offer
  that scores high on fast, certain, low-effort-for-the-buyer.
- **Fast-Cash money model:** a one-off, low-friction price (a payment link, not a subscription
  or a sales call) clears fastest for a first dollar.
- **Testing Business Ideas — evidence before build:** before the Builder builds anything, get a
  cheap demand signal (a reply, a "yes I'd pay", a comparable competitor selling it). Don't
  build on a hunch; that's how the $38-morning waste happens.

## Output of this skill

A single offer spec the CEO halts on for operator approval:
- **Offer name + one-line promise** (the dream outcome, ICP-specific).
- **Fixed scope** (exactly what the buyer gets) + **fixed price** (CHF).
- **Fulfilment plan** (which existing asset/infra the Builder uses; what's net-new).
- **Demand evidence** (the cheap signal that this will sell).
- **Why this is the shortest path to a cleared payment.**

Then: **HALT for operator approval** (`money-halt-protocol`) before committing. One offer at a
time — focus beats a portfolio when the cap is $300.
