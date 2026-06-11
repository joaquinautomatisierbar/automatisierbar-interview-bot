# Library Index

Distilled business-decision knowledge from the operator's reading library. Source PDFs/EPUBs live in Google Drive folder `1gBLoBEasP8626IjOL6VBDg1jDYcPrjMf` (not committed). Each topic file merges insights across multiple books with source attribution per chunk.

**Loaded by:** `.claude/skills/library/SKILL.md` (auto-triggers on relevant decision topics).

## Topic map

| Topic file | Covers | Source books |
|---|---|---|
| [offers-and-pricing.md](offers-and-pricing.md) | Value equation, value stack, guarantees, pricing psychology, price raises, money models, fast-cash plays | $100M Offers, $100M Money Models, Pricing Playbook, Price Raise Playbook, Fast Cash Playbook |
| [leads-and-acquisition.md](leads-and-acquisition.md) | Core Four lead methods, hooks, lead magnets, lead nurture, ads, marketing machine | $100M Leads, Hooks Playbook, Lead Nurture Playbook, GOATed Ads Playbook, Marketing Machine Playbook, ACQ Advertising Handbook |
| [sales-and-closing.md](sales-and-closing.md) | CLOSER framework, objection handling, sales call structure, follow-up cadences | Closing Playbook, ACQ Closer Handbook |
| [retention-and-ltv.md](retention-and-ltv.md) | Onboarding, churn reduction, NPS, lifetime value plays, lifecycle | Retention Playbook, Lifetime Value Playbook |
| [positioning-and-proof.md](positioning-and-proof.md) | Niche selection, avatar, proof assets, social proof, brand positioning | Proof Checklist Playbook, Lost Chapters |
| [business-validation.md](business-validation.md) | Hypothesis testing, MVP design, idea validation experiments | Testing Business Ideas (Osterwalder/Bland) |

## Status (2026-05-03)

All 6 topic files distilled with substantive content. **All 19 of 19 source books ingested.** The two ACQ handbooks (image-only scanned PDFs) were OCR'd via Tesseract — quality is workable, content captured.

| Source book | File ingested into | Status |
|---|---|---|
| $100M Offers (EPUB) | offers-and-pricing.md | ✅ Value Equation, Grand Slam Offer, MAGIC, Guarantees taxonomy |
| $100M Leads (EPUB) | leads-and-acquisition.md | ✅ Core Four, Lead Magnets, Hook-Retain-Reward, More-Better-New |
| $100M Money Models (EPUB) | offers-and-pricing.md | ✅ 4 offer types, Win-Your-Money-Back |
| $100M Pricing Playbook | offers-and-pricing.md | ✅ 3 Levers, 3 Models, 10 Profit Plays |
| $100M Price Raise Playbook | offers-and-pricing.md | ✅ RAISE letter, Virtuous Cycle |
| $100M Fast Cash Playbook | offers-and-pricing.md | ✅ Quarterly warm-list promo |
| $100M Hooks Playbook | leads-and-acquisition.md | ✅ 8 hook types, 70-20-10 rule, 121 best hooks |
| $100M Lead Nurture Playbook | leads-and-acquisition.md | ✅ 4 Pillars, BAMFAM, A-C-A |
| $100M Marketing Machine Playbook | leads-and-acquisition.md | ✅ 9-component proof harvest checklist |
| $100M GOATed Ads Playbook | leads-and-acquisition.md | ✅ Awareness Pyramid, Hook+Meat+CTA assembly |
| $100M Closing Playbook | sales-and-closing.md | ✅ Onion of Blame, 28 Rules, full close library |
| $100M Retention Playbook | retention-and-ltv.md | ✅ 5 Horsemen, 9-step Churn Checklist |
| $100M LTV Playbook | retention-and-ltv.md | ✅ Crazy 8 |
| $100M Proof Checklist | positioning-and-proof.md | ✅ 13-item Proof Checklist, Belief Continuum |
| $100M Branding Playbook | positioning-and-proof.md | ✅ Reach×Influence×Direction, 8 brand positions |
| $100M Lost Chapters | positioning-and-proof.md + offers-and-pricing.md | ✅ Vista Avatar Method, CFA framework (LTGP/CAC/PPD) |
| Testing Business Ideas (Osterwalder) | business-validation.md | ✅ 3 risks, Discovery vs Validation |
| ACQ Closer Handbook (54MB, 170pp) | sales-and-closing.md | ✅ OCR'd via Tesseract — 9-step Discovery, Plug-and-Chug Offer Stack, 5 Objection Buckets, Looping, ACQ Career Path |
| ACQ Advertising Handbook (50MB, 125pp) | leads-and-acquisition.md | ✅ OCR'd via Tesseract — Ad Kaleidoscope (Remix + Remake), 20 ad frameworks |

## Reading rules (for the agent)

1. Read INDEX.md first to identify which topic file(s) apply.
2. Load **at most 2 topic files** per turn. If a question spans more, ask the user to narrow.
3. When recommending, cite the named framework + source book ("per Hormozi's Value Equation in $100M Offers, p. X").
4. If a topic file is missing or thin, say so — don't fabricate frameworks.

## Extending

To add a new book:
1. Drop PDF/EPUB in the Drive folder.
2. Distill into the matching topic file(s) using `references/library/_TEMPLATE.md` as the per-section template.
3. Update this INDEX if a new topic emerges.
4. Update `.claude/skills/library/SKILL.md` routing table if needed.
