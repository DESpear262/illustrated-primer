"""
Integration tests for query operations.

Tests query wrappers for filtering events, skills, and topics.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4

from src.storage.db import Database, initialize_database
from src.storage.queries import (
    get_events_by_topic,
    get_events_by_time_range,
    get_events_by_skill,
    get_events_by_event_type,
    search_events_fts,
    get_skills_by_topic,
    get_skills_by_mastery_range,
    get_topics_by_parent,
    get_topic_hierarchy,
    get_recent_events,
    update_skill_state_with_evidence,
)
from src.models.base import Event, SkillState, TopicSummary


def create_test_database():
    """Create a test database with sample data."""
    db_path = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path.close()
    db_path = Path(db_path.name)
    
    initialize_database(db_path)
    
    with Database(db_path) as db:
        # Create topics
        parent_topic = TopicSummary(
            topic_id="calculus",
            summary="Introduction to calculus",
            parent_topic_id=None,
        )
        child_topic = TopicSummary(
            topic_id="derivatives",
            summary="Understanding derivatives",
            parent_topic_id="calculus",
        )
        db.insert_topic_summary(parent_topic)
        db.insert_topic_summary(child_topic)
        
        # Create skills
        skill = SkillState(
            skill_id="derivative_basic",
            p_mastery=0.6,
            topic_id="derivatives",
        )
        db.insert_skill_state(skill)
        
        # Create events
        now = datetime.utcnow()
        for i in range(5):
            event = Event(
                event_id=str(uuid4()),
                content=f"Learning about derivatives {i}",
                event_type="chat",
                actor="student",
                topics=["calculus", "derivatives"],
                skills=["derivative_basic"],
                created_at=now - timedelta(days=5-i),
            )
            db.insert_event(event)
    
    return db_path


class TestEventQueries:
    """Tests for event query operations."""
    
    def test_get_events_by_topic(self):
        """Test filtering events by topic."""
        db_path = create_test_database()
        
        try:
            events = get_events_by_topic("derivatives", db_path=db_path)
            
            assert len(events) > 0
            assert all("derivatives" in event.topics for event in events)
        finally:
            db_path.unlink()
    
    def test_get_events_by_time_range(self):
        """Test filtering events by time range."""
        db_path = create_test_database()
        
        try:
            now = datetime.utcnow()
            start_time = now - timedelta(days=3)
            end_time = now - timedelta(days=1)
            
            events = get_events_by_time_range(
                start_time=start_time,
                end_time=end_time,
                db_path=db_path,
            )
            
            assert len(events) > 0
            assert all(start_time <= event.created_at <= end_time for event in events)
        finally:
            db_path.unlink()
    
    def test_get_events_by_skill(self):
        """Test filtering events by skill."""
        db_path = create_test_database()
        
        try:
            events = get_events_by_skill("derivative_basic", db_path=db_path)
            
            assert len(events) > 0
            assert all("derivative_basic" in event.skills for event in events)
        finally:
            db_path.unlink()
    
    def test_get_events_by_event_type(self):
        """Test filtering events by event type."""
        db_path = create_test_database()
        
        try:
            events = get_events_by_event_type("chat", db_path=db_path)
            
            assert len(events) > 0
            assert all(event.event_type == "chat" for event in events)
        finally:
            db_path.unlink()
    
    def test_get_events_limit(self):
        """Test limiting number of events returned."""
        db_path = create_test_database()
        
        try:
            events = get_events_by_topic("derivatives", limit=2, db_path=db_path)
            
            assert len(events) <= 2
        finally:
            db_path.unlink()
    
    def test_search_events_fts(self):
        """Test FTS5 full-text search."""
        db_path = create_test_database()
        
        try:
            events = search_events_fts("derivatives", db_path=db_path)
            
            assert len(events) > 0
            assert all("derivatives" in event.content.lower() for event in events)
        finally:
            db_path.unlink()
    
    def test_get_recent_events(self):
        """Test getting recent events."""
        db_path = create_test_database()
        
        try:
            events = get_recent_events(days=7, db_path=db_path)
            
            assert len(events) > 0
            cutoff = datetime.utcnow() - timedelta(days=7)
            assert all(event.created_at >= cutoff for event in events)
        finally:
            db_path.unlink()


class TestSkillQueries:
    """Tests for skill query operations."""
    
    def test_get_skills_by_topic(self):
        """Test filtering skills by topic."""
        db_path = create_test_database()
        
        try:
            skills = get_skills_by_topic("derivatives", db_path=db_path)
            
            assert len(skills) > 0
            assert all(skill.topic_id == "derivatives" for skill in skills)
        finally:
            db_path.unlink()
    
    def test_get_skills_by_mastery_range(self):
        """Test filtering skills by mastery range."""
        db_path = create_test_database()
        
        try:
            skills = get_skills_by_mastery_range(
                min_mastery=0.5,
                max_mastery=0.7,
                db_path=db_path,
            )
            
            assert len(skills) > 0
            assert all(0.5 <= skill.p_mastery <= 0.7 for skill in skills)
        finally:
            db_path.unlink()


class TestTopicQueries:
    """Tests for topic query operations."""
    
    def test_get_topics_by_parent(self):
        """Test filtering topics by parent."""
        db_path = create_test_database()
        
        try:
            # Get root topics
            root_topics = get_topics_by_parent(parent_topic_id=None, db_path=db_path)
            
            assert len(root_topics) > 0
            assert all(topic.parent_topic_id is None for topic in root_topics)
            
            # Get child topics
            child_topics = get_topics_by_parent(
                parent_topic_id="calculus",
                db_path=db_path,
            )
            
            assert len(child_topics) > 0
            assert all(topic.parent_topic_id == "calculus" for topic in child_topics)
        finally:
            db_path.unlink()
    
    def test_get_topic_hierarchy(self):
        """Test getting topic hierarchy."""
        db_path = create_test_database()
        
        try:
            hierarchy = get_topic_hierarchy(db_path=db_path)
            
            assert "roots" in hierarchy
            assert len(hierarchy["roots"]) > 0
            
            # Check hierarchy structure
            root = hierarchy["roots"][0]
            assert "topic" in root
            assert "children" in root
        finally:
            db_path.unlink()


class TestSkillStateHelpers:
    """Tests for SkillState persistence helpers."""
    
    def test_update_skill_state_with_evidence(self):
        """Test updating skill state with evidence."""
        db_path = create_test_database()
        
        try:
            # Update with positive evidence
            skill = update_skill_state_with_evidence(
                "derivative_basic",
                new_evidence=True,
                db_path=db_path,
            )
            
            assert skill.evidence_count > 0
            assert skill.p_mastery > 0.6  # Should have increased
            
            # Update with negative evidence
            skill = update_skill_state_with_evidence(
                "derivative_basic",
                new_evidence=False,
                db_path=db_path,
            )
            
            assert skill.p_mastery < 1.0  # Should have decreased
            assert skill.p_mastery >= 0.0  # Should be bounded
        finally:
            db_path.unlink()

