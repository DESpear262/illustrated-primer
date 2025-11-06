"""
Unit and integration tests for hover provider.

Tests hover payload structure, caching, and performance.
"""

import pytest
import time
from pathlib import Path

from src.context.hover_provider import (
    get_hover_payload,
    invalidate_hover_cache,
)
from src.storage.db import Database, initialize_database
from src.models.base import Event, SkillState, TopicSummary


@pytest.fixture
def db_path(tmp_path) -> Path:
    """Fixture for a temporary database path."""
    path = tmp_path / "test_hover.db"
    initialize_database(path)
    return path


@pytest.fixture
def populated_db(db_path) -> Path:
    """Fixture with sample topics, skills, and events."""
    with Database(db_path) as db:
        # Create topic
        topic = TopicSummary(
            topic_id="math",
            summary="Mathematics fundamentals",
            event_count=5,
            open_questions=["What is calculus?"],
        )
        db.insert_topic_summary(topic)
        
        # Create skill
        skill = SkillState(
            skill_id="derivative_basic",
            topic_id="math",
            p_mastery=0.7,
            evidence_count=3,
        )
        db.insert_skill_state(skill)
        
        # Create event
        event = Event(
            event_id="e1",
            content="Student learned basic derivatives. This is a longer content snippet to test truncation.",
            event_type="chat",
            actor="student",
            topics=["math"],
            skills=["derivative_basic"],
        )
        db.insert_event(event)
    
    return db_path


class TestHoverProviderFormat:
    """Tests for hover payload format validation."""
    
    def test_topic_hover_payload_structure(self, populated_db):
        """Test that topic hover payload has correct structure."""
        payload = get_hover_payload("topic:math", db_path=populated_db)
        
        assert "title" in payload
        assert "type" in payload
        assert payload["type"] == "topic"
        assert "summary" in payload
        assert "event_count" in payload
        assert "last_event_at" in payload
        assert "open_questions" in payload
        assert "event_snippet" in payload
        assert "statistics" in payload
    
    def test_skill_hover_payload_structure(self, populated_db):
        """Test that skill hover payload has correct structure."""
        payload = get_hover_payload("skill:derivative_basic", db_path=populated_db)
        
        assert "title" in payload
        assert "type" in payload
        assert payload["type"] == "skill"
        assert "mastery" in payload
        assert "evidence_count" in payload
        assert "last_evidence_at" in payload
        assert "topic_id" in payload
        assert "event_snippet" in payload
        assert "statistics" in payload
    
    def test_event_hover_payload_structure(self, populated_db):
        """Test that event hover payload has correct structure."""
        payload = get_hover_payload("event:e1", db_path=populated_db)
        
        assert "title" in payload
        assert "type" in payload
        assert payload["type"] == "event"
        assert "content" in payload
        assert "event_type" in payload
        assert "actor" in payload
        assert "topics" in payload
        assert "skills" in payload
        assert "created_at" in payload
        assert "statistics" in payload
    
    def test_hover_payload_required_fields(self, populated_db):
        """Test that hover payload includes all required fields."""
        # Test topic
        topic_payload = get_hover_payload("topic:math", db_path=populated_db)
        assert topic_payload["title"] == "math"
        assert topic_payload["summary"] == "Mathematics fundamentals"
        assert topic_payload["event_count"] == 5
        assert "What is calculus?" in topic_payload["open_questions"]
        
        # Test skill
        skill_payload = get_hover_payload("skill:derivative_basic", db_path=populated_db)
        assert skill_payload["title"] == "derivative_basic"
        assert skill_payload["mastery"] == 0.7
        assert skill_payload["evidence_count"] == 3
        assert skill_payload["topic_id"] == "math"
        
        # Test event
        event_payload = get_hover_payload("event:e1", db_path=populated_db)
        assert event_payload["title"] == "e1"[:8]
        assert "derivatives" in event_payload["content"].lower()
        assert event_payload["event_type"] == "chat"
        assert event_payload["actor"] == "student"


