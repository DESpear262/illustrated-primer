"""
Unit and integration tests for graph provider.

Tests DAG JSON generation, filtering, and format validation.
"""

import pytest
from pathlib import Path

from src.context.graph_provider import get_graph_json
from src.storage.db import Database, initialize_database
from src.models.base import Event, SkillState, TopicSummary


@pytest.fixture
def db_path(tmp_path) -> Path:
    """Fixture for a temporary database path."""
    path = tmp_path / "test_graph.db"
    initialize_database(path)
    return path


@pytest.fixture
def populated_db(db_path) -> Path:
    """Fixture with sample topics, skills, and events."""
    with Database(db_path) as db:
        # Create root topic
        root_topic = TopicSummary(
            topic_id="math",
            summary="Mathematics fundamentals",
        )
        db.insert_topic_summary(root_topic)
        
        # Create child topic
        child_topic = TopicSummary(
            topic_id="calculus",
            parent_topic_id="math",
            summary="Calculus basics",
        )
        db.insert_topic_summary(child_topic)
        
        # Create grandchild topic
        grandchild_topic = TopicSummary(
            topic_id="derivatives",
            parent_topic_id="calculus",
            summary="Derivatives",
        )
        db.insert_topic_summary(grandchild_topic)
        
        # Create skills
        skill1 = SkillState(
            skill_id="derivative_basic",
            topic_id="derivatives",
            p_mastery=0.7,
        )
        db.insert_skill_state(skill1)
        
        skill2 = SkillState(
            skill_id="derivative_chain",
            topic_id="derivatives",
            p_mastery=0.5,
        )
        db.insert_skill_state(skill2)
        
        # Create events
        event1 = Event(
            event_id="e1",
            content="Student learned basic derivatives",
            event_type="chat",
            actor="student",
            topics=["derivatives"],
            skills=["derivative_basic"],
        )
        db.insert_event(event1)
        
        event2 = Event(
            event_id="e2",
            content="Student practiced chain rule",
            event_type="chat",
            actor="student",
            topics=["derivatives"],
            skills=["derivative_chain"],
        )
        db.insert_event(event2)
    
    return db_path


class TestGraphProviderFormat:
    """Tests for graph JSON format validation."""
    
    def test_graph_json_structure(self, populated_db):
        """Test that graph JSON has correct structure."""
        graph = get_graph_json(db_path=populated_db)
        
        assert "nodes" in graph
        assert "edges" in graph
        assert isinstance(graph["nodes"], list)
        assert isinstance(graph["edges"], list)
    
    def test_node_format(self, populated_db):
        """Test that nodes match Cytoscape.js format."""
        graph = get_graph_json(db_path=populated_db)
        
        for node in graph["nodes"]:
            assert "data" in node
            node_data = node["data"]
            assert "id" in node_data
            assert "type" in node_data
            assert "label" in node_data
            assert node_data["type"] in ("topic", "skill", "event")
    
    def test_edge_format(self, populated_db):
        """Test that edges match Cytoscape.js format."""
        graph = get_graph_json(db_path=populated_db)
        
        for edge in graph["edges"]:
            assert "data" in edge
            edge_data = edge["data"]
            assert "id" in edge_data
            assert "source" in edge_data
            assert "target" in edge_data
            assert "type" in edge_data
    
    def test_node_ids_format(self, populated_db):
        """Test that node IDs use correct format (type:id)."""
        graph = get_graph_json(db_path=populated_db)
        
        for node in graph["nodes"]:
            node_id = node["data"]["id"]
            assert ":" in node_id
            node_type, node_identifier = node_id.split(":", 1)
            assert node_type in ("topic", "skill", "event")
            assert len(node_identifier) > 0


