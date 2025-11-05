"""
AI CLI commands for AI Tutor Proof of Concept.

Provides commands to test AI functionality and view routing configuration.
"""

from typing import Optional
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.services.ai.router import get_router, AITask
from src.services.ai.client import get_client, AIClient
from src.services.ai.prompts import SummaryOutput, ClassificationOutput
from src.storage.db import Database
from src.config import DB_PATH

app = typer.Typer(help="AI service commands")
console = Console()


@app.command()
def routes():
    """Show model routing configuration."""
    router = get_router()
    
    table = Table(title="Model Routing Configuration")
    table.add_column("Task", style="cyan")
    table.add_column("Model", style="green")
    table.add_column("Token Budget", style="yellow")
    table.add_column("Streaming", style="magenta")
    table.add_column("JSON Mode", style="blue")
    
    for task in AITask:
        route = router.get_route(task)
        table.add_row(
            task.value,
            route.model_name,
            str(route.token_budget),
            "✓" if route.supports_streaming else "✗",
            "✓" if route.supports_json_mode else "✗",
        )
    
    console.print(table)


@app.command()
def test(
    task: str = typer.Argument(..., help="Task type: summarize, classify, chat"),
    text: Optional[str] = typer.Option(None, "--text", "-t", help="Input text"),
    event_id: Optional[str] = typer.Option(None, "--event-id", "-e", help="Event ID to summarize"),
    db_path: Path = typer.Option(None, "--db", help="Path to database file"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Override model"),
):
    """
    Test AI functionality.
    
    Examples:
    - ai test summarize --event-id abc123
    - ai test classify --text "Learning about derivatives"
    - ai test chat --text "What is a derivative?"
    """
    client = get_client()
    db_path = db_path or DB_PATH
    
    try:
        if task == "summarize":
            if event_id:
                # Get event from database
                with Database(db_path) as db:
                    event = db.get_event_by_id(event_id)
                    if not event:
                        console.print(f"[red]Event not found: {event_id}[/red]")
                        raise typer.Exit(code=1)
                    
                    content = event.content
                    console.print(f"[cyan]Summarizing event: {event_id}[/cyan]")
            elif text:
                content = text
            else:
                console.print("[red]Either --event-id or --text required for summarize[/red]")
                raise typer.Exit(code=1)
            
            result = client.summarize_event(content, override_model=model)
            
            panel = Panel(
                f"[bold]Summary:[/bold] {result.summary}\n\n"
                f"[bold]Topics:[/bold] {', '.join(result.topics)}\n"
                f"[bold]Skills:[/bold] {', '.join(result.skills)}\n"
                f"[bold]Key Points:[/bold] {len(result.key_points)} points\n"
                f"[bold]Open Questions:[/bold] {len(result.open_questions)} questions",
                title="Summarization Result",
            )
            console.print(panel)
        
        elif task == "classify":
            if not text:
                console.print("[red]--text required for classify[/red]")
                raise typer.Exit(code=1)
            
            result = client.classify_topics(text, override_model=model)
            
            panel = Panel(
                f"[bold]Topics:[/bold] {', '.join(result.topics)}\n"
                f"[bold]Skills:[/bold] {', '.join(result.skills)}\n"
                f"[bold]Confidence:[/bold] {result.confidence:.2f}",
                title="Classification Result",
            )
            console.print(panel)
        
        elif task == "chat":
            if not text:
                console.print("[red]--text required for chat[/red]")
                raise typer.Exit(code=1)
            
            response = client.chat_reply(text, override_model=model)
            
            panel = Panel(
                response,
                title="Chat Response",
            )
            console.print(panel)
        
        else:
            console.print(f"[red]Unknown task: {task}[/red]")
            console.print("[yellow]Valid tasks: summarize, classify, chat[/yellow]")
            raise typer.Exit(code=1)
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()

