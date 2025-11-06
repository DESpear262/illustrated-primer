"""
Unit tests for hover provider.

Tests per-node summaries, statistics, and caching.
"""

from __future__ import annotations

import time
import pytest
from pathlib import Path
from uuid import uuid4
from datetime import datetime

from src.context.hover_provider import (
    get_hover_payload,
    clear_cache,
    get_cache_stats,
    CACHE_TTL_SECONDS,
)
from src.storage.db import Database, initialize_database
from src.models.base import TopicSummary, SkillState, Event
from src.config import DB_PATH


@pytest.fixture
def test_db(tmp_path):
    """Create a test database with sample data."""
    db_path = tmp_path / "test.db"
    initialize_database(db_path)
    
    with Database(db_path) as db:
        # Create topic
        topic = TopicSummary(
            topic_id="math",
            parent_topic_id=None,
            summary="Mathematics summary",
            event_count=10,
            last_event_at=datetime.utcnow(),
            open_questions=["Question 1", "Question 2"],
        )
        db.insert_topic_summary(topic)
        
        # Create skills for topic
        skill1 = SkillState(
            skill_id="arithmetic",
            topic_id="math",
            p_mastery=0.8,
            evidence_count=5,
            last_evidence_at=datetime.utcnow(),
        )
        db.insert_skill_state(skill1)
        
        skill2 = SkillState(
            skill_id="algebra",
            topic_id="math",
            p_mastery=0.6,
            evidence_count=3,
            last_evidence_at=datetime.utcnow(),
        )
        db.insert_skill_state(skill2)
        
        # Create event for skill
        event = Event(
            event_id=str(uuid4()),
            content="This is a test event about arithmetic skills.",
            event_type="chat",
            actor="student",
            skills=["arithmetic"],
            created_at=datetime.utcnow(),
        )
        db.insert_event(event)
    
    return db_path


