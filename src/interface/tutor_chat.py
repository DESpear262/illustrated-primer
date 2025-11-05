"""
Tutor Chat TUI for AI Tutor Proof of Concept.

Implements interactive chat sessions with start/resume/list commands.
Logs each turn as Event and summarizes on session end. Supports basic
document upload during a session.
"""

from __future__ import annotations

import sys
from typing import Optional, List
from uuid import uuid4
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.config import (
    DB_PATH,
    CHAT_HISTORY_TOKENS,
    CHAT_STREAM,
    CHAT_SPINNER_STYLE,
)
from src.storage.db import Database
from src.models.base import Event
from src.services.ai.client import get_client
from src.services.ai.router import get_router, AITask
from src.context.assembler import ContextAssembler
from src.interface.utils import (
    generate_session_id,
    build_history_messages,
    stitch_transcript,
)


console = Console()


class ChatSession:
    """In-memory representation of a chat session."""

    def __init__(self, session_id: Optional[str] = None, title: Optional[str] = None):
        self.session_id = session_id or generate_session_id()
        self.title = title
        self.turn_index = 0

    def next_turn(self) -> int:
        self.turn_index += 1
        return self.turn_index


def _load_session_events(session_id: str, db_path: Path) -> List[Event]:
    """Load all events for a session (metadata.session_id)."""
    with Database(db_path) as db:
        cursor = db.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM events
            WHERE json_extract(metadata, '$.session_id') = ?
            ORDER BY created_at ASC
            """,
            (session_id,),
        )
        rows = cursor.fetchall()
        return [db._row_to_event(r) for r in rows]


def list_sessions(db_path: Path = DB_PATH, limit: int = 20) -> List[dict]:
    """List recent sessions by scanning events grouped by session_id."""
    with Database(db_path) as db:
        cursor = db.conn.cursor()
        cursor.execute(
            """
            SELECT metadata, MIN(created_at) AS first_at, MAX(created_at) AS last_at, COUNT(*) AS cnt
            FROM events
            WHERE metadata LIKE '%"session_id":%'
            GROUP BY json_extract(metadata, '$.session_id')
            ORDER BY last_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        results = []
        for row in cursor.fetchall():
            meta = row[0]
            # naive parse for title and session_id
            import json
            try:
                m = json.loads(meta)
            except Exception:
                m = {}
            results.append(
                {
                    "session_id": m.get("session_id", "unknown"),
                    "title": m.get("session_title", "(untitled)"),
                    "first_at": row[1],
                    "last_at": row[2],
                    "count": row[3],
                }
            )
        return results


def suggest_session_title(first_user_text: str) -> str:
    """Use LLM to suggest a short session title based on first interaction."""
    from src.services.ai.router import AITask, ModelRoute
    
    client = get_client()
    # Use a very constrained system prompt and explicit user prompt
    system_prompt = (
        "You generate session titles. Output ONLY a 3-7 word title. "
        "No sentences, no greetings, no explanations. Just the title."
    )
    user_prompt = f"First message: {first_user_text}\n\nTitle (3-7 words):"
    
    # Use the classification route (nano model) for speed and lower cost
    route = ModelRoute(
        model_name="gpt-4o-mini",
        token_budget=100,  # Very small budget to encourage brevity
        supports_json_mode=False,
        supports_streaming=False,
    )
    
    # Call the API directly with our custom prompts
    response = client._call_api(route, system_prompt, user_prompt)
    title = response.choices[0].message.content.strip()
    
    # Aggressive cleanup: take first line only, strip quotes, limit length
    title = title.strip().strip('"').strip("'").strip(".")
    # Remove any conversational prefixes
    for prefix in ["Title:", "Session title:", "Title (3-7 words):", "Title (3-7 words only):"]:
        if title.lower().startswith(prefix.lower()):
            title = title[len(prefix):].strip()
    # Take only first line and stop at first sentence-ending punctuation
    title = title.split('\n')[0].split('.')[0].split('!')[0].split('?')[0].strip()
    if len(title) > 60:
        # Truncate at word boundary
        words = title[:60].rsplit(' ', 1)[0]
        title = words if words else title[:57] + "..."
    
    return title


def summarize_session(events: List[Event]) -> str:
    """Summarize a session using the AI client over stitched transcript."""
    client = get_client()
    transcript = stitch_transcript(events)
    summary = client.summarize_event(transcript)
    return summary.summary


