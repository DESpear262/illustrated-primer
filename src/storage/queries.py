"""
Query wrappers for AI Tutor Proof of Concept.

Provides high-level query functions for filtering events, skills, topics,
and other entities by topic, time, skill, and other criteria.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path

from src.storage.db import Database
from src.models.base import Event, SkillState, TopicSummary
from src.utils.serialization import (
    deserialize_json_list,
    deserialize_json_dict,
    deserialize_datetime,
)


def get_events_by_topic(
    topic_id: str,
    limit: Optional[int] = None,
    offset: int = 0,
    db_path: Optional[Path] = None,
) -> List[Event]:
    """
    Get events filtered by topic.
    
    Args:
        topic_id: Topic identifier to filter by
        limit: Maximum number of events to return (None for all)
        offset: Number of events to skip
        db_path: Path to database file (defaults to config.DB_PATH)
        
    Returns:
        List of Event objects matching the topic
    """
    with Database(db_path) as db:
        if not db.conn:
            raise ValueError("Database connection not established")
        
        cursor = db.conn.cursor()
        
        # Search for topic in JSON array
        query = """
            SELECT * FROM events
            WHERE topics LIKE ?
            ORDER BY created_at DESC
        """
        
        params = [f"%{topic_id}%"]
        
        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [db._row_to_event(row) for row in rows]


def get_events_by_time_range(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: Optional[int] = None,
    offset: int = 0,
    db_path: Optional[Path] = None,
) -> List[Event]:
    """
    Get events filtered by time range.
    
    Args:
        start_time: Start of time range (None for no lower bound)
        end_time: End of time range (None for no upper bound)
        limit: Maximum number of events to return (None for all)
        offset: Number of events to skip
        db_path: Path to database file (defaults to config.DB_PATH)
        
    Returns:
        List of Event objects within the time range
    """
    with Database(db_path) as db:
        if not db.conn:
            raise ValueError("Database connection not established")
        
        cursor = db.conn.cursor()
        
        conditions = []
        params = []
        
        if start_time:
            conditions.append("created_at >= ?")
            params.append(start_time.isoformat())
        
        if end_time:
            conditions.append("created_at <= ?")
            params.append(end_time.isoformat())
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT * FROM events
            WHERE {where_clause}
            ORDER BY created_at DESC
        """
        
        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [db._row_to_event(row) for row in rows]


def get_events_by_skill(
    skill_id: str,
    limit: Optional[int] = None,
    offset: int = 0,
    db_path: Optional[Path] = None,
) -> List[Event]:
    """
    Get events filtered by skill.
    
    Args:
        skill_id: Skill identifier to filter by
        limit: Maximum number of events to return (None for all)
        offset: Number of events to skip
        db_path: Path to database file (defaults to config.DB_PATH)
        
    Returns:
        List of Event objects matching the skill
    """
    with Database(db_path) as db:
        if not db.conn:
            raise ValueError("Database connection not established")
        
        cursor = db.conn.cursor()
        
        query = """
            SELECT * FROM events
            WHERE skills LIKE ?
            ORDER BY created_at DESC
        """
        
        params = [f"%{skill_id}%"]
        
        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [db._row_to_event(row) for row in rows]


def get_events_by_event_type(
    event_type: str,
    limit: Optional[int] = None,
    offset: int = 0,
    db_path: Optional[Path] = None,
) -> List[Event]:
    """
    Get events filtered by event type.
    
    Args:
        event_type: Event type ('chat', 'transcript', 'quiz', 'assessment')
        limit: Maximum number of events to return (None for all)
        offset: Number of events to skip
        db_path: Path to database file (defaults to config.DB_PATH)
        
    Returns:
        List of Event objects of the specified type
    """
    with Database(db_path) as db:
        if not db.conn:
            raise ValueError("Database connection not established")
        
        cursor = db.conn.cursor()
        
        query = """
            SELECT * FROM events
            WHERE event_type = ?
            ORDER BY created_at DESC
        """
        
        params = [event_type]
        
        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [db._row_to_event(row) for row in rows]


