"""
Hover provider for AI Tutor Proof of Concept.

Provides per-node summaries and statistics for knowledge tree visualization.
Includes caching with TTL to minimize repeated lookups.
"""

from __future__ import annotations

import time
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from src.config import DB_PATH
from src.storage.db import Database
from src.storage.queries import (
    get_skills_by_topic,
    get_events_by_skill,
    get_events_by_topic,
)
from src.models.base import TopicSummary, SkillState


# Cache configuration
CACHE_TTL_SECONDS = 300  # 5 minutes
_cache: Dict[str, tuple[Dict[str, Any], float]] = {}


def get_hover_payload(
    node_id: str,
    node_type: str,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Get hover payload for a node (topic or skill).
    
    Args:
        node_id: Node identifier (topic_id or skill_id)
        node_type: Node type ("topic" or "skill")
        db_path: Path to database file (defaults to config.DB_PATH)
        
    Returns:
        Dictionary with hover payload:
        - For topics: title, summary, event_count, last_event_at, average_mastery, child_skills_count
        - For skills: title, p_mastery, last_evidence_at, evidence_count, recent_event_snippet
        
    Raises:
        ValueError: If node_type is invalid or node not found
    """
    db_path = db_path or DB_PATH
    
    # Validate node_type
    if node_type not in ("topic", "skill"):
        raise ValueError(f"Invalid node_type: {node_type}. Must be 'topic' or 'skill'")
    
    # Check cache
    cache_key = f"{node_type}:{node_id}"
    if cache_key in _cache:
        payload, timestamp = _cache[cache_key]
        if time.time() - timestamp < CACHE_TTL_SECONDS:
            return payload
    
    # Build payload
    if node_type == "topic":
        payload = _get_topic_hover_payload(node_id, db_path)
    else:  # skill
        payload = _get_skill_hover_payload(node_id, db_path)
    
    # Cache payload
    _cache[cache_key] = (payload, time.time())
    
    return payload


def _get_topic_hover_payload(topic_id: str, db_path: Path) -> Dict[str, Any]:
    """
    Get hover payload for a topic node.
    
    Args:
        topic_id: Topic identifier
        db_path: Path to database file
        
    Returns:
        Dictionary with topic hover payload
    """
    with Database(db_path) as db:
        topic = db.get_topic_summary_by_id(topic_id)
        
        if not topic:
            raise ValueError(f"Topic not found: {topic_id}")
        
        # Get child skills
        skills = get_skills_by_topic(topic_id, db_path)
        
        # Calculate average mastery from child skills
        if skills:
            average_mastery = sum(skill.p_mastery for skill in skills) / len(skills)
        else:
            average_mastery = None
        
        # Build payload
        payload = {
            "title": topic_id,
            "summary": topic.summary,
            "event_count": topic.event_count,
            "last_event_at": topic.last_event_at.isoformat() if topic.last_event_at else None,
            "average_mastery": average_mastery,
            "child_skills_count": len(skills),
            "open_questions": topic.open_questions,
        }
        
        return payload


def _get_skill_hover_payload(skill_id: str, db_path: Path) -> Dict[str, Any]:
    """
    Get hover payload for a skill node.
    
    Args:
        skill_id: Skill identifier
        db_path: Path to database file
        
    Returns:
        Dictionary with skill hover payload
    """
    with Database(db_path) as db:
        skill = db.get_skill_state_by_id(skill_id)
        
        if not skill:
            raise ValueError(f"Skill not found: {skill_id}")
        
        # Get recent events for this skill
        events = get_events_by_skill(skill_id, limit=1, db_path=db_path)
        
        # Get recent event snippet
        recent_event_snippet = None
        if events:
            event = events[0]
            # Truncate content to 200 characters
            content = event.content
            if len(content) > 200:
                content = content[:200] + "..."
            recent_event_snippet = {
                "content": content,
                "created_at": event.created_at.isoformat() if event.created_at else None,
                "event_type": event.event_type,
            }
        
        # Build payload
        payload = {
            "title": skill_id,
            "p_mastery": skill.p_mastery,
            "last_evidence_at": skill.last_evidence_at.isoformat() if skill.last_evidence_at else None,
            "evidence_count": skill.evidence_count,
            "topic_id": skill.topic_id,
            "recent_event_snippet": recent_event_snippet,
        }
        
        return payload


def clear_cache(node_id: Optional[str] = None, node_type: Optional[str] = None) -> None:
    """
    Clear hover payload cache.
    
    Args:
        node_id: Optional node identifier to clear specific cache entry
        node_type: Optional node type to clear cache entries for that type
    """
    global _cache
    
    if node_id and node_type:
        # Clear specific entry
        cache_key = f"{node_type}:{node_id}"
        _cache.pop(cache_key, None)
    elif node_type:
        # Clear all entries for this type
        keys_to_remove = [k for k in _cache.keys() if k.startswith(f"{node_type}:")]
        for key in keys_to_remove:
            _cache.pop(key, None)
    else:
        # Clear all cache
        _cache.clear()


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.
    
    Returns:
        Dictionary with cache statistics (size, entries, etc.)
    """
    current_time = time.time()
    valid_entries = {
        k: v for k, (payload, timestamp) in _cache.items()
        if current_time - timestamp < CACHE_TTL_SECONDS
    }
    
    return {
        "total_entries": len(_cache),
        "valid_entries": len(valid_entries),
        "expired_entries": len(_cache) - len(valid_entries),
        "cache_ttl_seconds": CACHE_TTL_SECONDS,
    }

