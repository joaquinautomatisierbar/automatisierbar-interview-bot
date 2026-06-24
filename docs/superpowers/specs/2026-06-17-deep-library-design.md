# Deep Library — Tier-2 Full-Text Knowledge Base

**Date:** 2026-06-17
**Status:** Design approved, pending implementation plan
**Owner:** Operator (Automatisierbar / Revenue Lab)

## Problem

The distilled book library (`references/library/`, 19 Hormozi + business-validation
books in 6 topic files) gives **principles and summaries**. When a task needs depth —
e.g. rebuilding the Lena voice-agent pitch per Hormozi's exact recap/close structure —
the summaries are not enough. Today the operator has to open NotebookLM manually, find
the right passage, paste it to Claude, and only then can it be used. The operator is a
human bottleneck on every deep lookup.

**Goal:** when Claude (operator side) or a Paperclip agent (VPS side) detects "a look
into the actual book would help here," it can query the **full text of all 19 books**
directly — semantically, with citations — without the operator in the loop. Reusable
findings get saved back so the fast layer grows. The base is easily expandable.

## Decisions (locked)

| Decision | Choice | Rationale |
|---|---|---|
| Live-link NotebookLM? | **No** | NotebookLM (consumer) has no public API. We build our own queryable store over the *same books* — better: local, free per query, version-controlled, callable by Paperclip. |
| Retrieval method | **Local semantic** | NotebookLM-grade recall on fuzzy questions, ~0 cost per query, fully in operator's control, syncable to VPS. |
| Corpus | **The same 19 books** already in Drive folder `1gBLoBEasP8626IjOL6VBDg1jDYcPrjMf` | Operator confirmed NotebookLM == that Drive folder. Step 1 is pure processing, no uploads. |
| Embedding provider | **OpenAI `text-embedding-3-small` @ 512 dims** | Key already wired; no heavy ML deps on MacBook/VPS; one-time index of all 19 books < $0.50; per-query cost negligible. Same model for ingest + query (consistency requirement). |
| Vector search | **Brute-force cosine in numpy** | ≤ ~8k chunks → <50 ms. No FAISS / vector-DB dependency. |

## Architecture — two tiers, one interface

- **Tier 1 (exists):** 6 distilled topic files = fast router/overview layer, auto-triggered
  by the `library` skill on business-decision topics.
- **Tier 2 (new):** semantically searchable full text of all 19 books in a local sqlite
  vector store, queried **on demand** when Tier 1 is insufficient.
- **One interface for both sides:** `tools/library_search.py "<question>"` — invoked
  identically by Claude (operator) and any Paperclip agent (VPS) via the command line.

## Components

| File | Purpose |
|---|---|
| `tools/library_ingest.py` | Build/update the store: Drive PDF/EPUB → full text (reuse `tools/extract_pdf_text.py` + Tesseract OCR for the 2 scanned PDFs; add EPUB handling) → ~600-token chunks (~80-token overlap) with `{book, section, ≈page}` metadata → embed → upsert into sqlite. `--add <file>` for a single new book. |
| `references/library/fulltext.db` | sqlite store. Schema below. ~15–20 MB. **gitignored** (regenerable), synced to VPS via rsync. |
| `tools/library_search.py` | Query: embed question → cosine over all chunks → top-k passages with citation `Book — §Chapter (≈p.N)`. Flags: `--book`, `--k` (default 5), `--topic`. |
| `.claude/skills/library/SKILL.md` | Extended: Tier-1 routing unchanged; new section — "if the summary isn't enough → call `library_search.py` for exact passages." |
| `workflows/library_deep_search.md` | WAT SOP: trigger / inputs / tool sequence / outputs / edge cases for deep lookups. |
| Paperclip company skill (recall-style) | Instructs VPS agents: on a knowledge gap, call `library_search.py` instead of guessing. |

## Storage schema (`fulltext.db`)

```
chunks(
  id          INTEGER PRIMARY KEY,
  book        TEXT,      -- canonical book title
  section     TEXT,      -- chapter / section heading if detectable, else ""
  page        INTEGER,   -- approximate source page
  text        TEXT,      -- the chunk (~600 tokens)
  embedding   BLOB       -- float32[512], same model as query time
)
meta(key TEXT, value TEXT)  -- embedding_model, dims, ingest_date, book_count
```

## Data flow

- **Ingest (once + on new book):** Drive file → text → chunks → embeddings → `fulltext.db`.
  Adding a book = `library_ingest.py --add <file>`; propagates to VPS on next sync.
- **Query (runtime):** Claude/agent detects a knowledge gap →
  `library_search.py "how does Hormozi structure the pitch recap?"` → returns 3–5 exact
  passages + citations → used directly in the build. Operator no longer in the loop.

## Save-back & expand loop

- A deep search that yields a **reusable** insight gets distilled (via the `remember`
  skill) into the matching **Tier-1 topic file** → surfaces automatically next time, no
  repeat deep search. The fast layer grows with usage.
- New books: drop in Drive → `--add` → done.

## Paperclip wiring

- `fulltext.db` + `library_search.py` added to `MOUNT_PATHS` in
  `tools/paperclip/scripts/sync-context.sh` → land under `~/_context/` on the VPS.
- Embedding key bound to the agents that need it (CEO/Builder) via existing
  secret-ref env binding.
- A recall-style company skill tells agents: knowledge gap → call the tool, don't guess.
- **No-Burn compliance:** one lookup = one bounded tool call (fraction of a cent), no
  loop, no heartbeat. Consistent with the agent-budget policy.

## Rollout (Bike-Method phasing)

1. **Phase 1 — Operator side:** ingest 19 books + `library_search.py` + skill extension.
   Validate on a real query (e.g. voice-agent pitch). Proof = correct passages + citations.
2. **Phase 2 — Paperclip side:** sync wiring + key binding + agent instruction. Validate
   on one real agent run that actually calls the tool.
3. **Phase 3 — Loop:** save-back convention + expand docs + the `library_deep_search.md` SOP.

## Non-goals / YAGNI

- No NotebookLM API integration (doesn't exist for consumer).
- No FAISS / external vector DB — corpus is small enough for brute-force cosine.
- No re-embedding on the VPS — the prebuilt `.db` is rsynced; VPS only embeds the short query.
- No hosted RAG (Gemini/OpenAI vector store) — rejected for cost + data-egress + No-Burn fit.

## Risks / open items

- **Scanned-PDF OCR quality** for the 2 ACQ handbooks — already OCR'd workably for Tier 1;
  reuse that text, accept slightly noisier chunks.
- **EPUB extraction** — confirm/add an EPUB→text path in ingest (most books are EPUB).
- **`.db` size in git** — kept out of git, pushed via rsync only.
- **Embedding-model drift** — ingest and query MUST use the same model+dims; enforced by
  reading `meta.embedding_model` in `library_search.py` and failing loudly on mismatch.
