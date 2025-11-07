"""
Hover API routes for AI Tutor Proof of Concept.

Provides REST endpoints for hover payload operations.
"""

from fastapi import APIRouter, HTTPException, Path as PathParam, Query
from pathlib import Path
from typing import Optional, Dict, Any

from src.context.hover_provider import get_hover_payload
from src.interface_common.models import HoverPayload

router = APIRouter()


@router.get("/{node_id}", response_model=HoverPayload)
async def get_hover(
    node_id: str = PathParam(..., description="Node ID in format 'type:id'"),
    db_path: Optional[str] = Query(None, description="Path to database file"),
):
    """
    Get hover payload for a node in the knowledge tree.
    
    Args:
        node_id: Node ID in format "type:id" (e.g., "topic:math", "skill:derivative")
        db_path: Path to database file
        
    Returns:
        HoverPayload with node summary and statistics
    """
    try:
        path = Path(db_path) if db_path else None
        payload = get_hover_payload(node_id, db_path=path)
        
        # Validate payload matches HoverPayload model
        # The payload is already a dict, so we need to validate it
        if payload.get("type") == "topic":
            from src.interface_common.models import TopicHoverPayload
            return TopicHoverPayload.model_validate(payload)
        elif payload.get("type") == "skill":
            from src.interface_common.models import SkillHoverPayload
            return SkillHoverPayload.model_validate(payload)
        elif payload.get("type") == "event":
            from src.interface_common.models import EventHoverPayload
            return EventHoverPayload.model_validate(payload)
        else:
            raise ValueError(f"Unknown node type: {payload.get('type')}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hover payload generation failed: {str(e)}")

