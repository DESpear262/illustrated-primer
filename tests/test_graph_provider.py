"""
Unit tests for graph provider.

Tests DAG JSON generation, networkx traversal, and filtering.
"""

from __future__ import annotations

import pytest
from pathlib import Path
from uuid import uuid4

from src.context.graph_provider import get_graph, _build_dag
from src.storage.db import Database, initialize_database
from src.models.base import TopicSummary, SkillState
from src.config import DB_PATH


@pytest.fixture
def test_db(tmp_path):
    """Create a test database with sample data."""
    db_path = tmp_path / "test.db"
    initialize_database(db_path)
    
    with Database(db_path) as db:
        # Create root topic
        root_topic = TopicSummary(
            topic_id="math",
            parent_topic_id=None,
            summary="Mathematics",
            event_count=10,
        )
        db.insert_topic_summary(root_topic)
        
        # Create child topic
        child_topic = TopicSummary(
            topic_id="calculus",
            parent_topic_id="math",
            summary="Calculus",
            event_count=5,
        )
        db.insert_topic_summary(child_topic)
        
        # Create skill for root topic
        root_skill = SkillState(
            skill_id="arithmetic",
            topic_id="math",
            p_mastery=0.8,
            evidence_count=5,
        )
        db.insert_skill_state(root_skill)
        
        # Create skill for child topic
        child_skill = SkillState(
            skill_id="derivatives",
            topic_id="calculus",
            p_mastery=0.6,
            evidence_count=3,
        )
        db.insert_skill_state(child_skill)
    
    return db_path


class TestGraphProvider:
    """Tests for graph provider."""
    
    def test_get_graph_all_scope(self, test_db):
        """Test get_graph with scope='all'."""
        result = get_graph(scope="all", db_path=test_db)
        
        assert "nodes" in result
        assert "edges" in result
        assert isinstance(result["nodes"], list)
        assert isinstance(result["edges"], list)
        
        # Should have 2 topics and 2 skills
        topic_nodes = [n for n in result["nodes"] if n["data"]["type"] == "topic"]
        skill_nodes = [n for n in result["nodes"] if n["data"]["type"] == "skill"]
        
        assert len(topic_nodes) == 2
        assert len(skill_nodes) == 2
    
    def test_get_graph_root_scope(self, test_db):
        """Test get_graph with scope='root'."""
        result = get_graph(scope="root", db_path=test_db)
        
        # Should only have root topics
        topic_nodes = [n for n in result["nodes"] if n["data"]["type"] == "topic"]
        assert len(topic_nodes) == 1
        assert topic_nodes[0]["data"]["id"] == "math"
    
    def test_get_graph_topic_scope(self, test_db):
        """Test get_graph with scope='topic:<id>'."""
        result = get_graph(scope="topic:calculus", db_path=test_db)
        
        # Should have calculus topic and its skill
        node_ids = [n["data"]["id"] for n in result["nodes"]]
        assert "calculus" in node_ids
        assert "derivatives" in node_ids
    
    def test_get_graph_depth_filter(self, test_db):
        """Test get_graph with depth filter."""
        result = get_graph(scope="all", depth=0, db_path=test_db)
        
        # Depth 0 should only include root topics
        topic_nodes = [n for n in result["nodes"] if n["data"]["type"] == "topic"]
        assert len(topic_nodes) == 1
        assert topic_nodes[0]["data"]["id"] == "math"
    
    def test_get_graph_relation_filter_parent_child(self, test_db):
        """Test get_graph with relation='parent-child'."""
        result = get_graph(scope="all", relation="parent-child", db_path=test_db)
        
        # Should only have topic→topic edges
        edges = result["edges"]
        assert all(e["data"]["type"] == "parent-child" for e in edges)
        
        # Should have math→calculus edge
        edge_ids = [e["data"]["id"] for e in edges]
        assert "math-calculus" in edge_ids
    
    def test_get_graph_relation_filter_topic_skill(self, test_db):
        """Test get_graph with relation='topic-skill'."""
        result = get_graph(scope="all", relation="topic-skill", db_path=test_db)
        
        # Should only have topic→skill edges
        edges = result["edges"]
        assert all(e["data"]["type"] == "topic-skill" for e in edges)
        
        # Should have math→arithmetic and calculus→derivatives edges
        edge_ids = [e["data"]["id"] for e in edges]
        assert "math-arithmetic" in edge_ids
        assert "calculus-derivatives" in edge_ids
    
    def test_get_graph_cytoscape_format(self, test_db):
        """Test that graph JSON matches Cytoscape.js format."""
        result = get_graph(scope="all", db_path=test_db)
        
        # Check nodes format
        for node in result["nodes"]:
            assert "data" in node
            assert "id" in node["data"]
            assert "type" in node["data"]
        
        # Check edges format
        for edge in result["edges"]:
            assert "data" in edge
            assert "id" in edge["data"]
            assert "source" in edge["data"]
            assert "target" in edge["data"]
            assert "type" in edge["data"]
    
    def test_get_graph_invalid_scope(self, test_db):
        """Test get_graph with invalid scope."""
        with pytest.raises(ValueError, match="Invalid scope"):
            get_graph(scope="invalid", db_path=test_db)
    
    def test_get_graph_invalid_relation(self, test_db):
        """Test get_graph with invalid relation."""
        with pytest.raises(ValueError, match="Invalid relation"):
            get_graph(relation="invalid", db_path=test_db)
    
    def test_get_graph_empty_database(self, tmp_path):
        """Test get_graph with empty database."""
        db_path = tmp_path / "empty.db"
        initialize_database(db_path)
        
        result = get_graph(scope="all", db_path=db_path)
        
        assert result["nodes"] == []
        assert result["edges"] == []
    
    def test_build_dag(self, test_db):
        """Test _build_dag function."""
        import networkx as nx
        
        G = _build_dag(test_db)
        
        assert isinstance(G, nx.DiGraph)
        assert len(G.nodes()) == 4  # 2 topics + 2 skills
        assert len(G.edges()) == 3  # 1 parent-child + 2 topic-skill
        
        # Check node types
        node_types = {G.nodes[n].get("type") for n in G.nodes()}
        assert "topic" in node_types
        assert "skill" in node_types
    
    def test_get_graph_node_data(self, test_db):
        """Test that node data includes required fields."""
        result = get_graph(scope="all", db_path=test_db)
        
        # Find topic node
        topic_node = next(n for n in result["nodes"] if n["data"]["id"] == "math")
        
        assert "label" in topic_node["data"]
        assert "summary" in topic_node["data"]
        assert "event_count" in topic_node["data"]
        
        # Find skill node
        skill_node = next(n for n in result["nodes"] if n["data"]["id"] == "arithmetic")
        
        assert "label" in skill_node["data"]
        assert "p_mastery" in skill_node["data"]
        assert "topic_id" in skill_node["data"]

