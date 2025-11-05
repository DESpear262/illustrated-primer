"""
Unit tests for FAISS index and chunking.
"""

import sqlite3
import tempfile
from pathlib import Path

import numpy as np

from src.retrieval.faiss_index import (
    create_flat_ip_index,
    add_vectors,
    search_vectors,
    save_index,
    load_index,
)
from src.retrieval.pipeline import chunk_text, default_stub_embed


def test_chunk_text_basic():
    text = "This is a short text to chunk. " * 50
    chunks = chunk_text(text, max_tokens=50, overlap_tokens=10)
    assert len(chunks) > 1
    # Overlap implies adjacent chunks share content
    assert chunks[0][-10:] in chunks[1]


def test_faiss_add_search_and_persist(tmp_path: Path):
    index = create_flat_ip_index(32)

    rng = np.random.default_rng(42)
    vectors = rng.standard_normal((10, 32)).astype(np.float32)
    start_id, count = add_vectors(index, vectors)
    assert count == 10

    # Query the first vector
    ids, dists = search_vectors(index, vectors[0:1], top_k=3)
    assert ids.shape == (1, 3)
    assert int(ids[0][0]) >= 0

    # Persist and reload
    idx_path = tmp_path / "faiss_index.bin"
    save_index(index, idx_path)
    loaded = load_index(idx_path, dimension=32)

    ids2, _ = search_vectors(loaded, vectors[0:1], top_k=3)
    assert int(ids2[0][0]) == int(ids[0][0])


