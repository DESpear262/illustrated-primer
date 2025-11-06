"""
Integration tests for graph and hover providers.

Tests combined FAISS + SQLite queries and performance requirements.
"""

import pytest
import time
from pathlib import Path

from src.context.graph_provider import get_graph_json
from src.context.hover_provider import get_hover_payload
from src.storage.db import Database, initialize_database
from src.models.base import Event, SkillState, TopicSummary


@pytest.fixture
def db_path(tmp_path) -> Path:
    """Fixture for a temporary database path."""
    path = tmp_path / "test_integration.db"
    initialize_database(path)
    return path


@pytest.fixture
def large_populated_db(db_path) -> Path:
    """Fixture with large dataset (500+ nodes) for performance testing."""
    with Database(db_path) as db:
        # Create 50 root topics
        for i in range(50):
            topic = TopicSummary(
                topic_id=f"topic_{i}",
                summary=f"Topic {i} summary",
                event_count=10,
            )
            db.insert_topic_summary(topic)
            
            # Create 5 child topics per root
            for j in range(5):
                child_topic = TopicSummary(
                    topic_id=f"topic_{i}_child_{j}",
                    parent_topic_id=f"topic_{i}",
                    summary=f"Child topic {i}-{j} summary",
                    event_count=5,
                )
                db.insert_topic_summary(child_topic)
                
                # Create 2 skills per child topic
                for k in range(2):
                    skill = SkillState(
                        skill_id=f"skill_{i}_{j}_{k}",
                        topic_id=f"topic_{i}_child_{j}",
                        p_mastery=0.5 + (k * 0.1),
                        evidence_count=3,
                    )
                    db.insert_skill_state(skill)
                    
                    # Create 1 event per skill
                    event = Event(
                        event_id=f"event_{i}_{j}_{k}",
                        content=f"Event content for skill {i}-{j}-{k}",
                        event_type="chat",
                        actor="student",
                        topics=[f"topic_{i}_child_{j}"],
                        skills=[f"skill_{i}_{j}_{k}"],
                    )
                    db.insert_event(event)
    
    return db_path


class TestGraphHoverIntegration:
    """Integration tests for graph and hover providers."""
    
    def test_graph_and_hover_combined(self, large_populated_db):
        """Test that graph and hover work together."""
        # Get graph
        graph = get_graph_json(db_path=large_populated_db)
        
        assert len(graph["nodes"]) > 0
        assert len(graph["edges"]) > 0
        
        # Get hover for first topic node
        topic_nodes = [n for n in graph["nodes"] if n["data"]["type"] == "topic"]
        assert len(topic_nodes) > 0
        
        first_topic_id = topic_nodes[0]["data"]["id"]
        hover_payload = get_hover_payload(first_topic_id, db_path=large_populated_db)
        
        assert hover_payload is not None
        assert hover_payload["type"] == "topic"
        assert hover_payload["title"] in first_topic_id
    
    def test_hover_latency_requirement(self, large_populated_db):
        """Test that hover latency is <200ms for 500 nodes."""
        # Get graph with many nodes
        graph = get_graph_json(db_path=large_populated_db)
        
        # Get all node IDs
        node_ids = [node["data"]["id"] for node in graph["nodes"]]
        
        # Limit to 500 nodes for test
        node_ids = node_ids[:500]
        
        # Measure hover latency for all nodes
        start_time = time.time()
        for node_id in node_ids:
            payload = get_hover_payload(node_id, db_path=large_populated_db)
            assert payload is not None
        total_duration = time.time() - start_time
        
        # Average latency per node should be < 200ms
        avg_latency = total_duration / len(node_ids)
        assert avg_latency < 0.2, f"Average latency {avg_latency:.3f}s exceeds 200ms requirement"
    
    def test_graph_with_events_integration(self, large_populated_db):
        """Test graph generation with events included."""
        # Get graph with events
        graph = get_graph_json(include_events=True, db_path=large_populated_db)
        
        # Should have event nodes
        event_nodes = [n for n in graph["nodes"] if n["data"]["type"] == "event"]
        assert len(event_nodes) > 0
        
        # Should have evidence edges
        evidence_edges = [e for e in graph["edges"] if e["data"]["type"] == "evidence"]
        assert len(evidence_edges) > 0
        
        # Test hover for event node
        first_event_id = event_nodes[0]["data"]["id"]
        hover_payload = get_hover_payload(first_event_id, db_path=large_populated_db)
        
        assert hover_payload is not None
        assert hover_payload["type"] == "event"
    
    def test_filtered_graph_and_hover(self, large_populated_db):
        """Test that filtered graph works with hover."""
        # Get filtered graph (scope and depth)
        graph = get_graph_json(
            scope="topic_0",
            depth=2,
            db_path=large_populated_db,
        )
        
        assert len(graph["nodes"]) > 0
        
        # Get hover for nodes in filtered graph
        for node in graph["nodes"][:10]:  # Test first 10 nodes
            node_id = node["data"]["id"]
            hover_payload = get_hover_payload(node_id, db_path=large_populated_db)
            
            assert hover_payload is not None
            assert hover_payload["type"] == node["data"]["type"]
    
    def test_cache_performance_improvement(self, large_populated_db):
        """Test that caching improves performance."""
        node_id = "topic:topic_0"
        
        # First request (cache miss)
        start_time = time.time()
        payload1 = get_hover_payload(node_id, db_path=large_populated_db)
        first_duration = time.time() - start_time
        
        # Second request (cache hit)
        start_time = time.time()
        payload2 = get_hover_payload(node_id, db_path=large_populated_db)
        second_duration = time.time() - start_time
        
        # Should be identical
        assert payload1 == payload2
        
        # Cache hit should be faster
        assert second_duration < first_duration
    
    def test_graph_json_schema_validation(self, large_populated_db):
        """Test that graph JSON matches expected schema."""
        graph = get_graph_json(db_path=large_populated_db)
        
        # Validate structure
        assert "nodes" in graph
        assert "edges" in graph
        
        # Validate nodes
        for node in graph["nodes"]:
            assert "data" in node
            data = node["data"]
            assert "id" in data
            assert "type" in data
            assert "label" in data
            
            # Type-specific validation
            if data["type"] == "topic":
                assert "summary" in data
                assert "event_count" in data
            elif data["type"] == "skill":
                assert "mastery" in data
                assert "evidence_count" in data
        
        # Validate edges
        for edge in graph["edges"]:
            assert "data" in edge
            data = edge["data"]
            assert "id" in data
            assert "source" in data
            assert "target" in data
            assert "type" in data
            
            # Verify source and target exist in nodes
            source_exists = any(n["data"]["id"] == data["source"] for n in graph["nodes"])
            target_exists = any(n["data"]["id"] == data["target"] for n in graph["nodes"])
            assert source_exists, f"Edge source {data['source']} not found in nodes"
            assert target_exists, f"Edge target {data['target']} not found in nodes"

