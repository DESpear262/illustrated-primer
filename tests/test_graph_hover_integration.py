"""
Integration tests for graph and hover providers.

Tests FAISS + SQLite combined queries, hover latency, and real-world scenarios.
"""

from __future__ import annotations

import time
import pytest
from pathlib import Path
from uuid import uuid4
from datetime import datetime

from src.context.graph_provider import get_graph
from src.context.hover_provider import get_hover_payload, clear_cache
from src.storage.db import Database, initialize_database
from src.models.base import TopicSummary, SkillState, Event
from src.config import DB_PATH


@pytest.fixture
def large_test_db(tmp_path):
    """Create a test database with many nodes for performance testing."""
    db_path = tmp_path / "large_test.db"
    initialize_database(db_path)
    
    with Database(db_path) as db:
        # Create 50 topics in a hierarchy
        topics = []
        for i in range(50):
            parent_id = f"topic_{i // 10}" if i >= 10 else None
            topic = TopicSummary(
                topic_id=f"topic_{i}",
                parent_topic_id=parent_id,
                summary=f"Topic {i} summary",
                event_count=i * 2,
                last_event_at=datetime.utcnow(),
            )
            db.insert_topic_summary(topic)
            topics.append(topic)
        
        # Create 450 skills (9 per topic)
        skills = []
        for i in range(50):
            for j in range(9):
                skill = SkillState(
                    skill_id=f"skill_{i}_{j}",
                    topic_id=f"topic_{i}",
                    p_mastery=0.5 + (j * 0.05),
                    evidence_count=j,
                    last_evidence_at=datetime.utcnow(),
                )
                db.insert_skill_state(skill)
                skills.append(skill)
        
        # Create events for skills
        for skill in skills[:100]:  # Create events for first 100 skills
            event = Event(
                event_id=str(uuid4()),
                content=f"Event for {skill.skill_id}: This is a test event.",
                event_type="chat",
                actor="student",
                skills=[skill.skill_id],
                created_at=datetime.utcnow(),
            )
            db.insert_event(event)
    
    return db_path


@pytest.fixture
def test_db_with_events(tmp_path):
    """Create a test database with topics, skills, and events."""
    db_path = tmp_path / "test.db"
    initialize_database(db_path)
    
    with Database(db_path) as db:
        # Create topic
        topic = TopicSummary(
            topic_id="math",
            parent_topic_id=None,
            summary="Mathematics",
            event_count=5,
            last_event_at=datetime.utcnow(),
        )
        db.insert_topic_summary(topic)
        
        # Create skill
        skill = SkillState(
            skill_id="arithmetic",
            topic_id="math",
            p_mastery=0.8,
            evidence_count=3,
            last_evidence_at=datetime.utcnow(),
        )
        db.insert_skill_state(skill)
        
        # Create events
        for i in range(3):
            event = Event(
                event_id=str(uuid4()),
                content=f"Event {i}: This is a test event about arithmetic.",
                event_type="chat",
                actor="student",
                topics=["math"],
                skills=["arithmetic"],
                created_at=datetime.utcnow(),
            )
            db.insert_event(event)
    
    return db_path


