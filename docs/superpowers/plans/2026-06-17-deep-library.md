# Deep Library — Tier-2 Full-Text Knowledge Base — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give Claude (operator) and Paperclip agents on-demand semantic access to the full text of all 19 distilled books, with citations, so deep lookups no longer route through the operator manually.

**Architecture:** A local sqlite vector store (`references/library/fulltext.db`) holds chunked, OpenAI-embedded full text of every book. `tools/library_ingest.py` builds it; `tools/library_search.py` queries it (embed question → brute-force cosine in numpy → top-k passages + citations). Both sides call the same CLI tool. The store + search tool sync to the VPS so Paperclip agents query it identically.

**Tech Stack:** Python 3.9 (`.venv/bin/python`), PyMuPDF/`fitz` (PDF+EPUB extraction), OpenAI `text-embedding-3-small` @ 512 dims (via `requests`, no SDK), numpy (cosine), sqlite3 (stdlib), pytest (pure-logic tests).

## Global Constraints

- **Python interpreter:** always `.venv/bin/python` (repo venv, Python 3.9.7). Use `from __future__ import annotations` for `list[...]`/`str | None` hints (3.9 floor).
- **Embedding model is canonical and fixed:** `text-embedding-3-small`, `dimensions=512`. Ingest and query MUST use the same — `guard_model()` enforces this and fails loudly on mismatch.
- **No new heavy deps.** Only `requests` (present), `numpy` (present), `fitz`/pymupdf (present), `pytest` (dev, install into venv). Do NOT add the `openai` SDK — call the REST endpoint with `requests`.
- **Tools must be CWD-independent.** Paperclip agents run them from `~/_context/`, not the repo root. Resolve paths via `Path(__file__)`, never `os.getcwd()`.
- **Cost guard (CLAUDE.md halt policy):** the one-time full ingest of 19 books is a real spend (~$0.50) — it is the single approved batch; do NOT re-run it casually. A single sanity embed call is fine. Per-query embeds are a fraction of a cent.
- **Commits:** this plan includes per-task `git commit` steps (frequent-commit convention). Per CLAUDE.md, commits happen on the operator's say-so — treat each commit step as "stage + propose," and only push/commit once the operator has opted in for this branch.
- **Branch:** work happens on the current branch (`experiment/revenue-lab-company`) unless the operator says otherwise.

---

## File Structure

| File | Responsibility |
|---|---|
| `tools/library_common.py` | Shared: constants (model/dims/db path), `embed_texts()`, `pack/unpack_embedding()`, `chunk_pages()`, `cosine_topk()`, `format_citation()`, `connect()`, `guard_model()`. Pure logic + the one OpenAI call. |
| `tools/library_ingest.py` | Build/update the store: extract (fitz) → chunk → embed → write sqlite. `--add <file>`, `--src-dir`. |
| `tools/library_search.py` | Query the store: embed question → cosine → top-k passages + citations. `--k`, `--book`. |
| `tests/test_library.py` | pytest unit tests for the pure functions in `library_common.py`. |
| `references/library/fulltext.db` | Generated sqlite store. gitignored; rsynced to VPS. |
| `.claude/skills/library/SKILL.md` | Extended with a Tier-2 section pointing at `library_search.py`. |
| `tools/paperclip/scripts/sync-context.sh` | `MOUNT_PATHS` extended with the db + the two query-side tools. |
| `tools/paperclip/companies/<company>/skills/deep-library/SKILL.md` | Paperclip-side skill instructing agents to query the store on a knowledge gap. |
| `workflows/library_deep_search.md` | WAT SOP: when/how to use deep search + the save-back loop. |

---

## PHASE 1 — Operator side (build it, prove it works locally)

### Task 1: `library_common.py` — shared core + unit tests

**Files:**
- Create: `tools/library_common.py`
- Test: `tests/test_library.py`

**Interfaces:**
- Produces (consumed by Tasks 2 & 3):
  - `DB_PATH: Path`, `EMBED_MODEL: str = "text-embedding-3-small"`, `EMBED_DIMS: int = 512`
  - `embed_texts(texts: list[str]) -> list[np.ndarray]`
  - `pack_embedding(vec) -> bytes`, `unpack_embedding(blob: bytes) -> np.ndarray`
  - `chunk_pages(pages: list[tuple[int, str]]) -> list[tuple[int, str]]` → `(start_page, chunk_text)`
  - `cosine_topk(query: np.ndarray, matrix: np.ndarray, k: int) -> list[int]`
  - `format_citation(book: str, page: int) -> str`
  - `connect(db_path=DB_PATH) -> sqlite3.Connection`, `guard_model(conn) -> None`

