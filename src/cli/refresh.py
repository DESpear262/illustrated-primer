"""
Refresh CLI commands for AI Tutor Proof of Concept.

Provides commands to refresh topic summaries and skill states.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.config import DB_PATH
from src.summarizers.update import (
    refresh_topic_summaries,
    get_topics_needing_refresh,
    update_topic_summary,
)
from src.storage.db import Database

app = typer.Typer(help="Refresh commands")
console = Console()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.command()
def summaries(
    topic: Optional[str] = typer.Option(None, "--topic", help="Refresh specific topic ID"),
    since: Optional[str] = typer.Option(None, "--since", help="Refresh topics with events since timestamp (ISO format)"),
    force: bool = typer.Option(False, "--force", help="Force refresh even if recently updated"),
    db_path: Optional[Path] = typer.Option(None, "--db-path", help="Path to database file"),
):
    """
    Refresh topic summaries for topics with new events.
    
    Updates topic summaries with aggregated content from recent events.
    Can refresh all topics, specific topics, or topics with events since a timestamp.
    """
    db_path = db_path or DB_PATH
    
    # Parse since timestamp if provided
    since_timestamp = None
    if since:
        try:
            since_timestamp = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError as e:
            console.print(f"[red]✗ Invalid timestamp format:[/red] {e}")
            raise typer.Exit(code=1)
    
    try:
        # Initialize database
        with Database(db_path) as db:
            db.initialize()
        
        # Determine topics to refresh
        if topic:
            # Refresh specific topic
            console.print(f"[cyan]Refreshing topic:[/cyan] {topic}")
            results = refresh_topic_summaries(
                topic_ids=[topic],
                since=since_timestamp,
                force=force,
                db_path=db_path,
            )
        else:
            # Get topics needing refresh
            if since_timestamp:
                topics_needing_refresh = get_topics_needing_refresh(
                    since=since_timestamp,
                    db_path=db_path,
                )
            else:
                topics_needing_refresh = get_topics_needing_refresh(db_path=db_path)
            
            if not topics_needing_refresh:
                console.print("[yellow]No topics need summarization refresh[/yellow]")
                return
            
            console.print(f"[cyan]Refreshing {len(topics_needing_refresh)} topics[/cyan]")
            
            # Refresh topics
            results = refresh_topic_summaries(
                topic_ids=topics_needing_refresh,
                since=since_timestamp,
                force=force,
                db_path=db_path,
            )
        
        # Display results
        success_count = 0
        failure_count = 0
        total_tokens = 0
        
        results_table = Table(title="Refresh Results", show_header=True, header_style="bold magenta")
        results_table.add_column("Topic ID", style="cyan")
        results_table.add_column("Status", style="green")
        results_table.add_column("Summary Version", style="yellow")
        results_table.add_column("Tokens Used", style="blue")
        results_table.add_column("Event Count", style="magenta")
        
        for topic_id, (updated_topic, tokens_used) in results.items():
            if updated_topic:
                status = "[green]✓ Success[/green]"
                success_count += 1
                version = updated_topic.metadata.get("summary_version", "N/A")
                event_count = updated_topic.event_count
                tokens = tokens_used or 0
                total_tokens += tokens
            else:
                status = "[red]✗ Failed[/red]"
                failure_count += 1
                version = "N/A"
                event_count = "N/A"
                tokens = 0
            
            results_table.add_row(
                topic_id,
                status,
                str(version),
                str(tokens),
                str(event_count),
            )
        
        console.print(results_table)
        
        # Summary
        summary_panel = Panel(
            f"[green]Success:[/green] {success_count}\n"
            f"[red]Failures:[/red] {failure_count}\n"
            f"[cyan]Total Topics:[/cyan] {len(results)}\n"
            f"[yellow]Total Tokens:[/yellow] {total_tokens}",
            title="Refresh Summary",
            border_style="green",
        )
        console.print(summary_panel)
        
        if failure_count > 0:
            console.print(f"[yellow]Warning: {failure_count} topics failed to refresh[/yellow]")
            raise typer.Exit(code=1)
        
        console.print(f"[green]✓ Successfully refreshed {success_count} topics[/green]")
        
    except Exception as e:
        logger.exception("Unexpected error during refresh")
        console.print(f"[red]✗ Unexpected error:[/red] {e}")
        raise typer.Exit(code=1)


@app.command()
def status(
    db_path: Optional[Path] = typer.Option(None, "--db-path", help="Path to database file"),
):
    """
    Show status of topics needing summarization refresh.
    
    Displays topics that have unprocessed events and need summarization.
    """
    db_path = db_path or DB_PATH
    
    try:
        # Initialize database
        with Database(db_path) as db:
            db.initialize()
        
        # Get topics needing refresh
        topics_needing_refresh = get_topics_needing_refresh(db_path=db_path)
        
        if not topics_needing_refresh:
            console.print("[green]✓ All topics are up to date[/green]")
            return
        
        # Display topics
        status_table = Table(title="Topics Needing Refresh", show_header=True, header_style="bold yellow")
        status_table.add_column("Topic ID", style="cyan")
        status_table.add_column("Unprocessed Events", style="yellow")
        
        for topic_id in topics_needing_refresh:
            # Get unprocessed event count
            from src.summarizers.update import get_unprocessed_events
            events = get_unprocessed_events(topic_id, limit=None, db_path=db_path)
            event_count = len(events)
            
            status_table.add_row(topic_id, str(event_count))
        
        console.print(status_table)
        console.print(f"[yellow]{len(topics_needing_refresh)} topics need summarization refresh[/yellow]")
        
    except Exception as e:
        logger.exception("Unexpected error during status check")
        console.print(f"[red]✗ Unexpected error:[/red] {e}")
        raise typer.Exit(code=1)

