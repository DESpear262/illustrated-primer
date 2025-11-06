"""
Unit tests for interface common models.

Tests Pydantic models for GUI interfaces, ensuring consistent
data models and round-trip serialization safety.
"""

from __future__ import annotations

import pytest
import json
from datetime import datetime
from typing import Dict, Any

from src.interface_common.models import (
    GraphNode,
    GraphEdge,
    HoverPayload,
    ChatMessage,
    CommandResult,
    graph_node_to_json,
    graph_node_from_json,
    graph_nodes_to_json,
    graph_nodes_from_json,
    graph_edge_to_json,
    graph_edge_from_json,
    graph_edges_to_json,
    graph_edges_from_json,
    hover_payload_to_json,
    hover_payload_from_json,
    chat_message_to_json,
    chat_message_from_json,
    chat_messages_to_json,
    chat_messages_from_json,
    command_result_to_json,
    command_result_from_json,
)


class TestGraphNode:
    """Tests for GraphNode model."""
    
    def test_graph_node_topic_creation(self):
        """Test creating a topic GraphNode."""
        node = GraphNode(
            id="math",
            type="topic",
            label="Mathematics",
            summary="Math summary",
            event_count=10,
        )
        
        assert node.id == "math"
        assert node.type == "topic"
        assert node.label == "Mathematics"
        assert node.summary == "Math summary"
        assert node.event_count == 10
        assert node.p_mastery is None
    
    def test_graph_node_skill_creation(self):
        """Test creating a skill GraphNode."""
        node = GraphNode(
            id="arithmetic",
            type="skill",
            label="Arithmetic",
            p_mastery=0.8,
            topic_id="math",
        )
        
        assert node.id == "arithmetic"
        assert node.type == "skill"
        assert node.label == "Arithmetic"
        assert node.p_mastery == 0.8
        assert node.topic_id == "math"
        assert node.summary is None
    
    def test_graph_node_validation(self):
        """Test GraphNode validation."""
        # Valid node
        node = GraphNode(id="test", type="topic", label="Test")
        assert node.id == "test"
        
        # Invalid type
        with pytest.raises(Exception):  # Pydantic validation error
            GraphNode(id="test", type="invalid", label="Test")
        
        # Invalid p_mastery range
        with pytest.raises(Exception):  # Pydantic validation error
            GraphNode(id="test", type="skill", label="Test", p_mastery=1.5)
    
    def test_graph_node_serialization_round_trip(self):
        """Test that GraphNode serialization is round-trip safe."""
        node = GraphNode(
            id="math",
            type="topic",
            label="Mathematics",
            summary="Math summary",
            event_count=10,
            metadata={"key": "value"},
        )
        
        # Serialize
        json_data = graph_node_to_json(node)
        
        # Deserialize
        node2 = graph_node_from_json(json_data)
        
        # Should be equal
        assert node2.id == node.id
        assert node2.type == node.type
        assert node2.label == node.label
        assert node2.summary == node.summary
        assert node2.event_count == node.event_count
        assert node2.metadata == node.metadata
    
    def test_graph_nodes_list_serialization(self):
        """Test serialization of list of GraphNodes."""
        nodes = [
            GraphNode(id="math", type="topic", label="Mathematics"),
            GraphNode(id="arithmetic", type="skill", label="Arithmetic", p_mastery=0.8),
        ]
        
        # Serialize
        json_data = graph_nodes_to_json(nodes)
        
        # Deserialize
        nodes2 = graph_nodes_from_json(json_data)
        
        # Should be equal
        assert len(nodes2) == len(nodes)
        assert nodes2[0].id == nodes[0].id
        assert nodes2[1].id == nodes[1].id


