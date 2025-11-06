"""
Graph provider for AI Tutor Proof of Concept.

Provides DAG JSON generation from database for knowledge tree visualization.
Uses networkx for DAG traversal and converts to Cytoscape.js format.
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional, Set
from pathlib import Path
from datetime import datetime

import networkx as nx

from src.config import DB_PATH
from src.storage.db import Database
from src.storage.queries import (
    get_topics_by_parent,
    get_skills_by_topic,
    get_topic_hierarchy,
)
from src.models.base import TopicSummary, SkillState


def get_graph(
    scope: str = "all",
    depth: Optional[int] = None,
    relation: str = "all",
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Get DAG JSON from database in Cytoscape.js format.
    
    Args:
        scope: Graph scope - "all" (all nodes), "root" (root topics only), "topic:<id>" (subtree from topic)
        depth: Maximum depth from scope root (None for unlimited)
        relation: Edge types to include - "all", "parent-child" (topic→topic), "topic-skill" (topic→skill)
        db_path: Path to database file (defaults to config.DB_PATH)
        
    Returns:
        Dictionary with "nodes" and "edges" lists in Cytoscape.js format
        
    Raises:
        ValueError: If scope or relation is invalid
    """
    db_path = db_path or DB_PATH
    
    # Validate scope
    if scope not in ("all", "root") and not scope.startswith("topic:"):
        raise ValueError(f"Invalid scope: {scope}. Must be 'all', 'root', or 'topic:<id>'")
    
    # Validate relation
    if relation not in ("all", "parent-child", "topic-skill"):
        raise ValueError(f"Invalid relation: {relation}. Must be 'all', 'parent-child', or 'topic-skill'")
    
    # Build networkx DAG
    G = _build_dag(db_path)
    
    # Filter by scope
    if scope == "root":
        # Only root topics (nodes with no incoming edges)
        root_nodes = [n for n in G.nodes() if G.in_degree(n) == 0 and G.nodes[n].get("type") == "topic"]
        G = G.subgraph(root_nodes).copy()
    elif scope.startswith("topic:"):
        # Subtree from specific topic
        topic_id = scope.split(":", 1)[1]
        if topic_id not in G:
            return {"nodes": [], "edges": []}
        
        # Get all descendants
        descendants = set(nx.descendants(G, topic_id))
        descendants.add(topic_id)
        
        # Include skills for included topics
        for node_id in list(descendants):
            if G.nodes[node_id].get("type") == "topic":
                # Get skills for this topic
                with Database(db_path) as db:
                    skills = get_skills_by_topic(node_id, db_path)
                    for skill in skills:
                        descendants.add(skill.skill_id)
        
        G = G.subgraph(descendants).copy()
    
    # Filter by depth
    if depth is not None and depth >= 0:
        if scope == "all":
            # Find root topics
            root_nodes = [n for n in G.nodes() if G.in_degree(n) == 0 and G.nodes[n].get("type") == "topic"]
        elif scope.startswith("topic:"):
            topic_id = scope.split(":", 1)[1]
            root_nodes = [topic_id] if topic_id in G else []
        else:  # scope == "root"
            root_nodes = [n for n in G.nodes() if G.in_degree(n) == 0 and G.nodes[n].get("type") == "topic"]
        
        # BFS to get nodes within depth
        nodes_within_depth = set()
        for root in root_nodes:
            nodes_within_depth.add(root)
            if depth > 0:
                for node, dist in nx.single_source_shortest_path_length(G, root, cutoff=depth).items():
                    nodes_within_depth.add(node)
        
        G = G.subgraph(nodes_within_depth).copy()
    
    # Filter by relation
    if relation == "parent-child":
        # Only topic→topic edges
        edges_to_remove = [
            (u, v) for u, v in G.edges()
            if G.nodes[u].get("type") != "topic" or G.nodes[v].get("type") != "topic"
        ]
        G.remove_edges_from(edges_to_remove)
    elif relation == "topic-skill":
        # Only topic→skill edges
        edges_to_remove = [
            (u, v) for u, v in G.edges()
            if G.nodes[u].get("type") != "topic" or G.nodes[v].get("type") != "skill"
        ]
        G.remove_edges_from(edges_to_remove)
    # relation == "all" - keep all edges
    
    # Convert to Cytoscape.js format
    nodes = []
    edges = []
    
    for node_id in G.nodes():
        node_data = G.nodes[node_id]
        node_type = node_data.get("type", "unknown")
        
        # Build node data
        cytoscape_node = {
            "data": {
                "id": node_id,
                "type": node_type,
            }
        }
        
        # Add type-specific data
        if node_type == "topic":
            cytoscape_node["data"]["label"] = node_data.get("topic_id", node_id)
            cytoscape_node["data"]["summary"] = node_data.get("summary", "")
            cytoscape_node["data"]["event_count"] = node_data.get("event_count", 0)
        elif node_type == "skill":
            cytoscape_node["data"]["label"] = node_data.get("skill_id", node_id)
            cytoscape_node["data"]["p_mastery"] = node_data.get("p_mastery", 0.0)
            cytoscape_node["data"]["topic_id"] = node_data.get("topic_id", "")
        
        nodes.append(cytoscape_node)
    
    for u, v in G.edges():
        edge_data = G.edges[u, v]
        edge_type = edge_data.get("type", "unknown")
        
        cytoscape_edge = {
            "data": {
                "id": f"{u}-{v}",
                "source": u,
                "target": v,
                "type": edge_type,
            }
        }
        
        edges.append(cytoscape_edge)
    
    return {
        "nodes": nodes,
        "edges": edges,
    }


def _build_dag(db_path: Path) -> nx.DiGraph:
    """
    Build networkx DAG from database.
    
    Args:
        db_path: Path to database file
        
    Returns:
        NetworkX DiGraph with topics and skills as nodes
    """
    G = nx.DiGraph()
    
    with Database(db_path) as db:
        # Get all topics
        cursor = db.conn.cursor()
        cursor.execute("SELECT * FROM topics")
        topic_rows = cursor.fetchall()
        
        # Add topic nodes
        for row in topic_rows:
            topic = db._row_to_topic_summary(row)
            G.add_node(
                topic.topic_id,
                type="topic",
                topic_id=topic.topic_id,
                parent_topic_id=topic.parent_topic_id,
                summary=topic.summary,
                event_count=topic.event_count,
                last_event_at=topic.last_event_at.isoformat() if topic.last_event_at else None,
            )
        
        # Add topic→topic edges (parent-child)
        for row in topic_rows:
            topic = db._row_to_topic_summary(row)
            if topic.parent_topic_id:
                G.add_edge(
                    topic.parent_topic_id,
                    topic.topic_id,
                    type="parent-child",
                )
        
        # Get all skills
        cursor.execute("SELECT * FROM skills")
        skill_rows = cursor.fetchall()
        
        # Add skill nodes and topic→skill edges
        for row in skill_rows:
            skill = db._row_to_skill_state(row)
            G.add_node(
                skill.skill_id,
                type="skill",
                skill_id=skill.skill_id,
                topic_id=skill.topic_id,
                p_mastery=skill.p_mastery,
                last_evidence_at=skill.last_evidence_at.isoformat() if skill.last_evidence_at else None,
                evidence_count=skill.evidence_count,
            )
            
            # Add topic→skill edge
            if skill.topic_id:
                G.add_edge(
                    skill.topic_id,
                    skill.skill_id,
                    type="topic-skill",
                )
    
    return G

