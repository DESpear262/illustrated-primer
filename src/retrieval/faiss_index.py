"""
FAISS index operations for AI Tutor Proof of Concept.

Provides utilities to create, update, search, and persist a FAISS index
using cosine similarity (via inner product on normalized vectors).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple

import faiss  # type: ignore
import numpy as np

from src.config import FAISS_INDEX_PATH, EMBEDDING_DIMENSION


def _ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def normalize_vectors(vectors: np.ndarray) -> np.ndarray:
    """L2-normalize vectors for cosine similarity with IndexFlatIP."""
    norms = np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-12
    return vectors / norms


def create_flat_ip_index(dimension: int = EMBEDDING_DIMENSION) -> faiss.Index:
    """Create a flat inner-product FAISS index for cosine similarity."""
    return faiss.IndexFlatIP(dimension)


def add_vectors(index: faiss.Index, vectors: np.ndarray) -> Tuple[int, int]:
    """
    Add vectors to index.

    Returns:
        (start_id, count) of added vectors
    """
    if vectors.dtype != np.float32:
        vectors = vectors.astype(np.float32)
    vectors = normalize_vectors(vectors)
    start_id = index.ntotal
    index.add(vectors)
    return start_id, vectors.shape[0]


def search_vectors(index: faiss.Index, query_vectors: np.ndarray, top_k: int = 5) -> Tuple[np.ndarray, np.ndarray]:
    """Search top-k nearest neighbors for given query vectors."""
    if query_vectors.dtype != np.float32:
        query_vectors = query_vectors.astype(np.float32)
    query_vectors = normalize_vectors(query_vectors)
    distances, ids = index.search(query_vectors, top_k)
    return ids, distances


def save_index(index: faiss.Index, path: Path = FAISS_INDEX_PATH) -> None:
    """Persist FAISS index to disk."""
    _ensure_dir(path)
    faiss.write_index(index, str(path))


def load_index(path: Path = FAISS_INDEX_PATH, dimension: int = EMBEDDING_DIMENSION) -> faiss.Index:
    """
    Load FAISS index from disk, or create a new one if not present.
    """
    if path.exists():
        return faiss.read_index(str(path))
    return create_flat_ip_index(dimension)


