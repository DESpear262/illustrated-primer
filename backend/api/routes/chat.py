"""
Chat API routes for AI Tutor Proof of Concept.

Provides REST endpoints for chat operations.
"""

from fastapi import APIRouter, HTTPException, Query, Body
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

from backend.api.facade import get_facade
from src.interface_common.models import CommandResult
from src.interface_common.exceptions import FacadeError

router = APIRouter()


class ChatStartRequest(BaseModel):
    """Request model for chat start."""
    title: Optional[str] = None
    db_path: Optional[str] = None


@router.post("/start", response_model=CommandResult)
async def chat_start(request: ChatStartRequest = Body(...)):
    """
    Start a new chat session.
    
    Args:
        request: Chat start request with title and db_path
        
    Returns:
        CommandResult with session information
    """
    try:
        facade = get_facade()
        db_path = Path(request.db_path) if request.db_path else None
        result = await facade.chat_start(title=request.title, db_path=db_path)
        return CommandResult.from_facade_response(result)
    except FacadeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


class ChatResumeRequest(BaseModel):
    """Request model for chat resume."""
    session_id: str
    db_path: Optional[str] = None


@router.post("/resume", response_model=CommandResult)
async def chat_resume(request: ChatResumeRequest = Body(...)):
    """
    Resume an existing chat session.
    
    Args:
        request: Chat resume request with session_id and db_path
        
    Returns:
        CommandResult with session information
    """
    try:
        facade = get_facade()
        db_path = Path(request.db_path) if request.db_path else None
        result = await facade.chat_resume(session_id=request.session_id, db_path=db_path)
        return CommandResult.from_facade_response(result)
    except FacadeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/list", response_model=CommandResult)
async def chat_list(db_path: Optional[str] = Query(None, description="Path to database file")):
    """
    List all chat sessions.
    
    Args:
        db_path: Optional path to database file
        
    Returns:
        CommandResult with session list
    """
    try:
        facade = get_facade()
        path = Path(db_path) if db_path else None
        result = await facade.chat_list(db_path=path)
        return CommandResult.from_facade_response(result)
    except FacadeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


class ChatTurnRequest(BaseModel):
    """Request model for chat turn."""
    session_id: str
    user_message: str
    db_path: Optional[str] = None


@router.post("/turn", response_model=CommandResult)
async def chat_turn(request: ChatTurnRequest = Body(...)):
    """
    Process a chat turn (user message and tutor reply).
    
    Args:
        request: Chat turn request with session_id, user_message, and db_path
        
    Returns:
        CommandResult with turn results
    """
    try:
        facade = get_facade()
        db_path = Path(request.db_path) if request.db_path else None
        result = await facade.chat_turn(
            session_id=request.session_id,
            user_message=request.user_message,
            db_path=db_path,
        )
        return CommandResult.from_facade_response(result)
    except FacadeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

