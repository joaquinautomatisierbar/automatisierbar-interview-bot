---
name: library
description: Use when the operator is making business decisions about offers, pricing, guarantees, value stacks, value equation, lead generation, lead magnets, hooks, advertising, marketing funnels, lead nurture, sales conversations, objection handling, closing, sales scripts, follow-up, scaling operations, hiring, retention, churn, lifetime value, LTV/CAC, positioning, niche selection, avatar, social proof, money models, fast cash plays, business validation, MVP testing, or any product/client/team/marketing strategy decision. Pulls from a distilled library of Alex Hormozi's $100M series + business validation books to ground recommendations in named frameworks (Value Equation, Core Four leads, CLOSER framework, etc.) with source attribution.
---

# Library lookup routing

Activated when the operator is making a business decision that named frameworks can ground. Read `references/library/INDEX.md` if topic isn't obvious from the question, else jump straight to the matching topic file(s).

## Routing table

| If the operator is asking about... | Read |
|---|---|
| Pricing, offers, guarantees, value stack, value equation, money models, price raises, fast cash | `references/library/offers-and-pricing.md` |
| Lead gen, hooks, lead magnets, ads, marketing funnels, content, lead nurture | `references/library/leads-and-acquisition.md` |
| Sales calls, objections, closing, CLOSER framework, follow-up, sales scripts | `references/library/sales-and-closing.md` |
| Onboarding, churn, retention, NPS, LTV, lifecycle plays | `references/library/retention-and-ltv.md` |
| Positioning, niche, avatar, social proof, brand, proof assets | `references/library/positioning-and-proof.md` |
| Idea validation, MVP, hypothesis testing, market discovery | `references/library/business-validation.md` |

## Tier 2 — full-text deep search (when summaries aren't enough)

The routing table above is **Tier 1** (distilled summaries). When a task needs the
*exact wording, a specific step, or detail not in the summary* (e.g. rebuilding a
sales script, quoting a framework verbatim), query the full text of all 19 books:

    .venv/bin/python tools/library_search.py "<your question>" --k 5
    # optional: --book "100M Offers" to scope to one book

Returns the top matching passages with `Book (≈S.N)` citations. Use these exact
passages, cite them, and prefer them over paraphrase when precision matters.

**Save-back:** if a deep-search passage yields a reusable rule worth having on the
fast path, distill it into the matching Tier-1 topic file (via the `remember` skill)
so it surfaces automatically next time — the fast layer grows with use.

## Loading rules

1. Load **at most 2 topic files per turn.** If the question spans more, narrow it with the operator first.
2. Skim `## Frameworks` first — they're the highest-leverage units. Use `## Heuristics` and `## Anti-patterns` as quick checks.
3. **Cite sources.** Every recommendation grounded in the library should name the framework + book ("per Hormozi's Value Equation in *$100M Offers*").
4. **If a topic file is missing or thin**, say so explicitly — don't invent frameworks. Tell the operator the relevant book hasn't been distilled yet.

## Stay-out-of-the-way rules

This skill is NOT for:
- Pure code/engineering decisions (use general knowledge)
- n8n workflow building (use n8n-* skills)
- Generic conversation or trivia
- The operator-principles framework itself (already inlined in CLAUDE.md + `references/operator-principles.md`)

If the question doesn't map cleanly to one of the routing table topics, don't force-fit it — just skip the library lookup.

## Output convention

When grounding a recommendation:

> **Recommendation:** <what to do>
>
> **Framework:** <name> (*Source: Book, ch/p*)
>
> **Why this fits:** <one-line link from the question to the framework's "When to use"*

Keep it tight. The operator wants the framework name + the leverage move, not a book report.
