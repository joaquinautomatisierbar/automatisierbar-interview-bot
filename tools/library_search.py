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
