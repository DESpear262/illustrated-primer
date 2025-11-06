"""
Transcript importer for AI Tutor Proof of Concept.

Parses transcripts from various formats (.txt, .md, .json), infers actors,
extracts topics/skills via AI classification, and creates events with
summarization and embedding.
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from uuid import uuid4

import sqlite3
import numpy as np

from src.config import (
    DB_PATH,
    FAISS_INDEX_PATH,
    OPENAI_EMBEDDING_MODEL,
    OPENAI_MODEL_NANO,
    BATCH_EMBED_SIZE,
    EMBEDDING_DIMENSION,
    OPENAI_API_KEY,
)
from src.models.base import Event, SkillState, TopicSummary
from src.storage.db import Database
from src.storage.queries import get_events_by_topic, update_skill_state_with_evidence
from src.services.ai.client import AIClient, get_client
from src.services.ai.router import AITask
from src.summarizers.update import (
    update_topic_summary as update_topic_summary_new,
    update_skill_states as update_skill_states_new,
)
from src.retrieval.pipeline import (
    upsert_event_chunks,
    embed_and_index_chunks,
    ChunkRecord,
)
from src.retrieval.faiss_index import load_index, save_index
from src.utils.serialization import (
    serialize_json_list,
    serialize_embedding,
)
from openai import OpenAI

logger = logging.getLogger(__name__)


def infer_actor_from_text(text: str) -> str:
    """
    Infer actor (student/tutor/system) from transcript text.
    
    Looks for speaker labels like "Tutor:", "Student:", "Teacher:", etc.
    Defaults to 'tutor' if unclear.
    
    Args:
        text: Transcript text content
        
    Returns:
        'student', 'tutor', or 'system'
    """
    # Look for speaker labels at start of lines
    tutor_patterns = [
        r"^(?:tutor|teacher|instructor|professor|prof):",
        r"^(?:t|tutor|teacher):",
    ]
    student_patterns = [
        r"^(?:student|learner|pupil|user):",
        r"^(?:s|student):",
    ]
    
    lines = text.split("\n")
    tutor_count = 0
    student_count = 0
    
    for line in lines[:10]:  # Check first 10 lines
        line_lower = line.strip().lower()
        for pattern in tutor_patterns:
            if re.match(pattern, line_lower):
                tutor_count += 1
                break
        for pattern in student_patterns:
            if re.match(pattern, line_lower):
                student_count += 1
                break
    
    # If we found clear speaker labels, use them
    if tutor_count > student_count:
        return "tutor"
    elif student_count > tutor_count:
        return "student"
    
    # Default to tutor for imported transcripts (human tutor sessions)
    return "tutor"


def parse_timestamp(text: str, file_mtime: Optional[datetime] = None) -> Optional[datetime]:
    """
    Parse timestamp from transcript text or use file modification time.
    
    Looks for common timestamp formats in the text (ISO format, date strings, etc.).
    Falls back to file modification time if provided.
    
    Args:
        text: Transcript text content
        file_mtime: File modification time (optional)
        
    Returns:
        Parsed datetime or None
    """
    # Try to find ISO format timestamps
    iso_pattern = r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?"
    match = re.search(iso_pattern, text)
    if match:
        try:
            return datetime.fromisoformat(match.group(0).replace(" ", "T"))
        except (ValueError, AttributeError):
            pass
    
    # Try common date formats
    date_patterns = [
        r"\d{4}-\d{2}-\d{2}",
        r"\d{2}/\d{2}/\d{4}",
        r"\d{2}-\d{2}-\d{4}",
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                # Try parsing with common formats
                date_str = match.group(0)
                if "-" in date_str and len(date_str) == 10:
                    return datetime.strptime(date_str, "%Y-%m-%d")
                elif "/" in date_str:
                    return datetime.strptime(date_str, "%m/%d/%Y")
            except (ValueError, AttributeError):
                pass
    
    # Fall back to file modification time
    if file_mtime:
        return file_mtime
    
    return None


def parse_txt_transcript(file_path: Path) -> Tuple[str, Optional[datetime]]:
    """
    Parse plain text transcript file.
    
    Args:
        file_path: Path to .txt file
        
    Returns:
        Tuple of (content, recorded_at timestamp)
    """
    content = file_path.read_text(encoding="utf-8")
    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
    recorded_at = parse_timestamp(content, mtime)
    return content, recorded_at


def parse_md_transcript(file_path: Path) -> Tuple[str, Optional[datetime]]:
    """
    Parse markdown transcript file.
    
    For MVP, treats entire file as single transcript.
    TODO: Support multi-section transcripts in future.
    
    Args:
        file_path: Path to .md file
        
    Returns:
        Tuple of (content, recorded_at timestamp)
    """
    content = file_path.read_text(encoding="utf-8")
    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
    recorded_at = parse_timestamp(content, mtime)
    return content, recorded_at


def parse_json_transcript(file_path: Path) -> Tuple[str, Optional[datetime], Optional[Dict[str, Any]]]:
    """
    Parse JSON transcript file.
    
    Supports flexible JSON structure:
    - Simple: {"content": "...", "timestamp": "...", "topics": [...], ...}
    - Array of messages: [{"speaker": "...", "text": "...", ...}, ...]
    - Single content field: {"text": "...", "transcript": "...", ...}
    
    Args:
        file_path: Path to .json file
        
    Returns:
        Tuple of (content, recorded_at timestamp, metadata dict)
    """
    data = json.loads(file_path.read_text(encoding="utf-8"))
    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
    
    # Handle different JSON structures
    content = ""
    recorded_at = None
    metadata = {}
    
    # If it's an array of messages
    if isinstance(data, list):
        messages = []
        for msg in data:
            if isinstance(msg, dict):
                # Extract text from various field names
                text = msg.get("text") or msg.get("content") or msg.get("message") or ""
                speaker = msg.get("speaker") or msg.get("actor") or ""
                timestamp = msg.get("timestamp") or msg.get("time") or msg.get("created_at")
                
                if text:
                    if speaker:
                        messages.append(f"{speaker}: {text}")
                    else:
                        messages.append(text)
                
                # Try to parse timestamp from first message
                if recorded_at is None and timestamp:
                    try:
                        if isinstance(timestamp, str):
                            recorded_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        elif isinstance(timestamp, (int, float)):
                            recorded_at = datetime.fromtimestamp(timestamp)
                    except (ValueError, TypeError):
                        pass
        content = "\n".join(messages)
        if not recorded_at:
            recorded_at = parse_timestamp(content, mtime)
    
    # If it's a single object
    elif isinstance(data, dict):
        # Try various content field names
        content = (
            data.get("content") or
            data.get("text") or
            data.get("transcript") or
            data.get("message") or
            str(data)
        )
        
        # Extract timestamp
        timestamp = data.get("timestamp") or data.get("time") or data.get("created_at") or data.get("recorded_at")
        if timestamp:
            try:
                if isinstance(timestamp, str):
                    recorded_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                elif isinstance(timestamp, (int, float)):
                    recorded_at = datetime.fromtimestamp(timestamp)
            except (ValueError, TypeError):
                pass
        
        if not recorded_at:
            recorded_at = parse_timestamp(content, mtime)
        
        # Extract metadata (everything except content/timestamp fields)
        metadata = {k: v for k, v in data.items() if k not in ("content", "text", "transcript", "message", "timestamp", "time", "created_at", "recorded_at")}
    
    if not content:
        raise ValueError(f"No content found in JSON file: {file_path}")
    
    return content, recorded_at, metadata


def create_openai_embed_fn() -> callable:
    """
    Create OpenAI embedding function for real embeddings.
    
    Returns:
        Embedding function that takes list of texts and returns numpy array
    """
    if not OPENAI_API_KEY:
        logger.warning("No OpenAI API key - falling back to stub embeddings")
        from src.retrieval.pipeline import default_stub_embed
        return default_stub_embed
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    def embed_fn(texts: List[str]) -> np.ndarray:
        """Embed texts using OpenAI API."""
        try:
            response = client.embeddings.create(
                model=OPENAI_EMBEDDING_MODEL,
                input=texts,
            )
            vectors = np.array([item.embedding for item in response.data], dtype=np.float32)
            return vectors
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            # Fallback to stub
            from src.retrieval.pipeline import default_stub_embed
            return default_stub_embed(texts)
    
    return embed_fn


# Legacy functions for backward compatibility - now use summarizers.update
def update_topic_summary(
    topic_id: str,
    event_content: str,
    summary_output: Optional[Any] = None,
    db_path: Optional[Path] = None,
) -> TopicSummary:
    """
    Update or create topic summary after event import.
    
    Legacy function - now uses summarizers.update.update_topic_summary.
    Kept for backward compatibility.
    """
    topic, _ = update_topic_summary_new(
        topic_id=topic_id,
        event_content=event_content,
        summary_output=summary_output,
        db_path=db_path,
    )
    return topic


def update_skill_states(
    skills: List[str],
    event_content: str,
    db_path: Optional[Path] = None,
) -> List[SkillState]:
    """
    Update or create skill states after event import.
    
    Legacy function - now uses summarizers.update.update_skill_states.
    Kept for backward compatibility.
    """
    return update_skill_states_new(
        skills=skills,
        event_content=event_content,
        db_path=db_path,
    )


def import_transcript(
    file_path: Path,
    manual_topics: Optional[List[str]] = None,
    manual_skills: Optional[List[str]] = None,
    db_path: Optional[Path] = None,
    use_real_embeddings: bool = True,
) -> Event:
    """
    Import a transcript file and create an event with summarization and embedding.
    
    Parses transcript from .txt, .md, or .json format, infers actor and timestamp,
    classifies topics/skills via AI, creates event, summarizes, embeds, and updates
    topic summaries and skill states.
    
    Args:
        file_path: Path to transcript file (.txt, .md, or .json)
        manual_topics: Optional list of topics to add (in addition to AI classification)
        manual_skills: Optional list of skills to add (in addition to AI classification)
        db_path: Path to database file (defaults to config.DB_PATH)
        use_real_embeddings: Whether to use real OpenAI embeddings (default: True)
        
    Returns:
        Created Event object
        
    Raises:
        ValueError: If file format is not supported or parsing fails
        IOError: If file cannot be read
    """
    db_path = db_path or DB_PATH
    
    # Parse transcript based on file extension
    if not file_path.exists():
        raise IOError(f"File not found: {file_path}")
    
    suffix = file_path.suffix.lower()
    content = ""
    recorded_at = None
    metadata = {}
    
    try:
        if suffix == ".txt":
            content, recorded_at = parse_txt_transcript(file_path)
        elif suffix == ".md":
            content, recorded_at = parse_md_transcript(file_path)
        elif suffix == ".json":
            content, recorded_at, metadata = parse_json_transcript(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}. Supported: .txt, .md, .json")
    except Exception as e:
        logger.error(f"Failed to parse transcript {file_path}: {e}")
        raise ValueError(f"Failed to parse transcript: {e}") from e
    
    if not content.strip():
        raise ValueError(f"Empty transcript content: {file_path}")
    
    # Infer actor
    actor = infer_actor_from_text(content)
    
    # Classify topics and skills using AI
    client = get_client()
    classification = None
    topics = []
    skills = []
    
    try:
        classification = client.classify_topics(content, override_model=OPENAI_MODEL_NANO)
        topics = classification.topics
        skills = classification.skills
    except Exception as e:
        logger.warning(f"AI classification failed: {e}. Using empty topics/skills.")
    
    # Add manual tags if provided
    if manual_topics:
        topics = list(set(topics + manual_topics))
    if manual_skills:
        skills = list(set(skills + manual_skills))
    
    # Build provenance metadata
    provenance_metadata = {
        "source_file_path": str(file_path.absolute()),
        "import_timestamp": datetime.utcnow().isoformat(),
        "import_method": f"transcript_{suffix[1:]}",
        "import_model_version": OPENAI_MODEL_NANO,
        "classification_confidence": getattr(classification, "confidence", None) if classification else None,
    }
    
    # Merge with parsed metadata
    metadata.update(provenance_metadata)
    
    # Create event
    event = Event(
        event_id=str(uuid4()),
        content=content,
        event_type="transcript",
        actor=actor,
        topics=topics,
        skills=skills,
        recorded_at=recorded_at,
        metadata=metadata,
        source="imported_transcript",
    )
    
    # Store event in database
    with Database(db_path) as db:
        db.initialize()
        event = db.insert_event(event)
    
    # Summarize event
    summary_output = None
    try:
        summary_output = client.summarize_event(content)
        # Update topics and skills from summary if they were empty
        if not topics and summary_output.topics:
            topics = summary_output.topics
            event.topics = topics
            with Database(db_path) as db_update:
                event = db_update.update_event(event)
        if not skills and summary_output.skills:
            skills = summary_output.skills
            event.skills = skills
            with Database(db_path) as db_update:
                event = db_update.update_event(event)
    except Exception as e:
        logger.warning(f"Event summarization failed: {e}")
    
    # Chunk and embed
    try:
        # Use Database context manager for consistency
        with Database(db_path) as db_embed:
            if not db_embed.conn:
                raise ValueError("Database connection not established")
            
            records = upsert_event_chunks(db_embed.conn, event.event_id, content, topics, skills)
            
            # Use real embeddings if requested
            if use_real_embeddings:
                embed_fn = create_openai_embed_fn()
            else:
                from src.retrieval.pipeline import default_stub_embed
                embed_fn = default_stub_embed
            
            embed_and_index_chunks(db_embed.conn, records, embed_fn=embed_fn, faiss_path=FAISS_INDEX_PATH)
    except Exception as e:
        logger.warning(f"Embedding/indexing failed: {e}")
    
    # Update topic summaries and skill states
    # Use event IDs for audit logging
    event_ids_list = [event.event_id]
    
    for topic_id in topics:
        try:
            update_topic_summary_new(
                topic_id=topic_id,
                event_ids=event_ids_list,
                event_content=content,
                summary_output=summary_output,
                db_path=db_path,
            )
        except Exception as e:
            logger.warning(f"Failed to update topic summary {topic_id}: {e}")
    
    for skill_id in skills:
        try:
            update_skill_states_new(
                skills=[skill_id],
                event_ids=event_ids_list,
                event_content=content,
                db_path=db_path,
            )
        except Exception as e:
            logger.warning(f"Failed to update skill state {skill_id}: {e}")
    
    logger.info(f"Successfully imported transcript: {file_path} -> event_id={event.event_id}")
    return event

