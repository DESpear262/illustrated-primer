"""
Summarization update functions for AI Tutor Proof of Concept.

Provides functions for updating topic summaries and skill states with
batch processing, aggregation, and audit logging.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from uuid import uuid4

from src.config import (
    DB_PATH,
    SUMMARIZATION_BATCH_SIZE,
    OPENAI_MODEL_NANO,
)
from src.models.base import Event, SkillState, TopicSummary
from src.storage.db import Database
from src.storage.queries import (
    get_events_by_topic,
    update_skill_state_with_evidence,
    get_events_by_time_range,
)
from src.services.ai.client import AIClient, get_client
from src.services.ai.prompts import SummaryOutput
from src.utils.serialization import (
    serialize_json_list,
    deserialize_json_list,
    serialize_json_dict,
    deserialize_json_dict,
)

logger = logging.getLogger(__name__)


def log_audit(
    log_type: str,
    status: str,
    event_ids: List[str],
    topic_id: Optional[str] = None,
    skill_id: Optional[str] = None,
    summary_version: Optional[int] = None,
    model_version: Optional[str] = None,
    tokens_used: Optional[int] = None,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    db_path: Optional[Path] = None,
) -> None:
    """
    Log summarization operation to audit log.
    
    Args:
        log_type: Type of log ('summarization', 'skill_update', 'topic_update')
        status: Status ('success', 'failed', 'partial')
        event_ids: List of event IDs processed
        topic_id: Optional topic ID
        skill_id: Optional skill ID
        summary_version: Optional summary version number
        model_version: Optional AI model version used
        tokens_used: Optional number of tokens used
        error_message: Optional error message if failed
        metadata: Optional additional metadata
        db_path: Path to database file (defaults to config.DB_PATH)
    """
    db_path = db_path or DB_PATH
    
    with Database(db_path) as db:
        if not db.conn:
            raise ValueError("Database connection not established")
        
        cursor = db.conn.cursor()
        cursor.execute(
            """
            INSERT INTO audit_logs (
                log_type, topic_id, skill_id, event_ids, summary_version,
                model_version, tokens_used, status, error_message, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log_type,
                topic_id,
                skill_id,
                serialize_json_list(event_ids),
                summary_version,
                model_version,
                tokens_used,
                status,
                error_message,
                serialize_json_dict(metadata or {}),
            ),
        )
        db.conn.commit()


def get_topic_summary_version(topic_id: str, db_path: Optional[Path] = None) -> int:
    """
    Get current summary version for a topic.
    
    Args:
        topic_id: Topic identifier
        db_path: Path to database file (defaults to config.DB_PATH)
        
    Returns:
        Current summary version number (0 if no version tracked)
    """
    db_path = db_path or DB_PATH
    
    with Database(db_path) as db:
        topic = db.get_topic_summary_by_id(topic_id)
        if topic:
            # Get summary version from metadata
            version = topic.metadata.get("summary_version", 0)
            return int(version) if isinstance(version, (int, str)) else 0
        return 0


def get_unprocessed_events(
    topic_id: str,
    since: Optional[datetime] = None,
    limit: Optional[int] = None,
    db_path: Optional[Path] = None,
) -> List[Event]:
    """
    Get events for a topic that haven't been summarized yet.
    
    Uses last_summarized_at timestamp from topic metadata to determine
    which events need processing.
    
    Args:
        topic_id: Topic identifier
        since: Optional timestamp to get events since (defaults to last_summarized_at)
        limit: Optional limit on number of events to return
        db_path: Path to database file (defaults to config.DB_PATH)
        
    Returns:
        List of unprocessed Event objects
    """
    db_path = db_path or DB_PATH
    
    with Database(db_path) as db:
        topic = db.get_topic_summary_by_id(topic_id)
        
        # Determine cutoff timestamp
        if since:
            cutoff = since
        elif topic and topic.metadata:
            last_summarized = topic.metadata.get("last_summarized_at")
            if last_summarized:
                try:
                    cutoff = datetime.fromisoformat(last_summarized)
                except (ValueError, TypeError):
                    cutoff = None
            else:
                cutoff = None
        else:
            cutoff = None
        
        # Get events for topic
        if cutoff:
            events = get_events_by_time_range(
                start_time=cutoff,
                end_time=None,
                limit=limit,
                db_path=db_path,
            )
            # Filter by topic
            events = [e for e in events if topic_id in e.topics]
        else:
            # Get all events for topic
            events = get_events_by_topic(topic_id, limit=limit, db_path=db_path)
        
        return events