- [ ] **Step 1: Install pytest into the venv**

Run: `.venv/bin/pip install pytest`
Expected: `Successfully installed pytest-...`

- [ ] **Step 2: Write the failing tests**

Create `tests/test_library.py`:

```python
import sqlite3
import sys
import pathlib

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "tools"))

from library_common import (  # noqa: E402
    chunk_pages, pack_embedding, unpack_embedding, format_citation,
    cosine_topk, guard_model, EMBED_MODEL, EMBED_DIMS,
)


def test_chunk_pages_tags_start_page():
    pages = [(1, "a " * 500), (2, "b " * 200)]
    chunks = chunk_pages(pages)
    assert chunks
    assert chunks[0][0] == 1
    assert all(isinstance(c[1], str) and c[1] for c in chunks)


def test_chunk_pages_overlaps_into_multiple():
    pages = [(1, " ".join(f"w{i}" for i in range(1000)))]
    chunks = chunk_pages(pages)
    assert len(chunks) >= 2


def test_embedding_roundtrip():
    v = np.arange(EMBED_DIMS, dtype=np.float32)
    assert np.array_equal(unpack_embedding(pack_embedding(v)), v)


def test_format_citation():
    assert format_citation("$100M Offers", 42) == "$100M Offers (≈S.42)"


def test_cosine_topk_orders_by_similarity():
    q = np.array([1.0, 0.0], dtype=np.float32)
    m = np.array([[1.0, 0.0], [0.9, 0.1], [-1.0, 0.0]], dtype=np.float32)
    assert cosine_topk(q, m, 2) == [0, 1]


def test_cosine_topk_empty_matrix():
    assert cosine_topk(np.array([1.0, 0.0], dtype=np.float32), np.empty((0, 2), dtype=np.float32), 5) == []


def test_guard_model_mismatch_raises():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE meta (key TEXT, value TEXT)")
    conn.executemany("INSERT INTO meta VALUES (?,?)",
                     [("embedding_model", "wrong"), ("dims", "1536")])
    with pytest.raises(RuntimeError):
        guard_model(conn)


def test_guard_model_match_ok():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE meta (key TEXT, value TEXT)")
    conn.executemany("INSERT INTO meta VALUES (?,?)",
                     [("embedding_model", EMBED_MODEL), ("dims", str(EMBED_DIMS))])
    guard_model(conn)  # must not raise
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_library.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'library_common'`

- [ ] **Step 4: Implement `library_common.py`**

Create `tools/library_common.py`:

