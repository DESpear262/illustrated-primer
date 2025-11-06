"""
Main CLI entry point for AI Tutor Proof of Concept.

Provides top-level CLI commands for the application.
"""

import typer
from rich.console import Console

from src.cli import db as db_cli
from src.cli import index as index_cli
from src.cli import ai as ai_cli
from src.cli import chat as chat_cli
from src.cli import review as review_cli
from src.cli import import_cmd as import_cli_module
from src.cli import refresh as refresh_cli
from src.cli import progress as progress_cli

app = typer.Typer(help="AI Tutor Proof of Concept CLI")
console = Console()

# Add subcommands
app.add_typer(db_cli.app, name="db", help="Database management commands")
app.add_typer(index_cli.app, name="index", help="Index management commands")
app.add_typer(ai_cli.app, name="ai", help="AI service commands")
app.add_typer(chat_cli.app, name="chat", help="Tutor chat interface commands")
app.add_typer(review_cli.app, name="review", help="Review scheduler commands")
app.add_typer(import_cli_module.app, name="import", help="Import commands")
app.add_typer(refresh_cli.app, name="refresh", help="Refresh commands")
app.add_typer(progress_cli.app, name="progress", help="Progress tracking commands")


@app.command()
def version():
    """Show version information."""
    console.print("[bold]AI Tutor Proof of Concept[/bold]")
    console.print("Version: 0.1.0")


if __name__ == "__main__":
    app()

