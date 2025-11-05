"""
Embedding and chunking pipeline for AI Tutor Proof of Concept.

Implements token-aware (or char-heuristic) chunking and an embedding
pipeline that batches texts for embedding and saves chunk rows to SQLite
and vectors to FAISS.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Tuple
from uuid import uuid4

import numpy as np

from src.config import (
    DB_PATH,
    OPENAI_EMBEDDING_MODEL,
    USE_TIKTOKEN,
    CHUNK_TOKENS,
    CHUNK_OVERLAP_TOKENS,
    BATCH_EMBED_SIZE,
    EMBEDDING_DIMENSION,
)
from src.utils.serialization import (
    serialize_json_list,
    serialize_embedding,
)
from src.retrieval.faiss_index import load_index, add_vectors, save_index


try:
    import tiktoken  # type: ignore
except Exception:  # pragma: no cover - optional dep
    tiktoken = None


def _tokenize(text: str) -> List[int]:
    if USE_TIKTOKEN and tiktoken is not None:
        enc = tiktoken.get_encoding("cl100k_base")
        return enc.encode(text)
    # Fallback: char-based pseudo tokens
    return list(text)


def chunk_text(text: str, max_tokens: int = CHUNK_TOKENS, overlap_tokens: int = CHUNK_OVERLAP_TOKENS) -> List[str]:
    """
    Chunk text into overlapping windows using tokens when available
    (via tiktoken), otherwise a character-length heuristic.
    """
    tokens = _tokenize(text)
    chunks: List[str] = []
    start = 0
    while start < len(tokens):
        end = min(len(tokens), start + max_tokens)
        if USE_TIKTOKEN and tiktoken is not None:
            enc = tiktoken.get_encoding("cl100k_base")
            chunk = enc.decode(tokens[start:end])
        else:
            # Fallback to slicing characters
            chunk = "".join(tokens[start:end])  # tokens are chars here
        chunks.append(chunk)
        if end == len(tokens):
            break
        start = max(0, end - overlap_tokens)
    return chunks


# Embedding function type: takes list of strings, returns np.ndarray of shape (N, D)
EmbedFn = Callable[[List[str]], np.ndarray]


def default_stub_embed(texts: List[str]) -> np.ndarray:
    """
    Deterministic stub embedding for tests (no API call).
    Uses simple hashing to map text to a vector space.
    """
    rng = np.random.default_rng(0)
    vectors = np.zeros((len(texts), EMBEDDING_DIMENSION), dtype=np.float32)
    for i, t in enumerate(texts):
        h = abs(hash(t))
        rng = np.random.default_rng(h % (2**32))
        vectors[i] = rng.standard_normal(EMBEDDING_DIMENSION).astype(np.float32)
    return vectors


@dataclass
class ChunkRecord:
    chunk_id: str
    event_id: str
    chunk_index: int
    text: str
    topics: List[str]
    skills: List[str]


def upsert_event_chunks(
    conn: sqlite3.Connection,
    event_id: str,
    content: str,
    topics: List[str],
    skills: List[str],
) -> List[ChunkRecord]:
    """
    Chunk content, remove existing chunks for the event, insert new rows,
    and return the inserted chunk records (without embeddings yet).
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM event_chunks WHERE event_id = ?", (event_id,))

    chunks = chunk_text(content)
    records: List[ChunkRecord] = []
    for idx, text in enumerate(chunks):
        chunk_id = str(uuid4())
        cursor.execute(
            """
            INSERT INTO event_chunks (
                chunk_id, event_id, chunk_index, text, topics, skills
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                chunk_id,
                event_id,
                idx,
                text,
                serialize_json_list(topics),
                serialize_json_list(skills),
            ),
        )
        records.append(ChunkRecord(chunk_id, event_id, idx, text, topics, skills))
    conn.commit()
    return records


def embed_and_index_chunks(
    conn: sqlite3.Connection,
    records: List[ChunkRecord],
    embed_fn: EmbedFn = default_stub_embed,
    faiss_path: Path = None,
) -> None:
    """
    Compute embeddings for chunk records, update SQLite rows with BLOBs,
    add vectors to FAISS, and persist the index.
    """
    faiss_path = faiss_path or Path(FAISS_INDEX_PATH)
    index = load_index(faiss_path)

    # Batch for embedding
    texts = [r.text for r in records]
    vectors = np.zeros((0, EMBEDDING_DIMENSION), dtype=np.float32)
    for i in range(0, len(texts), BATCH_EMBED_SIZE):
        batch = texts[i : i + BATCH_EMBED_SIZE]
        vecs = embed_fn(batch)
        vectors = np.vstack([vectors, vecs])

    start_id, _ = add_vectors(index, vectors)

    # Update SQLite with embedding bytes and embedding_id
    cursor = conn.cursor()
    for i, rec in enumerate(records):
        embedding = vectors[i]
        embedding_id = start_id + i
        cursor.execute(
            """
            UPDATE event_chunks
            SET embedding = ?, embedding_id = ?
            WHERE chunk_id = ?
            """,
            (serialize_embedding(embedding.tolist()), embedding_id, rec.chunk_id),
        )
    conn.commit()

    save_index(index, faiss_path)


