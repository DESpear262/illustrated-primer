"""
AI API routes for AI Tutor Proof of Concept.

Provides REST endpoints for AI operations.
"""

from fastapi import APIRouter, HTTPException, Body
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

from backend.api.facade import get_facade
from src.interface_common.models import CommandResult
from src.interface_common.exceptions import FacadeError

router = APIRouter()


@router.get("/routes", response_model=CommandResult)
async def ai_routes():
    """
    Show model routing configuration.
    
    Returns:
        CommandResult with routing configuration
    """
    try:
        facade = get_facade()
        result = await facade.ai_routes()
        return CommandResult.from_facade_response(result)
    except FacadeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


class AITestRequest(BaseModel):
    """Request model for AI test."""
    task: str
    text: Optional[str] = None
    event_id: Optional[str] = None
    db_path: Optional[str] = None
    model: Optional[str] = None


@router.post("/test", response_model=CommandResult)
async def ai_test(request: AITestRequest = Body(...)):
    """
    Test AI functionality.
    
    Args:
        request: AI test request with task, text, event_id, db_path, and model
        
    Returns:
        CommandResult with test results
    """
    try:
        facade = get_facade()
        db_path = Path(request.db_path) if request.db_path else None
        result = await facade.ai_test(
            task=request.task,
            text=request.text,
            event_id=request.event_id,
            db_path=db_path,
            model=request.model,
        )
        return CommandResult.from_facade_response(result)
    except FacadeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

