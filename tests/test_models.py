"""
Unit tests for Pydantic models.

Tests schema validation, serialization, and model behavior.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from src.models.base import (
    Event,
    SkillState,
    TopicSummary,
    Goal,
    Commitment,
    NudgeLog,
)


class TestEvent:
    """Tests for Event model."""
    
    def test_event_creation_minimal(self):
        """Test creating an event with minimal required fields."""
        event = Event(
            event_id=str(uuid4()),
            content="Test content",
            event_type="chat",
            actor="student",
        )
        assert event.content == "Test content"
        assert event.event_type == "chat"
        assert event.actor == "student"
        assert event.topics == []
        assert event.skills == []
        assert event.metadata == {}
    
    def test_event_creation_full(self):
        """Test creating an event with all fields."""
        topics = ["calculus", "derivatives"]
        skills = ["derivative_basic"]
        metadata = {"session_id": "test_session"}
        
        event = Event(
            event_id=str(uuid4()),
            content="Test content",
            event_type="chat",
            actor="student",
            topics=topics,
            skills=skills,
            metadata=metadata,
        )
        assert event.topics == topics
        assert event.skills == skills
        assert event.metadata == metadata
    
    def test_event_validation_event_type(self):
        """Test event_type validation."""
        with pytest.raises(Exception):
            Event(
                event_id=str(uuid4()),
                content="Test",
                event_type="invalid",
                actor="student",
            )
    
    def test_event_validation_actor(self):
        """Test actor validation."""
        with pytest.raises(Exception):
            Event(
                event_id=str(uuid4()),
                content="Test",
                event_type="chat",
                actor="invalid",
            )


class TestSkillState:
    """Tests for SkillState model."""
    
    def test_skill_state_creation(self):
        """Test creating a skill state."""
        skill = SkillState(
            skill_id="test_skill",
            p_mastery=0.75,
        )
        assert skill.skill_id == "test_skill"
        assert skill.p_mastery == 0.75
        assert skill.evidence_count == 0
    
    def test_skill_state_p_mastery_bounds(self):
        """Test p_mastery bounds validation."""
        # Valid values
        SkillState(skill_id="test", p_mastery=0.0)
        SkillState(skill_id="test", p_mastery=1.0)
        SkillState(skill_id="test", p_mastery=0.5)
        
        # Invalid values
        with pytest.raises(Exception):
            SkillState(skill_id="test", p_mastery=-0.1)
        
        with pytest.raises(Exception):
            SkillState(skill_id="test", p_mastery=1.1)


class TestTopicSummary:
    """Tests for TopicSummary model."""
    
    def test_topic_summary_creation(self):
        """Test creating a topic summary."""
        topic = TopicSummary(
            topic_id="test_topic",
            summary="Test summary",
        )
        assert topic.topic_id == "test_topic"
        assert topic.summary == "Test summary"
        assert topic.open_questions == []
        assert topic.parent_topic_id is None
    
    def test_topic_summary_hierarchy(self):
        """Test hierarchical topic relationships."""
        parent = TopicSummary(
            topic_id="parent",
            summary="Parent topic",
        )
        child = TopicSummary(
            topic_id="child",
            parent_topic_id="parent",
            summary="Child topic",
        )
        assert child.parent_topic_id == "parent"


class TestGoal:
    """Tests for Goal model."""
    
    def test_goal_creation(self):
        """Test creating a goal."""
        goal = Goal(
            goal_id=str(uuid4()),
            title="Test Goal",
        )
        assert goal.title == "Test Goal"
        assert goal.status == "active"
        assert goal.topic_ids == []
        assert goal.skill_ids == []
    
    def test_goal_status_validation(self):
        """Test goal status validation."""
        goal = Goal(
            goal_id=str(uuid4()),
            title="Test",
            status="completed",
        )
        assert goal.status == "completed"
        
        with pytest.raises(Exception):
            Goal(
                goal_id=str(uuid4()),
                title="Test",
                status="invalid",
            )


class TestCommitment:
    """Tests for Commitment model."""
    
    def test_commitment_creation(self):
        """Test creating a commitment."""
        commitment = Commitment(
            commitment_id=str(uuid4()),
            description="Test commitment",
            frequency="daily",
        )
        assert commitment.description == "Test commitment"
        assert commitment.frequency == "daily"
        assert commitment.status == "active"
    
    def test_commitment_frequency_validation(self):
        """Test commitment frequency validation."""
        with pytest.raises(Exception):
            Commitment(
                commitment_id=str(uuid4()),
                description="Test",
                frequency="invalid",
            )


class TestNudgeLog:
    """Tests for NudgeLog model."""
    
    def test_nudge_log_creation(self):
        """Test creating a nudge log."""
        nudge = NudgeLog(
            nudge_id=str(uuid4()),
            nudge_type="reminder",
            message="Test message",
        )
        assert nudge.nudge_type == "reminder"
        assert nudge.message == "Test message"
        assert nudge.status == "sent"
    
    def test_nudge_log_type_validation(self):
        """Test nudge type validation."""
        with pytest.raises(Exception):
            NudgeLog(
                nudge_id=str(uuid4()),
                nudge_type="invalid",
                message="Test",
            )

