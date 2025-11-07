"""
Index API routes for AI Tutor Proof of Concept.

Provides REST endpoints for FAISS index operations.
"""

from fastapi import APIRouter, HTTPException, Query, Body
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

from backend.api.facade import get_facade
from src.interface_common.models import CommandResult
from src.interface_common.exceptions import FacadeError

router = APIRouter()


class IndexBuildRequest(BaseModel):
    """Request model for index build."""
    db_path: Optional[str] = None
    event_id: Optional[str] = None
    use_stub: bool = True


@router.post("/build", response_model=CommandResult)
async def index_build(request: IndexBuildRequest = Body(...)):
    """
    Build or update FAISS index from database events.
    
    Args:
        request: Index build request with db_path, event_id, and use_stub
        
    Returns:
        CommandResult with build results
    """
    try:
        facade = get_facade()
        db_path = Path(request.db_path) if request.db_path else None
        result = await facade.index_build(
            db_path=db_path,
            event_id=request.event_id,
            use_stub=request.use_stub,
        )
        return CommandResult.from_facade_response(result)
    except FacadeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/status", response_model=CommandResult)
async def index_status(index_path: Optional[str] = Query(None, description="Path to index file")):
    """
    Show FAISS index status.
    
    Args:
        index_path: Optional path to index file
        
    Returns:
        CommandResult with index status
    """
    try:
        facade = get_facade()
        path = Path(index_path) if index_path else None
        result = await facade.index_status(index_path=path)
        return CommandResult.from_facade_response(result)
    except FacadeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


class IndexSearchRequest(BaseModel):
    """Request model for index search."""
    query: str
    topk: int = 5
    use_stub: bool = True
    index_path: Optional[str] = None


@router.post("/search", response_model=CommandResult)
async def index_search(request: IndexSearchRequest = Body(...)):
    """
    Search FAISS index for query text.
    
    Args:
        request: Search request with query, topk, use_stub, and index_path
        
    Returns:
        CommandResult with search results
    """
    try:
        facade = get_facade()
        index_path = Path(request.index_path) if request.index_path else None
        result = await facade.index_search(
            query=request.query,
            topk=request.topk,
            use_stub=request.use_stub,
            index_path=index_path,
        )
        return CommandResult.from_facade_response(result)
    except FacadeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