```python
"""library_common.py — Shared helpers for the Deep Library full-text store.

Both library_ingest.py (build) and library_search.py (query) import from here so
the embedding model, dimensions, chunking, and vector math live in ONE place.
A model mismatch between ingest and query silently returns garbage —
guard_model() makes that failure loud.
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import numpy as np
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "references" / "library" / "fulltext.db"

EMBED_MODEL = "text-embedding-3-small"
EMBED_DIMS = 512
OPENAI_EMBED_URL = "https://api.openai.com/v1/embeddings"

CHUNK_WORDS = 450          # ~600 tokens
CHUNK_OVERLAP_WORDS = 60


def _api_key() -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        env = PROJECT_ROOT / ".env"
        if env.exists():
            for line in env.read_text().splitlines():
                if line.startswith("OPENAI_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not key:
        raise RuntimeError("OPENAI_API_KEY not set (checked env and .env)")
    return key


def embed_texts(texts: list[str]) -> list[np.ndarray]:
    """Embed a batch with the canonical model+dims. Returns float32 arrays in order."""
    if not texts:
        return []
    key = _api_key()
    out: list[np.ndarray] = []
    for i in range(0, len(texts), 100):
        batch = texts[i:i + 100]
        resp = requests.post(
            OPENAI_EMBED_URL,
            headers={"Authorization": f"Bearer {key}"},
            json={"model": EMBED_MODEL, "input": batch, "dimensions": EMBED_DIMS},
            timeout=60,
        )
        resp.raise_for_status()
        data = sorted(resp.json()["data"], key=lambda d: d["index"])
        out.extend(np.asarray(d["embedding"], dtype=np.float32) for d in data)
    return out


def pack_embedding(vec: np.ndarray) -> bytes:
    return np.asarray(vec, dtype=np.float32).tobytes()


def unpack_embedding(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


def chunk_pages(pages: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """[(page_no, page_text), ...] -> [(start_page, chunk_text), ...].

    Word-windowed with overlap. start_page = the page the chunk began on.
    """
    words: list[tuple[str, int]] = []
    for page_no, text in pages:
        for w in text.split():
            words.append((w, page_no))
    chunks: list[tuple[int, str]] = []
    step = CHUNK_WORDS - CHUNK_OVERLAP_WORDS
    for start in range(0, len(words), step):
        window = words[start:start + CHUNK_WORDS]
        if not window:
            break
        start_page = window[0][1]
        chunk_text = " ".join(w for w, _ in window).strip()
        if chunk_text:
            chunks.append((start_page, chunk_text))
        if start + CHUNK_WORDS >= len(words):
            break
    return chunks


def format_citation(book: str, page: int) -> str:
    return f"{book} (≈S.{page})"


def cosine_topk(query: np.ndarray, matrix: np.ndarray, k: int) -> list[int]:
    """Indices of the top-k rows in `matrix` most similar to `query`."""
    if matrix.shape[0] == 0:
        return []
    q = query / (np.linalg.norm(query) + 1e-9)
    m = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-9)
    sims = m @ q
    k = min(k, sims.shape[0])
    return np.argsort(-sims)[:k].tolist()


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    return sqlite3.connect(str(db_path))


def guard_model(conn: sqlite3.Connection) -> None:
    """Fail loudly if the store was built with a different embedding model/dims."""
    meta = dict(conn.execute("SELECT key, value FROM meta").fetchall())
    if meta.get("embedding_model") != EMBED_MODEL or int(meta.get("dims", 0)) != EMBED_DIMS:
        raise RuntimeError(
            f"Embedding mismatch: store built with "
            f"{meta.get('embedding_model')}/{meta.get('dims')} but querying with "
            f"{EMBED_MODEL}/{EMBED_DIMS}. Rebuild with library_ingest.py."
        )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_library.py -v`
Expected: PASS — 7 passed.

- [ ] **Step 6: Commit**

```bash
git add tools/library_common.py tests/test_library.py
git commit -m "feat(library): Tier-2 deep-library shared core + unit tests"
```

---

### Task 2: `library_ingest.py` — build the store

**Files:**
- Create: `tools/library_ingest.py`
- Modify: `.gitignore` (add the generated db)
- Test: extend `tests/test_library.py` with a `book_title` + db-roundtrip test

**Interfaces:**
- Consumes from Task 1: `DB_PATH, EMBED_MODEL, EMBED_DIMS, chunk_pages, embed_texts, pack_embedding, connect`
- Produces: `extract_pages(path) -> list[tuple[int,str]]`, `book_title(path) -> str`, `init_db(conn)`, `ingest_book(conn, path) -> int`, `set_meta(conn)`; CLI building `references/library/fulltext.db`

- [ ] **Step 1: gitignore the generated store**

Add to `.gitignore` (new line):
```
references/library/fulltext.db
```

- [ ] **Step 2: Write the failing test (title normalization + db schema)**

Append to `tests/test_library.py`:

```python
def test_book_title_normalizes(tmp_path):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "tools"))
    from library_ingest import book_title
    assert book_title(pathlib.Path("/x/100M_Offers.epub")) == "100M Offers"


def test_init_db_creates_tables(tmp_path):
    from library_ingest import init_db
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"chunks", "meta"} <= names
```

