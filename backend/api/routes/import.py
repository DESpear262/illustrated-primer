"""
Import API routes for AI Tutor Proof of Concept.

Provides REST endpoints for transcript import operations.
"""

from fastapi import APIRouter, HTTPException, Body, UploadFile, File
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel
import tempfile
import os

from backend.api.main import get_facade
from src.interface_common.models import CommandResult
from src.interface_common.exceptions import FacadeError

router = APIRouter()


class ImportTranscriptRequest(BaseModel):
    """Request model for transcript import."""
    file_path: str
    topics: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    db_path: Optional[str] = None
    use_stub_embeddings: bool = False


@router.post("/transcript", response_model=CommandResult)
async def import_transcript(request: ImportTranscriptRequest = Body(...)):
    """
    Import a transcript file.
    
    Args:
        request: Import request with file_path, topics, skills, db_path, and use_stub_embeddings
        
    Returns:
        CommandResult with import results
    """
    try:
        facade = get_facade()
        file_path = Path(request.file_path)
        db_path = Path(request.db_path) if request.db_path else None
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")
        
        result = await facade.import_transcript(
            file_path=file_path,
            topics=request.topics,
            skills=request.skills,
            db_path=db_path,
            use_stub_embeddings=request.use_stub_embeddings,
        )
        return CommandResult.from_facade_response(result)
    except FacadeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/transcript/upload", response_model=CommandResult)
async def import_transcript_upload(
    file: UploadFile = File(...),
    topics: Optional[str] = None,
    skills: Optional[str] = None,
    db_path: Optional[str] = None,
    use_stub_embeddings: bool = False,
):
    """
    Import a transcript file from upload.
    
    Args:
        file: Uploaded file
        topics: Optional comma-separated topics
        skills: Optional comma-separated skills
        db_path: Path to database file
        use_stub_embeddings: Use stub embeddings
        
    Returns:
        CommandResult with import results
    """
    try:
        facade = get_facade()
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = Path(tmp_file.name)
        
        try:
            # Parse topics and skills
            topics_list = [t.strip() for t in topics.split(",")] if topics else None
            skills_list = [s.strip() for s in skills.split(",")] if skills else None
            
            db_path_obj = Path(db_path) if db_path else None
            
            result = await facade.import_transcript(
                file_path=tmp_path,
                topics=topics_list,
                skills=skills_list,
                db_path=db_path_obj,
                use_stub_embeddings=use_stub_embeddings,
            )
            return CommandResult.from_facade_response(result)
        finally:
            # Clean up temporary file
            if tmp_path.exists():
                os.unlink(tmp_path)
    except FacadeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