def search_events_fts(
    query_text: str,
    limit: int = 10,
    offset: int = 0,
    db_path: Optional[Path] = None,
) -> List[Event]:
    """
    Search events using FTS5 full-text search.
    
    Args:
        query_text: Search query text
        limit: Maximum number of events to return
        offset: Number of events to skip
        db_path: Path to database file (defaults to config.DB_PATH)
        
    Returns:
        List of Event objects matching the search query
    """
    with Database(db_path) as db:
        if not db.conn:
            raise ValueError("Database connection not established")
        
        cursor = db.conn.cursor()
        
        # FTS5 search query
        query = """
            SELECT e.* FROM events e
            JOIN events_fts ON e.id = events_fts.rowid
            WHERE events_fts MATCH ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        
        cursor.execute(query, (query_text, limit, offset))
        rows = cursor.fetchall()
        
        return [db._row_to_event(row) for row in rows]


def get_skills_by_topic(
    topic_id: str,
    db_path: Optional[Path] = None,
) -> List[SkillState]:
    """
    Get skills filtered by topic.
    
    Args:
        topic_id: Topic identifier to filter by
        db_path: Path to database file (defaults to config.DB_PATH)
        
    Returns:
        List of SkillState objects for the topic
    """
    with Database(db_path) as db:
        if not db.conn:
            raise ValueError("Database connection not established")
        
        cursor = db.conn.cursor()
        
        query = """
            SELECT * FROM skills
            WHERE topic_id = ?
            ORDER BY p_mastery ASC, last_evidence_at DESC NULLS LAST
        """
        
        cursor.execute(query, (topic_id,))
        rows = cursor.fetchall()
        
        return [db._row_to_skill_state(row) for row in rows]


def get_skills_by_mastery_range(
    min_mastery: float = 0.0,
    max_mastery: float = 1.0,
    db_path: Optional[Path] = None,
) -> List[SkillState]:
    """
    Get skills filtered by mastery range.
    
    Args:
        min_mastery: Minimum mastery probability (0.0-1.0)
        max_mastery: Maximum mastery probability (0.0-1.0)
        db_path: Path to database file (defaults to config.DB_PATH)
        
    Returns:
        List of SkillState objects within the mastery range
    """
    with Database(db_path) as db:
        if not db.conn:
            raise ValueError("Database connection not established")
        
        cursor = db.conn.cursor()
        
        query = """
            SELECT * FROM skills
            WHERE p_mastery >= ? AND p_mastery <= ?
            ORDER BY p_mastery ASC
        """
        
        cursor.execute(query, (min_mastery, max_mastery))
        rows = cursor.fetchall()
        
        return [db._row_to_skill_state(row) for row in rows]


def get_topics_by_parent(
    parent_topic_id: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> List[TopicSummary]:
    """
    Get topics filtered by parent topic.
    
    Args:
        parent_topic_id: Parent topic identifier (None for root topics)
        db_path: Path to database file (defaults to config.DB_PATH)
        
    Returns:
        List of TopicSummary objects for the parent topic
    """
    with Database(db_path) as db:
        if not db.conn:
            raise ValueError("Database connection not established")
        
        cursor = db.conn.cursor()
        
        if parent_topic_id is None:
            query = "SELECT * FROM topics WHERE parent_topic_id IS NULL"
            params = []
        else:
            query = "SELECT * FROM topics WHERE parent_topic_id = ?"
            params = [parent_topic_id]
        
        query += " ORDER BY topic_id ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [db._row_to_topic_summary(row) for row in rows]


def get_topic_hierarchy(
    root_topic_id: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Get topic hierarchy starting from root topic.
    
    Args:
        root_topic_id: Root topic identifier (None for all root topics)
        db_path: Path to database file (defaults to config.DB_PATH)
        
    Returns:
        Dictionary with topic hierarchy structure
    """
    with Database(db_path) as db:
        if not db.conn:
            raise ValueError("Database connection not established")
        
        cursor = db.conn.cursor()
        
        if root_topic_id is None:
            # Get all root topics
            query = "SELECT * FROM topics WHERE parent_topic_id IS NULL"
            cursor.execute(query)
        else:
            # Get specific root topic
            query = "SELECT * FROM topics WHERE topic_id = ?"
            cursor.execute(query, (root_topic_id,))
        
        root_rows = cursor.fetchall()
        
        def build_topic_tree(topic_row):
            """Recursively build topic tree."""
            topic = db._row_to_topic_summary(topic_row)
            
            # Get children
            cursor.execute(
                "SELECT * FROM topics WHERE parent_topic_id = ?",
                (topic.topic_id,)
            )
            child_rows = cursor.fetchall()
            
            children = [build_topic_tree(row) for row in child_rows]
            
            return {
                "topic": topic,
                "children": children,
            }
        
        return {
            "roots": [build_topic_tree(row) for row in root_rows],
        }


def get_recent_events(
    days: int = 7,
    limit: int = 50,
    db_path: Optional[Path] = None,
) -> List[Event]:
    """
    Get recent events from the last N days.
    
    Args:
        days: Number of days to look back
        limit: Maximum number of events to return
        db_path: Path to database file (defaults to config.DB_PATH)
        
    Returns:
        List of Event objects from the last N days
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    
    return get_events_by_time_range(
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        db_path=db_path,
    )


def update_skill_state_with_evidence(
    skill_id: str,
    new_evidence: bool,
    evidence_timestamp: Optional[datetime] = None,
    db_path: Optional[Path] = None,
) -> SkillState:
    """
    Update skill state with new evidence.
    
    Persistence helper for SkillState updates. Increments evidence_count,
    updates last_evidence_at, and adjusts p_mastery based on evidence.
    
    Args:
        skill_id: Skill identifier
        new_evidence: True if evidence of mastery, False if evidence of non-mastery
        evidence_timestamp: Timestamp of evidence (defaults to now)
        db_path: Path to database file (defaults to config.DB_PATH)
        
    Returns:
        Updated SkillState
    """
    with Database(db_path) as db:
        skill = db.get_skill_state_by_id(skill_id)
        
        if not skill:
            raise ValueError(f"Skill not found: {skill_id}")
        
        # Update evidence
        skill.evidence_count += 1
        skill.last_evidence_at = evidence_timestamp or datetime.utcnow()
        skill.updated_at = datetime.utcnow()
        
        # Simple mastery update: increment by 0.1 for positive evidence,
        # decrement by 0.05 for negative evidence, bounded to [0, 1]
        if new_evidence:
            skill.p_mastery = min(1.0, skill.p_mastery + 0.1)
        else:
            skill.p_mastery = max(0.0, skill.p_mastery - 0.05)
        
        # Update in database
        return db.update_skill_state(skill)

