"""
Unit tests for interface common models.

Tests Pydantic model validation, serialization, and round-trip safety.
Also validates that facade outputs match model schemas.
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from src.interface_common.models import (
    GraphNode,
    GraphEdge,
    HoverPayload,
    TopicHoverPayload,
    SkillHoverPayload,
    EventHoverPayload,
    EventSnippet,
    HoverStatistics,
    ChatMessage,
    CommandResult,
)


class TestGraphNode:
    """Tests for GraphNode model."""
    
    def test_topic_node_creation(self):
        """Test creating a topic node."""
        node = GraphNode(
            id="topic:math",
            type="topic",
            label="Math",
            summary="Mathematics fundamentals",
            event_count=5,
            last_event_at="2024-01-15T10:30:00Z",
        )
        
        assert node.id == "topic:math"
        assert node.type == "topic"
        assert node.label == "Math"
        assert node.summary == "Mathematics fundamentals"
        assert node.event_count == 5
        assert node.last_event_at == "2024-01-15T10:30:00Z"
    
    def test_skill_node_creation(self):
        """Test creating a skill node."""
        node = GraphNode(
            id="skill:derivative",
            type="skill",
            label="Derivative",
            mastery=0.7,
            evidence_count=3,
            last_evidence_at="2024-01-15T10:30:00Z",
        )
        
        assert node.id == "skill:derivative"
        assert node.type == "skill"
        assert node.mastery == 0.7
        assert node.evidence_count == 3
    
    def test_event_node_creation(self):
        """Test creating an event node."""
        node = GraphNode(
            id="event:abc123",
            type="event",
            label="Event 1",
            content="Event content",
            event_type="chat",
            actor="student",
            created_at="2024-01-15T10:30:00Z",
        )
        
        assert node.id == "event:abc123"
        assert node.type == "event"
        assert node.content == "Event content"
        assert node.event_type == "chat"
        assert node.actor == "student"
    
    def test_node_serialization(self):
        """Test node serialization to dict."""
        node = GraphNode(
            id="topic:math",
            type="topic",
            label="Math",
            summary="Mathematics fundamentals",
        )
        
        data = node.model_dump()
        assert data["id"] == "topic:math"
        assert data["type"] == "topic"
        assert data["label"] == "Math"
        assert data["summary"] == "Mathematics fundamentals"
    
    def test_node_deserialization(self):
        """Test node deserialization from dict."""
        data = {
            "id": "topic:math",
            "type": "topic",
            "label": "Math",
            "summary": "Mathematics fundamentals",
            "event_count": 5,
        }
        
        node = GraphNode.model_validate(data)
        assert node.id == "topic:math"
        assert node.type == "topic"
        assert node.summary == "Mathematics fundamentals"
        assert node.event_count == 5
    
    def test_node_round_trip(self):
        """Test round-trip serialization."""
        node = GraphNode(
            id="skill:derivative",
            type="skill",
            label="Derivative",
            mastery=0.7,
        )
        
        data = node.model_dump()
        node2 = GraphNode.model_validate(data)
        
        assert node2.id == node.id
        assert node2.type == node.type
        assert node2.mastery == node.mastery
    
    def test_node_validation_fails_invalid_type(self):
        """Test that invalid node type raises validation error."""
        with pytest.raises(Exception):  # Pydantic validation error
            GraphNode(
                id="topic:math",
                type="invalid",  # Invalid type
                label="Math",
            )
    
    def test_node_validation_fails_invalid_mastery(self):
        """Test that invalid mastery value raises validation error."""
        with pytest.raises(Exception):  # Pydantic validation error
            GraphNode(
                id="skill:derivative",
                type="skill",
                label="Derivative",
                mastery=1.5,  # Invalid: > 1.0
            )


class TestGraphEdge:
    """Tests for GraphEdge model."""
    
    def test_edge_creation(self):
        """Test creating an edge."""
        edge = GraphEdge(
            id="e1",
            source="topic:math",
            target="skill:derivative",
            type="belongs-to",
            label="has-skill",
        )
        
        assert edge.id == "e1"
        assert edge.source == "topic:math"
        assert edge.target == "skill:derivative"
        assert edge.type == "belongs-to"
        assert edge.label == "has-skill"
    
    def test_edge_serialization(self):
        """Test edge serialization to dict."""
        edge = GraphEdge(
            id="e1",
            source="topic:math",
            target="skill:derivative",
            type="belongs-to",
            label="has-skill",
        )
        
        data = edge.model_dump()
        assert data["id"] == "e1"
        assert data["source"] == "topic:math"
        assert data["target"] == "skill:derivative"
    
    def test_edge_round_trip(self):
        """Test round-trip serialization."""
        edge = GraphEdge(
            id="e1",
            source="topic:math",
            target="skill:derivative",
            type="belongs-to",
            label="has-skill",
        )
        
        data = edge.model_dump()
        edge2 = GraphEdge.model_validate(data)
        
        assert edge2.id == edge.id
        assert edge2.source == edge.source
        assert edge2.target == edge.target


class TestHoverPayload:
    """Tests for HoverPayload models."""
    
    def test_topic_hover_payload_creation(self):
        """Test creating a topic hover payload."""
        payload = TopicHoverPayload(
            title="math",
            type="topic",
            summary="Mathematics fundamentals",
            event_count=5,
            last_event_at="2024-01-15T10:30:00Z",
            open_questions=["What is calculus?"],
            event_snippet=EventSnippet(
                content="Student learned derivatives",
                actor="student",
                created_at="2024-01-15T10:30:00Z",
            ),
            statistics=HoverStatistics(
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-15T10:30:00Z",
            ),
        )
        
        assert payload.title == "math"
        assert payload.type == "topic"
        assert payload.summary == "Mathematics fundamentals"
        assert payload.event_count == 5
        assert len(payload.open_questions) == 1
    
    def test_skill_hover_payload_creation(self):
        """Test creating a skill hover payload."""
        payload = SkillHoverPayload(
            title="derivative",
            type="skill",
            mastery=0.7,
            evidence_count=3,
            last_evidence_at="2024-01-15T10:30:00Z",
            topic_id="math",
            statistics=HoverStatistics(
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-15T10:30:00Z",
            ),
        )
        
        assert payload.title == "derivative"
        assert payload.type == "skill"
        assert payload.mastery == 0.7
        assert payload.evidence_count == 3
    
    def test_event_hover_payload_creation(self):
        """Test creating an event hover payload."""
        payload = EventHoverPayload(
            title="e1",
            type="event",
            content="Event content",
            event_type="chat",
            actor="student",
            topics=["math"],
            skills=["derivative"],
            created_at="2024-01-15T10:30:00Z",
            statistics=HoverStatistics(
                content_length=100,
            ),
        )
        
        assert payload.title == "e1"
        assert payload.type == "event"
        assert payload.content == "Event content"
        assert payload.event_type == "chat"
        assert len(payload.topics) == 1
    
    def test_hover_payload_serialization(self):
        """Test hover payload serialization."""
        payload = TopicHoverPayload(
            title="math",
            type="topic",
            summary="Mathematics fundamentals",
            event_count=5,
            statistics=HoverStatistics(),
        )
        
        data = payload.model_dump()
        assert data["title"] == "math"
        assert data["type"] == "topic"
        assert data["summary"] == "Mathematics fundamentals"
    
    def test_hover_payload_round_trip(self):
        """Test round-trip serialization."""
        payload = SkillHoverPayload(
            title="derivative",
            type="skill",
            mastery=0.7,
            evidence_count=3,
            statistics=HoverStatistics(),
        )
        
        data = payload.model_dump()
        payload2 = SkillHoverPayload.model_validate(data)
        
        assert payload2.title == payload.title
        assert payload2.mastery == payload.mastery
        assert payload2.evidence_count == payload.evidence_count
    
    def test_hover_payload_validation_fails_invalid_mastery(self):
        """Test that invalid mastery value raises validation error."""
        with pytest.raises(Exception):  # Pydantic validation error
            SkillHoverPayload(
                title="derivative",
                type="skill",
                mastery=1.5,  # Invalid: > 1.0
                evidence_count=3,
                statistics=HoverStatistics(),
            )


class TestChatMessage:
    """Tests for ChatMessage model."""
    
    def test_chat_message_creation(self):
        """Test creating a chat message."""
        message = ChatMessage(
            role="student",
            content="Hello, tutor!",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            session_id="session_123",
            event_id="event_456",
        )
        
        assert message.role == "student"
        assert message.content == "Hello, tutor!"
        assert message.session_id == "session_123"
        assert message.event_id == "event_456"
    
    def test_chat_message_serialization(self):
        """Test chat message serialization."""
        message = ChatMessage(
            role="tutor",
            content="Hello, student!",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            session_id="session_123",
        )
        
        data = message.model_dump()
        assert data["role"] == "tutor"
        assert data["content"] == "Hello, student!"
        assert "timestamp" in data
        assert data["session_id"] == "session_123"
    
    def test_chat_message_round_trip(self):
        """Test round-trip serialization."""
        message = ChatMessage(
            role="student",
            content="Hello!",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            session_id="session_123",
        )
        
        data = message.model_dump()
        message2 = ChatMessage.model_validate(data)
        
        assert message2.role == message.role
        assert message2.content == message.content
        assert message2.session_id == message.session_id


class TestCommandResult:
    """Tests for CommandResult model."""
    
    def test_command_result_success(self):
        """Test creating a successful command result."""
        result = CommandResult(
            success=True,
            result={"status": "ok", "message": "Operation completed"},
            duration_seconds=0.5,
        )
        
        assert result.success is True
        assert result.result is not None
        assert result.result["status"] == "ok"
        assert result.error is None
        assert result.duration_seconds == 0.5
    
    def test_command_result_failure(self):
        """Test creating a failed command result."""
        result = CommandResult(
            success=False,
            error={
                "error_type": "DatabaseError",
                "message": "Database connection failed",
                "details": {},
            },
            duration_seconds=0.1,
        )
        
        assert result.success is False
        assert result.result is None
        assert result.error is not None
        assert result.error["error_type"] == "DatabaseError"
    
    def test_command_result_from_facade_response_success(self):
        """Test creating CommandResult from successful facade response."""
        facade_response = {
            "success": True,
            "result": {"status": "ok"},
            "duration_seconds": 0.5,
        }
        
        result = CommandResult.from_facade_response(facade_response)
        
        assert result.success is True
        assert result.result is not None
        assert result.error is None
        assert result.duration_seconds == 0.5
    
    def test_command_result_from_facade_response_failure(self):
        """Test creating CommandResult from failed facade response."""
        facade_response = {
            "success": False,
            "error": {
                "error_type": "TimeoutError",
                "message": "Operation timed out",
                "details": {"timeout_seconds": 30},
            },
            "duration_seconds": 30.0,
        }
        
        result = CommandResult.from_facade_response(facade_response)
        
        assert result.success is False
        assert result.result is None
        assert result.error is not None
        assert result.error["error_type"] == "TimeoutError"
        assert result.duration_seconds == 30.0
    
    def test_command_result_serialization(self):
        """Test command result serialization."""
        result = CommandResult(
            success=True,
            result={"status": "ok"},
            duration_seconds=0.5,
        )
        
        data = result.model_dump()
        assert data["success"] is True
        assert data["result"] is not None
        assert data["duration_seconds"] == 0.5
    
    def test_command_result_round_trip(self):
        """Test round-trip serialization."""
        result = CommandResult(
            success=True,
            result={"status": "ok"},
            duration_seconds=0.5,
        )
        
        data = result.model_dump()
        result2 = CommandResult.model_validate(data)
        
        assert result2.success == result.success
        assert result2.result == result.result
        assert result2.duration_seconds == result.duration_seconds


class TestModelValidation:
    """Tests for validating facade outputs against models."""
    
    def test_graph_provider_output_matches_graph_node(self):
        """Test that graph_provider output can be validated against GraphNode."""
        # Simulate graph_provider output
        node_data = {
            "id": "topic:math",
            "type": "topic",
            "label": "Math",
            "summary": "Mathematics fundamentals",
            "event_count": 5,
            "last_event_at": "2024-01-15T10:30:00Z",
        }
        
        # Should validate successfully
        node = GraphNode.model_validate(node_data)
        assert node.id == "topic:math"
        assert node.type == "topic"
    
    def test_graph_provider_output_matches_graph_edge(self):
        """Test that graph_provider output can be validated against GraphEdge."""
        # Simulate graph_provider output
        edge_data = {
            "id": "e1",
            "source": "topic:math",
            "target": "skill:derivative",
            "type": "belongs-to",
            "label": "has-skill",
        }
        
        # Should validate successfully
        edge = GraphEdge.model_validate(edge_data)
        assert edge.id == "e1"
        assert edge.source == "topic:math"
    
    def test_hover_provider_output_matches_hover_payload(self):
        """Test that hover_provider output can be validated against HoverPayload."""
        # Simulate hover_provider output for topic
        topic_payload_data = {
            "title": "math",
            "type": "topic",
            "summary": "Mathematics fundamentals",
            "event_count": 5,
            "last_event_at": "2024-01-15T10:30:00Z",
            "open_questions": ["What is calculus?"],
            "event_snippet": {
                "content": "Student learned derivatives",
                "actor": "student",
                "created_at": "2024-01-15T10:30:00Z",
            },
            "statistics": {
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            },
        }
        
        # Should validate successfully
        payload = TopicHoverPayload.model_validate(topic_payload_data)
        assert payload.title == "math"
        assert payload.type == "topic"
        
        # Simulate hover_provider output for skill
        skill_payload_data = {
            "title": "derivative",
            "type": "skill",
            "mastery": 0.7,
            "evidence_count": 3,
            "last_evidence_at": "2024-01-15T10:30:00Z",
            "topic_id": "math",
            "statistics": {
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            },
        }
        
        # Should validate successfully
        skill_payload = SkillHoverPayload.model_validate(skill_payload_data)
        assert skill_payload.title == "derivative"
        assert skill_payload.mastery == 0.7
    
    def test_facade_output_matches_command_result(self):
        """Test that facade output can be validated against CommandResult."""
        # Simulate facade output
        facade_output = {
            "success": True,
            "result": {"status": "ok", "message": "Operation completed"},
            "duration_seconds": 0.5,
        }
        
        # Should validate successfully
        result = CommandResult.from_facade_response(facade_output)
        assert result.success is True
        assert result.result is not None
        assert result.duration_seconds == 0.5

