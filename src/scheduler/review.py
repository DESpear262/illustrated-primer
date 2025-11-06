"""
Review scheduler for spaced repetition and mastery tracking.

Implements decay-based mastery model and review priority computation
for generating spaced repetition review lists.
"""

from datetime import datetime
from typing import List, Optional
from pathlib import Path
import math
import uuid

from src.models.base import Event, SkillState
from src.storage.db import Database
from src.storage.queries import (
    get_skills_by_topic,
    get_skills_by_mastery_range,
    update_skill_state_with_evidence,
)
from src.config import (
    DB_PATH,
    REVIEW_DECAY_TAU_DAYS,
    REVIEW_GRACE_PERIOD_DAYS,
)


class ReviewItem:
    """
    Represents a skill recommended for review.
    
    Contains skill information and computed priority score
    for spaced repetition scheduling.
    """
    
    def __init__(
        self,
        skill: SkillState,
        priority_score: float,
        days_since_review: float,
        decayed_mastery: float,
    ):
        """
        Initialize review item.
        
        Args:
            skill: SkillState to review
            priority_score: Computed priority score (higher = more urgent)
            days_since_review: Days since last evidence
            decayed_mastery: Mastery after applying decay
        """
        self.skill = skill
        self.priority_score = priority_score
        self.days_since_review = days_since_review
        self.decayed_mastery = decayed_mastery


def compute_decayed_mastery(
    current_mastery: float,
    days_since_evidence: float,
    tau_days: float = REVIEW_DECAY_TAU_DAYS,
    grace_period_days: float = REVIEW_GRACE_PERIOD_DAYS,
) -> float:
    """
    Compute mastery after applying exponential decay.
    
    Mastery decays exponentially over time, but with a grace period
    where no decay occurs immediately after review.
    
    Formula: decayed = p_mastery * e^(-max(0, days - grace_period) / tau)
    
    Args:
        current_mastery: Current mastery probability (0.0-1.0)
        days_since_evidence: Days since last evidence was recorded
        tau_days: Time constant for exponential decay (default: 30 days)
        grace_period_days: Days with no decay after review (default: 7 days)
        
    Returns:
        Decayed mastery probability (0.0-1.0)
    """
    if days_since_evidence <= grace_period_days:
        # Grace period: no decay
        return current_mastery
    
    # Exponential decay: decayed = p * e^(-t/tau)
    # where t = days_since_evidence - grace_period
    effective_days = days_since_evidence - grace_period_days
    decay_factor = math.exp(-effective_days / tau_days)
    
    return current_mastery * decay_factor


def compute_review_priority(
    p_mastery: float,
    days_since_review: float,
) -> float:
    """
    Compute review priority score.
    
    Priority is higher for:
    - Lower mastery (skills that need reinforcement)
    - More time since last review (skills that are fading)
    
    Formula: priority = (1 - p_mastery) * (1 + days_since_review / 30)
    
    Args:
        p_mastery: Current mastery probability (0.0-1.0)
        days_since_review: Days since last evidence was recorded
        
    Returns:
        Priority score (higher = more urgent to review)
    """
    # Base priority from inverse mastery (lower mastery = higher priority)
    mastery_component = 1.0 - p_mastery
    
    # Recency component: increases with days since review
    # Normalize by 30 days to get reasonable scaling
    recency_component = 1.0 + (days_since_review / 30.0)
    
    # Combined priority
    priority = mastery_component * recency_component
    
    return priority


def get_next_reviews(
    limit: int = 10,
    min_mastery: Optional[float] = None,
    max_mastery: Optional[float] = None,
    topic_id: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> List[ReviewItem]:
    """
    Get next skills to review, prioritized by spaced repetition algorithm.
    
    Retrieves skills from database, computes decayed mastery and priority,
    and returns top N skills sorted by priority.
    
    Args:
        limit: Maximum number of review items to return
        min_mastery: Minimum mastery to include (None for all)
        max_mastery: Maximum mastery to include (None for all)
        topic_id: Filter by topic (None for all topics)
        db_path: Path to database file (defaults to config.DB_PATH)
        
    Returns:
        List of ReviewItem objects sorted by priority (highest first)
    """
    now = datetime.utcnow()
    
    # Get skills from database
    if topic_id:
        skills = get_skills_by_topic(topic_id, db_path=db_path)
    elif min_mastery is not None or max_mastery is not None:
        min_m = min_mastery or 0.0
        max_m = max_mastery or 1.0
        skills = get_skills_by_mastery_range(min_m, max_m, db_path=db_path)
    else:
        # Get all skills
        with Database(db_path) as db:
            if not db.conn:
                raise ValueError("Database connection not established")
            
            cursor = db.conn.cursor()
            cursor.execute("SELECT * FROM skills ORDER BY skill_id ASC")
            rows = cursor.fetchall()
            skills = [db._row_to_skill_state(row) for row in rows]
    
    # Compute priority for each skill
    review_items = []
    
    for skill in skills:
        # Calculate days since last evidence
        if skill.last_evidence_at:
            days_since = (now - skill.last_evidence_at).total_seconds() / 86400.0
        else:
            # No evidence yet: treat as very old
            days_since = 365.0
        
        # Compute decayed mastery
        decayed = compute_decayed_mastery(
            skill.p_mastery,
            days_since,
        )
        
        # Compute priority
        priority = compute_review_priority(
            decayed,
            days_since,
        )
        
        # Create review item
        review_items.append(
            ReviewItem(
                skill=skill,
                priority_score=priority,
                days_since_review=days_since,
                decayed_mastery=decayed,
            )
        )
    
    # Sort by priority (highest first)
    review_items.sort(key=lambda x: x.priority_score, reverse=True)
    
    # Return top N
    return review_items[:limit]


def record_review_outcome(
    skill_id: str,
    mastered: bool,
    review_content: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> Event:
    """
    Record a review outcome as a new Event and update skill state.
    
    Creates an assessment Event with the review outcome, then updates
    the skill state with the new evidence.
    
    Args:
        skill_id: Skill identifier that was reviewed
        mastered: True if skill was mastered, False otherwise
        review_content: Optional text describing the review
        db_path: Path to database file (defaults to config.DB_PATH)
        
    Returns:
        Created Event object
    """
    # Get skill to get topic association
    with Database(db_path) as db:
        skill = db.get_skill_state_by_id(skill_id)
        
        if not skill:
            raise ValueError(f"Skill not found: {skill_id}")
        
        # Create event content
        if review_content:
            content = review_content
        else:
            outcome = "mastered" if mastered else "not mastered"
            content = f"Review of {skill_id}: {outcome}"
        
        # Create assessment event
        event = Event(
            event_id=str(uuid.uuid4()),
            content=content,
            event_type="assessment",
            actor="student",
            topics=[skill.topic_id] if skill.topic_id else [],
            skills=[skill_id],
            metadata={
                "review_outcome": "mastered" if mastered else "not_mastered",
                "skill_id": skill_id,
                "p_mastery_before": skill.p_mastery,
            },
        )
        
        # Insert event
        event = db.insert_event(event)
        
        # Update skill state with evidence
        updated_skill = update_skill_state_with_evidence(
            skill_id=skill_id,
            new_evidence=mastered,
            evidence_timestamp=datetime.utcnow(),
            db_path=db_path,
        )
        
        # Add updated mastery to event metadata
        event.metadata["p_mastery_after"] = updated_skill.p_mastery
        event = db.update_event(event)
        
        return event