- [ ] **Step 3: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_library.py -k "book_title or init_db" -v`
Expected: FAIL — `No module named 'library_ingest'`

- [ ] **Step 4: Implement `library_ingest.py`**

Create `tools/library_ingest.py`:

```python
"""library_ingest.py — Build/update the Deep Library full-text vector store.

Reads source books (PDF/EPUB) from a local dir, extracts text per page, chunks,
embeds via OpenAI, writes references/library/fulltext.db.

Prereq: source files in --src-dir (default .tmp/library_src/). Get them there by
downloading the 19 books from Drive folder 1gBLoBEasP8626IjOL6VBDg1jDYcPrjMf.

Usage:
  .venv/bin/python tools/library_ingest.py                  # all books in .tmp/library_src/
  .venv/bin/python tools/library_ingest.py --add book.epub  # add/refresh one book
  .venv/bin/python tools/library_ingest.py --src-dir DIR
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import fitz  # pymupdf — opens PDF, EPUB, MOBI

sys.path.insert(0, str(Path(__file__).resolve().parent))
from library_common import (  # noqa: E402
    DB_PATH, EMBED_MODEL, EMBED_DIMS, chunk_pages, embed_texts, pack_embedding, connect,
)

DEFAULT_SRC = Path(".tmp/library_src")
MIN_CHARS_FOR_TEXT = 200   # below this a file is image-only (needs OCR)


def extract_pages(path: Path) -> list[tuple[int, str]]:
    doc = fitz.open(str(path))
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text").strip()
        if text:
            pages.append((i + 1, text))
    doc.close()
    return pages


def book_title(path: Path) -> str:
    return path.stem.replace("_", " ").strip()


def init_db(conn) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY,
            book TEXT, section TEXT, page INTEGER, text TEXT, embedding BLOB
        );
        CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
        CREATE INDEX IF NOT EXISTS idx_chunks_book ON chunks(book);
        """
    )


def ingest_book(conn, path: Path) -> int:
    title = book_title(path)
    pages = extract_pages(path)
    if sum(len(t) for _, t in pages) < MIN_CHARS_FOR_TEXT:
        print(f"  ⚠ {title}: image-only / no text — skipped (needs OCR)", file=sys.stderr)
        return 0
    chunks = chunk_pages(pages)
    vecs = embed_texts([c for _, c in chunks])
    conn.execute("DELETE FROM chunks WHERE book = ?", (title,))
    conn.executemany(
        "INSERT INTO chunks (book, section, page, text, embedding) VALUES (?,?,?,?,?)",
        [(title, "", pg, txt, pack_embedding(v)) for (pg, txt), v in zip(chunks, vecs)],
    )
    conn.commit()
    print(f"  ✓ {title}: {len(chunks)} chunks")
    return len(chunks)


