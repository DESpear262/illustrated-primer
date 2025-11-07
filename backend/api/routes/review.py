"""
Review API routes for AI Tutor Proof of Concept.

Provides REST endpoints for review operations.
"""

from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
from typing import Optional

from backend.api.facade import get_facade
from src.interface_common.models import CommandResult
from src.interface_common.exceptions import FacadeError

router = APIRouter()


@router.get("/next", response_model=CommandResult)
async def review_next(
    limit: int = Query(10, description="Maximum number of skills to return"),
    topic: Optional[str] = Query(None, description="Filter by topic ID"),
    min_mastery: Optional[float] = Query(None, description="Minimum mastery to include"),
    max_mastery: Optional[float] = Query(None, description="Maximum mastery to include"),
    db_path: Optional[str] = Query(None, description="Path to database file"),
):
    """
    Get next skills to review.
    
    Args:
        limit: Maximum number of skills to return
        topic: Filter by topic ID
        min_mastery: Minimum mastery to include
        max_mastery: Maximum mastery to include
        db_path: Path to database file
        
    Returns:
        CommandResult with review items
    """
    try:
        facade = get_facade()
        path = Path(db_path) if db_path else None
        result = await facade.review_next(
            limit=limit,
            topic=topic,
            min_mastery=min_mastery,
            max_mastery=max_mastery,
            db_path=path,
        )
        return CommandResult.from_facade_response(result)
    except FacadeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

