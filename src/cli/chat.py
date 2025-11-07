"""
Chat CLI for AI Tutor Proof of Concept.

Commands:
  - start: start a new chat session (optional --title)
  - resume: resume an existing chat session by ID
  - list: list recent sessions
"""

from __future__ import annotations

from typing import Optional
from pathlib import Path
from uuid import uuid4

import typer
from rich.console import Console

from src.config import DB_PATH
from src.interface.tutor_chat import ChatSession, run_session, list_sessions, render_session_list


app = typer.Typer(help="Tutor chat interface commands")
console = Console()


@app.command()
def start(
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Optional session title"),
    db_path: Optional[Path] = typer.Option(None, "--db", help="Path to the SQLite database file."),
):
    """Start a new chat session."""
    db_path = db_path or DB_PATH
    session = ChatSession(title=title)
    run_session(session, db_path)


@app.command()
def resume(
    session_id: str = typer.Argument(..., help="Session ID to resume"),
    db_path: Optional[Path] = typer.Option(None, "--db", help="Path to the SQLite database file."),
):
    """Resume an existing chat session by ID."""
    db_path = db_path or DB_PATH
    session = ChatSession(session_id=session_id)
    run_session(session, db_path)


@app.command()
def list(
    db_path: Optional[Path] = typer.Option(None, "--db", help="Path to the SQLite database file."),
    limit: int = typer.Option(20, "--limit", "-n", help="Max sessions to display"),
):
    """List recent chat sessions."""
    db_path = db_path or DB_PATH
    rows = list_sessions(db_path=db_path, limit=limit)
    render_session_list(rows)


if __name__ == "__main__":
    app()