def update_topic_summary(
    topic_id: str,
    event_ids: Optional[List[str]] = None,
    event_content: Optional[str] = None,
    summary_output: Optional[SummaryOutput] = None,
    force: bool = False,
    db_path: Optional[Path] = None,
) -> Tuple[TopicSummary, Optional[int]]:
    """
    Update or create topic summary after event import.
    
    Uses AI summarization to update topic summary with new event content.
    If topic doesn't exist, creates a new one. Aggregates multiple events
    into a single summary update.
    
    Args:
        topic_id: Topic identifier
        event_ids: Optional list of event IDs processed (for audit logging)
        event_content: Optional event content to summarize (if not provided, gets unprocessed events)
        summary_output: Optional SummaryOutput from AI summarization (if already computed)
        force: Force refresh even if recently updated
        db_path: Path to database file (defaults to config.DB_PATH)
        
    Returns:
        Tuple of (updated TopicSummary, tokens_used)
    """
    db_path = db_path or DB_PATH
    event_ids = event_ids or []
    tokens_used = None
    
    try:
        with Database(db_path) as db:
            # Get existing topic summary
            topic = db.get_topic_summary_by_id(topic_id)
            
            # Get unprocessed events if content not provided
            if not event_content:
                if not force and topic:
                    # Check if recently updated
                    last_summarized = topic.metadata.get("last_summarized_at")
                    if last_summarized:
                        try:
                            last_time = datetime.fromisoformat(last_summarized)
                            if (datetime.utcnow() - last_time).total_seconds() < 300:  # 5 minutes
                                logger.debug(f"Topic {topic_id} recently summarized, skipping")
                                return topic, None
                        except (ValueError, TypeError):
                            pass
                
                # Get unprocessed events
                events = get_unprocessed_events(topic_id, limit=SUMMARIZATION_BATCH_SIZE, db_path=db_path)
                if not events:
                    logger.debug(f"No unprocessed events for topic {topic_id}")
                    return topic or TopicSummary(topic_id=topic_id, summary="", event_count=0), None
                
                # Aggregate event content
                event_content = "\n\n".join([e.content for e in events])
                event_ids = [e.event_id for e in events]
            
            # Get recent events for context
            recent_events = get_events_by_topic(topic_id, limit=5, db_path=db_path)
            context = "\n".join([e.content[:500] for e in recent_events[-3:]]) if recent_events else None
            
            # Summarize with context (use provided summary or compute new one)
            if summary_output:
                summary_result = summary_output
            else:
                client = get_client()
                summary_result = client.summarize_event(event_content, context=context)
                # Estimate tokens used (rough approximation)
                tokens_used = len(event_content.split()) + (len(context.split()) if context else 0)
            
            # Get current version
            version = get_topic_summary_version(topic_id, db_path=db_path)
            new_version = version + 1
            
            if topic:
                # Update existing topic - merge summary with existing
                existing_summary = topic.summary
                new_summary = summary_result.summary
                
                # Combine summaries if both exist
                if existing_summary and new_summary:
                    merged_summary = f"{existing_summary}\n\nNew content: {new_summary}"
                else:
                    merged_summary = new_summary or existing_summary
                
                # Merge open questions
                existing_questions = set(topic.open_questions)
                new_questions = set(summary_result.open_questions) if hasattr(summary_result, 'open_questions') else set()
                all_questions = list(existing_questions | new_questions)
                
                # Update metadata
                metadata = topic.metadata.copy()
                metadata["summary_version"] = new_version
                metadata["last_summarized_at"] = datetime.utcnow().isoformat()
                metadata["last_summarization_event_ids"] = event_ids
                
                topic.summary = merged_summary
                topic.open_questions = all_questions
                topic.event_count += len(event_ids) if event_ids else 1
                topic.last_event_at = datetime.utcnow()
                topic.updated_at = datetime.utcnow()
                topic.metadata = metadata
                
                updated_topic = db.update_topic_summary(topic)
                
                # Log audit
                log_audit(
                    log_type="topic_update",
                    status="success",
                    event_ids=event_ids,
                    topic_id=topic_id,
                    summary_version=new_version,
                    model_version=OPENAI_MODEL_NANO,
                    tokens_used=tokens_used,
                    db_path=db_path,
                )
                
                return updated_topic, tokens_used
            else:
                # Create new topic
                new_topic = TopicSummary(
                    topic_id=topic_id,
                    summary=summary_result.summary if hasattr(summary_result, 'summary') else "",
                    open_questions=summary_result.open_questions if hasattr(summary_result, 'open_questions') else [],
                    event_count=len(event_ids) if event_ids else 1,
                    last_event_at=datetime.utcnow(),
                    metadata={
                        "summary_version": new_version,
                        "last_summarized_at": datetime.utcnow().isoformat(),
                        "last_summarization_event_ids": event_ids,
                    },
                )
                inserted_topic = db.insert_topic_summary(new_topic)
                
                # Log audit
                log_audit(
                    log_type="topic_update",
                    status="success",
                    event_ids=event_ids,
                    topic_id=topic_id,
                    summary_version=new_version,
                    model_version=OPENAI_MODEL_NANO,
                    tokens_used=tokens_used,
                    db_path=db_path,
                )
                
                return inserted_topic, tokens_used
    
    except Exception as e:
        logger.error(f"Failed to update topic summary {topic_id}: {e}")
        
        # Log audit failure
        log_audit(
            log_type="topic_update",
            status="failed",
            event_ids=event_ids,
            topic_id=topic_id,
            error_message=str(e),
            db_path=db_path,
        )
        
        raise


