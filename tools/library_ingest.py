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
import re
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


SYNTH_PAGE_WORDS = 400   # pseudo-page size for flat .txt without [Seite N] markers


def pages_from_text(text: str) -> list[tuple[int, str]]:
    """Recover (page_no, text) from a pre-extracted .txt.

    Uses '[Seite N]' markers (extract_pdf_text.py format) when present; otherwise
    paginates synthetically into ~SYNTH_PAGE_WORDS-word blocks so citations stay
    granular even for flat OCR dumps.
    """
    parts = re.split(r"\[Seite (\d+)\]", text)
    if len(parts) > 1:
        rest = parts[1:]
        pages = []
        for i in range(0, len(rest) - 1, 2):
            body = rest[i + 1].strip()
            if body:
                pages.append((int(rest[i]), body))
        if pages:
            return pages
    words = text.split()
    return [
        (i // SYNTH_PAGE_WORDS + 1, " ".join(words[i:i + SYNTH_PAGE_WORDS]))
        for i in range(0, len(words), SYNTH_PAGE_WORDS)
    ]


def extract_pages(path: Path) -> list[tuple[int, str]]:
    if path.suffix.lower() == ".txt":
        return pages_from_text(path.read_text(encoding="utf-8", errors="replace"))
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
        # Prefer pre-extracted .txt over the binary source (esp. the image-only ACQ
        # PDFs, where fitz yields nothing and only the OCR'd .txt is usable).
        pref = {".txt": 0, ".epub": 1, ".pdf": 2, ".mobi": 3}
        by_stem: dict[str, Path] = {}
        for p in src.glob("*"):
            if p.suffix.lower() not in pref:
                continue
            cur = by_stem.get(p.stem)
            if cur is None or pref[p.suffix.lower()] < pref[cur.suffix.lower()]:
                by_stem[p.stem] = p
        files = sorted(by_stem.values())
        if not files:
            print(f"No book files in {src} — fetch the books from Drive first.", file=sys.stderr)
            sys.exit(1)
        for p in files:
            ingest_book(conn, p)

    set_meta(conn)
    n = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    m = conn.execute("SELECT COUNT(DISTINCT book) FROM chunks").fetchone()[0]
    print(f"Done. {n} chunks across {m} books -> {DB_PATH}")


if __name__ == "__main__":
    main()
