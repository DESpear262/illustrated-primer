"""
Database API routes for AI Tutor Proof of Concept.

Provides REST endpoints for database operations.
"""

from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
from typing import Optional

from backend.api.facade import get_facade
from src.interface_common.models import CommandResult
from src.interface_common.exceptions import FacadeError

router = APIRouter()


@router.get("/check", response_model=CommandResult)
async def db_check(db_path: Optional[str] = Query(None, description="Path to database file")):
    """
    Check database health.
    
    Args:
        db_path: Optional path to database file
        
    Returns:
        CommandResult with health check results
    """
    try:
        facade = get_facade()
        path = Path(db_path) if db_path else None
        result = await facade.db_check(db_path=path)
        return CommandResult.from_facade_response(result)
    except FacadeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/init", response_model=CommandResult)
async def db_init(db_path: Optional[str] = Query(None, description="Path to database file")):
    """
    Initialize database with schema.
    
    Args:
        db_path: Optional path to database file
        
    Returns:
        CommandResult with initialization results
    """
    try:
        facade = get_facade()
        path = Path(db_path) if db_path else None
        result = await facade.db_init(db_path=path)
        return CommandResult.from_facade_response(result)
    except FacadeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

