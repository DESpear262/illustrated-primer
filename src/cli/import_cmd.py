"""
Import CLI commands for AI Tutor Proof of Concept.

Provides commands to import transcripts from various formats.
"""

import logging
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.config import DB_PATH
from src.ingestion.transcripts import import_transcript

app = typer.Typer(help="Import commands")
console = Console()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.command()
def transcript(
    file_path: Path = typer.Argument(..., help="Path to transcript file (.txt, .md, or .json)"),
    topics: Optional[str] = typer.Option(None, "--topics", help="Comma-separated list of topics to add manually"),
    skills: Optional[str] = typer.Option(None, "--skills", help="Comma-separated list of skills to add manually"),
    db_path: Optional[Path] = typer.Option(None, "--db-path", help="Path to database file"),
    use_stub_embeddings: bool = typer.Option(False, "--use-stub-embeddings", help="Use stub embeddings instead of OpenAI"),
):
    """
    Import a transcript file and create an event with summarization and embedding.
    
    Supports .txt, .md, and .json formats. Automatically classifies topics and skills
    using AI, with optional manual tagging.
    """
    db_path = db_path or DB_PATH
    
    # Parse manual topics and skills
    manual_topics = None
    if topics:
        manual_topics = [t.strip() for t in topics.split(",") if t.strip()]
    
    manual_skills = None
    if skills:
        manual_skills = [s.strip() for s in skills.split(",") if s.strip()]
    
    # Import transcript
    try:
        console.print(f"[cyan]Importing transcript:[/cyan] {file_path}")
        
        event = import_transcript(
            file_path=file_path,
            manual_topics=manual_topics,
            manual_skills=manual_skills,
            db_path=db_path,
            use_real_embeddings=not use_stub_embeddings,
        )
        
        # Display results
        table = Table(title="Import Results", show_header=True, header_style="bold magenta")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Event ID", event.event_id)
        table.add_row("Event Type", event.event_type)
        table.add_row("Actor", event.actor)
        table.add_row("Topics", ", ".join(event.topics) if event.topics else "(none)")
        table.add_row("Skills", ", ".join(event.skills) if event.skills else "(none)")
        if event.recorded_at:
            table.add_row("Recorded At", event.recorded_at.isoformat())
        table.add_row("Created At", event.created_at.isoformat())
        
        console.print(table)
        
        # Show metadata
        if event.metadata:
            metadata_table = Table(title="Import Metadata", show_header=True, header_style="bold yellow")
            metadata_table.add_column("Key", style="cyan")
            metadata_table.add_column("Value", style="green")
            
            for key, value in event.metadata.items():
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                metadata_table.add_row(key, str(value))
            
            console.print(metadata_table)
        
        console.print(f"[green]✓ Successfully imported transcript[/green]")
        
    except ValueError as e:
        console.print(f"[red]✗ Import failed:[/red] {e}")
        raise typer.Exit(code=1)
    except IOError as e:
        console.print(f"[red]✗ File error:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.exception("Unexpected error during import")
        console.print(f"[red]✗ Unexpected error:[/red] {e}")
        raise typer.Exit(code=1)


@app.command()
def batch(
    directory: Path = typer.Argument(..., help="Directory containing transcript files"),
    pattern: str = typer.Option("*.txt,*.md,*.json", "--pattern", help="File pattern to match (comma-separated)"),
    db_path: Optional[Path] = typer.Option(None, "--db-path", help="Path to database file"),
    use_stub_embeddings: bool = typer.Option(False, "--use-stub-embeddings", help="Use stub embeddings instead of OpenAI"),
):
    """
    Import multiple transcript files from a directory.
    
    Processes all matching files in the directory and logs errors for files
    that fail to import.
    """
    db_path = db_path or DB_PATH
    
    if not directory.exists() or not directory.is_dir():
        console.print(f"[red]✗ Directory not found:[/red] {directory}")
        raise typer.Exit(code=1)
    
    # Parse patterns
    patterns = [p.strip() for p in pattern.split(",")]
    
    # Find matching files
    files = []
    for pattern_item in patterns:
        files.extend(directory.glob(pattern_item))
    
    if not files:
        console.print(f"[yellow]No files found matching patterns: {pattern}[/yellow]")
        return
    
    console.print(f"[cyan]Found {len(files)} files to import[/cyan]")
    
    # Import each file
    success_count = 0
    error_count = 0
    
    for file_path in sorted(files):
        try:
            console.print(f"\n[cyan]Importing:[/cyan] {file_path.name}")
            event = import_transcript(
                file_path=file_path,
                db_path=db_path,
                use_real_embeddings=not use_stub_embeddings,
            )
            console.print(f"  [green]✓[/green] Event ID: {event.event_id}")
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to import {file_path}: {e}")
            console.print(f"  [red]✗[/red] {e}")
            error_count += 1
    
    # Summary
    console.print(f"\n[bold]Import Summary[/bold]")
    console.print(f"  [green]Success:[/green] {success_count}")
    console.print(f"  [red]Errors:[/red] {error_count}")
    console.print(f"  [cyan]Total:[/cyan] {len(files)}")

