"""
Review CLI for AI Tutor Proof of Concept.

Commands:
  - next: get next skills to review, prioritized by spaced repetition
"""

from __future__ import annotations

from typing import Optional
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from src.config import DB_PATH, REVIEW_DEFAULT_LIMIT
from src.scheduler.review import get_next_reviews

app = typer.Typer(help="Review scheduler commands")
console = Console()


@app.command()
def next(
    limit: int = typer.Option(
        REVIEW_DEFAULT_LIMIT,
        "--limit",
        "-n",
        help="Maximum number of skills to review",
    ),
    topic: Optional[str] = typer.Option(
        None,
        "--topic",
        "-t",
        help="Filter by topic ID",
    ),
    min_mastery: Optional[float] = typer.Option(
        None,
        "--min-mastery",
        help="Minimum mastery to include (0.0-1.0)",
    ),
    max_mastery: Optional[float] = typer.Option(
        None,
        "--max-mastery",
        help="Maximum mastery to include (0.0-1.0)",
    ),
    db_path: Optional[Path] = typer.Option(
        None,
        "--db",
        help="Path to the SQLite database file",
    ),
):
    """
    Get next skills to review, prioritized by spaced repetition algorithm.
    
    Displays a table of skills sorted by review priority, showing:
    - Skill ID
    - Topic (if available)
    - Current mastery
    - Decayed mastery (after time decay)
    - Days since last review
    - Priority score
    """
    db_path = db_path or DB_PATH
    
    # Validate mastery range
    if min_mastery is not None and (min_mastery < 0.0 or min_mastery > 1.0):
        console.print("[red]Error: min_mastery must be between 0.0 and 1.0[/red]")
        raise typer.Exit(1)
    
    if max_mastery is not None and (max_mastery < 0.0 or max_mastery > 1.0):
        console.print("[red]Error: max_mastery must be between 0.0 and 1.0[/red]")
        raise typer.Exit(1)
    
    if min_mastery is not None and max_mastery is not None and min_mastery > max_mastery:
        console.print("[red]Error: min_mastery must be <= max_mastery[/red]")
        raise typer.Exit(1)
    
    try:
        # Get review items
        review_items = get_next_reviews(
            limit=limit,
            min_mastery=min_mastery,
            max_mastery=max_mastery,
            topic_id=topic,
            db_path=db_path,
        )
        
        if not review_items:
            console.print("[yellow]No skills found for review.[/yellow]")
            return
        
        # Create table
        table = Table(title="Next Skills to Review", show_header=True, header_style="bold magenta")
        table.add_column("Skill ID", style="cyan", no_wrap=True)
        table.add_column("Topic", style="blue")
        table.add_column("Current Mastery", justify="right", style="green")
        table.add_column("Decayed Mastery", justify="right", style="yellow")
        table.add_column("Days Since Review", justify="right")
        table.add_column("Priority", justify="right", style="bold red")
        
        # Add rows
        for item in review_items:
            skill = item.skill
            topic_str = skill.topic_id or "—"
            
            table.add_row(
                skill.skill_id,
                topic_str,
                f"{skill.p_mastery:.2f}",
                f"{item.decayed_mastery:.2f}",
                f"{item.days_since_review:.1f}",
                f"{item.priority_score:.2f}",
            )
        
        console.print(table)
        console.print(f"\n[dim]Showing {len(review_items)} of {limit} recommended reviews[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()