def update_skill_states(
    skills: List[str],
    event_ids: Optional[List[str]] = None,
    event_content: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> List[SkillState]:
    """
    Update or create skill states after event import.
    
    For each skill, creates or updates skill state with evidence from event.
    
    Args:
        skills: List of skill identifiers
        event_ids: Optional list of event IDs processed (for audit logging)
        event_content: Event content used as evidence (unused for now, but kept for future use)
        db_path: Path to database file (defaults to config.DB_PATH)
        
    Returns:
        List of updated or created SkillStates
    """
    updated_skills = []
    event_ids = event_ids or []
    
    for skill_id in skills:
        try:
            with Database(db_path) as db:
                skill = db.get_skill_state_by_id(skill_id)
                
                if skill:
                    # Update existing skill with positive evidence (imported transcripts are learning events)
                    updated_skill = update_skill_state_with_evidence(
                        skill_id=skill_id,
                        new_evidence=True,
                        evidence_timestamp=datetime.utcnow(),
                        db_path=db_path,
                    )
                    updated_skills.append(updated_skill)
                    
                    # Log audit
                    log_audit(
                        log_type="skill_update",
                        status="success",
                        event_ids=event_ids,
                        skill_id=skill_id,
                        db_path=db_path,
                    )
                else:
                    # Create new skill with initial mastery
                    new_skill = SkillState(
                        skill_id=skill_id,
                        p_mastery=0.5,  # Default initial mastery
                        evidence_count=1,
                        last_evidence_at=datetime.utcnow(),
                    )
                    inserted_skill = db.insert_skill_state(new_skill)
                    updated_skills.append(inserted_skill)
                    
                    # Log audit
                    log_audit(
                        log_type="skill_update",
                        status="success",
                        event_ids=event_ids,
                        skill_id=skill_id,
                        db_path=db_path,
                    )
        
        except Exception as e:
            logger.error(f"Failed to update skill state {skill_id}: {e}")
            
            # Log audit failure
            log_audit(
                log_type="skill_update",
                status="failed",
                event_ids=event_ids,
                skill_id=skill_id,
                error_message=str(e),
                db_path=db_path,
            )
    
    return updated_skills


def refresh_topic_summaries(
    topic_ids: Optional[List[str]] = None,
    since: Optional[datetime] = None,
    force: bool = False,
    db_path: Optional[Path] = None,
) -> Dict[str, Tuple[TopicSummary, Optional[int]]]:
    """
    Refresh topic summaries for multiple topics.
    
    Args:
        topic_ids: Optional list of topic IDs to refresh (None for all topics with new events)
        since: Optional timestamp to refresh topics with events since this time
        force: Force refresh even if recently updated
        db_path: Path to database file (defaults to config.DB_PATH)
        
    Returns:
        Dictionary mapping topic_id to (TopicSummary, tokens_used) tuple
    """
    db_path = db_path or DB_PATH
    
    with Database(db_path) as db:
        if topic_ids:
            topics_to_process = topic_ids
        else:
            # Get all topics with recent events
            if since:
                events = get_events_by_time_range(
                    start_time=since,
                    end_time=None,
                    limit=None,
                    db_path=db_path,
                )
                # Get unique topic IDs
                topics_to_process = list(set(topic_id for e in events for topic_id in e.topics))
            else:
                # Get all topics from database
                cursor = db.conn.cursor()
                cursor.execute("SELECT DISTINCT topic_id FROM topics")
                rows = cursor.fetchall()
                topics_to_process = [row[0] for row in rows]
    
    results = {}
    for topic_id in topics_to_process:
        try:
            topic, tokens = update_topic_summary(
                topic_id=topic_id,
                force=force,
                db_path=db_path,
            )
            results[topic_id] = (topic, tokens)
        except Exception as e:
            logger.error(f"Failed to refresh topic {topic_id}: {e}")
            results[topic_id] = (None, None)
    
    return results


def get_topics_needing_refresh(
    since: Optional[datetime] = None,
    db_path: Optional[Path] = None,
) -> List[str]:
    """
    Get list of topic IDs that need summarization refresh.
    
    Args:
        since: Optional timestamp to check for events since this time
        db_path: Path to database file (defaults to config.DB_PATH)
        
    Returns:
        List of topic IDs that have unprocessed events
    """
    db_path = db_path or DB_PATH
    
    topics_needing_refresh = []
    
    with Database(db_path) as db:
        # Get all topics
        cursor = db.conn.cursor()
        cursor.execute("SELECT topic_id FROM topics")
        rows = cursor.fetchall()
        all_topics = [row[0] for row in rows]
        
        # Check each topic for unprocessed events
        for topic_id in all_topics:
            events = get_unprocessed_events(topic_id, since=since, limit=1, db_path=db_path)
            if events:
                topics_needing_refresh.append(topic_id)
        
        # Also check for events without topics (shouldn't happen, but check anyway)
        if since:
            events = get_events_by_time_range(
                start_time=since,
                end_time=None,
                limit=None,
                db_path=db_path,
            )
        else:
            # Get recent events (last 24 hours)
            since = datetime.utcnow() - timedelta(days=1)
            events = get_events_by_time_range(
                start_time=since,
                end_time=None,
                limit=None,
                db_path=db_path,
            )
        
        # Get unique topic IDs from events
        event_topics = set()
        for e in events:
            event_topics.update(e.topics)
        
        # Add topics that are in events but not in topics_needing_refresh
        for topic_id in event_topics:
            if topic_id not in topics_needing_refresh and topic_id not in all_topics:
                topics_needing_refresh.append(topic_id)
    
    return topics_needing_refresh