class TestHoverProvider:
    """Tests for hover provider."""
    
    def test_get_hover_payload_topic(self, test_db):
        """Test get_hover_payload for topic node."""
        payload = get_hover_payload("math", "topic", db_path=test_db)
        
        assert "title" in payload
        assert "summary" in payload
        assert "event_count" in payload
        assert "last_event_at" in payload
        assert "average_mastery" in payload
        assert "child_skills_count" in payload
        assert "open_questions" in payload
        
        assert payload["title"] == "math"
        assert payload["summary"] == "Mathematics summary"
        assert payload["event_count"] == 10
        assert payload["child_skills_count"] == 2
        assert payload["average_mastery"] == 0.7  # (0.8 + 0.6) / 2
    
    def test_get_hover_payload_skill(self, test_db):
        """Test get_hover_payload for skill node."""
        payload = get_hover_payload("arithmetic", "skill", db_path=test_db)
        
        assert "title" in payload
        assert "p_mastery" in payload
        assert "last_evidence_at" in payload
        assert "evidence_count" in payload
        assert "topic_id" in payload
        assert "recent_event_snippet" in payload
        
        assert payload["title"] == "arithmetic"
        assert payload["p_mastery"] == 0.8
        assert payload["evidence_count"] == 5
        assert payload["topic_id"] == "math"
        assert payload["recent_event_snippet"] is not None
        assert "content" in payload["recent_event_snippet"]
    
    def test_get_hover_payload_topic_no_skills(self, tmp_path):
        """Test get_hover_payload for topic with no skills."""
        db_path = tmp_path / "test.db"
        initialize_database(db_path)
        
        with Database(db_path) as db:
            topic = TopicSummary(
                topic_id="empty_topic",
                parent_topic_id=None,
                summary="Empty topic",
                event_count=0,
            )
            db.insert_topic_summary(topic)
        
        payload = get_hover_payload("empty_topic", "topic", db_path=db_path)
        
        assert payload["average_mastery"] is None
        assert payload["child_skills_count"] == 0
    
    def test_get_hover_payload_skill_no_events(self, tmp_path):
        """Test get_hover_payload for skill with no events."""
        db_path = tmp_path / "test.db"
        initialize_database(db_path)
        
        with Database(db_path) as db:
            skill = SkillState(
                skill_id="no_events_skill",
                topic_id="math",
                p_mastery=0.5,
                evidence_count=0,
            )
            db.insert_skill_state(skill)
        
        payload = get_hover_payload("no_events_skill", "skill", db_path=db_path)
        
        assert payload["recent_event_snippet"] is None
    
    def test_get_hover_payload_invalid_node_type(self, test_db):
        """Test get_hover_payload with invalid node_type."""
        with pytest.raises(ValueError, match="Invalid node_type"):
            get_hover_payload("math", "invalid", db_path=test_db)
    
    def test_get_hover_payload_node_not_found(self, test_db):
        """Test get_hover_payload with non-existent node."""
        with pytest.raises(ValueError, match="Topic not found"):
            get_hover_payload("nonexistent", "topic", db_path=test_db)
        
        with pytest.raises(ValueError, match="Skill not found"):
            get_hover_payload("nonexistent", "skill", db_path=test_db)
    
    def test_hover_payload_caching(self, test_db):
        """Test that hover payloads are cached."""
        # Clear cache
        clear_cache()
        
        # Get payload (should populate cache)
        payload1 = get_hover_payload("math", "topic", db_path=test_db)
        
        # Get cache stats
        stats = get_cache_stats()
        assert stats["valid_entries"] >= 1
        
        # Get payload again (should use cache)
        payload2 = get_hover_payload("math", "topic", db_path=test_db)
        
        # Should be same payload
        assert payload1 == payload2
    
    def test_hover_payload_cache_expiration(self, test_db):
        """Test that cache entries expire after TTL."""
        # Clear cache
        clear_cache()
        
        # Get payload
        get_hover_payload("math", "topic", db_path=test_db)
        
        # Manually expire cache by modifying timestamps
        from src.context.hover_provider import _cache
        cache_key = "topic:math"
        if cache_key in _cache:
            payload, _ = _cache[cache_key]
            # Set timestamp to past
            _cache[cache_key] = (payload, time.time() - CACHE_TTL_SECONDS - 1)
        
        # Get cache stats
        stats = get_cache_stats()
        assert stats["expired_entries"] >= 1
    
    def test_clear_cache_specific_entry(self, test_db):
        """Test clearing specific cache entry."""
        # Clear cache
        clear_cache()
        
        # Get payloads
        get_hover_payload("math", "topic", db_path=test_db)
        get_hover_payload("arithmetic", "skill", db_path=test_db)
        
        # Clear specific entry
        clear_cache(node_id="math", node_type="topic")
        
        # Check cache stats
        stats = get_cache_stats()
        assert stats["valid_entries"] == 1  # Only skill entry remains
    
    def test_clear_cache_by_type(self, test_db):
        """Test clearing cache by type."""
        # Clear cache
        clear_cache()
        
        # Get payloads
        get_hover_payload("math", "topic", db_path=test_db)
        get_hover_payload("arithmetic", "skill", db_path=test_db)
        
        # Clear all topic entries
        clear_cache(node_type="topic")
        
        # Check cache stats
        stats = get_cache_stats()
        assert stats["valid_entries"] == 1  # Only skill entry remains
    
    def test_clear_cache_all(self, test_db):
        """Test clearing all cache."""
        # Get payloads
        get_hover_payload("math", "topic", db_path=test_db)
        get_hover_payload("arithmetic", "skill", db_path=test_db)
        
        # Clear all cache
        clear_cache()
        
        # Check cache stats
        stats = get_cache_stats()
        assert stats["total_entries"] == 0
    
    def test_get_cache_stats(self, test_db):
        """Test get_cache_stats function."""
        # Clear cache
        clear_cache()
        
        # Get stats (should be empty)
        stats = get_cache_stats()
        assert stats["total_entries"] == 0
        assert stats["valid_entries"] == 0
        assert stats["expired_entries"] == 0
        
        # Get payload
        get_hover_payload("math", "topic", db_path=test_db)
        
        # Get stats again
        stats = get_cache_stats()
        assert stats["total_entries"] >= 1
        assert stats["valid_entries"] >= 1
        assert "cache_ttl_seconds" in stats