class TestGraphEdge:
    """Tests for GraphEdge model."""
    
    def test_graph_edge_creation(self):
        """Test creating a GraphEdge."""
        edge = GraphEdge(
            id="math-calculus",
            source="math",
            target="calculus",
            type="parent-child",
        )
        
        assert edge.id == "math-calculus"
        assert edge.source == "math"
        assert edge.target == "calculus"
        assert edge.type == "parent-child"
    
    def test_graph_edge_validation(self):
        """Test GraphEdge validation."""
        # Valid edge
        edge = GraphEdge(id="test", source="a", target="b", type="parent-child")
        assert edge.id == "test"
        
        # Invalid type
        with pytest.raises(Exception):  # Pydantic validation error
            GraphEdge(id="test", source="a", target="b", type="invalid")
    
    def test_graph_edge_serialization_round_trip(self):
        """Test that GraphEdge serialization is round-trip safe."""
        edge = GraphEdge(
            id="math-calculus",
            source="math",
            target="calculus",
            type="parent-child",
            metadata={"key": "value"},
        )
        
        # Serialize
        json_data = graph_edge_to_json(edge)
        
        # Deserialize
        edge2 = graph_edge_from_json(json_data)
        
        # Should be equal
        assert edge2.id == edge.id
        assert edge2.source == edge.source
        assert edge2.target == edge.target
        assert edge2.type == edge.type
        assert edge2.metadata == edge.metadata
    
    def test_graph_edges_list_serialization(self):
        """Test serialization of list of GraphEdges."""
        edges = [
            GraphEdge(id="e1", source="a", target="b", type="parent-child"),
            GraphEdge(id="e2", source="c", target="d", type="topic-skill"),
        ]
        
        # Serialize
        json_data = graph_edges_to_json(edges)
        
        # Deserialize
        edges2 = graph_edges_from_json(json_data)
        
        # Should be equal
        assert len(edges2) == len(edges)
        assert edges2[0].id == edges[0].id
        assert edges2[1].id == edges[1].id


class TestHoverPayload:
    """Tests for HoverPayload model."""
    
    def test_hover_payload_topic_creation(self):
        """Test creating a topic HoverPayload."""
        payload = HoverPayload(
            title="math",
            node_type="topic",
            summary="Math summary",
            event_count=10,
            average_mastery=0.7,
            child_skills_count=5,
        )
        
        assert payload.title == "math"
        assert payload.node_type == "topic"
        assert payload.summary == "Math summary"
        assert payload.event_count == 10
        assert payload.average_mastery == 0.7
        assert payload.child_skills_count == 5
        assert payload.p_mastery is None
    
    def test_hover_payload_skill_creation(self):
        """Test creating a skill HoverPayload."""
        payload = HoverPayload(
            title="arithmetic",
            node_type="skill",
            p_mastery=0.8,
            last_evidence_at=datetime.utcnow(),
            evidence_count=5,
            topic_id="math",
            recent_event_snippet={
                "content": "Test event",
                "created_at": datetime.utcnow().isoformat(),
                "event_type": "chat",
            },
        )
        
        assert payload.title == "arithmetic"
        assert payload.node_type == "skill"
        assert payload.p_mastery == 0.8
        assert payload.evidence_count == 5
        assert payload.topic_id == "math"
        assert payload.summary is None
    
    def test_hover_payload_validation(self):
        """Test HoverPayload validation."""
        # Valid payload
        payload = HoverPayload(title="test", node_type="topic")
        assert payload.title == "test"
        
        # Invalid node_type
        with pytest.raises(Exception):  # Pydantic validation error
            HoverPayload(title="test", node_type="invalid")
        
        # Invalid p_mastery range
        with pytest.raises(Exception):  # Pydantic validation error
            HoverPayload(title="test", node_type="skill", p_mastery=1.5)
    
    def test_hover_payload_serialization_round_trip(self):
        """Test that HoverPayload serialization is round-trip safe."""
        payload = HoverPayload(
            title="math",
            node_type="topic",
            summary="Math summary",
            event_count=10,
            last_event_at=datetime.utcnow(),
            average_mastery=0.7,
            child_skills_count=5,
            open_questions=["Question 1", "Question 2"],
        )
        
        # Serialize
        json_data = hover_payload_to_json(payload)
        
        # Deserialize
        payload2 = hover_payload_from_json(json_data)
        
        # Should be equal
        assert payload2.title == payload.title
        assert payload2.node_type == payload.node_type
        assert payload2.summary == payload.summary
        assert payload2.event_count == payload.event_count
        assert payload2.average_mastery == payload.average_mastery
        assert payload2.child_skills_count == payload.child_skills_count
        assert payload2.open_questions == payload.open_questions