class TestGraphProviderFiltering:
    """Tests for graph filtering (scope, depth, relation)."""
    
    def test_scope_filter(self, populated_db):
        """Test filtering by scope (topic ID)."""
        # Get graph for calculus topic only
        graph = get_graph_json(scope="calculus", db_path=populated_db)
        
        # Should include calculus and its descendants (derivatives)
        node_ids = {node["data"]["id"] for node in graph["nodes"]}
        assert "topic:calculus" in node_ids
        assert "topic:derivatives" in node_ids
        assert "topic:math" not in node_ids  # Parent not included
    
    def test_depth_filter(self, populated_db):
        """Test filtering by depth."""
        # Get graph with depth=0 (root only)
        graph_depth_0 = get_graph_json(depth=0, db_path=populated_db)
        node_ids_depth_0 = {node["data"]["id"] for node in graph_depth_0["nodes"]}
        
        # Should include math (root) but not descendants
        assert "topic:math" in node_ids_depth_0
        assert "topic:calculus" not in node_ids_depth_0
        assert "topic:derivatives" not in node_ids_depth_0
        
        # Get graph with depth=1 (root and first level children)
        graph_depth_1 = get_graph_json(depth=1, db_path=populated_db)
        node_ids_depth_1 = {node["data"]["id"] for node in graph_depth_1["nodes"]}
        
        # Should include math and calculus, but not derivatives
        assert "topic:math" in node_ids_depth_1
        assert "topic:calculus" in node_ids_depth_1
        assert "topic:derivatives" not in node_ids_depth_1
        
        # Get graph with depth=2 (root, children, and grandchildren)
        graph_depth_2 = get_graph_json(depth=2, db_path=populated_db)
        node_ids_depth_2 = {node["data"]["id"] for node in graph_depth_2["nodes"]}
        
        # Should include math, calculus, and derivatives
        assert "topic:math" in node_ids_depth_2
        assert "topic:calculus" in node_ids_depth_2
        assert "topic:derivatives" in node_ids_depth_2
    
    def test_scope_and_depth_combined(self, populated_db):
        """Test combining scope and depth filters."""
        # Get graph for calculus with depth=0 (only calculus itself)
        graph = get_graph_json(scope="calculus", depth=0, db_path=populated_db)
        
        node_ids = {node["data"]["id"] for node in graph["nodes"]}
        assert "topic:calculus" in node_ids
        assert "topic:derivatives" not in node_ids  # Depth limit
        
        # Get graph for calculus with depth=1 (calculus and its children)
        graph_depth_1 = get_graph_json(scope="calculus", depth=1, db_path=populated_db)
        node_ids_depth_1 = {node["data"]["id"] for node in graph_depth_1["nodes"]}
        assert "topic:calculus" in node_ids_depth_1
        assert "topic:derivatives" in node_ids_depth_1  # Within depth limit
    
    def test_relation_filter_parent_child(self, populated_db):
        """Test filtering by relation type (parent-child only)."""
        graph = get_graph_json(relation="parent-child", db_path=populated_db)
        
        # Should only have parent-child edges
        for edge in graph["edges"]:
            assert edge["data"]["type"] == "parent-child"
    
    def test_relation_filter_belongs_to(self, populated_db):
        """Test filtering by relation type (belongs-to only)."""
        graph = get_graph_json(relation="belongs-to", db_path=populated_db)
        
        # Should only have belongs-to edges
        for edge in graph["edges"]:
            assert edge["data"]["type"] == "belongs-to"
    
    def test_include_events(self, populated_db):
        """Test including event nodes."""
        graph = get_graph_json(include_events=True, db_path=populated_db)
        
        # Should include event nodes
        node_types = {node["data"]["type"] for node in graph["nodes"]}
        assert "event" in node_types
        
        # Should have event edges
        edge_types = {edge["data"]["type"] for edge in graph["edges"]}
        assert "evidence" in edge_types


class TestGraphProviderContent:
    """Tests for graph content accuracy."""
    
    def test_topic_nodes_have_summary(self, populated_db):
        """Test that topic nodes include summary."""
        graph = get_graph_json(db_path=populated_db)
        
        topic_nodes = [n for n in graph["nodes"] if n["data"]["type"] == "topic"]
        assert len(topic_nodes) > 0
        
        for node in topic_nodes:
            assert "summary" in node["data"]
            assert len(node["data"]["summary"]) > 0
    
    def test_skill_nodes_have_mastery(self, populated_db):
        """Test that skill nodes include mastery."""
        graph = get_graph_json(db_path=populated_db)
        
        skill_nodes = [n for n in graph["nodes"] if n["data"]["type"] == "skill"]
        assert len(skill_nodes) > 0
        
        for node in skill_nodes:
            assert "mastery" in node["data"]
            assert 0.0 <= node["data"]["mastery"] <= 1.0
    
    def test_parent_child_edges(self, populated_db):
        """Test that parent-child edges are correctly created."""
        graph = get_graph_json(db_path=populated_db)
        
        # Find parent-child edges
        parent_child_edges = [
            e for e in graph["edges"]
            if e["data"]["type"] == "parent-child"
        ]
        
        assert len(parent_child_edges) >= 2  # math->calculus, calculus->derivatives
        
        # Verify edge sources and targets
        edge_map = {
            e["data"]["source"]: e["data"]["target"]
            for e in parent_child_edges
        }
        
        assert "topic:math" in edge_map
        assert edge_map["topic:math"] == "topic:calculus"
        assert "topic:calculus" in edge_map
        assert edge_map["topic:calculus"] == "topic:derivatives"
    
    def test_topic_skill_edges(self, populated_db):
        """Test that topic-skill edges are correctly created."""
        graph = get_graph_json(db_path=populated_db)
        
        # Find belongs-to edges
        belongs_to_edges = [
            e for e in graph["edges"]
            if e["data"]["type"] == "belongs-to"
        ]
        
        assert len(belongs_to_edges) >= 2  # derivatives->skill1, derivatives->skill2
        
        # Verify edges connect topics to skills
        for edge in belongs_to_edges:
            source = edge["data"]["source"]
            target = edge["data"]["target"]
            assert source.startswith("topic:")
            assert target.startswith("skill:")


class TestGraphProviderEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_database(self, db_path):
        """Test graph generation with empty database."""
        graph = get_graph_json(db_path=db_path)
        
        assert graph["nodes"] == []
        assert graph["edges"] == []
    
    def test_invalid_scope(self, populated_db):
        """Test graph generation with invalid scope."""
        # Should return empty graph for non-existent topic
        graph = get_graph_json(scope="nonexistent", db_path=populated_db)
        
        assert len(graph["nodes"]) == 0
        assert len(graph["edges"]) == 0
    
    def test_depth_zero(self, populated_db):
        """Test graph generation with depth=0."""
        graph = get_graph_json(depth=0, db_path=populated_db)
        
        # Should only include root topics (depth 0)
        node_ids = {node["data"]["id"] for node in graph["nodes"]}
        assert "topic:math" in node_ids
        assert "topic:calculus" not in node_ids

