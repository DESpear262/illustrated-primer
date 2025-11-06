"""
Unified GUI–Backend Facade for AI Tutor Proof of Concept.

Provides async wrappers for all CLI commands, error handling, timeout guards,
and a unified command dispatcher for GUI use.
"""

from __future__ import annotations

import asyncio
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from uuid import uuid4

import sqlite3

from src.config import (
    DB_PATH,
    FAISS_INDEX_PATH,
    REQUEST_TIMEOUT,
    REVIEW_DEFAULT_LIMIT,
)
from src.storage.db import Database, initialize_database
from src.storage.db import DatabaseError as StorageDatabaseError
# Lazy imports for optional dependencies
# from src.retrieval.faiss_index import load_index, save_index, search_vectors, create_flat_ip_index
# from src.retrieval.pipeline import upsert_event_chunks, embed_and_index_chunks, default_stub_embed
from src.services.ai.client import get_client, AIClient
from src.services.ai.router import get_router, AITask
from src.services.ai.utils import AIError as ServiceAIError
from src.interface.tutor_chat import (
    ChatSession,
    list_sessions as _list_sessions,
    _load_session_events,
    suggest_session_title,
    summarize_session,
)
from src.interface.utils import generate_session_id, build_history_messages, stitch_transcript
from src.context.assembler import ContextAssembler
from src.models.base import Event
from src.scheduler.review import get_next_reviews
from src.ingestion.transcripts import import_transcript
from src.summarizers.update import refresh_topic_summaries, get_topics_needing_refresh
from src.analysis.performance import generate_progress_report, report_to_json, report_to_markdown, ReportFormat

from src.interface_common.exceptions import (
    FacadeError,
    FacadeTimeoutError,
    FacadeDatabaseError,
    FacadeIndexError,
    FacadeAIError,
    FacadeChatError,
)

# Configure logging for GUI operations
logger = logging.getLogger(__name__)
gui_logger = logging.getLogger("gui_operations")

# Timeout configuration
LLM_TIMEOUT_SECONDS = 60.0  # Default timeout for LLM calls
FAISS_TIMEOUT_SECONDS = 30.0  # Default timeout for FAISS operations
DB_TIMEOUT_SECONDS = 30.0  # Default timeout for database operations


