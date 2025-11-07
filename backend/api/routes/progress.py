"""
Progress API routes for AI Tutor Proof of Concept.

Provides REST endpoints for progress tracking operations.
"""

from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
from typing import Optional

from backend.api.facade import get_facade
from src.interface_common.models import CommandResult
from src.interface_common.exceptions import FacadeError

router = APIRouter()


@router.get("/summary", response_model=CommandResult)
async def progress_summary(
    start: Optional[str] = Query(None, description="Start timestamp (ISO or relative)"),
    end: Optional[str] = Query(None, description="End timestamp (ISO or relative)"),
    days: Optional[int] = Query(None, description="Compare N days ago to now"),
    topic: Optional[str] = Query(None, description="Filter by topic ID"),
    format: str = Query("json", description="Output format (json, markdown, table)"),
    db_path: Optional[str] = Query(None, description="Path to database file"),
):
    """
    Generate progress report.
    
    Args:
        start: Start timestamp (ISO or relative)
        end: End timestamp (ISO or relative)
        days: Compare N days ago to now
        topic: Filter by topic ID
        format: Output format (json, markdown, table)
        db_path: Path to database file
        
    Returns:
        CommandResult with progress report
    """
    try:
        facade = get_facade()
        path = Path(db_path) if db_path else None
        result = await facade.progress_summary(
            start=start,
            end=end,
            days=days,
            topic=topic,
            format=format,
            db_path=path,
        )
        return CommandResult.from_facade_response(result)
    except FacadeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