class TestHoverProviderCaching:
    """Tests for hover payload caching."""
    
    def test_cache_hit(self, populated_db):
        """Test that cache is used on second request."""
        # First request (cache miss)
        payload1 = get_hover_payload("topic:math", db_path=populated_db)
        
        # Second request (cache hit)
        start_time = time.time()
        payload2 = get_hover_payload("topic:math", db_path=populated_db)
        duration = time.time() - start_time
        
        # Should be identical
        assert payload1 == payload2
        
        # Should be fast (< 10ms for cache hit)
        assert duration < 0.01
    
    def test_cache_invalidation(self, populated_db):
        """Test that cache can be invalidated."""
        # Get payload (cache it)
        payload1 = get_hover_payload("topic:math", db_path=populated_db)
        
        # Verify cache hit on second request
        start_time = time.time()
        payload_cached = get_hover_payload("topic:math", db_path=populated_db)
        cached_duration = time.time() - start_time
        
        # Should be fast (cache hit)
        assert cached_duration < 0.01
        
        # Invalidate cache
        invalidate_hover_cache("topic:math")
        
        # Next request should be fresh (cache miss, may have different timestamps)
        start_time = time.time()
        payload2 = get_hover_payload("topic:math", db_path=populated_db)
        fresh_duration = time.time() - start_time
        
        # Should be slower (cache miss, database query)
        assert fresh_duration > cached_duration
        
        # Core data should be the same (excluding timestamps)
        assert payload1["title"] == payload2["title"]
        assert payload1["type"] == payload2["type"]
        assert payload1["summary"] == payload2["summary"]
        assert payload1["event_count"] == payload2["event_count"]
    
    def test_cache_clear_all(self, populated_db):
        """Test that all cache can be cleared."""
        # Cache multiple entries
        get_hover_payload("topic:math", db_path=populated_db)
        get_hover_payload("skill:derivative_basic", db_path=populated_db)
        
        # Clear all cache
        invalidate_hover_cache()
        
        # Next requests should be fresh
        payload = get_hover_payload("topic:math", db_path=populated_db)
        assert payload is not None


class TestHoverProviderContent:
    """Tests for hover payload content accuracy."""
    
    def test_topic_event_snippet(self, populated_db):
        """Test that topic hover includes event snippet."""
        payload = get_hover_payload("topic:math", db_path=populated_db)
        
        assert payload["event_snippet"] is not None
        assert "content" in payload["event_snippet"]
        assert "actor" in payload["event_snippet"]
        assert "created_at" in payload["event_snippet"]
        assert "derivatives" in payload["event_snippet"]["content"].lower()
    
    def test_skill_event_snippet(self, populated_db):
        """Test that skill hover includes event snippet."""
        payload = get_hover_payload("skill:derivative_basic", db_path=populated_db)
        
        assert payload["event_snippet"] is not None
        assert "content" in payload["event_snippet"]
        assert "derivatives" in payload["event_snippet"]["content"].lower()
    
    def test_content_truncation(self, populated_db):
        """Test that content is properly truncated."""
        # Event content should be truncated to 500 chars
        payload = get_hover_payload("event:e1", db_path=populated_db)
        
        assert len(payload["content"]) <= 500
    
    def test_statistics_included(self, populated_db):
        """Test that statistics are included in payload."""
        topic_payload = get_hover_payload("topic:math", db_path=populated_db)
        assert "statistics" in topic_payload
        assert "created_at" in topic_payload["statistics"]
        assert "updated_at" in topic_payload["statistics"]
        
        skill_payload = get_hover_payload("skill:derivative_basic", db_path=populated_db)
        assert "statistics" in skill_payload
        assert "created_at" in skill_payload["statistics"]
        assert "updated_at" in skill_payload["statistics"]
        
        event_payload = get_hover_payload("event:e1", db_path=populated_db)
        assert "statistics" in event_payload
        assert "content_length" in event_payload["statistics"]


class TestHoverProviderErrorHandling:
    """Tests for error handling."""
    
    def test_invalid_node_id_format(self, populated_db):
        """Test that invalid node ID format raises error."""
        with pytest.raises(ValueError, match="Invalid node ID format"):
            get_hover_payload("invalid", db_path=populated_db)
    
    def test_unknown_node_type(self, populated_db):
        """Test that unknown node type raises error."""
        with pytest.raises(ValueError, match="Unknown node type"):
            get_hover_payload("unknown:test", db_path=populated_db)
    
    def test_nonexistent_topic(self, populated_db):
        """Test that nonexistent topic raises error."""
        with pytest.raises(ValueError, match="Topic not found"):
            get_hover_payload("topic:nonexistent", db_path=populated_db)
    
    def test_nonexistent_skill(self, populated_db):
        """Test that nonexistent skill raises error."""
        with pytest.raises(ValueError, match="Skill not found"):
            get_hover_payload("skill:nonexistent", db_path=populated_db)
    
    def test_nonexistent_event(self, populated_db):
        """Test that nonexistent event raises error."""
        with pytest.raises(ValueError, match="Event not found"):
            get_hover_payload("event:nonexistent", db_path=populated_db)


class TestHoverProviderPerformance:
    """Tests for hover provider performance."""
    
    def test_hover_latency_single_node(self, populated_db):
        """Test that single hover request is fast."""
        start_time = time.time()
        payload = get_hover_payload("topic:math", db_path=populated_db)
        duration = time.time() - start_time
        
        assert payload is not None
        # Should be fast (< 100ms for single node)
        assert duration < 0.1
    
    def test_hover_latency_multiple_nodes(self, populated_db):
        """Test that multiple hover requests are fast."""
        node_ids = [
            "topic:math",
            "skill:derivative_basic",
            "event:e1",
        ]
        
        start_time = time.time()
        for node_id in node_ids:
            payload = get_hover_payload(node_id, db_path=populated_db)
            assert payload is not None
        duration = time.time() - start_time
        
        # Should be fast (< 300ms for 3 nodes)
        assert duration < 0.3

