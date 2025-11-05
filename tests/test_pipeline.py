"""
Integration tests for embedding pipeline: chunking -> SQLite -> FAISS.
"""

import sqlite3
import tempfile
from pathlib import Path
from uuid import uuid4

from src.retrieval.pipeline import (
    upsert_event_chunks,
    embed_and_index_chunks,
    default_stub_embed,
)
from src.retrieval.faiss_index import load_index, search_vectors
from src.utils.serialization import deserialize_embedding


def test_upsert_embed_index_roundtrip(tmp_path: Path):
    # Setup temporary DB
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    # Load schema (reuse project schema)
    from pathlib import Path as P
    schema_file = P(__file__).parent.parent / "src" / "storage" / "schema.sql"
    with open(schema_file, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()

    event_id = str(uuid4())
    content = "Derivatives are rates of change. " * 40
    topics = ["calculus", "derivatives"]
    skills = ["derivative_basic"]

    # Insert a minimal event row to satisfy FK
    cur = conn.cursor()
    import json
    cur.execute(
        """
        INSERT INTO events (event_id, content, event_type, actor, topics, skills)
        VALUES (?, ?, 'chat', 'student', ?, ?)
        """,
        (event_id, content, json.dumps(topics), json.dumps(skills)),
    )
    conn.commit()

    # Upsert chunks
    records = upsert_event_chunks(conn, event_id, content, topics, skills)
    assert len(records) > 1

    # Embed and index
    idx_path = tmp_path / "faiss_index.bin"
    embed_and_index_chunks(conn, records, embed_fn=default_stub_embed, faiss_path=idx_path)

    # Validate SQLite rows updated
    cur.execute("SELECT embedding, embedding_id FROM event_chunks WHERE event_id = ?", (event_id,))
    rows = cur.fetchall()
    assert len(rows) == len(records)
    # Ensure embeddings are present
    assert all(rows[i][0] is not None for i in range(len(rows)))

    # Validate FAISS index contains vectors
    index = load_index(idx_path)
    assert index.ntotal >= len(records)


