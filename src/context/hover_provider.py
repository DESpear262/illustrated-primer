"""
Hover provider for AI Tutor Proof of Concept.

Provides per-node summaries and statistics for knowledge tree visualization.
Includes caching to minimize repeated lookups and ensure <200ms latency.
"""

from __future__ import annotations

from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta
from functools import lru_cache
import time

from src.config import DB_PATH
from src.storage.db import Database
from src.storage.queries import (
    get_events_by_topic,
    get_events_by_skill,
    get_events_by_event_type,
)


# Cache configuration
_HOVER_CACHE_TTL_SECONDS = 300  # 5 minutes
_hover_cache: Dict[str, tuple[Dict[str, Any], float]] = {}
_cache_max_size = 1000  # Maximum number of cached entries


def _get_cache_key(node_id: str) -> str:
    """Get cache key for node ID."""
    return f"hover:{node_id}"


def _is_cache_valid(cached_time: float) -> bool:
    """Check if cache entry is still valid."""
    return (time.time() - cached_time) < _HOVER_CACHE_TTL_SECONDS


def _invalidate_cache(node_id: Optional[str] = None):
    """
    Invalidate cache entries.
    
    Args:
        node_id: Specific node ID to invalidate (None to clear all)
    """
    global _hover_cache
    
    if node_id:
        cache_key = _get_cache_key(node_id)
        _hover_cache.pop(cache_key, None)
    else:
        _hover_cache.clear()


def _trim_cache():
    """Trim cache to max size, removing oldest entries."""
    global _hover_cache
    
    if len(_hover_cache) <= _cache_max_size:
        return
    
    # Sort by timestamp and remove oldest
    sorted_items = sorted(_hover_cache.items(), key=lambda x: x[1][1])
    items_to_remove = len(_hover_cache) - _cache_max_size
    
    for key, _ in sorted_items[:items_to_remove]:
        _hover_cache.pop(key, None)


def get_hover_payload(
    node_id: str,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Get hover payload for a node in the knowledge tree.
    
    Returns summary information including title, mastery, last evidence,
    and statistics for display in hover tooltips.
    
    Args:
        node_id: Node ID in format "type:id" (e.g., "topic:math", "skill:derivative", "event:abc123")
        db_path: Path to database file (defaults to config.DB_PATH)
        
    Returns:
        Dictionary with hover payload information:
        - title: Display title
        - type: Node type (topic, skill, event)
        - summary: Summary text (for topics)
        - mastery: Mastery probability (for skills)
        - last_evidence: Last evidence timestamp
        - statistics: Additional statistics
        - event_snippet: Recent event content snippet (if applicable)
        
    Example:
        {
            "title": "Math",
            "type": "topic",
            "summary": "Mathematics fundamentals...",
            "event_count": 42,
            "last_event_at": "2024-01-15T10:30:00Z",
            "open_questions": ["Question 1", "Question 2"],
        }
    """
    db_path = db_path or DB_PATH
    
    # Check cache
    cache_key = _get_cache_key(node_id)
    if cache_key in _hover_cache:
        payload, cached_time = _hover_cache[cache_key]
        if _is_cache_valid(cached_time):
            return payload
    
    # Parse node ID
    if ":" not in node_id:
        raise ValueError(f"Invalid node ID format: {node_id}. Expected 'type:id'")
    
    node_type, node_identifier = node_id.split(":", 1)
    
    with Database(db_path) as db:
        if node_type == "topic":
            # Get topic information
            topic = db.get_topic_summary_by_id(node_identifier)
            
            if not topic:
                raise ValueError(f"Topic not found: {node_identifier}")
            
            # Get recent events for snippet
            recent_events = get_events_by_topic(
                node_identifier,
                limit=1,
                db_path=db_path,
            )
            
            event_snippet = None
            if recent_events:
                event = recent_events[0]
                event_snippet = {
                    "content": event.content[:200],  # Truncated content
                    "actor": event.actor,
                    "created_at": event.created_at.isoformat(),
                }
            
            payload = {
                "title": topic.topic_id,
                "type": "topic",
                "summary": topic.summary,
                "event_count": topic.event_count,
                "last_event_at": topic.last_event_at.isoformat() if topic.last_event_at else None,
                "open_questions": topic.open_questions,
                "event_snippet": event_snippet,
                "statistics": {
                    "created_at": topic.created_at.isoformat(),
                    "updated_at": topic.updated_at.isoformat(),
                },
            }
        
        elif node_type == "skill":
            # Get skill information
            skill = db.get_skill_state_by_id(node_identifier)
            
            if not skill:
                raise ValueError(f"Skill not found: {node_identifier}")
            
            # Get recent events for snippet
            recent_events = get_events_by_skill(
                node_identifier,
                limit=1,
                db_path=db_path,
            )
            
            event_snippet = None
            if recent_events:
                event = recent_events[0]
                event_snippet = {
                    "content": event.content[:200],
                    "actor": event.actor,
                    "created_at": event.created_at.isoformat(),
                }
            
            payload = {
                "title": skill.skill_id,
                "type": "skill",
                "mastery": skill.p_mastery,
                "evidence_count": skill.evidence_count,
                "last_evidence_at": skill.last_evidence_at.isoformat() if skill.last_evidence_at else None,
                "topic_id": skill.topic_id,
                "event_snippet": event_snippet,
                "statistics": {
                    "created_at": skill.created_at.isoformat(),
                    "updated_at": skill.updated_at.isoformat(),
                },
            }
        
        elif node_type == "event":
            # Get event information
            event = db.get_event_by_id(node_identifier)
            
            if not event:
                raise ValueError(f"Event not found: {node_identifier}")
            
            payload = {
                "title": event.event_id[:8],  # Short ID
                "type": "event",
                "content": event.content[:500],  # Truncated content
                "event_type": event.event_type,
                "actor": event.actor,
                "topics": event.topics,
                "skills": event.skills,
                "created_at": event.created_at.isoformat(),
                "recorded_at": event.recorded_at.isoformat() if event.recorded_at else None,
                "statistics": {
                    "content_length": len(event.content),
                },
            }
        
        else:
            raise ValueError(f"Unknown node type: {node_type}")
    
    # Cache payload
    _hover_cache[cache_key] = (payload, time.time())
    _trim_cache()
    
    return payload


def invalidate_hover_cache(node_id: Optional[str] = None):
    """
    Invalidate hover cache for a specific node or all nodes.
    
    Args:
        node_id: Node ID to invalidate (None to clear all cache)
    """
    _invalidate_cache(node_id)

