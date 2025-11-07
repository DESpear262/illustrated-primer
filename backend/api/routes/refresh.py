"""
Refresh API routes for AI Tutor Proof of Concept.

Provides REST endpoints for summarization refresh operations.
"""

from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
from typing import Optional

from backend.api.facade import get_facade
from src.interface_common.models import CommandResult
from src.interface_common.exceptions import FacadeError

router = APIRouter()


@router.post("/summaries", response_model=CommandResult)
async def refresh_summaries(
    topic: Optional[str] = Query(None, description="Topic ID to refresh"),
    since: Optional[str] = Query(None, description="ISO timestamp for filtering"),
    force: bool = Query(False, description="Force refresh even if recently updated"),
    db_path: Optional[str] = Query(None, description="Path to database file"),
):
    """
    Refresh topic summaries.
    
    Args:
        topic: Optional topic ID to refresh
        since: Optional ISO timestamp for filtering
        force: Force refresh even if recently updated
        db_path: Path to database file
        
    Returns:
        CommandResult with refresh results
    """
    try:
        facade = get_facade()
        path = Path(db_path) if db_path else None
        result = await facade.refresh_summaries(
            topic=topic,
            since=since,
            force=force,
            db_path=path,
        )
        return CommandResult.from_facade_response(result)
    except FacadeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

