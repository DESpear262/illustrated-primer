"""
Database CLI commands for AI Tutor Proof of Concept.

Provides CLI commands for database operations and health checks.
"""

import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table

from src.storage.db import Database, initialize_database
from src.config import DB_PATH

app = typer.Typer(help="Database management commands")
console = Console()


@app.command()
def check(
    db_path: Path = typer.Option(None, help="Path to database file"),
):
    """
    Check database health.
    
    Validates database connection, table existence, and basic queries.
    """
    db_path = db_path or DB_PATH
    
    db_path_str = str(db_path) if db_path else None
    console.print(f"[bold]Checking database:[/bold] {db_path_str or DB_PATH}")
    
    try:
        with Database(db_path) as db:
            health = db.health_check()
            
            if health["status"] == "ok":
                console.print("[green]✓ Database is healthy[/green]")
                
                # Display table information
                table = Table(title="Database Status")
                table.add_column("Property", style="cyan")
                table.add_column("Value", style="green")
                
                table.add_row("Status", health["status"])
                table.add_row("Tables", str(len(health.get("tables", []))))
                table.add_row("Event Count", str(health.get("event_count", 0)))
                
                console.print(table)
            else:
                console.print(f"[red]✗ Database error:[/red] {health.get('message', 'Unknown error')}")
                if "missing_tables" in health:
                    console.print(f"[yellow]Missing tables:[/yellow] {', '.join(health['missing_tables'])}")
                raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise typer.Exit(code=1)


@app.command()
def init(
    db_path: Path = typer.Option(None, help="Path to database file"),
):
    """
    Initialize database with schema.
    
    Creates database file and all tables if they don't exist.
    """
    db_path_str = str(db_path) if db_path else None
    console.print(f"[bold]Initializing database:[/bold] {db_path_str or DB_PATH}")
    
    try:
        initialize_database(db_path)
        console.print("[green]✓ Database initialized successfully[/green]")
    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()

