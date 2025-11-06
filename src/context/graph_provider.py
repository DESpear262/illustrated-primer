"""
Graph provider for AI Tutor Proof of Concept.

Provides DAG JSON generation from database for knowledge tree visualization.
Supports filtering by scope, depth, and relation type.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List, Set
from pathlib import Path
from collections import defaultdict

import networkx as nx

from src.config import DB_PATH
from src.storage.db import Database
from src.storage.queries import (
    get_topics_by_parent,
    get_skills_by_topic,
    get_events_by_topic,
    get_events_by_skill,
)


def _get_topic_descendants(
    topic_id: str,
    max_depth: Optional[int],
    current_depth: int,
    visited: Set[str],
    db: Database,
) -> Set[str]:
    """
    Get all descendant topic IDs recursively.
    
    Args:
        topic_id: Starting topic ID
        max_depth: Maximum depth to traverse (None for unlimited)
        current_depth: Current depth in traversal
        visited: Set of visited topic IDs to prevent cycles
        db: Database connection
        
    Returns:
        Set of descendant topic IDs including the starting topic
    """
    if topic_id in visited:
        return set()
    
    if max_depth is not None and current_depth > max_depth:
        return set()  # Don't include this topic if we've exceeded max depth
    
    visited.add(topic_id)
    descendants = {topic_id}
    
    # Get child topics
    cursor = db.conn.cursor()
    cursor.execute(
        "SELECT topic_id FROM topics WHERE parent_topic_id = ?",
        (topic_id,)
    )
    child_rows = cursor.fetchall()
    
    for row in child_rows:
        child_id = row[0]
        child_descendants = _get_topic_descendants(
            child_id,
            max_depth,
            current_depth + 1,
            visited,
            db,
        )
        descendants.update(child_descendants)
    
    return descendants


def get_graph_json(
    scope: Optional[str] = None,
    depth: Optional[int] = None,
    relation: Optional[str] = None,
    include_events: bool = False,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Get DAG JSON from database for knowledge tree visualization.
    
    Returns graph in Cytoscape.js format with nodes and edges.
    Nodes represent topics and skills; edges represent relationships.
    
    Args:
        scope: Topic ID to filter by (includes all descendants if depth allows)
        depth: Maximum depth of topic hierarchy to include (None for unlimited)
        relation: Relationship type filter ("direct", "all", "parent-child", "belongs-to")
        include_events: Whether to include event nodes (default: False)
        db_path: Path to database file (defaults to config.DB_PATH)
        
    Returns:
        Dictionary with "nodes" and "edges" lists in Cytoscape.js format
        
    Example:
        {
            "nodes": [
                {"data": {"id": "topic:math", "type": "topic", "label": "Math"}},
                {"data": {"id": "skill:derivative", "type": "skill", "label": "Derivative"}},
            ],
            "edges": [
                {"data": {"id": "e1", "source": "topic:math", "target": "skill:derivative", "type": "belongs-to"}},
            ]
        }
    """
    db_path = db_path or DB_PATH
    
    with Database(db_path) as db:
        # Build networkx DAG
        G = nx.DiGraph()
        
        # Determine topic IDs to include
        topic_ids_to_include: Set[str] = set()
        
        if scope:
            # Get all descendants of scope topic
            visited = set()
            topic_ids_to_include = _get_topic_descendants(
                scope,
                depth,
                0,
                visited,
                db,
            )
        else:
            # Get all topics up to depth
            if depth is None:
                # Get all topics
                cursor = db.conn.cursor()
                cursor.execute("SELECT topic_id FROM topics")
                topic_ids_to_include = {row[0] for row in cursor.fetchall()}
            else:
                # Get root topics and traverse to depth
                root_topics = get_topics_by_parent(None, db_path=db_path)
                visited = set()
                for root_topic in root_topics:
                    descendants = _get_topic_descendants(
                        root_topic.topic_id,
                        depth,
                        0,
                        visited,
                        db,
                    )
                    topic_ids_to_include.update(descendants)
        
        # Add topic nodes
        cursor = db.conn.cursor()
        if topic_ids_to_include:
            placeholders = ",".join("?" * len(topic_ids_to_include))
            cursor.execute(
                f"SELECT * FROM topics WHERE topic_id IN ({placeholders})",
                list(topic_ids_to_include)
            )
        else:
            cursor.execute("SELECT * FROM topics")
        
        topic_rows = cursor.fetchall()
        
        for row in topic_rows:
            topic = db._row_to_topic_summary(row)
            node_id = f"topic:{topic.topic_id}"
            
            # Add topic node
            G.add_node(
                node_id,
                type="topic",
                label=topic.topic_id,
                summary=topic.summary,
                event_count=topic.event_count,
                last_event_at=topic.last_event_at.isoformat() if topic.last_event_at else None,
            )
            
            # Add parent-child edge if parent exists and is in scope
            if topic.parent_topic_id:
                parent_node_id = f"topic:{topic.parent_topic_id}"
                if parent_node_id in G or not scope:  # Include if parent is in graph or no scope filter
                    if relation is None or relation in ("all", "parent-child"):
                        G.add_edge(
                            parent_node_id,
                            node_id,
                            type="parent-child",
                            label="parent-of",
                        )
        
        # Add skill nodes and edges
        for topic_id in topic_ids_to_include:
            skills = get_skills_by_topic(topic_id, db_path=db_path)
            
            for skill in skills:
                skill_node_id = f"skill:{skill.skill_id}"
                topic_node_id = f"topic:{topic_id}"
                
                # Add skill node
                G.add_node(
                    skill_node_id,
                    type="skill",
                    label=skill.skill_id,
                    mastery=skill.p_mastery,
                    evidence_count=skill.evidence_count,
                    last_evidence_at=skill.last_evidence_at.isoformat() if skill.last_evidence_at else None,
                )
                
                # Add topic-skill edge
                if topic_node_id in G:
                    if relation is None or relation in ("all", "belongs-to"):
                        G.add_edge(
                            topic_node_id,
                            skill_node_id,
                            type="belongs-to",
                            label="has-skill",
                        )
        
        # Optionally add event nodes
        if include_events:
            # Get events for included topics/skills
            event_ids_added = set()
            
            for topic_id in topic_ids_to_include:
                events = get_events_by_topic(topic_id, limit=10, db_path=db_path)
                
                for event in events:
                    if event.event_id in event_ids_added:
                        continue
                    event_ids_added.add(event.event_id)
                    
                    event_node_id = f"event:{event.event_id}"
                    
                    # Add event node
                    G.add_node(
                        event_node_id,
                        type="event",
                        label=event.event_id[:8],  # Short ID for display
                        content=event.content[:100],  # Truncated content
                        event_type=event.event_type,
                        actor=event.actor,
                        created_at=event.created_at.isoformat(),
                    )
                    
                    # Add topic-event edge
                    topic_node_id = f"topic:{topic_id}"
                    if topic_node_id in G:
                        if relation is None or relation in ("all", "evidence"):
                            G.add_edge(
                                topic_node_id,
                                event_node_id,
                                type="evidence",
                                label="has-event",
                            )
            
            # Add skill-event edges
            for topic_id in topic_ids_to_include:
                skills = get_skills_by_topic(topic_id, db_path=db_path)
                
                for skill in skills:
                    events = get_events_by_skill(skill.skill_id, limit=5, db_path=db_path)
                    
                    for event in events:
                        if event.event_id in event_ids_added:
                            continue
                        event_ids_added.add(event.event_id)
                        
                        event_node_id = f"event:{event.event_id}"
                        skill_node_id = f"skill:{skill.skill_id}"
                        
                        # Add event node if not already added
                        if event_node_id not in G:
                            G.add_node(
                                event_node_id,
                                type="event",
                                label=event.event_id[:8],
                                content=event.content[:100],
                                event_type=event.event_type,
                                actor=event.actor,
                                created_at=event.created_at.isoformat(),
                            )
                        
                        # Add skill-event edge
                        if skill_node_id in G:
                            if relation is None or relation in ("all", "evidence"):
                                G.add_edge(
                                    skill_node_id,
                                    event_node_id,
                                    type="evidence",
                                    label="has-evidence",
                                )
        
        # Convert to Cytoscape.js format
        nodes = []
        edges = []
        
        for node_id, data in G.nodes(data=True):
            node_data = {
                "id": node_id,
                "type": data.get("type", "unknown"),
                "label": data.get("label", node_id),
            }
            
            # Add type-specific data
            if data.get("type") == "topic":
                node_data["summary"] = data.get("summary", "")
                node_data["event_count"] = data.get("event_count", 0)
                node_data["last_event_at"] = data.get("last_event_at")
            elif data.get("type") == "skill":
                node_data["mastery"] = data.get("mastery", 0.0)
                node_data["evidence_count"] = data.get("evidence_count", 0)
                node_data["last_evidence_at"] = data.get("last_evidence_at")
            elif data.get("type") == "event":
                node_data["content"] = data.get("content", "")
                node_data["event_type"] = data.get("event_type", "")
                node_data["actor"] = data.get("actor", "")
                node_data["created_at"] = data.get("created_at")
            
            nodes.append({"data": node_data})
        
        edge_id_counter = 1
        for source, target, data in G.edges(data=True):
            edge_data = {
                "id": f"e{edge_id_counter}",
                "source": source,
                "target": target,
                "type": data.get("type", "unknown"),
                "label": data.get("label", ""),
            }
            edges.append({"data": edge_data})
            edge_id_counter += 1
        
        return {
            "nodes": nodes,
            "edges": edges,
        }

