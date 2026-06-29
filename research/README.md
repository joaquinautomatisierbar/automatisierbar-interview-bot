# research/

Pre-build research dossiers produced by the **`/storm`** skill (`.claude/skills/storm/`).

Each file is a verified, multi-perspective markdown dossier the agent reads **before building something**, so we pick the best available approach instead of the first one. Not disposable — these are version-controlled and meant to be re-read by future build sessions (and by `/level-up`).

## Convention

- **Filename:** `<topic-slug>-YYYY-MM-DD.md` (kebab-case slug + the date it was produced).
- **Producer:** `/storm <topic>` — see the skill SOP for the full pipeline (lenses → contradiction map → synthesis → verify).
- **Structure (recommendation-first):** header + verification banner → recommended approach (TL;DR) → reliability-ranked findings → per-lens summaries → contradiction map → build implications for us → pitfalls → source audit → open questions / missing lens.

## How to use a dossier

1. Before a build, check here for an existing dossier on the topic. Re-run `/storm` if it's stale (the field moves; recency matters).
2. Build against the **Recommended approach** + **Build implications for us** sections.
3. The **Source audit** shows what was CONFIRMED / CORRECTED / DEMOTED — trust findings accordingly.
4. To deepen, ask `/storm` to add a lens and run V2 — it appends a fresh dossier, it doesn't overwrite.

## Caveats

- The expert panel is **author-built** — agreement across lenses is a strong hypothesis, not independent field consensus.
- **Reliability scores = evidence quality**, not how confident a lens sounded.
- Dossiers reflect what was true on their date. Verify load-bearing facts before betting the build on them.
