"""
Progress CLI for AI Tutor Proof of Concept.

Commands:
  - summary: generate performance report with delta calculations
"""

from __future__ import annotations

from typing import Optional
from pathlib import Path
from datetime import datetime, timedelta

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.config import DB_PATH
from src.analysis.performance import (
    generate_progress_report,
    report_to_json,
    report_to_markdown,
    create_chart_data,
    ReportFormat,
)

app = typer.Typer(help="Progress tracking commands")
console = Console()


def parse_timestamp(value: str) -> datetime:
    """
    Parse timestamp from string.
    
    Supports ISO format and relative times like "7 days ago", "last week", etc.
    
    Args:
        value: Timestamp string
        
    Returns:
        Parsed datetime
    """
    # Try relative time parsing first
    value_lower = value.lower().strip()
    
    if value_lower == "now":
        return datetime.utcnow()
    elif value_lower == "today":
        return datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    elif value_lower == "yesterday":
        return (datetime.utcnow() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif "days ago" in value_lower:
        try:
            days = int(value_lower.split("days ago")[0].strip())
            return datetime.utcnow() - timedelta(days=days)
        except ValueError:
            pass
    elif "weeks ago" in value_lower:
        try:
            weeks = int(value_lower.split("weeks ago")[0].strip())
            return datetime.utcnow() - timedelta(weeks=weeks)
        except ValueError:
            pass
    elif "months ago" in value_lower:
        try:
            months = int(value_lower.split("months ago")[0].strip())
            return datetime.utcnow() - timedelta(days=months * 30)
        except ValueError:
            pass
    
    # Try ISO format parsing
    try:
        # Try ISO format first
        if "T" in value or " " in value:
            # ISO format with T or space separator
            return datetime.fromisoformat(value.replace(" ", "T"))
        else:
            # Date only format
            return datetime.fromisoformat(value + "T00:00:00")
    except (ValueError, TypeError):
        # Try other common formats
        try:
            # Try YYYY-MM-DD HH:MM:SS
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                # Try YYYY-MM-DD
                return datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                raise typer.BadParameter(f"Invalid timestamp format: {value}")


@app.command()
def summary(
    start: Optional[str] = typer.Option(
        None,
        "--start",
        "-s",
        help="Start timestamp (ISO format or relative like '7 days ago', '30 days ago')",
    ),
    end: Optional[str] = typer.Option(
        None,
        "--end",
        "-e",
        help="End timestamp (defaults to now)",
    ),
    days: Optional[int] = typer.Option(
        None,
        "--days",
        "-d",
        help="Compare N days ago to now (alternative to --start)",
    ),
    topic: Optional[str] = typer.Option(
        None,
        "--topic",
        "-t",
        help="Filter by topic ID",
    ),
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: json, markdown, or table",
    ),
    chart: bool = typer.Option(
        False,
        "--chart",
        "-c",
        help="Display chart of top skills by delta",
    ),
    db_path: Optional[Path] = typer.Option(
        None,
        "--db",
        help="Path to the SQLite database file",
    ),
):
    """
    Generate performance report with delta calculations.
    
    Compares skill mastery between two timestamps and generates a report
    showing improvements, declines, and summary statistics.
    
    Examples:
        # Compare last 30 days to now
        progress summary --days 30
        
        # Compare specific dates
        progress summary --start "2024-01-01" --end "2024-02-01"
        
        # Generate JSON report
        progress summary --days 7 --format json
        
        # Show chart
        progress summary --days 30 --chart
    """
    db_path = db_path or DB_PATH
    
    # Parse timestamps
    if days is not None:
        # Compare N days ago to now
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
    elif start:
        # Explicit start time
        start_time = parse_timestamp(start)
        if end:
            end_time = parse_timestamp(end)
        else:
            end_time = datetime.utcnow()
    else:
        # Default: compare 30 days ago to now
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=30)
    
    # Validate timestamps
    if start_time >= end_time:
        console.print("[red]Error: start time must be before end time[/red]")
        raise typer.Exit(1)
    
    # Validate format
    try:
        report_format = ReportFormat(format.lower())
    except ValueError:
        console.print(f"[red]Error: invalid format '{format}'. Must be json, markdown, or table[/red]")
        raise typer.Exit(1)
    
    try:
        # Generate report
        report = generate_progress_report(
            start_time=start_time,
            end_time=end_time,
            topic_id=topic,
            db_path=db_path,
        )
        
        # Format output
        if report_format == ReportFormat.JSON:
            output = report_to_json(report)
            console.print(output)
        elif report_format == ReportFormat.MARKDOWN:
            output = report_to_markdown(report)
            console.print(output)
        else:  # TABLE
            # Display summary table
            summary_table = Table(title="Performance Summary", show_header=True, header_style="bold magenta")
            summary_table.add_column("Metric", style="cyan")
            summary_table.add_column("Value", justify="right", style="green")
            
            s = report.summary
            summary_table.add_row("Total Skills", str(s["total_skills"]))
            summary_table.add_row("Skills Improved", f"[green]{s['skills_improved']}[/green]")
            summary_table.add_row("Skills Declined", f"[red]{s['skills_declined']}[/red]")
            summary_table.add_row("New Skills", f"[yellow]{s['skills_new']}[/yellow]")
            summary_table.add_row("Unchanged Skills", str(s["skills_unchanged"]))
            summary_table.add_row("Average Delta", f"{s['average_delta']:+.3f}")
            summary_table.add_row("Average Current Mastery", f"{s['average_current_mastery']:.3f}")
            summary_table.add_row("Total Topics", str(s["total_topics"]))
            
            console.print(summary_table)
            console.print()
            
            # Display topic summary table
            if report.topic_deltas:
                topic_table = Table(title="Topic Summary", show_header=True, header_style="bold blue")
                topic_table.add_column("Topic", style="cyan")
                topic_table.add_column("Skills", justify="right")
                topic_table.add_column("Avg Mastery", justify="right", style="green")
                topic_table.add_column("Avg Delta", justify="right")
                topic_table.add_column("Improved", justify="right", style="green")
                topic_table.add_column("Declined", justify="right", style="red")
                topic_table.add_column("New", justify="right", style="yellow")
                
                for topic in sorted(report.topic_deltas, key=lambda t: t.avg_delta, reverse=True):
                    topic_table.add_row(
                        topic.topic_id,
                        str(topic.skill_count),
                        f"{topic.current_avg_mastery:.2f}",
                        f"{topic.avg_delta:+.3f}",
                        str(topic.skills_improved),
                        str(topic.skills_declined),
                        str(topic.skills_new),
                    )
                
                console.print(topic_table)
                console.print()
            
            # Display top skill deltas table
            if report.skill_deltas:
                skills_table = Table(title="Top Skills by Delta", show_header=True, header_style="bold yellow")
                skills_table.add_column("Skill ID", style="cyan")
                skills_table.add_column("Topic", style="blue")
                skills_table.add_column("Current", justify="right", style="green")
                skills_table.add_column("Previous", justify="right")
                skills_table.add_column("Delta", justify="right")
                skills_table.add_column("% Change", justify="right")
                skills_table.add_column("Status", justify="center")
                
                # Show top 20 by absolute delta
                top_skills = sorted(report.skill_deltas, key=lambda d: abs(d.delta), reverse=True)[:20]
                
                for delta in top_skills:
                    topic_str = delta.topic_id or "—"
                    prev_str = f"{delta.previous_mastery:.2f}" if delta.previous_mastery is not None else "N/A"
                    
                    if delta.is_new:
                        status = "[yellow]🆕 New[/yellow]"
                    elif delta.delta > 0.01:
                        status = "[green]📈 Improved[/green]"
                    elif delta.delta < -0.01:
                        status = "[red]📉 Declined[/red]"
                    else:
                        status = "[dim]➖ Unchanged[/dim]"
                    
                    delta_style = "green" if delta.delta > 0 else "red" if delta.delta < 0 else "dim"
                    
                    skills_table.add_row(
                        delta.skill_id,
                        topic_str,
                        f"{delta.current_mastery:.2f}",
                        prev_str,
                        f"[{delta_style}]{delta.delta:+.3f}[/{delta_style}]",
                        f"{delta.percentage_change:+.1f}%",
                        status,
                    )
                
                console.print(skills_table)
        
        # Display chart if requested
        if chart and report.skill_deltas:
            chart_data = create_chart_data(report, top_n=10)
            
            if chart_data:
                # Create simple bar chart using text
                chart_lines = []
                chart_lines.append("\n[bold]Top Skills by Delta (Absolute Value)[/bold]\n")
                
                max_abs_delta = max(abs(delta) for _, delta in chart_data) if chart_data else 1.0
                bar_width = 40
                
                for skill_id, delta in chart_data:
                    bar_length = int((abs(delta) / max_abs_delta) * bar_width)
                    bar = "█" * bar_length
                    style = "green" if delta > 0 else "red"
                    delta_str = f"{delta:+.3f}"
                    
                    chart_lines.append(
                        f"[{style}]{skill_id[:25]:<25}[/{style}] "
                        f"[{style}]{bar}[/{style}] {delta_str}"
                    )
                
                chart_text = "\n".join(chart_lines)
                console.print(Panel(chart_text, title="Delta Chart", border_style="blue"))
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()

