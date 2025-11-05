"""
Index CLI commands for AI Tutor Proof of Concept.

Provides commands to build, check status, and search the FAISS index.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from src.config import DB_PATH, FAISS_INDEX_PATH
from src.retrieval.faiss_index import load_index, save_index
from src.retrieval.pipeline import upsert_event_chunks, embed_and_index_chunks, default_stub_embed

app = typer.Typer(help="Index management commands")
console = Console()


@app.command()
def build(
    db_path: Path = typer.Option(None, help="Path to database file"),
    event_id: Optional[str] = typer.Option(None, help="Reindex only a specific event_id"),
    use_stub: bool = typer.Option(True, help="Use stub embedder (no OpenAI)"),
):
    """Build or update the FAISS index from database events."""
    db_path = db_path or DB_PATH
    embed_fn = default_stub_embed if use_stub else default_stub_embed

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        if event_id:
            cursor.execute("SELECT event_id, content, topics, skills FROM events WHERE event_id = ?", (event_id,))
        else:
            cursor.execute("SELECT event_id, content, topics, skills FROM events")

        rows = cursor.fetchall()
        total_chunks = 0
        for row in rows:
            ev_id, content, topics_json, skills_json = row
            topics = __import__('json').loads(topics_json)
            skills = __import__('json').loads(skills_json)
            records = upsert_event_chunks(conn, ev_id, content, topics, skills)
            embed_and_index_chunks(conn, records, embed_fn=embed_fn)
            total_chunks += len(records)

        console.print(f"[green]✓ Indexed {len(rows)} events into {total_chunks} chunks[/green]")
    finally:
        conn.close()


@app.command()
def status(
    index_path: Path = typer.Option(None, help="Path to FAISS index file"),
):
    """Show FAISS index status (size and path)."""
    index_path = index_path or FAISS_INDEX_PATH
    index = load_index(index_path)

    table = Table(title="FAISS Index Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Path", str(index_path))
    table.add_row("Vectors", str(index.ntotal))
    console.print(table)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query text"),
    topk: int = typer.Option(5, help="Top-K results"),
    use_stub: bool = typer.Option(True, help="Use stub embedder (no OpenAI)"),
    index_path: Path = typer.Option(None, help="Path to FAISS index file"),
):
    """Search the FAISS index for the given query text."""
    import numpy as np
    from src.retrieval.faiss_index import search_vectors

    index_path = index_path or FAISS_INDEX_PATH
    index = load_index(index_path)
    embed_fn = default_stub_embed if use_stub else default_stub_embed

    vectors = embed_fn([query])
    ids, dists = search_vectors(index, vectors, top_k=topk)

    table = Table(title="Index Search Results")
    table.add_column("Rank", style="cyan")
    table.add_column("VectorID", style="magenta")
    table.add_column("Score", style="green")

    for i in range(ids.shape[1]):
        table.add_row(str(i + 1), str(int(ids[0][i])), f"{float(dists[0][i]):.4f}")
    console.print(table)


