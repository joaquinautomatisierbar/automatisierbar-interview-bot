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


def test_book_title_normalizes():
    from library_ingest import book_title
    assert book_title(pathlib.Path("/x/100M_Offers.epub")) == "100M Offers"


def test_init_db_creates_tables():
    from library_ingest import init_db
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"chunks", "meta"} <= names


def test_pages_from_text_uses_seite_markers():
    from library_ingest import pages_from_text
    txt = "[Seite 2]\nhello world\n\n[Seite 3]\nsecond page here"
    pages = pages_from_text(txt)
    assert pages == [(2, "hello world"), (3, "second page here")]


def test_pages_from_text_synthetic_when_no_markers():
    from library_ingest import pages_from_text
    txt = " ".join(f"w{i}" for i in range(900))   # no markers -> ~400-word pages
    pages = pages_from_text(txt)
    assert [p[0] for p in pages] == [1, 2, 3]
    assert pages[0][1].startswith("w0 ")