class TestChatMessage:
    """Tests for ChatMessage model."""
    
    def test_chat_message_creation(self):
        """Test creating a ChatMessage."""
        message = ChatMessage(
            role="user",
            content="Hello",
            session_id="session-123",
            turn_index=1,
        )
        
        assert message.role == "user"
        assert message.content == "Hello"
        assert message.session_id == "session-123"
        assert message.turn_index == 1
        assert message.context_used is None
    
    def test_chat_message_validation(self):
        """Test ChatMessage validation."""
        # Valid message
        message = ChatMessage(role="user", content="Test", session_id="s1", turn_index=1)
        assert message.role == "user"
        
        # Invalid role
        with pytest.raises(Exception):  # Pydantic validation error
            ChatMessage(role="invalid", content="Test", session_id="s1", turn_index=1)
    
    def test_chat_message_serialization_round_trip(self):
        """Test that ChatMessage serialization is round-trip safe."""
        message = ChatMessage(
            role="tutor",
            content="Hello, how can I help?",
            session_id="session-123",
            turn_index=1,
            context_used=["chunk-1", "chunk-2"],
            metadata={"key": "value"},
        )
        
        # Serialize
        json_data = chat_message_to_json(message)
        
        # Deserialize
        message2 = chat_message_from_json(json_data)
        
        # Should be equal
        assert message2.role == message.role
        assert message2.content == message.content
        assert message2.session_id == message.session_id
        assert message2.turn_index == message.turn_index
        assert message2.context_used == message.context_used
        assert message2.metadata == message.metadata
    
    def test_chat_messages_list_serialization(self):
        """Test serialization of list of ChatMessages."""
        messages = [
            ChatMessage(role="user", content="Hello", session_id="s1", turn_index=1),
            ChatMessage(role="tutor", content="Hi there", session_id="s1", turn_index=2),
        ]
        
        # Serialize
        json_data = chat_messages_to_json(messages)
        
        # Deserialize
        messages2 = chat_messages_from_json(json_data)
        
        # Should be equal
        assert len(messages2) == len(messages)
        assert messages2[0].role == messages[0].role
        assert messages2[1].role == messages[1].role


class TestCommandResult:
    """Tests for CommandResult model."""
    
    def test_command_result_success_creation(self):
        """Test creating a successful CommandResult."""
        result = CommandResult(
            command_name="db.check",
            success=True,
            result_data={"status": "ok", "tables": 5},
            execution_time=0.5,
        )
        
        assert result.command_name == "db.check"
        assert result.success is True
        assert result.result_data == {"status": "ok", "tables": 5}
        assert result.error_message is None
        assert result.execution_time == 0.5
    
    def test_command_result_error_creation(self):
        """Test creating a failed CommandResult."""
        result = CommandResult(
            command_name="db.check",
            success=False,
            error_message="Database not found",
            error_details={"operation": "db.check"},
            execution_time=0.1,
        )
        
        assert result.command_name == "db.check"
        assert result.success is False
        assert result.error_message == "Database not found"
        assert result.result_data is None
        assert result.execution_time == 0.1
    
    def test_command_result_validation(self):
        """Test CommandResult validation."""
        # Valid result
        result = CommandResult(command_name="test", success=True)
        assert result.command_name == "test"
        
        # Invalid execution_time
        with pytest.raises(Exception):  # Pydantic validation error
            CommandResult(command_name="test", success=True, execution_time=-1.0)
    
    def test_command_result_serialization_round_trip(self):
        """Test that CommandResult serialization is round-trip safe."""
        result = CommandResult(
            command_name="chat.turn",
            success=True,
            result_data={
                "session_id": "session-123",
                "turn_index": 1,
                "user_message": "Hello",
                "ai_reply": "Hi there",
            },
            execution_time=1.5,
            metadata={"key": "value"},
        )
        
        # Serialize
        json_data = command_result_to_json(result)
        
        # Deserialize
        result2 = command_result_from_json(json_data)
        
        # Should be equal
        assert result2.command_name == result.command_name
        assert result2.success == result.success
        assert result2.result_data == result.result_data
        assert result2.execution_time == result.execution_time
        assert result2.metadata == result.metadata