def _sanitize_args(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize arguments for logging (remove sensitive data).
    
    Args:
        args: Arguments dictionary
        
    Returns:
        Sanitized arguments dictionary
    """
    sanitized = {}
    sensitive_keys = {"api_key", "password", "token", "secret"}
    
    for key, value in args.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, Path):
            sanitized[key] = str(value)
        elif isinstance(value, (datetime,)):
            sanitized[key] = value.isoformat()
        else:
            sanitized[key] = str(value)[:100]  # Truncate long values
    
    return sanitized


def _serialize_error(error: Exception) -> Dict[str, Any]:
    """
    Serialize exception to dictionary for JSON responses.
    
    Args:
        error: Exception to serialize
        
    Returns:
        Dictionary with error information
    """
    if isinstance(error, FacadeError):
        return error.to_dict()
    
    return {
        "error_type": error.__class__.__name__,
        "message": str(error),
        "details": {
            "traceback": traceback.format_exc(),
        },
    }


async def _with_timeout(coro, timeout_seconds: float, operation: str) -> Any:
    """
    Execute coroutine with timeout guard.
    
    Args:
        coro: Coroutine to execute
        timeout_seconds: Timeout in seconds
        operation: Operation name for error messages
        
    Returns:
        Result of coroutine
        
    Raises:
        FacadeTimeoutError: If operation times out
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise FacadeTimeoutError(
            f"Operation timed out after {timeout_seconds} seconds",
            operation=operation,
            timeout_seconds=timeout_seconds,
        )


class AppFacade:
    """
    Unified facade for GUI–backend operations.
    
    Provides async wrappers for all CLI commands with error handling,
    timeout guards, and logging hooks.
    """
    
    def __init__(self, db_path: Optional[Path] = None, index_path: Optional[Path] = None):
        """
        Initialize facade.
        
        Args:
            db_path: Path to database file (defaults to config)
            index_path: Path to FAISS index file (defaults to config)
        """
        self.db_path = db_path or DB_PATH
        self.index_path = index_path or FAISS_INDEX_PATH
        self._client: Optional[AIClient] = None
    
    @property
    def client(self) -> AIClient:
        """Get or create AI client."""
        if self._client is None:
            self._client = get_client()
        return self._client
    
    # ==================== Database Commands ====================
    
    async def db_check(self, db_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Check database health.
        
        Args:
            db_path: Path to database file (defaults to facade db_path)
            
        Returns:
            Dictionary with health check results
        """
        db_path = db_path or self.db_path
        operation = "db.check"
        start_time = datetime.utcnow()
        
        try:
            gui_logger.info(f"Starting {operation}", extra={"args": _sanitize_args({"db_path": str(db_path)})})
            
            async def _check():
                with Database(db_path) as db:
                    health = db.health_check()
                    return health
            
            result = await _with_timeout(_check(), DB_TIMEOUT_SECONDS, operation)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.info(f"Completed {operation} in {duration:.2f}s", extra={"success": True})
            
            return {
                "success": True,
                "result": result,
                "duration_seconds": duration,
            }
        
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.error(f"Failed {operation} after {duration:.2f}s", extra={"error": str(e)})
            
            if isinstance(e, (StorageDatabaseError, sqlite3.Error)):
                raise FacadeDatabaseError(
                    f"Database check failed: {e}",
                    operation=operation,
                    db_path=str(db_path),
                )
            raise FacadeError(f"Database check failed: {e}")
    
    async def db_init(self, db_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Initialize database with schema.
        
        Args:
            db_path: Path to database file (defaults to facade db_path)
            
        Returns:
            Dictionary with initialization results
        """
        db_path = db_path or self.db_path
        operation = "db.init"
        start_time = datetime.utcnow()
        
        try:
            gui_logger.info(f"Starting {operation}", extra={"args": _sanitize_args({"db_path": str(db_path)})})
            
            async def _init():
                initialize_database(db_path)
                return {"status": "initialized", "db_path": str(db_path)}
            
            result = await _with_timeout(_init(), DB_TIMEOUT_SECONDS, operation)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.info(f"Completed {operation} in {duration:.2f}s", extra={"success": True})
            
            return {
                "success": True,
                "result": result,
                "duration_seconds": duration,
            }
        
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.error(f"Failed {operation} after {duration:.2f}s", extra={"error": str(e)})
            
            if isinstance(e, (StorageDatabaseError, sqlite3.Error)):
                raise FacadeDatabaseError(
                    f"Database initialization failed: {e}",
                    operation=operation,
                    db_path=str(db_path),
                )
            raise FacadeError(f"Database initialization failed: {e}")
    
    # ==================== Index Commands ====================
    
    async def index_build(
        self,
        db_path: Optional[Path] = None,
        event_id: Optional[str] = None,
        use_stub: bool = True,
    ) -> Dict[str, Any]:
        """
        Build or update FAISS index from database events.
        
        Args:
            db_path: Path to database file (defaults to facade db_path)
            event_id: Optional event ID to reindex
            use_stub: Use stub embedder (no OpenAI)
            
        Returns:
            Dictionary with build results
        """
        db_path = db_path or self.db_path
        operation = "index.build"
        start_time = datetime.utcnow()
        
        try:
            gui_logger.info(
                f"Starting {operation}",
                extra={"args": _sanitize_args({"db_path": str(db_path), "event_id": event_id, "use_stub": use_stub})},
            )
            
            async def _build():
                from src.retrieval.pipeline import upsert_event_chunks, embed_and_index_chunks, default_stub_embed
                
                embed_fn = default_stub_embed
                conn = sqlite3.connect(db_path)
                try:
                    cursor = conn.cursor()
                    if event_id:
                        cursor.execute("SELECT event_id, content, topics, skills FROM events WHERE event_id = ?", (event_id,))
                    else:
                        cursor.execute("SELECT event_id, content, topics, skills FROM events")
                    
                    rows = cursor.fetchall()
                    total_chunks = 0
                    for row in rows:
                        ev_id, content, topics_json, skills_json = row
                        import json
                        topics = json.loads(topics_json)
                        skills = json.loads(skills_json)
                        records = upsert_event_chunks(conn, ev_id, content, topics, skills)
                        embed_and_index_chunks(conn, records, embed_fn=embed_fn)
                        total_chunks += len(records)
                    
                    return {"events_indexed": len(rows), "total_chunks": total_chunks}
                finally:
                    conn.close()
            
            result = await _with_timeout(_build(), FAISS_TIMEOUT_SECONDS, operation)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.info(f"Completed {operation} in {duration:.2f}s", extra={"success": True})
            
            return {
                "success": True,
                "result": result,
                "duration_seconds": duration,
            }
        
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.error(f"Failed {operation} after {duration:.2f}s", extra={"error": str(e)})
            
            raise FacadeIndexError(
                f"Index build failed: {e}",
                operation=operation,
                index_path=str(self.index_path),
            )
    
    async def index_status(self, index_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Show FAISS index status.
        
        Args:
            index_path: Path to index file (defaults to facade index_path)
            
        Returns:
            Dictionary with index status
        """
        index_path = index_path or self.index_path
        operation = "index.status"
        start_time = datetime.utcnow()
        
        try:
            gui_logger.info(f"Starting {operation}", extra={"args": _sanitize_args({"index_path": str(index_path)})})
            
            async def _status():
                from src.retrieval.faiss_index import load_index
                
                index = load_index(index_path)
                return {
                    "path": str(index_path),
                    "vectors": index.ntotal,
                }
            
            result = await _with_timeout(_status(), FAISS_TIMEOUT_SECONDS, operation)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.info(f"Completed {operation} in {duration:.2f}s", extra={"success": True})
            
            return {
                "success": True,
                "result": result,
                "duration_seconds": duration,
            }
        
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.error(f"Failed {operation} after {duration:.2f}s", extra={"error": str(e)})
            
            raise FacadeIndexError(
                f"Index status check failed: {e}",
                operation=operation,
                index_path=str(index_path),
            )
    
    async def index_search(
        self,
        query: str,
        topk: int = 5,
        use_stub: bool = True,
        index_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Search FAISS index for query text.
        
        Args:
            query: Search query text
            topk: Number of results to return
            use_stub: Use stub embedder (no OpenAI)
            index_path: Path to index file (defaults to facade index_path)
            
        Returns:
            Dictionary with search results
        """
        index_path = index_path or self.index_path
        operation = "index.search"
        start_time = datetime.utcnow()
        
        try:
            gui_logger.info(
                f"Starting {operation}",
                extra={"args": _sanitize_args({"query": query[:50], "topk": topk, "use_stub": use_stub})},
            )
            
            async def _search():
                from src.retrieval.faiss_index import load_index, search_vectors
                from src.retrieval.pipeline import default_stub_embed
                
                index = load_index(index_path)
                embed_fn = default_stub_embed
                
                vectors = embed_fn([query])
                ids, dists = search_vectors(index, vectors, top_k=topk)
                
                results = []
                for i in range(ids.shape[1]):
                    results.append({
                        "rank": i + 1,
                        "vector_id": int(ids[0][i]),
                        "score": float(dists[0][i]),
                    })
                
                return {"query": query, "results": results}
            
            result = await _with_timeout(_search(), FAISS_TIMEOUT_SECONDS, operation)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.info(f"Completed {operation} in {duration:.2f}s", extra={"success": True})
            
            return {
                "success": True,
                "result": result,
                "duration_seconds": duration,
            }
        
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.error(f"Failed {operation} after {duration:.2f}s", extra={"error": str(e)})
            
            raise FacadeIndexError(
                f"Index search failed: {e}",
                operation=operation,
                index_path=str(index_path),
            )
    
    # ==================== AI Commands ====================
    
    async def ai_routes(self) -> Dict[str, Any]:
        """
        Show model routing configuration.
        
        Returns:
            Dictionary with routing configuration
        """
        operation = "ai.routes"
        start_time = datetime.utcnow()
        
        try:
            gui_logger.info(f"Starting {operation}")
            
            async def _routes():
                router = get_router()
                routes = []
                for task in AITask:
                    route = router.get_route(task)
                    routes.append({
                        "task": task.value,
                        "model": route.model_name,
                        "token_budget": route.token_budget,
                        "supports_streaming": route.supports_streaming,
                        "supports_json_mode": route.supports_json_mode,
                    })
                return {"routes": routes}
            
            result = await _routes()
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.info(f"Completed {operation} in {duration:.2f}s", extra={"success": True})
            
            return {
                "success": True,
                "result": result,
                "duration_seconds": duration,
            }
        
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.error(f"Failed {operation} after {duration:.2f}s", extra={"error": str(e)})
            
            raise FacadeAIError(
                f"AI routes failed: {e}",
                operation=operation,
            )
    
    async def ai_test(
        self,
        task: str,
        text: Optional[str] = None,
        event_id: Optional[str] = None,
        db_path: Optional[Path] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Test AI functionality.
        
        Args:
            task: Task type (summarize, classify, chat)
            text: Input text
            event_id: Event ID to summarize
            db_path: Path to database file
            model: Override model
            
        Returns:
            Dictionary with test results
        """
        db_path = db_path or self.db_path
        operation = f"ai.test.{task}"
        start_time = datetime.utcnow()
        
        try:
            gui_logger.info(
                f"Starting {operation}",
                extra={"args": _sanitize_args({"task": task, "event_id": event_id, "model": model})},
            )
            
            async def _test():
                client = self.client
                
                if task == "summarize":
                    if event_id:
                        with Database(db_path) as db:
                            event = db.get_event_by_id(event_id)
                            if not event:
                                raise ValueError(f"Event not found: {event_id}")
                            content = event.content
                    elif text:
                        content = text
                    else:
                        raise ValueError("Either event_id or text required for summarize")
                    
                    result = client.summarize_event(content, override_model=model)
                    return {
                        "task": task,
                        "summary": result.summary,
                        "topics": result.topics,
                        "skills": result.skills,
                        "key_points": result.key_points,
                        "open_questions": result.open_questions,
                    }
                
                elif task == "classify":
                    if not text:
                        raise ValueError("text required for classify")
                    
                    result = client.classify_topics(text, override_model=model)
                    return {
                        "task": task,
                        "topics": result.topics,
                        "skills": result.skills,
                        "confidence": result.confidence,
                    }
                
                elif task == "chat":
                    if not text:
                        raise ValueError("text required for chat")
                    
                    response = client.chat_reply(text, override_model=model)
                    return {
                        "task": task,
                        "response": response,
                    }
                
                else:
                    raise ValueError(f"Unknown task: {task}")
            
            result = await _with_timeout(_test(), LLM_TIMEOUT_SECONDS, operation)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.info(f"Completed {operation} in {duration:.2f}s", extra={"success": True})
            
            return {
                "success": True,
                "result": result,
                "duration_seconds": duration,
            }
        
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.error(f"Failed {operation} after {duration:.2f}s", extra={"error": str(e)})
            
            if isinstance(e, ServiceAIError):
                raise FacadeAIError(
                    f"AI test failed: {e}",
                    operation=operation,
                    model=model,
                )
            raise FacadeAIError(
                f"AI test failed: {e}",
                operation=operation,
                model=model,
            )
    
    # ==================== Chat Commands ====================
    
    async def chat_start(
        self,
        title: Optional[str] = None,
        db_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Start a new chat session (non-interactive).
        
        Args:
            title: Optional session title
            db_path: Path to database file
            
        Returns:
            Dictionary with session information
        """
        db_path = db_path or self.db_path
        operation = "chat.start"
        start_time = datetime.utcnow()
        
        try:
            gui_logger.info(f"Starting {operation}", extra={"args": _sanitize_args({"title": title})})
            
            session = ChatSession(title=title)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.info(f"Completed {operation} in {duration:.2f}s", extra={"success": True})
            
            return {
                "success": True,
                "result": {
                    "session_id": session.session_id,
                    "title": session.title,
                },
                "duration_seconds": duration,
            }
        
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.error(f"Failed {operation} after {duration:.2f}s", extra={"error": str(e)})
            
            raise FacadeChatError(
                f"Chat start failed: {e}",
                operation=operation,
            )
    
    async def chat_resume(
        self,
        session_id: str,
        db_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Resume an existing chat session (non-interactive).
        
        Args:
            session_id: Session ID to resume
            db_path: Path to database file
            
        Returns:
            Dictionary with session information and messages
        """
        db_path = db_path or self.db_path
        operation = "chat.resume"
        start_time = datetime.utcnow()
        
        try:
            gui_logger.info(f"Starting {operation}", extra={"args": _sanitize_args({"session_id": session_id})})
            
            async def _resume():
                events = _load_session_events(session_id, db_path)
                if not events:
                    raise ValueError(f"Session not found: {session_id}")
                
                # Extract session metadata
                first_event = events[0]
                metadata = first_event.metadata or {}
                title = metadata.get("session_title", "(untitled)")
                
                # Build message list
                messages = []
                for event in events:
                    messages.append({
                        "event_id": event.event_id,
                        "actor": event.actor,
                        "content": event.content,
                        "created_at": event.created_at.isoformat(),
                    })
                
                return {
                    "session_id": session_id,
                    "title": title,
                    "messages": messages,
                    "message_count": len(messages),
                }
            
            result = await _with_timeout(_resume(), DB_TIMEOUT_SECONDS, operation)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.info(f"Completed {operation} in {duration:.2f}s", extra={"success": True})
            
            return {
                "success": True,
                "result": result,
                "duration_seconds": duration,
            }
        
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.error(f"Failed {operation} after {duration:.2f}s", extra={"error": str(e)})
            
            raise FacadeChatError(
                f"Chat resume failed: {e}",
                operation=operation,
                session_id=session_id,
            )
    
    async def chat_list(
        self,
        db_path: Optional[Path] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        List recent chat sessions.
        
        Args:
            db_path: Path to database file
            limit: Maximum number of sessions to return
            
        Returns:
            Dictionary with session list
        """
        db_path = db_path or self.db_path
        operation = "chat.list"
        start_time = datetime.utcnow()
        
        try:
            gui_logger.info(f"Starting {operation}", extra={"args": _sanitize_args({"limit": limit})})
            
            async def _list():
                sessions = _list_sessions(db_path=db_path, limit=limit)
                return {
                    "sessions": sessions,
                    "count": len(sessions),
                }
            
            result = await _with_timeout(_list(), DB_TIMEOUT_SECONDS, operation)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.info(f"Completed {operation} in {duration:.2f}s", extra={"success": True})
            
            return {
                "success": True,
                "result": result,
                "duration_seconds": duration,
            }
        
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.error(f"Failed {operation} after {duration:.2f}s", extra={"error": str(e)})
            
            raise FacadeChatError(
                f"Chat list failed: {e}",
                operation=operation,
            )
    
    async def chat_turn(
        self,
        session_id: str,
        user_message: str,
        db_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Process a single chat turn (non-interactive).
        
        Args:
            session_id: Session ID
            user_message: User message text
            db_path: Path to database file
            
        Returns:
            Dictionary with tutor reply and turn information
        """
        db_path = db_path or self.db_path
        operation = "chat.turn"
        start_time = datetime.utcnow()
        
        try:
            gui_logger.info(
                f"Starting {operation}",
                extra={"args": _sanitize_args({"session_id": session_id, "user_message": user_message[:50]})},
            )
            
            async def _turn():
                # Load session events
                events = _load_session_events(session_id, db_path)
                
                # Create user event
                user_event = Event(
                    event_id=str(uuid4()),
                    content=user_message,
                    event_type="chat",
                    actor="student",
                    metadata={
                        "session_id": session_id,
                        "turn_index": len(events) + 1,
                    },
                )
                
                # Save user event
                with Database(db_path) as db:
                    db.insert_event(user_event)
                
                # Build history
                all_events = events + [user_event]
                history_msgs = build_history_messages(all_events, token_budget=4000)
                
                # Extract session topics
                session_topics = set()
                for e in all_events:
                    session_topics.update(e.topics)
                session_topics = list(session_topics) if session_topics else None
                
                # Compose context
                assembler = ContextAssembler(db_path=db_path)
                router = get_router()
                route = router.get_route(AITask.CHAT_REPLY)
                system_prompt = "You are an AI tutor helping a student learn."
                
                composed_context, retrieval_decision = assembler.compose_context(
                    query_text=user_message,
                    history_messages=history_msgs,
                    system_prompt=system_prompt,
                    route=route,
                    session_topics=session_topics,
                )
                
                # Get tutor reply
                client = self.client
                reply = await asyncio.to_thread(
                    client.chat_reply,
                    user_message=user_message,
                    context=composed_context,
                    stream=False,
                )
                
                # Create tutor event
                tutor_event = Event(
                    event_id=str(uuid4()),
                    content=reply,
                    event_type="chat",
                    actor="tutor",
                    metadata={
                        "session_id": session_id,
                        "turn_index": len(all_events) + 1,
                    },
                )
                
                # Save tutor event
                with Database(db_path) as db:
                    db.insert_event(tutor_event)
                
                return {
                    "session_id": session_id,
                    "turn_index": len(all_events) + 1,
                    "user_message": user_message,
                    "tutor_reply": reply,
                    "context_chunks": len(composed_context.split("\n")) if composed_context else 0,
                }
            
            result = await _with_timeout(_turn(), LLM_TIMEOUT_SECONDS, operation)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.info(f"Completed {operation} in {duration:.2f}s", extra={"success": True})
            
            return {
                "success": True,
                "result": result,
                "duration_seconds": duration,
            }
        
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.error(f"Failed {operation} after {duration:.2f}s", extra={"error": str(e)})
            
            if isinstance(e, ServiceAIError):
                raise FacadeAIError(
                    f"Chat turn failed: {e}",
                    operation=operation,
                )
            raise FacadeChatError(
                f"Chat turn failed: {e}",
                operation=operation,
                session_id=session_id,
            )
    
    # ==================== Review Commands ====================
    
    async def review_next(
        self,
        limit: int = REVIEW_DEFAULT_LIMIT,
        topic: Optional[str] = None,
        min_mastery: Optional[float] = None,
        max_mastery: Optional[float] = None,
        db_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Get next skills to review.
        
        Args:
            limit: Maximum number of skills to return
            topic: Filter by topic ID
            min_mastery: Minimum mastery to include
            max_mastery: Maximum mastery to include
            db_path: Path to database file
            
        Returns:
            Dictionary with review items
        """
        db_path = db_path or self.db_path
        operation = "review.next"
        start_time = datetime.utcnow()
        
        try:
            gui_logger.info(
                f"Starting {operation}",
                extra={"args": _sanitize_args({"limit": limit, "topic": topic})},
            )
            
            async def _next():
                review_items = get_next_reviews(
                    limit=limit,
                    min_mastery=min_mastery,
                    max_mastery=max_mastery,
                    topic_id=topic,
                    db_path=db_path,
                )
                
                results = []
                for item in review_items:
                    results.append({
                        "skill_id": item.skill.skill_id,
                        "topic_id": item.skill.topic_id,
                        "current_mastery": item.skill.p_mastery,
                        "decayed_mastery": item.decayed_mastery,
                        "days_since_review": item.days_since_review,
                        "priority_score": item.priority_score,
                    })
                
                return {"items": results, "count": len(results)}
            
            result = await _with_timeout(_next(), DB_TIMEOUT_SECONDS, operation)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.info(f"Completed {operation} in {duration:.2f}s", extra={"success": True})
            
            return {
                "success": True,
                "result": result,
                "duration_seconds": duration,
            }
        
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.error(f"Failed {operation} after {duration:.2f}s", extra={"error": str(e)})
            
            raise FacadeError(f"Review next failed: {e}")
    
    # ==================== Import Commands ====================
    
    async def import_transcript(
        self,
        file_path: Path,
        topics: Optional[List[str]] = None,
        skills: Optional[List[str]] = None,
        db_path: Optional[Path] = None,
        use_stub_embeddings: bool = False,
    ) -> Dict[str, Any]:
        """
        Import a transcript file.
        
        Args:
            file_path: Path to transcript file
            topics: Optional manual topics
            skills: Optional manual skills
            db_path: Path to database file
            use_stub_embeddings: Use stub embeddings
            
        Returns:
            Dictionary with import results
        """
        db_path = db_path or self.db_path
        operation = "import.transcript"
        start_time = datetime.utcnow()
        
        try:
            gui_logger.info(
                f"Starting {operation}",
                extra={"args": _sanitize_args({"file_path": str(file_path)})},
            )
            
            async def _import():
                event = import_transcript(
                    file_path=file_path,
                    manual_topics=topics,
                    manual_skills=skills,
                    db_path=db_path,
                    use_real_embeddings=not use_stub_embeddings,
                )
                
                return {
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "actor": event.actor,
                    "topics": event.topics,
                    "skills": event.skills,
                    "created_at": event.created_at.isoformat(),
                }
            
            result = await _with_timeout(_import(), LLM_TIMEOUT_SECONDS, operation)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.info(f"Completed {operation} in {duration:.2f}s", extra={"success": True})
            
            return {
                "success": True,
                "result": result,
                "duration_seconds": duration,
            }
        
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.error(f"Failed {operation} after {duration:.2f}s", extra={"error": str(e)})
            
            raise FacadeError(f"Import transcript failed: {e}")
    
    # ==================== Refresh Commands ====================
    
    async def refresh_summaries(
        self,
        topic: Optional[str] = None,
        since: Optional[str] = None,
        force: bool = False,
        db_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Refresh topic summaries.
        
        Args:
            topic: Optional topic ID to refresh
            since: Optional ISO timestamp for filtering
            force: Force refresh even if recently updated
            db_path: Path to database file
            
        Returns:
            Dictionary with refresh results
        """
        db_path = db_path or self.db_path
        operation = "refresh.summaries"
        start_time = datetime.utcnow()
        
        try:
            gui_logger.info(
                f"Starting {operation}",
                extra={"args": _sanitize_args({"topic": topic, "since": since, "force": force})},
            )
            
            async def _refresh():
                from datetime import datetime as dt
                
                since_timestamp = None
                if since:
                    since_timestamp = dt.fromisoformat(since.replace("Z", "+00:00"))
                
                if topic:
                    topic_ids = [topic]
                else:
                    topic_ids = get_topics_needing_refresh(since=since_timestamp, db_path=db_path)
                
                results = refresh_topic_summaries(
                    topic_ids=topic_ids,
                    since=since_timestamp,
                    force=force,
                    db_path=db_path,
                )
                
                summary_results = []
                for topic_id, (updated_topic, tokens_used) in results.items():
                    summary_results.append({
                        "topic_id": topic_id,
                        "success": updated_topic is not None,
                        "tokens_used": tokens_used or 0,
                        "event_count": updated_topic.event_count if updated_topic else 0,
                    })
                
                return {
                    "topics_refreshed": len([r for r in summary_results if r["success"]]),
                    "topics_failed": len([r for r in summary_results if not r["success"]]),
                    "results": summary_results,
                }
            
            result = await _with_timeout(_refresh(), LLM_TIMEOUT_SECONDS, operation)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.info(f"Completed {operation} in {duration:.2f}s", extra={"success": True})
            
            return {
                "success": True,
                "result": result,
                "duration_seconds": duration,
            }
        
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.error(f"Failed {operation} after {duration:.2f}s", extra={"error": str(e)})
            
            raise FacadeError(f"Refresh summaries failed: {e}")
    
    # ==================== Progress Commands ====================
    
    async def progress_summary(
        self,
        start: Optional[str] = None,
        end: Optional[str] = None,
        days: Optional[int] = None,
        topic: Optional[str] = None,
        format: str = "json",
        db_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
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
            Dictionary with progress report
        """
        db_path = db_path or self.db_path
        operation = "progress.summary"
        start_time = datetime.utcnow()
        
        try:
            gui_logger.info(
                f"Starting {operation}",
                extra={"args": _sanitize_args({"start": start, "end": end, "days": days, "topic": topic})},
            )
            
            async def _summary():
                from datetime import timedelta
                
                # Parse timestamps
                if days is not None:
                    end_time = datetime.utcnow()
                    start_time = end_time - timedelta(days=days)
                elif start:
                    # Simple ISO parsing
                    start_time = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    if end:
                        end_time = datetime.fromisoformat(end.replace("Z", "+00:00"))
                    else:
                        end_time = datetime.utcnow()
                else:
                    end_time = datetime.utcnow()
                    start_time = end_time - timedelta(days=30)
                
                # Generate report
                report = generate_progress_report(
                    start_time=start_time,
                    end_time=end_time,
                    topic_id=topic,
                    db_path=db_path,
                )
                
                # Format output
                if format == "json":
                    output = report_to_json(report)
                elif format == "markdown":
                    output = report_to_markdown(report)
                else:
                    output = None
                
                return {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "format": format,
                    "output": output,
                    "summary": {
                        "total_skills": report.summary["total_skills"],
                        "skills_improved": report.summary["skills_improved"],
                        "skills_declined": report.summary["skills_declined"],
                        "average_delta": report.summary["average_delta"],
                    },
                }
            
            result = await _with_timeout(_summary(), DB_TIMEOUT_SECONDS, operation)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.info(f"Completed {operation} in {duration:.2f}s", extra={"success": True})
            
            return {
                "success": True,
                "result": result,
                "duration_seconds": duration,
            }
        
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            gui_logger.error(f"Failed {operation} after {duration:.2f}s", extra={"error": str(e)})
            
            raise FacadeError(f"Progress summary failed: {e}")


# ==================== Command Dispatcher ====================

async def run_command(command_name: str, **kwargs) -> Dict[str, Any]:
    """
    Unified command dispatcher for GUI use.
    
    Args:
        command_name: Command name (e.g., "db.check", "chat.start")
        **kwargs: Command arguments
        
    Returns:
        Dictionary with command results or error information
        
    Example:
        result = await run_command("db.check", db_path=Path("/path/to/db"))
        result = await run_command("chat.turn", session_id="...", user_message="Hello")
    """
    facade = AppFacade()
    
    # Parse command name
    parts = command_name.split(".")
    if len(parts) != 2:
        raise FacadeError(f"Invalid command name: {command_name}. Expected format: 'category.command'")
    
    category, command = parts
    
    # Map command names to methods
    method_name = f"{category}_{command}"
    if not hasattr(facade, method_name):
        raise FacadeError(f"Unknown command: {command_name}")
    
    method = getattr(facade, method_name)
    
    try:
        # Execute command
        result = await method(**kwargs)
        return result
    except FacadeError:
        # Re-raise facade errors as-is
        raise
    except Exception as e:
        # Wrap unexpected errors
        error_dict = _serialize_error(e)
        return {
            "success": False,
            "error": error_dict,
        }