def set_meta(conn) -> None:
    n_books = conn.execute("SELECT COUNT(DISTINCT book) FROM chunks").fetchone()[0]
    for k, v in [
        ("embedding_model", EMBED_MODEL), ("dims", str(EMBED_DIMS)),
        ("book_count", str(n_books)), ("ingest_date", date.today().isoformat()),
    ]:
        conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", (k, v))
    conn.commit()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src-dir", default=str(DEFAULT_SRC))
    ap.add_argument("--add", help="ingest/refresh a single file")
    args = ap.parse_args()

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = connect()
    init_db(conn)

    if args.add:
        ingest_book(conn, Path(args.add))
    else:
        src = Path(args.src_dir)
        files = sorted(p for p in src.glob("*") if p.suffix.lower() in {".pdf", ".epub", ".mobi"})
        if not files:
            print(f"No book files in {src} — fetch the 19 books from Drive first.", file=sys.stderr)
            sys.exit(1)
        for p in files:
            ingest_book(conn, p)

    set_meta(conn)
    n = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    print(f"Done. {n} chunks across {conn.execute('SELECT COUNT(DISTINCT book) FROM chunks').fetchone()[0]} books → {DB_PATH}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run unit tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_library.py -v`
Expected: PASS — all (now 9) passed.

- [ ] **Step 6: Fetch the source books, then smoke-test ingest on ONE book**

Prerequisite (orchestration — done by Claude at execution): download the 19 books from Drive folder `1gBLoBEasP8626IjOL6VBDg1jDYcPrjMf` into `.tmp/library_src/` (via the Google Drive MCP `download_file_content`, or copy from a local folder if the operator still has them). For this smoke step, ensure at least one `.epub`/`.pdf` is present.

Run (requires `OPENAI_API_KEY` in `.env` — see Task 3 Step 1 if not yet added):
`.venv/bin/python tools/library_ingest.py --add ".tmp/library_src/<one-book>.epub"`
Expected: `✓ <Title>: N chunks` then `Done. N chunks across 1 books → .../fulltext.db`

- [ ] **Step 7: Commit**

```bash
git add tools/library_ingest.py tests/test_library.py .gitignore
git commit -m "feat(library): ingest tool — extract/chunk/embed books into sqlite store"
```

---

### Task 3: `library_search.py` — query the store

**Files:**
- Create: `tools/library_search.py`

**Interfaces:**
- Consumes from Task 1: `embed_texts, unpack_embedding, cosine_topk, format_citation, connect, guard_model`
- Produces: `search(query: str, k: int = 5, book: str | None = None) -> list[dict]` (dicts: `{book, page, text}`); CLI printing cited passages.

- [ ] **Step 1: Add the embedding key + verify with ONE sanity call**

Operator action (credential — required, one-time): add to `.env`:
```
OPENAI_API_KEY=sk-...
```
Then verify the key works with the single approved sanity call:
Run: `.venv/bin/python -c "import sys; sys.path.insert(0,'tools'); from library_common import embed_texts; print(len(embed_texts(['hello'])[0]))"`
Expected: `512`

- [ ] **Step 2: Implement `library_search.py`**

Create `tools/library_search.py`:

```python
"""library_search.py — Query the Deep Library full-text store.

Claude (operator) and Paperclip agents call this on a knowledge gap:
  .venv/bin/python tools/library_search.py "how does Hormozi structure the pitch recap?"
  .venv/bin/python tools/library_search.py "guarantee types" --book "100M Offers" --k 8

Prints the top-k matching passages with citations.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from library_common import (  # noqa: E402
    embed_texts, unpack_embedding, cosine_topk, format_citation, connect, guard_model,
)


def search(query: str, k: int = 5, book: str | None = None) -> list[dict]:
    conn = connect()
    guard_model(conn)
    sql = "SELECT book, page, text, embedding FROM chunks"
    params: list = []
    if book:
        sql += " WHERE book = ?"
        params.append(book)
    rows = conn.execute(sql, params).fetchall()
    if not rows:
        return []
    matrix = np.vstack([unpack_embedding(r[3]) for r in rows])
    qvec = embed_texts([query])[0]
    idxs = cosine_topk(qvec, matrix, k)
    return [{"book": rows[i][0], "page": rows[i][1], "text": rows[i][2]} for i in idxs]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--book", default=None)
    args = ap.parse_args()
    results = search(args.query, k=args.k, book=args.book)
    if not results:
        print("No matches. Is the store built? Run library_ingest.py.", file=sys.stderr)
        sys.exit(1)
    for r in results:
        print(f"### {format_citation(r['book'], r['page'])}\n{r['text']}\n")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Smoke-test the query against the one ingested book**

Run: `.venv/bin/python tools/library_search.py "how do you structure a grand slam offer?" --k 3`
Expected: 3 `### <Book> (≈S.N)` blocks with relevant passage text. (If only one book is ingested so far, results all cite it — that's fine for the smoke.)

- [ ] **Step 4: Commit**

```bash
git add tools/library_search.py
git commit -m "feat(library): search tool — semantic query with citations + drift guard"
```

---

### Task 4: Wire the operator `library` skill to Tier-2

**Files:**
- Modify: `.claude/skills/library/SKILL.md` (add a Tier-2 section after the routing table)

**Interfaces:** none (documentation/routing only).

- [ ] **Step 1: Add the Tier-2 section**

Insert after the `## Routing table` section in `.claude/skills/library/SKILL.md`:

```markdown
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
```

- [ ] **Step 2: Verify the edit reads correctly**

Run: `grep -n "Tier 2" .claude/skills/library/SKILL.md`
Expected: one match on the new heading.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/library/SKILL.md
git commit -m "feat(library): route library skill to Tier-2 deep search"
```

---

### Task 5: Full ingest + end-to-end validation (Phase 1 gate)

**Files:** none created — this is the validation gate.

- [ ] **Step 1: Confirm all 19 source books are in `.tmp/library_src/`**

Run: `ls .tmp/library_src/ | wc -l`
Expected: `19` (or note which are missing). Image-only PDFs (the 2 ACQ handbooks) will be reported as skipped by ingest — acceptable; they remain Tier-1-only for now (logged, not silently dropped).

- [ ] **Step 2: Run the full ingest (the single approved batch spend ~$0.50)**

Run: `.venv/bin/python tools/library_ingest.py`
Expected: a `✓` line per text-bearing book, `⚠ … skipped` for image-only ones, final `Done. <N> chunks across <M> books`.

- [ ] **Step 3: Validate retrieval quality on the real motivating query**

Run: `.venv/bin/python tools/library_search.py "wie strukturiert Hormozi den Pitch-Recap und den Übergang zum Close?" --k 5`
Expected: passages from the sales/closing books (CLOSER, Closing Playbook) that actually address recap→close — proving the German-question→English-text cross-lingual retrieval works. Eyeball that the passages are on-topic.

- [ ] **Step 4: Checkpoint**

Run: `bash .claude/hooks/notify-telegram.sh checkpoint "Deep Library Phase 1 done: 19 books ingested, semantic search validated end-to-end"`

---

## PHASE 2 — Paperclip side (agents query the same store)

> Tasks 6–7 touch live infra + production agents. Per CLAUDE.md halt-before-acting: call `bash .claude/hooks/notify-telegram.sh halt "<reason>"` and confirm before the VPS push and before any live-agent run. Confirm the CURRENT VPS host first — a migration from `72.61.106.8` to `187.124.191.115` may be in progress; do not hardcode the old IP blindly.

### Task 6: Sync the store + bind the embedding key on the VPS

**Files:**
- Modify: `tools/paperclip/scripts/sync-context.sh` (`MOUNT_PATHS`)

**Interfaces:** none (infra wiring).

- [ ] **Step 1: Add the query-side assets to `MOUNT_PATHS`**

In `tools/paperclip/scripts/sync-context.sh`, add to the `MOUNT_PATHS=( ... )` array:
```bash
  "tools/library_common.py"
  "tools/library_search.py"
  "references/library/fulltext.db"
```
(Do NOT add `library_ingest.py` — agents query, they don't build.)

- [ ] **Step 2: Local sync + verify the db landed**

Run: `bash tools/paperclip/scripts/sync-context.sh`
Then: `ls -la ~/_context/references/library/fulltext.db && ls ~/_context/tools/library_search.py`
Expected: both present; db size ~15–20 MB.

- [ ] **Step 3: Push to the VPS (HALT-GATED)**

Confirm current host, then: `bash tools/paperclip/scripts/sync-context.sh --push-to-vps`
Expected: rsync transfers the db + tools to `~/_context/` on the VPS. Verify via SSH: `ls -la ~/_context/references/library/fulltext.db`.

- [ ] **Step 4: Bind `OPENAI_API_KEY` to the target agent (HALT-GATED)**

Bind the secret as a per-agent env via the documented secret-ref pattern (`PATCH /agents/:id` `adapterConfig.env`, see `tools/paperclip/scripts/wire_revenue_agents.py` and the agent-secrets reference). Target the agent(s) that do strategy/build work (e.g. CEO, Builder). Verify the agent can run: `.venv/bin/python` equivalent on VPS resolves `OPENAI_API_KEY` and one embed returns a 512-vector.

- [ ] **Step 5: Commit the sync-config change**

```bash
git add tools/paperclip/scripts/sync-context.sh
git commit -m "feat(library): sync Tier-2 store + search tool to VPS agents"
```

---

### Task 7: Paperclip `deep-library` skill + live-agent validation

**Files:**
- Create: `tools/paperclip/companies/automatisierbar-build/skills/deep-library/SKILL.md`

**Interfaces:** none (agent instruction).

- [ ] **Step 1: Create the company skill**

Create `tools/paperclip/companies/automatisierbar-build/skills/deep-library/SKILL.md`:

```markdown
---
name: deep-library
description: >
  When you hit a business-knowledge gap (offers, pricing, leads, sales scripts,
  objections, retention, positioning) and the distilled context isn't specific
  enough, query the full text of the 19-book library instead of guessing.
---

# Deep Library (full-text search)

The firm's books are indexed as a local semantic store. On a knowledge gap, run:

    python3 ~/_context/tools/library_search.py "<your question>" --k 5
    # optional: --book "100M Offers"

Returns top passages with `Book (≈S.N)` citations. Ground your decision in those
passages and cite them. One call per gap — do NOT loop (No-Burn policy).

## Rules
1. Query only on a real gap, after checking the distilled context you already have.
2. Cite the book + page when you use a passage.
3. If the tool errors (no key / no store), note it once and proceed with your best
   judgment — do not retry in a loop.
```

- [ ] **Step 2: Validate on ONE real agent run (HALT-GATED)**

Trigger a single heartbeat run of the target agent on a task that should hit the
library (e.g. "refine the offer guarantee"). Confirm via the run logs / execution
output that it invoked `library_search.py` and used a cited passage. One bounded run.

- [ ] **Step 3: Checkpoint + commit**

```bash
git add tools/paperclip/companies/automatisierbar-build/skills/deep-library/
git commit -m "feat(library): Paperclip deep-library skill for VPS agents"
```
Run: `bash .claude/hooks/notify-telegram.sh checkpoint "Deep Library Phase 2 done: VPS agents can query the full-text store"`

---

## PHASE 3 — Loop + docs (expandability + save-back)

### Task 8: WAT SOP + expand/save-back documentation

**Files:**
- Create: `workflows/library_deep_search.md`

**Interfaces:** none (SOP).

- [ ] **Step 1: Write the SOP**

Create `workflows/library_deep_search.md`:

```markdown
---
autonomy-level: L3
bike-method-phase: 1
kpi-bucket: more value per customer
kpi-metric: build quality (decisions grounded in cited frameworks vs. guessed)
---

# Workflow: Deep Library Search

Two-tier business-knowledge access. Tier 1 = distilled summaries (`references/library/`,
auto via the `library` skill). Tier 2 = full-text semantic search over all 19 books.

## The five elements
- **Trigger:** a task needs detail/exact wording the Tier-1 summary doesn't carry.
- **Data sources:** `references/library/fulltext.db` (chunked, embedded full text).
- **Transformations:** embed the question (OpenAI text-embedding-3-small @512) →
  cosine over all chunks → top-k passages.
- **Decision points:** is Tier-1 enough? If yes, stop. If no, deep-search. Is a
  result reusable enough to promote to Tier 1?
- **Destination:** cited passages used in the build; reusable rules promoted to the
  matching Tier-1 topic file.

## Use it
    .venv/bin/python tools/library_search.py "<question>" --k 5 [--book "<title>"]
Agents on the VPS: `python3 ~/_context/tools/library_search.py "<question>"`.

## Expand the library (add a book)
1. Drop the PDF/EPUB into Drive folder `1gBLoBEasP8626IjOL6VBDg1jDYcPrjMf`
   (and into `.tmp/library_src/`).
2. `.venv/bin/python tools/library_ingest.py --add ".tmp/library_src/<file>"`
3. Re-sync to VPS: `bash tools/paperclip/scripts/sync-context.sh --push-to-vps`

## Save-back loop
When a deep-search passage yields a reusable rule, distill it into the matching
Tier-1 topic file via the `remember` skill. The fast layer grows with use; the next
lookup finds it without a deep search.

## Constraints / gotchas
- Ingest and query MUST use the same embedding model — `guard_model()` enforces it.
- Full re-ingest is a real spend (~$0.50) — do it deliberately, not casually.
- Image-only PDFs (the 2 ACQ handbooks) are skipped by ingest (need OCR) and remain
  Tier-1-only until OCR'd. They are logged, never silently dropped.
- One query per gap on the agent side — no loops (No-Burn policy).
```

- [ ] **Step 2: Verify**

Run: `head -8 workflows/library_deep_search.md`
Expected: the frontmatter block with `autonomy-level: L3` / `bike-method-phase: 1`.

- [ ] **Step 3: Commit**

```bash
git add workflows/library_deep_search.md
git commit -m "docs(library): WAT SOP for deep search + expand/save-back loop"
```

---

## Self-Review (completed during planning)

- **Spec coverage:** two tiers ✅ (Tier-1 exists, Tier-2 = Tasks 1–3); one shared interface ✅ (`library_search.py`, Tasks 3/7); on-demand query ✅; citations ✅ (`format_citation`); save-back loop ✅ (Tasks 4/8); Paperclip wiring ✅ (Tasks 6–7); expandable ✅ (`--add`, Task 8); embedding-drift guard ✅ (`guard_model`, Task 1); local semantic + OpenAI-small @512 ✅; sqlite schema matches spec ✅; image-only/OCR risk handled (skip+log) ✅; `.db` out of git, rsynced ✅.
- **Placeholder scan:** none — all code is complete; the two operator actions (add `OPENAI_API_KEY`, fetch books from Drive) are real prerequisites, not placeholders.
- **Type consistency:** `chunk_pages` returns `(start_page, chunk_text)` and is consumed that way in `ingest_book`; `cosine_topk` returns `list[int]` indices used to index `rows`; `embed_texts` returns `list[np.ndarray]` zipped with chunks; `guard_model`/`connect`/`DB_PATH` names consistent across all three modules and both skills.
```
