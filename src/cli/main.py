"""
Main CLI entry point for AI Tutor Proof of Concept.

Provides top-level CLI commands for the application.
"""

import typer
from rich.console import Console

from src.cli import db as db_cli
from src.cli import index as index_cli

app = typer.Typer(help="AI Tutor Proof of Concept CLI")
console = Console()

# Add subcommands
app.add_typer(db_cli.app, name="db", help="Database management commands")
app.add_typer(index_cli.app, name="index", help="Index management commands")


@app.command()
def version():
    """Show version information."""
    console.print("[bold]AI Tutor Proof of Concept[/bold]")
    console.print("Version: 0.1.0")


if __name__ == "__main__":
    app()

