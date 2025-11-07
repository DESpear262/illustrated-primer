"""
Graph API routes for AI Tutor Proof of Concept.

Provides REST endpoints for graph operations.
"""

from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
from typing import Optional, Dict, Any

from src.context.graph_provider import get_graph_json
from src.interface_common.exceptions import FacadeError

router = APIRouter()


@router.get("", response_model=Dict[str, Any])
async def get_graph(
    scope: Optional[str] = Query(None, description="Topic ID to filter by"),
    depth: Optional[int] = Query(None, description="Maximum depth of topic hierarchy"),
    relation: Optional[str] = Query(None, description="Relationship type filter"),
    include_events: bool = Query(False, description="Whether to include event nodes"),
    db_path: Optional[str] = Query(None, description="Path to database file"),
):
    """
    Get DAG JSON from database for knowledge tree visualization.
    
    Args:
        scope: Topic ID to filter by (includes all descendants if depth allows)
        depth: Maximum depth of topic hierarchy to include
        relation: Relationship type filter ("direct", "all", "parent-child", "belongs-to")
        include_events: Whether to include event nodes
        db_path: Path to database file
        
    Returns:
        Dictionary with nodes and edges in Cytoscape.js format
    """
    try:
        path = Path(db_path) if db_path else None
        result = get_graph_json(
            scope=scope,
            depth=depth,
            relation=relation,
            include_events=include_events,
            db_path=path,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph generation failed: {str(e)}")