class TestModelValidation:
    """Tests for model validation with CLI outputs and GUI responses."""
    
    def test_graph_node_from_graph_provider_output(self):
        """Test that GraphNode can be created from graph_provider output."""
        # Simulate graph_provider output
        graph_data = {
            "nodes": [
                {
                    "data": {
                        "id": "math",
                        "type": "topic",
                        "label": "Mathematics",
                        "summary": "Math summary",
                        "event_count": 10,
                    }
                }
            ],
            "edges": []
        }
        
        # Convert to GraphNode
        node_data = graph_data["nodes"][0]["data"]
        node = GraphNode(**node_data)
        
        assert node.id == "math"
        assert node.type == "topic"
        assert node.label == "Mathematics"
        assert node.summary == "Math summary"
        assert node.event_count == 10
    
    def test_hover_payload_from_hover_provider_output(self):
        """Test that HoverPayload can be created from hover_provider output."""
        # Simulate hover_provider output
        payload_data = {
            "title": "math",
            "summary": "Math summary",
            "event_count": 10,
            "last_event_at": datetime.utcnow().isoformat(),
            "average_mastery": 0.7,
            "child_skills_count": 5,
            "open_questions": ["Question 1"],
        }
        
        # Add node_type (required by model)
        payload_data["node_type"] = "topic"
        
        # Convert to HoverPayload
        payload = HoverPayload(**payload_data)
        
        assert payload.title == "math"
        assert payload.node_type == "topic"
        assert payload.summary == "Math summary"
        assert payload.event_count == 10
        assert payload.average_mastery == 0.7
    
    def test_chat_message_from_facade_output(self):
        """Test that ChatMessage can be created from facade output."""
        # Simulate facade output
        message_data = {
            "session_id": "session-123",
            "turn_index": 1,
            "user_message": "Hello",
            "ai_reply": "Hi there",
        }
        
        # Convert to ChatMessages (user and tutor)
        user_message = ChatMessage(
            role="user",
            content=message_data["user_message"],
            session_id=message_data["session_id"],
            turn_index=message_data["turn_index"],
        )
        
        tutor_message = ChatMessage(
            role="tutor",
            content=message_data["ai_reply"],
            session_id=message_data["session_id"],
            turn_index=message_data["turn_index"] + 1,
        )
        
        assert user_message.role == "user"
        assert user_message.content == "Hello"
        assert tutor_message.role == "tutor"
        assert tutor_message.content == "Hi there"
    
    def test_command_result_from_facade_output(self):
        """Test that CommandResult can be created from facade output."""
        # Simulate facade output
        result_data = {
            "status": "ok",
            "tables": 5,
            "event_count": 10,
        }
        
        # Convert to CommandResult
        result = CommandResult(
            command_name="db.check",
            success=True,
            result_data=result_data,
            execution_time=0.5,
        )
        
        assert result.command_name == "db.check"
        assert result.success is True
        assert result.result_data == result_data
        assert result.execution_time == 0.5
    
    def test_models_validate_facade_outputs(self):
        """Test that models validate facade method outputs."""
        # Test db_check output
        db_check_output = {
            "status": "ok",
            "tables": ["events", "topics", "skills"],
            "event_count": 10,
        }
        
        result = CommandResult(
            command_name="db.check",
            success=True,
            result_data=db_check_output,
        )
        
        assert result.success is True
        assert result.result_data["status"] == "ok"
        
        # Test chat_turn output
        chat_turn_output = {
            "session_id": "session-123",
            "turn_index": 1,
            "user_message": "Hello",
            "ai_reply": "Hi there",
            "context_used": ["chunk-1"],
        }
        
        user_msg = ChatMessage(
            role="user",
            content=chat_turn_output["user_message"],
            session_id=chat_turn_output["session_id"],
            turn_index=chat_turn_output["turn_index"],
            context_used=chat_turn_output["context_used"],
        )
        
        assert user_msg.role == "user"
        assert user_msg.context_used == ["chunk-1"]