class TestGraphHoverIntegration:
    """Integration tests for graph and hover providers."""
    
    def test_graph_json_format_matches_schema(self, test_db_with_events):
        """Test that graph JSON format matches schema (nodes/edges)."""
        result = get_graph(scope="all", db_path=test_db_with_events)
        
        # Check structure
        assert "nodes" in result
        assert "edges" in result
        assert isinstance(result["nodes"], list)
        assert isinstance(result["edges"], list)
        
        # Check nodes have required fields
        for node in result["nodes"]:
            assert "data" in node
            assert "id" in node["data"]
            assert "type" in node["data"]
        
        # Check edges have required fields
        for edge in result["edges"]:
            assert "data" in edge
            assert "id" in edge["data"]
            assert "source" in edge["data"]
            assert "target" in edge["data"]
            assert "type" in edge["data"]
    
    def test_hover_payload_includes_required_fields(self, test_db_with_events):
        """Test that hover payload includes title, mastery, and last evidence."""
        # Test topic hover
        topic_payload = get_hover_payload("math", "topic", db_path=test_db_with_events)
        
        assert "title" in topic_payload
        assert "average_mastery" in topic_payload
        assert "last_event_at" in topic_payload
        
        # Test skill hover
        skill_payload = get_hover_payload("arithmetic", "skill", db_path=test_db_with_events)
        
        assert "title" in skill_payload
        assert "p_mastery" in skill_payload
        assert "last_evidence_at" in skill_payload
        assert "recent_event_snippet" in skill_payload
    
    def test_depth_filtering_truncates_output(self, large_test_db):
        """Test that depth filtering correctly truncates output."""
        # Get graph with depth 0 (only root topics)
        result_depth_0 = get_graph(scope="all", depth=0, db_path=large_test_db)
        
        # Get graph with depth 1 (root topics + first level)
        result_depth_1 = get_graph(scope="all", depth=1, db_path=large_test_db)
        
        # Get graph with unlimited depth
        result_unlimited = get_graph(scope="all", depth=None, db_path=large_test_db)
        
        # Depth 0 should have fewer nodes than depth 1
        assert len(result_depth_0["nodes"]) < len(result_depth_1["nodes"])
        
        # Depth 1 should have fewer nodes than unlimited
        assert len(result_depth_1["nodes"]) < len(result_unlimited["nodes"])
    
    def test_hover_latency_performance(self, large_test_db):
        """Test that hover latency <200ms for 500 nodes."""
        clear_cache()
        
        # Get all nodes from graph
        graph = get_graph(scope="all", db_path=large_test_db)
        nodes = graph["nodes"]
        
        # Test hover latency for first 50 nodes (representative sample)
        test_nodes = nodes[:50]
        
        total_time = 0.0
        for node in test_nodes:
            node_id = node["data"]["id"]
            node_type = node["data"]["type"]
            
            start_time = time.time()
            payload = get_hover_payload(node_id, node_type, db_path=large_test_db)
            elapsed = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            total_time += elapsed
            
            # Each individual hover should be fast
            assert elapsed < 200, f"Hover latency {elapsed}ms exceeds 200ms for {node_id}"
        
        # Average latency should be reasonable
        avg_latency = total_time / len(test_nodes)
        assert avg_latency < 200, f"Average hover latency {avg_latency}ms exceeds 200ms"
    
    def test_graph_with_scope_and_depth(self, large_test_db):
        """Test graph generation with different scope and depth combinations."""
        # Test root scope with depth 1
        result = get_graph(scope="root", depth=1, db_path=large_test_db)
        
        # Should only include root topics and their immediate children
        topic_nodes = [n for n in result["nodes"] if n["data"]["type"] == "topic"]
        assert len(topic_nodes) <= 10  # Root topics + first level
        
        # Test topic scope with depth 2
        result = get_graph(scope="topic:topic_0", depth=2, db_path=large_test_db)
        
        # Should include topic_0 and its descendants up to depth 2
        node_ids = [n["data"]["id"] for n in result["nodes"]]
        assert "topic_0" in node_ids
    
    def test_hover_payload_caching_performance(self, large_test_db):
        """Test that caching improves hover performance."""
        clear_cache()
        
        # First call (populates cache)
        start_time = time.time()
        payload1 = get_hover_payload("topic_0", "topic", db_path=large_test_db)
        first_call_time = (time.time() - start_time) * 1000
        
        # Second call (uses cache)
        start_time = time.time()
        payload2 = get_hover_payload("topic_0", "topic", db_path=large_test_db)
        second_call_time = (time.time() - start_time) * 1000
        
        # Cached call should be faster
        assert second_call_time < first_call_time
        assert payload1 == payload2
    
    def test_graph_relation_filtering(self, large_test_db):
        """Test graph generation with relation filtering."""
        # Get graph with only parent-child edges
        result_parent_child = get_graph(
            scope="all",
            relation="parent-child",
            db_path=large_test_db,
        )
        
        # All edges should be parent-child
        for edge in result_parent_child["edges"]:
            assert edge["data"]["type"] == "parent-child"
        
        # Get graph with only topic-skill edges
        result_topic_skill = get_graph(
            scope="all",
            relation="topic-skill",
            db_path=large_test_db,
        )
        
        # All edges should be topic-skill
        for edge in result_topic_skill["edges"]:
            assert edge["data"]["type"] == "topic-skill"
    
    def test_hover_payload_for_topic_with_many_skills(self, large_test_db):
        """Test hover payload for topic with many child skills."""
        # topic_0 should have 9 skills
        payload = get_hover_payload("topic_0", "topic", db_path=large_test_db)
        
        assert payload["child_skills_count"] == 9
        assert payload["average_mastery"] is not None
        assert 0.0 <= payload["average_mastery"] <= 1.0
    
    def test_graph_includes_all_node_types(self, test_db_with_events):
        """Test that graph includes both topics and skills."""
        result = get_graph(scope="all", db_path=test_db_with_events)
        
        node_types = {n["data"]["type"] for n in result["nodes"]}
        
        assert "topic" in node_types
        assert "skill" in node_types
    
    def test_hover_payload_recent_event_snippet(self, test_db_with_events):
        """Test that hover payload includes recent event snippet for skills."""
        payload = get_hover_payload("arithmetic", "skill", db_path=test_db_with_events)
        
        assert payload["recent_event_snippet"] is not None
        assert "content" in payload["recent_event_snippet"]
        assert "created_at" in payload["recent_event_snippet"]
        assert "event_type" in payload["recent_event_snippet"]
        
        # Content should be truncated if too long
        content = payload["recent_event_snippet"]["content"]
        assert len(content) <= 203  # 200 chars + "..."

