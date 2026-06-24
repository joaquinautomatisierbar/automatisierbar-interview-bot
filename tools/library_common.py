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