def handle_upload(path: Path) -> str:
    """Read a document from disk and return its text content."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    return text


def run_session(session: ChatSession, db_path: Path = DB_PATH) -> None:
    """
    Run an interactive chat session. Logs each turn as Event. On exit,
    summarizes the session and stores a system Event.
    """
    client = get_client()
    console.print(Panel.fit(f"Starting session: [bold]{session.title or '(untitled)'}[/bold]\nID: {session.session_id}", title="Tutor Chat"))
    console.print("Type your question. Commands: /end, /upload <path>, /help")

    try:
        first_title_suggested = False
        while True:
            user_input = Prompt.ask("[bold cyan]You[/bold cyan]")
            if user_input.strip() == "":
                continue
            if user_input.strip().lower() == "/help":
                console.print("Commands: /end, /upload <path>")
                continue
            if user_input.strip().lower() == "/end":
                break
            if user_input.strip().lower().startswith("/upload "):
                _, path_str = user_input.split(" ", 1)
                p = Path(path_str).expanduser()
                if not p.exists():
                    console.print(f"[red]File not found:[/red] {p}")
                    continue
                doc_text = handle_upload(p)
                # Log upload as student transcript event
                with Database(db_path) as db:
                    e = Event(
                        event_id=str(uuid4()),
                        content=doc_text,
                        event_type="transcript",
                        actor="student",
                        metadata={
                            "session_id": session.session_id,
                            "turn_index": session.next_turn(),
                            "session_title": session.title,
                            "upload_path": str(p),
                        },
                    )
                    db.insert_event(e)

                # Immediate summary for upload events
                events = _load_session_events(session.session_id, db_path)
                with Progress(SpinnerColumn(style=CHAT_SPINNER_STYLE), TextColumn("[progress.description]{task.description}")) as progress:
                    progress.add_task(description="Summarizing uploaded document...", total=None)
                    upload_summary = summarize_session([events[-1]])

                with Database(db_path) as db:
                    s_ev = Event(
                        event_id=str(uuid4()),
                        content=upload_summary,
                        event_type="chat",
                        actor="system",
                        metadata={
                            "session_id": session.session_id,
                            "turn_index": session.next_turn(),
                            "session_title": session.title,
                            "summary_for": "upload",
                        },
                    )
                    db.insert_event(s_ev)
                console.print(Panel(upload_summary, title="Upload Summary"))
                continue

            # Regular chat turn: log student input
            with Database(db_path) as db:
                e = Event(
                    event_id=str(uuid4()),
                    content=user_input,
                    event_type="chat",
                    actor="student",
                    metadata={
                        "session_id": session.session_id,
                        "turn_index": session.next_turn(),
                        "session_title": session.title,
                    },
                )
                db.insert_event(e)

            # Suggest title after first user turn
            if not session.title and not first_title_suggested:
                try:
                    session.title = suggest_session_title(user_input)
                    first_title_suggested = True
                    console.print(f"[green]Session title:[/green] {session.title}")
                except Exception:
                    pass

            # Build context using assembler
            events = _load_session_events(session.session_id, db_path)
            history_msgs = build_history_messages(events, token_budget=CHAT_HISTORY_TOKENS)
            
            # Extract session topics from events
            session_topics = set()
            for e in events:
                session_topics.update(e.topics)
            session_topics = list(session_topics)
            
            # Use context assembler to compose context
            assembler = ContextAssembler(db_path=db_path)
            router = get_router()
            route = router.get_route(AITask.CHAT_REPLY)
            system_prompt = "You are an AI tutor helping a student learn."
            
            composed_context, retrieval_decision = assembler.compose_context(
                query_text=user_input,
                history_messages=history_msgs,
                system_prompt=system_prompt,
                route=route,
                session_topics=session_topics if session_topics else None,
            )

            # Get tutor reply with spinner
            with Progress(SpinnerColumn(style=CHAT_SPINNER_STYLE), TextColumn("[progress.description]{task.description}")) as progress:
                progress.add_task(description="Thinking...", total=None)
                reply = client.chat_reply(user_message=user_input, context=composed_context, stream=False)

            with Database(db_path) as db:
                r = Event(
                    event_id=str(uuid4()),
                    content=reply,
                    event_type="chat",
                    actor="tutor",
                    metadata={
                        "session_id": session.session_id,
                        "turn_index": session.next_turn(),
                        "session_title": session.title,
                    },
                )
                db.insert_event(r)
            console.print(Panel.fit(reply, title="Tutor"))

    except (KeyboardInterrupt, EOFError):
        console.print("\n[yellow]Interrupted. Ending session...[/yellow]")

    # Summarize on exit
    events = _load_session_events(session.session_id, db_path)
    if events:
        with Progress(SpinnerColumn(style=CHAT_SPINNER_STYLE), TextColumn("[progress.description]{task.description}")) as progress:
            progress.add_task(description="Summarizing session...", total=None)
            summary_text = summarize_session(events)
        with Database(db_path) as db:
            s = Event(
                event_id=str(uuid4()),
                content=summary_text,
                event_type="chat",
                actor="system",
                metadata={
                    "session_id": session.session_id,
                    "turn_index": session.next_turn(),
                    "session_title": session.title,
                    "summary_for": "session_end",
                },
            )
            db.insert_event(s)
        console.print(Panel(summary_text, title="Session Summary"))


def render_session_list(rows: List[dict]) -> None:
    table = Table(title="Recent Sessions")
    table.add_column("Session ID", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Events", style="yellow")
    table.add_column("Last At", style="magenta")
    for r in rows:
        table.add_row(r["session_id"], r.get("title") or "(untitled)", str(r["count"]), str(r["last_at"]))
    console.print(table)


