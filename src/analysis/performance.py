"""
Performance tracking and progress analysis for AI Tutor Proof of Concept.

Provides delta calculation, progress reporting, and visualization for
skill mastery tracking over time.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path
from enum import Enum

from src.models.base import SkillState, Event
from src.storage.db import Database
from src.storage.queries import get_events_by_skill, get_events_by_time_range
from src.config import DB_PATH


class ReportFormat(str, Enum):
    """Report format options."""
    JSON = "json"
    MARKDOWN = "markdown"
    TABLE = "table"


@dataclass
class SkillDelta:
    """
    Represents a mastery delta for a single skill between two time points.
    
    Contains current and previous mastery values, along with computed
    delta and percentage change.
    """
    skill_id: str
    topic_id: Optional[str]
    current_mastery: float
    previous_mastery: Optional[float]
    delta: float
    percentage_change: float
    is_new: bool
    current_evidence_count: int
    previous_evidence_count: Optional[int]


@dataclass
class TopicDelta:
    """
    Represents aggregated mastery delta for a topic.
    
    Aggregates all skills within a topic to show overall progress.
    """
    topic_id: str
    skill_count: int
    current_avg_mastery: float
    previous_avg_mastery: Optional[float]
    avg_delta: float
    skills_improved: int
    skills_declined: int
    skills_new: int


@dataclass
class ProgressReport:
    """
    Comprehensive progress report containing skill and topic deltas.
    
    Includes metadata, summary statistics, and detailed breakdowns.
    """
    start_time: datetime
    end_time: datetime
    generated_at: datetime
    skill_deltas: List[SkillDelta]
    topic_deltas: List[TopicDelta]
    summary: Dict[str, Any]


def reconstruct_skill_state_at_time(
    skill_id: str,
    target_time: datetime,
    db_path: Optional[Path] = None,
) -> Optional[SkillState]:
    """
    Reconstruct skill state at a specific point in time.
    
    Uses events up to the target time to reconstruct mastery state.
    For skills without events before the target time, uses current state.
    
    Args:
        skill_id: Skill identifier
        target_time: Target timestamp to reconstruct state at
        db_path: Path to database file (defaults to config.DB_PATH)
        
    Returns:
        Reconstructed SkillState at target time, or None if skill doesn't exist
    """
    db_path = db_path or DB_PATH
    
    with Database(db_path) as db:
        # Get current skill state
        current_skill = db.get_skill_state_by_id(skill_id)
        if not current_skill:
            return None
        
        # If skill was created after target time, return None (didn't exist)
        if current_skill.created_at > target_time:
            return None
    
    # Get events for this skill up to target time (outside context manager)
    events = get_events_by_skill(skill_id, db_path=db_path)
    events_before = [e for e in events if e.created_at <= target_time]
    
    # Determine initial mastery
    # Default to 0.5 (standard initial mastery)
    # For skills with no events before target_time, we can use current mastery
    # if skill was created very recently (within 1 hour of target_time)
    # Otherwise, we reconstruct from events
    initial_mastery = 0.5  # Default initial mastery
    
    # If skill was created very recently (within 1 hour) and has no events,
    # we can use current mastery as initial (skill hasn't changed yet)
    # But if there are events, we need to reconstruct
    
    # If no events before target time, use initial mastery
    if not events_before:
        return SkillState(
            skill_id=skill_id,
            p_mastery=initial_mastery,
            evidence_count=0,
            last_evidence_at=None,
            topic_id=current_skill.topic_id,
            created_at=current_skill.created_at,
            updated_at=current_skill.created_at,
            metadata=current_skill.metadata,
        )
    
    # Reconstruct mastery from events
    # Count evidence events (assessments, reviews, etc.)
    evidence_events = [e for e in events_before if e.event_type in ('assessment', 'quiz')]
    
    # Count positive vs negative evidence from metadata
    positive_evidence = 0
    negative_evidence = 0
    
    for event in evidence_events:
        outcome = event.metadata.get('review_outcome') or event.metadata.get('outcome')
        if outcome == 'mastered' or outcome is True:
            positive_evidence += 1
        elif outcome == 'not_mastered' or outcome is False:
            negative_evidence += 1
        # Default to positive if unclear (learning events are positive)
        else:
            positive_evidence += 1
    
    # Calculate mastery from evidence (simple model: +0.1 for positive, -0.05 for negative)
    # Start from initial mastery
    reconstructed_mastery = initial_mastery
    for _ in range(positive_evidence):
        reconstructed_mastery = min(1.0, reconstructed_mastery + 0.1)
    for _ in range(negative_evidence):
        reconstructed_mastery = max(0.0, reconstructed_mastery - 0.05)
    
    # Get last evidence timestamp
    last_evidence = max((e.created_at for e in evidence_events), default=None)
    
    return SkillState(
        skill_id=skill_id,
        p_mastery=reconstructed_mastery,
        evidence_count=len(evidence_events),
        last_evidence_at=last_evidence,
        topic_id=current_skill.topic_id,
        created_at=current_skill.created_at,
        updated_at=last_evidence or current_skill.created_at,
        metadata=current_skill.metadata,
    )


def calculate_skill_deltas(
    start_time: datetime,
    end_time: datetime,
    topic_id: Optional[str] = None,
    skill_ids: Optional[List[str]] = None,
    db_path: Optional[Path] = None,
) -> List[SkillDelta]:
    """
    Calculate mastery deltas for skills between two time points.
    
    Reconstructs skill states at start_time and end_time, then computes
    deltas for all skills or filtered subset.
    
    Args:
        start_time: Start timestamp for comparison
        end_time: End timestamp for comparison
        topic_id: Optional topic filter (only skills in this topic)
        skill_ids: Optional list of specific skill IDs to include
        db_path: Path to database file (defaults to config.DB_PATH)
        
    Returns:
        List of SkillDelta objects
    """
    db_path = db_path or DB_PATH
    
    # Get current skills (at end_time)
    if topic_id:
        from src.storage.queries import get_skills_by_topic
        current_skills = get_skills_by_topic(topic_id, db_path=db_path)
    elif skill_ids:
        with Database(db_path) as db:
            current_skills = [db.get_skill_state_by_id(sid) for sid in skill_ids]
            current_skills = [s for s in current_skills if s is not None]
    else:
        # Get all skills
        with Database(db_path) as db:
            if not db.conn:
                raise ValueError("Database connection not established")
            cursor = db.conn.cursor()
            cursor.execute("SELECT * FROM skills")
            rows = cursor.fetchall()
            current_skills = [db._row_to_skill_state(row) for row in rows]
    
    deltas = []
    
    for current_skill in current_skills:
        # Reconstruct state at start_time
        previous_skill = reconstruct_skill_state_at_time(
            current_skill.skill_id,
            start_time,
            db_path=db_path,
        )
        
        # If skill didn't exist at start_time, mark as new
        if previous_skill is None:
            delta = SkillDelta(
                skill_id=current_skill.skill_id,
                topic_id=current_skill.topic_id,
                current_mastery=current_skill.p_mastery,
                previous_mastery=None,
                delta=current_skill.p_mastery,  # Gain from 0 to current
                percentage_change=100.0 if current_skill.p_mastery > 0 else 0.0,
                is_new=True,
                current_evidence_count=current_skill.evidence_count,
                previous_evidence_count=None,
            )
        else:
            delta_value = current_skill.p_mastery - previous_skill.p_mastery
            # Calculate percentage change (avoid division by zero)
            if previous_skill.p_mastery > 0:
                percentage_change = (delta_value / previous_skill.p_mastery) * 100.0
            else:
                percentage_change = 100.0 if delta_value > 0 else 0.0
            
            delta = SkillDelta(
                skill_id=current_skill.skill_id,
                topic_id=current_skill.topic_id,
                current_mastery=current_skill.p_mastery,
                previous_mastery=previous_skill.p_mastery,
                delta=delta_value,
                percentage_change=percentage_change,
                is_new=False,
                current_evidence_count=current_skill.evidence_count,
                previous_evidence_count=previous_skill.evidence_count,
            )
        
        deltas.append(delta)
    
    return deltas


def aggregate_topic_deltas(
    skill_deltas: List[SkillDelta],
) -> List[TopicDelta]:
    """
    Aggregate skill deltas by topic.
    
    Groups skills by topic and computes aggregate statistics.
    
    Args:
        skill_deltas: List of skill deltas to aggregate
        
    Returns:
        List of TopicDelta objects
    """
    # Group by topic
    topic_groups: Dict[str, List[SkillDelta]] = {}
    for delta in skill_deltas:
        topic = delta.topic_id or "uncategorized"
        if topic not in topic_groups:
            topic_groups[topic] = []
        topic_groups[topic].append(delta)
    
    topic_deltas = []
    
    for topic_id, deltas in topic_groups.items():
        skill_count = len(deltas)
        current_avg = sum(d.current_mastery for d in deltas) / skill_count if skill_count > 0 else 0.0
        
        # Calculate previous average (excluding new skills)
        previous_deltas = [d for d in deltas if not d.is_new and d.previous_mastery is not None]
        previous_avg = (
            sum(d.previous_mastery for d in previous_deltas) / len(previous_deltas)
            if previous_deltas else None
        )
        
        avg_delta = current_avg - (previous_avg or 0.0)
        
        skills_improved = sum(1 for d in deltas if d.delta > 0)
        skills_declined = sum(1 for d in deltas if d.delta < 0)
        skills_new = sum(1 for d in deltas if d.is_new)
        
        topic_deltas.append(TopicDelta(
            topic_id=topic_id,
            skill_count=skill_count,
            current_avg_mastery=current_avg,
            previous_avg_mastery=previous_avg,
            avg_delta=avg_delta,
            skills_improved=skills_improved,
            skills_declined=skills_declined,
            skills_new=skills_new,
        ))
    
    return topic_deltas


def generate_progress_report(
    start_time: datetime,
    end_time: datetime,
    topic_id: Optional[str] = None,
    skill_ids: Optional[List[str]] = None,
    db_path: Optional[Path] = None,
) -> ProgressReport:
    """
    Generate comprehensive progress report between two time points.
    
    Calculates skill deltas, aggregates by topic, and generates summary statistics.
    
    Args:
        start_time: Start timestamp for comparison
        end_time: End timestamp for comparison
        topic_id: Optional topic filter
        skill_ids: Optional list of specific skill IDs
        db_path: Path to database file (defaults to config.DB_PATH)
        
    Returns:
        ProgressReport with all calculated data
    """
    db_path = db_path or DB_PATH
    
    # Calculate skill deltas
    skill_deltas = calculate_skill_deltas(
        start_time=start_time,
        end_time=end_time,
        topic_id=topic_id,
        skill_ids=skill_ids,
        db_path=db_path,
    )
    
    # Aggregate by topic
    topic_deltas = aggregate_topic_deltas(skill_deltas)
    
    # Generate summary statistics
    total_skills = len(skill_deltas)
    skills_improved = sum(1 for d in skill_deltas if d.delta > 0)
    skills_declined = sum(1 for d in skill_deltas if d.delta < 0)
    skills_new = sum(1 for d in skill_deltas if d.is_new)
    skills_unchanged = sum(1 for d in skill_deltas if d.delta == 0 and not d.is_new)
    
    avg_delta = sum(d.delta for d in skill_deltas) / total_skills if total_skills > 0 else 0.0
    avg_current_mastery = sum(d.current_mastery for d in skill_deltas) / total_skills if total_skills > 0 else 0.0
    
    summary = {
        "total_skills": total_skills,
        "skills_improved": skills_improved,
        "skills_declined": skills_declined,
        "skills_new": skills_new,
        "skills_unchanged": skills_unchanged,
        "average_delta": avg_delta,
        "average_current_mastery": avg_current_mastery,
        "total_topics": len(topic_deltas),
    }
    
    return ProgressReport(
        start_time=start_time,
        end_time=end_time,
        generated_at=datetime.utcnow(),
        skill_deltas=skill_deltas,
        topic_deltas=topic_deltas,
        summary=summary,
    )


def report_to_json(report: ProgressReport) -> str:
    """
    Convert progress report to JSON format.
    
    Args:
        report: ProgressReport to convert
        
    Returns:
        JSON string representation
    """
    def serialize_datetime(dt: datetime) -> str:
        return dt.isoformat()
    
    # Convert dataclasses to dicts
    data = {
        "start_time": serialize_datetime(report.start_time),
        "end_time": serialize_datetime(report.end_time),
        "generated_at": serialize_datetime(report.generated_at),
        "summary": report.summary,
        "skill_deltas": [asdict(d) for d in report.skill_deltas],
        "topic_deltas": [asdict(d) for d in report.topic_deltas],
    }
    
    # Convert datetime fields in nested dicts
    for delta in data["skill_deltas"]:
        # No datetime fields in SkillDelta, just float/str
        pass
    
    for topic_delta in data["topic_deltas"]:
        # No datetime fields in TopicDelta
        pass
    
    return json.dumps(data, indent=2)


def report_to_markdown(report: ProgressReport) -> str:
    """
    Convert progress report to Markdown format.
    
    Args:
        report: ProgressReport to convert
        
    Returns:
        Markdown string representation
    """
    lines = []
    
    # Header
    lines.append("# Progress Report")
    lines.append("")
    lines.append(f"**Period:** {report.start_time.strftime('%Y-%m-%d %H:%M:%S')} to {report.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    # Summary
    lines.append("## Summary")
    lines.append("")
    s = report.summary
    lines.append(f"- **Total Skills:** {s['total_skills']}")
    lines.append(f"- **Skills Improved:** {s['skills_improved']}")
    lines.append(f"- **Skills Declined:** {s['skills_declined']}")
    lines.append(f"- **New Skills:** {s['skills_new']}")
    lines.append(f"- **Unchanged Skills:** {s['skills_unchanged']}")
    lines.append(f"- **Average Delta:** {s['average_delta']:.3f}")
    lines.append(f"- **Average Current Mastery:** {s['average_current_mastery']:.3f}")
    lines.append(f"- **Total Topics:** {s['total_topics']}")
    lines.append("")
    
    # Topic Deltas
    if report.topic_deltas:
        lines.append("## Topic Summary")
        lines.append("")
        lines.append("| Topic | Skills | Avg Mastery | Avg Delta | Improved | Declined | New |")
        lines.append("|-------|--------|-------------|-----------|----------|----------|-----|")
        
        for topic in sorted(report.topic_deltas, key=lambda t: t.avg_delta, reverse=True):
            prev_avg = f"{topic.previous_avg_mastery:.2f}" if topic.previous_avg_mastery is not None else "N/A"
            lines.append(
                f"| {topic.topic_id} | {topic.skill_count} | {topic.current_avg_mastery:.2f} "
                f"| {topic.avg_delta:+.3f} | {topic.skills_improved} | {topic.skills_declined} | {topic.skills_new} |"
            )
        lines.append("")
    
    # Skill Deltas
    if report.skill_deltas:
        lines.append("## Skill Details")
        lines.append("")
        lines.append("| Skill ID | Topic | Current | Previous | Delta | % Change | Status |")
        lines.append("|----------|-------|---------|----------|-------|----------|--------|")
        
        for delta in sorted(report.skill_deltas, key=lambda d: d.delta, reverse=True):
            topic_str = delta.topic_id or "—"
            prev_str = f"{delta.previous_mastery:.2f}" if delta.previous_mastery is not None else "N/A"
            status = "🆕 New" if delta.is_new else ("📈 Improved" if delta.delta > 0 else ("📉 Declined" if delta.delta < 0 else "➖ Unchanged"))
            
            lines.append(
                f"| {delta.skill_id} | {topic_str} | {delta.current_mastery:.2f} | {prev_str} | "
                f"{delta.delta:+.3f} | {delta.percentage_change:+.1f}% | {status} |"
            )
        lines.append("")
    
    return "\n".join(lines)


def create_chart_data(report: ProgressReport, top_n: int = 10) -> List[tuple]:
    """
    Create chart data for visualization.
    
    Returns top N skills by absolute delta value for charting.
    
    Args:
        report: ProgressReport to extract chart data from
        top_n: Number of top skills to include
        
    Returns:
        List of tuples (skill_id, delta) sorted by absolute delta
    """
    # Sort by absolute delta value
    sorted_deltas = sorted(report.skill_deltas, key=lambda d: abs(d.delta), reverse=True)
    top_deltas = sorted_deltas[:top_n]
    
    # Return as (label, value) tuples for rich charts
    return [(d.skill_id, d.delta) for d in top_deltas]

