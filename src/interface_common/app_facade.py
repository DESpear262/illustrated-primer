"""
Unified GUI-backend facade for AI Tutor Proof of Concept.

Provides async wrappers for all backend operations, enabling GUI interfaces
to interact with the backend without blocking the main thread. Includes
error handling, timeout guards, and logging hooks.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.config import (
    DB_PATH,
    FAISS_INDEX_PATH,
    REQUEST_TIMEOUT,
)
from src.storage.db import Database, initialize_database, DatabaseError
from src.retrieval.faiss_index import load_index, search_vectors, create_flat_ip_index
from src.retrieval.pipeline import (
    upsert_event_chunks,
    embed_and_index_chunks,
    default_stub_embed,
)
from src.services.ai.router import get_router, AITask, ModelRoute
from src.services.ai.client import get_client, AIClient
from src.services.ai.prompts import SummaryOutput, ClassificationOutput
from src.context.assembler import ContextAssembler
from src.interface.tutor_chat import (
    ChatSession,
    list_sessions,
    _load_session_events,
    suggest_session_title,
    summarize_session,
)
from src.interface.utils import build_history_messages, stitch_transcript
from src.models.base import Event
from src.interface_common.exceptions import (
    FacadeError,
    FacadeTimeoutError,
    FacadeValidationError,
)

logger = logging.getLogger(__name__)

# Timeout configuration (in seconds)
TIMEOUT_LLM = 30.0
TIMEOUT_FAISS = 10.0
TIMEOUT_DB = 5.0


class AppFacade:
    """
    Unified facade for GUI-backend operations.
    
    Provides async wrappers for all backend functions, with error handling,
    timeout guards, and logging hooks. All operations are non-blocking.
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        index_path: Optional[Path] = None,
        ai_client: Optional[AIClient] = None,
    ):
        """
        Initialize facade.
        
        Args:
            db_path: Path to database file (defaults to config.DB_PATH)
            index_path: Path to FAISS index file (defaults to config.FAISS_INDEX_PATH)
            ai_client: AI client instance (defaults to global client)
        """
        self.db_path = db_path or DB_PATH
        self.index_path = index_path or FAISS_INDEX_PATH
        self.ai_client = ai_client or get_client()
        self.router = get_router()

    # ==================== Database Operations ====================

    async def db_check(self) -> Dict[str, Any]:
        """
        Check database health.
        
        Returns:
            Dictionary with status, tables, and event_count
            
        Raises:
            FacadeError: If database check fails
            FacadeTimeoutError: If operation times out
        """
        operation = "db.check"
        logger.info(f"Starting {operation}")
        start_time = datetime.utcnow()
        
        try:
            def _check():
                with Database(self.db_path) as db:
                    return db.health_check()
            
            result = await asyncio.wait_for(
                asyncio.to_thread(_check),
                timeout=TIMEOUT_DB,
            )
            
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Completed {operation} in {elapsed:.2f}s")
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"{operation} timed out after {TIMEOUT_DB}s")
            raise FacadeTimeoutError(operation, TIMEOUT_DB)
        except DatabaseError as e:
            logger.error(f"{operation} failed: {e}")
            raise FacadeError(f"Database check failed: {e}", {"operation": operation})
        except Exception as e:
            logger.exception(f"{operation} unexpected error")
            raise FacadeError(f"Unexpected error in {operation}: {e}", {"operation": operation})

    async def db_init(self) -> Dict[str, Any]:
        """
        Initialize database with schema.
        
        Returns:
            Dictionary with success status and message
            
        Raises:
            FacadeError: If initialization fails
            FacadeTimeoutError: If operation times out
        """
        operation = "db.init"
        logger.info(f"Starting {operation}")
        start_time = datetime.utcnow()
        
        try:
            def _init():
                initialize_database(self.db_path)
                return {"status": "ok", "message": "Database initialized successfully"}
            
            result = await asyncio.wait_for(
                asyncio.to_thread(_init),
                timeout=TIMEOUT_DB,
            )
            
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Completed {operation} in {elapsed:.2f}s")
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"{operation} timed out after {TIMEOUT_DB}s")
            raise FacadeTimeoutError(operation, TIMEOUT_DB)
        except DatabaseError as e:
            logger.error(f"{operation} failed: {e}")
            raise FacadeError(f"Database initialization failed: {e}", {"operation": operation})
        except Exception as e:
            logger.exception(f"{operation} unexpected error")
            raise FacadeError(f"Unexpected error in {operation}: {e}", {"operation": operation})

    # ==================== Index Operations ====================

    async def index_build(
        self,
        event_id: Optional[str] = None,
        use_stub: bool = True,
    ) -> Dict[str, Any]:
        """
        Build or update the FAISS index from database events.
        
        Args:
            event_id: Optional event ID to reindex (if None, reindexes all)
            use_stub: Whether to use stub embeddings (no OpenAI)
            
        Returns:
            Dictionary with event_count and chunk_count
            
        Raises:
            FacadeError: If index build fails
            FacadeTimeoutError: If operation times out
        """
        operation = "index.build"
        logger.info(f"Starting {operation} (event_id={event_id}, use_stub={use_stub})")
        start_time = datetime.utcnow()
        
        try:
            import sqlite3
            
            def _build():
                embed_fn = default_stub_embed if use_stub else default_stub_embed
                conn = sqlite3.connect(self.db_path)
                try:
                    cursor = conn.cursor()
                    if event_id:
                        cursor.execute(
                            "SELECT event_id, content, topics, skills FROM events WHERE event_id = ?",
                            (event_id,),
                        )
                    else:
                        cursor.execute("SELECT event_id, content, topics, skills FROM events")
                    
                    rows = cursor.fetchall()
                    total_chunks = 0
                    for row in rows:
                        ev_id, content, topics_json, skills_json = row
                        import json
                        topics = json.loads(topics_json) if topics_json else []
                        skills = json.loads(skills_json) if skills_json else []
                        records = upsert_event_chunks(conn, ev_id, content, topics, skills)
                        embed_and_index_chunks(conn, records, embed_fn=embed_fn)
                        total_chunks += len(records)
                    
                    return {"event_count": len(rows), "chunk_count": total_chunks}
                finally:
                    conn.close()
            
            result = await asyncio.wait_for(
                asyncio.to_thread(_build),
                timeout=TIMEOUT_FAISS,
            )
            
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Completed {operation} in {elapsed:.2f}s")
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"{operation} timed out after {TIMEOUT_FAISS}s")
            raise FacadeTimeoutError(operation, TIMEOUT_FAISS)
        except Exception as e:
            logger.exception(f"{operation} unexpected error")
            raise FacadeError(f"Unexpected error in {operation}: {e}", {"operation": operation})

    async def index_status(self) -> Dict[str, Any]:
        """
        Get FAISS index status.
        
        Returns:
            Dictionary with path and vector_count
            
        Raises:
            FacadeError: If status check fails
            FacadeTimeoutError: If operation times out
        """
        operation = "index.status"
        logger.info(f"Starting {operation}")
        start_time = datetime.utcnow()
        
        try:
            def _status():
                index = load_index(self.index_path)
                return {
                    "path": str(self.index_path),
                    "vector_count": index.ntotal,
                }
            
            result = await asyncio.wait_for(
                asyncio.to_thread(_status),
                timeout=TIMEOUT_FAISS,
            )
            
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Completed {operation} in {elapsed:.2f}s")
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"{operation} timed out after {TIMEOUT_FAISS}s")
            raise FacadeTimeoutError(operation, TIMEOUT_FAISS)
        except Exception as e:
            logger.exception(f"{operation} unexpected error")
            raise FacadeError(f"Unexpected error in {operation}: {e}", {"operation": operation})

    async def index_search(
        self,
        query: str,
        topk: int = 5,
        use_stub: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Search the FAISS index for the given query.
        
        Args:
            query: Search query text
            topk: Number of results to return
            use_stub: Whether to use stub embeddings (no OpenAI)
            
        Returns:
            List of dictionaries with vector_id and score
            
        Raises:
            FacadeError: If search fails
            FacadeTimeoutError: If operation times out
        """
        operation = "index.search"
        logger.info(f"Starting {operation} (query={query[:50]}..., topk={topk})")
        start_time = datetime.utcnow()
        
        try:
            def _search():
                index = load_index(self.index_path)
                embed_fn = default_stub_embed if use_stub else default_stub_embed
                vectors = embed_fn([query])
                ids, dists = search_vectors(index, vectors, top_k=topk)
                
                results = []
                for i in range(ids.shape[1]):
                    results.append({
                        "rank": i + 1,
                        "vector_id": int(ids[0][i]),
                        "score": float(dists[0][i]),
                    })
                return results
            
            result = await asyncio.wait_for(
                asyncio.to_thread(_search),
                timeout=TIMEOUT_FAISS,
            )
            
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Completed {operation} in {elapsed:.2f}s")
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"{operation} timed out after {TIMEOUT_FAISS}s")
            raise FacadeTimeoutError(operation, TIMEOUT_FAISS)
        except Exception as e:
            logger.exception(f"{operation} unexpected error")
            raise FacadeError(f"Unexpected error in {operation}: {e}", {"operation": operation})

    # ==================== AI Operations ====================

    async def ai_routes(self) -> List[Dict[str, Any]]:
        """
        Get model routing configuration.
        
        Returns:
            List of dictionaries with task, model, token_budget, etc.
            
        Raises:
            FacadeError: If routes retrieval fails
        """
        operation = "ai.routes"
        logger.info(f"Starting {operation}")
        start_time = datetime.utcnow()
        
        try:
            routes = []
            for task in AITask:
                route = self.router.get_route(task)
                routes.append({
                    "task": task.value,
                    "model": route.model_name,
                    "token_budget": route.token_budget,
                    "supports_streaming": route.supports_streaming,
                    "supports_json_mode": route.supports_json_mode,
                })
            
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Completed {operation} in {elapsed:.2f}s")
            
            return routes
            
        except Exception as e:
            logger.exception(f"{operation} unexpected error")
            raise FacadeError(f"Unexpected error in {operation}: {e}", {"operation": operation})

    async def ai_test_summarize(
        self,
        text: Optional[str] = None,
        event_id: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Test AI summarization.
        
        Args:
            text: Input text to summarize
            event_id: Optional event ID to summarize from database
            model: Optional model override
            
        Returns:
            Dictionary with summary, topics, skills, key_points, open_questions
            
        Raises:
            FacadeValidationError: If neither text nor event_id provided
            FacadeError: If summarization fails
            FacadeTimeoutError: If operation times out
        """
        operation = "ai.test.summarize"
        logger.info(f"Starting {operation} (event_id={event_id}, model={model})")
        start_time = datetime.utcnow()
        
        try:
            # Get content
            if event_id:
                def _get_event():
                    with Database(self.db_path) as db:
                        event = db.get_event_by_id(event_id)
                        if not event:
                            raise FacadeValidationError("event_id", event_id, "Event not found")
                        return event.content
                
                content = await asyncio.wait_for(
                    asyncio.to_thread(_get_event),
                    timeout=TIMEOUT_DB,
                )
            elif text:
                content = text
            else:
                raise FacadeValidationError(
                    "text/event_id",
                    None,
                    "Either text or event_id must be provided",
                )
            
            # Summarize
            def _summarize():
                return self.ai_client.summarize_event(content, override_model=model)
            
            result_obj = await asyncio.wait_for(
                asyncio.to_thread(_summarize),
                timeout=TIMEOUT_LLM,
            )
            
            result = {
                "summary": result_obj.summary,
                "topics": result_obj.topics,
                "skills": result_obj.skills,
                "key_points": result_obj.key_points,
                "open_questions": result_obj.open_questions,
            }
            
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Completed {operation} in {elapsed:.2f}s")
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"{operation} timed out after {TIMEOUT_LLM}s")
            raise FacadeTimeoutError(operation, TIMEOUT_LLM)
        except FacadeValidationError:
            raise
        except Exception as e:
            logger.exception(f"{operation} unexpected error")
            raise FacadeError(f"Unexpected error in {operation}: {e}", {"operation": operation})

    async def ai_test_classify(
        self,
        text: str,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Test AI topic/skill classification.
        
        Args:
            text: Input text to classify
            model: Optional model override
            
        Returns:
            Dictionary with topics, skills, confidence
            
        Raises:
            FacadeValidationError: If text not provided
            FacadeError: If classification fails
            FacadeTimeoutError: If operation times out
        """
        operation = "ai.test.classify"
        logger.info(f"Starting {operation} (text={text[:50]}..., model={model})")
        start_time = datetime.utcnow()
        
        try:
            if not text:
                raise FacadeValidationError("text", text, "Text must be provided")
            
            def _classify():
                return self.ai_client.classify_topics(text, override_model=model)
            
            result_obj = await asyncio.wait_for(
                asyncio.to_thread(_classify),
                timeout=TIMEOUT_LLM,
            )
            
            result = {
                "topics": result_obj.topics,
                "skills": result_obj.skills,
                "confidence": result_obj.confidence,
            }
            
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Completed {operation} in {elapsed:.2f}s")
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"{operation} timed out after {TIMEOUT_LLM}s")
            raise FacadeTimeoutError(operation, TIMEOUT_LLM)
        except FacadeValidationError:
            raise
        except Exception as e:
            logger.exception(f"{operation} unexpected error")
            raise FacadeError(f"Unexpected error in {operation}: {e}", {"operation": operation})

    async def ai_test_chat(
        self,
        text: str,
        model: Optional[str] = None,
    ) -> str:
        """
        Test AI chat reply.
        
        Args:
            text: User message
            model: Optional model override
            
        Returns:
            Chat response text
            
        Raises:
            FacadeValidationError: If text not provided
            FacadeError: If chat fails
            FacadeTimeoutError: If operation times out
        """
        operation = "ai.test.chat"
        logger.info(f"Starting {operation} (text={text[:50]}..., model={model})")
        start_time = datetime.utcnow()
        
        try:
            if not text:
                raise FacadeValidationError("text", text, "Text must be provided")
            
            def _chat():
                return self.ai_client.chat_reply(text, override_model=model)
            
            result = await asyncio.wait_for(
                asyncio.to_thread(_chat),
                timeout=TIMEOUT_LLM,
            )
            
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Completed {operation} in {elapsed:.2f}s")
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"{operation} timed out after {TIMEOUT_LLM}s")
            raise FacadeTimeoutError(operation, TIMEOUT_LLM)
        except FacadeValidationError:
            raise
        except Exception as e:
            logger.exception(f"{operation} unexpected error")
            raise FacadeError(f"Unexpected error in {operation}: {e}", {"operation": operation})

    # ==================== Chat Operations ====================

    async def chat_start(
        self,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Start a new chat session.
        
        Args:
            title: Optional session title
            
        Returns:
            Dictionary with session_id and title
            
        Raises:
            FacadeError: If session creation fails
        """
        operation = "chat.start"
        logger.info(f"Starting {operation} (title={title})")
        start_time = datetime.utcnow()
        
        try:
            session = ChatSession(title=title)
            
            result = {
                "session_id": session.session_id,
                "title": session.title,
            }
            
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Completed {operation} in {elapsed:.2f}s")
            
            return result
            
        except Exception as e:
            logger.exception(f"{operation} unexpected error")
            raise FacadeError(f"Unexpected error in {operation}: {e}", {"operation": operation})

    async def chat_resume(
        self,
        session_id: str,
    ) -> Dict[str, Any]:
        """
        Resume an existing chat session.
        
        Args:
            session_id: Session ID to resume
            
        Returns:
            Dictionary with session_id, title, and event_count
            
        Raises:
            FacadeValidationError: If session not found
            FacadeError: If session resume fails
        """
        operation = "chat.resume"
        logger.info(f"Starting {operation} (session_id={session_id})")
        start_time = datetime.utcnow()
        
        try:
            def _resume():
                events = _load_session_events(session_id, self.db_path)
                if not events:
                    raise FacadeValidationError("session_id", session_id, "Session not found")
                
                # Extract title from first event metadata
                title = None
                if events:
                    metadata = events[0].metadata or {}
                    title = metadata.get("session_title")
                
                return {
                    "session_id": session_id,
                    "title": title,
                    "event_count": len(events),
                }
            
            result = await asyncio.wait_for(
                asyncio.to_thread(_resume),
                timeout=TIMEOUT_DB,
            )
            
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Completed {operation} in {elapsed:.2f}s")
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"{operation} timed out after {TIMEOUT_DB}s")
            raise FacadeTimeoutError(operation, TIMEOUT_DB)
        except FacadeValidationError:
            raise
        except Exception as e:
            logger.exception(f"{operation} unexpected error")
            raise FacadeError(f"Unexpected error in {operation}: {e}", {"operation": operation})

    async def chat_list(
        self,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        List recent chat sessions.
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of dictionaries with session_id, title, first_at, last_at, count
            
        Raises:
            FacadeError: If list retrieval fails
        """
        operation = "chat.list"
        logger.info(f"Starting {operation} (limit={limit})")
        start_time = datetime.utcnow()
        
        try:
            def _list():
                return list_sessions(db_path=self.db_path, limit=limit)
            
            result = await asyncio.wait_for(
                asyncio.to_thread(_list),
                timeout=TIMEOUT_DB,
            )
            
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Completed {operation} in {elapsed:.2f}s")
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"{operation} timed out after {TIMEOUT_DB}s")
            raise FacadeTimeoutError(operation, TIMEOUT_DB)
        except Exception as e:
            logger.exception(f"{operation} unexpected error")
            raise FacadeError(f"Unexpected error in {operation}: {e}", {"operation": operation})

    async def chat_turn(
        self,
        session_id: str,
        user_message: str,
        suggest_title: bool = False,
    ) -> Dict[str, Any]:
        """
        Process a single chat turn (user message + AI reply).
        
        Args:
            session_id: Session ID
            user_message: User message text
            suggest_title: Whether to suggest session title (if first turn)
            
        Returns:
            Dictionary with session_id, turn_index, user_message, ai_reply, context_used
            
        Raises:
            FacadeValidationError: If session_id or user_message not provided
            FacadeError: If chat turn fails
            FacadeTimeoutError: If operation times out
        """
        operation = "chat.turn"
        logger.info(f"Starting {operation} (session_id={session_id}, suggest_title={suggest_title})")
        start_time = datetime.utcnow()
        
        try:
            if not session_id:
                raise FacadeValidationError("session_id", session_id, "Session ID must be provided")
            if not user_message:
                raise FacadeValidationError("user_message", user_message, "User message must be provided")
            
            def _turn():
                from uuid import uuid4
                
                # Load session events
                events = _load_session_events(session_id, self.db_path)
                
                # Get session title from metadata
                title = None
                if events:
                    metadata = events[0].metadata or {}
                    title = metadata.get("session_title")
                
                # Determine turn index
                turn_index = len(events) + 1
                
                # Log user message as event
                user_event = Event(
                    event_id=str(uuid4()),
                    content=user_message,
                    event_type="chat",
                    actor="student",
                    metadata={
                        "session_id": session_id,
                        "turn_index": turn_index,
                        "session_title": title,
                    },
                )
                
                with Database(self.db_path) as db:
                    db.insert_event(user_event)
                
                # Suggest title if first turn and requested
                if suggest_title and turn_index == 1 and not title:
                    try:
                        title = suggest_session_title(user_message)
                        # Update first event with title
                        with Database(self.db_path) as db:
                            first_event = events[0] if events else user_event
                            if first_event.id:
                                metadata = first_event.metadata or {}
                                metadata["session_title"] = title
                                first_event.metadata = metadata
                                db.update_event(first_event)
                    except Exception as e:
                        logger.warning(f"Failed to suggest title: {e}")
                
                # Build context for AI reply
                assembler = ContextAssembler(db_path=self.db_path)
                router = get_router()
                route = router.get_route(AITask.CHAT_REPLY)
                system_prompt = "You are an AI tutor helping a student learn."
                
                # Build history messages
                all_events = events + [user_event]
                history = build_history_messages(all_events)
                
                # Compose context from retrieved memory and history
                composed_context, retrieval_decision = assembler.compose_context(
                    query_text=user_message,
                    history_messages=history,
                    system_prompt=system_prompt,
                    route=route,
                    session_topics=None,  # Could extract from events
                )
                
                # Get AI reply
                ai_reply = self.ai_client.chat_reply(
                    user_message,
                    context=composed_context,
                )
                
                # Log AI reply as event
                ai_event = Event(
                    event_id=str(uuid4()),
                    content=ai_reply,
                    event_type="chat",
                    actor="tutor",
                    metadata={
                        "session_id": session_id,
                        "turn_index": turn_index + 1,
                        "session_title": title,
                    },
                )
                
                with Database(self.db_path) as db:
                    db.insert_event(ai_event)
                
                return {
                    "session_id": session_id,
                    "turn_index": turn_index,
                    "user_message": user_message,
                    "ai_reply": ai_reply,
                    "context_used": retrieval_decision.get("selected_chunk_ids", []) if retrieval_decision else [],
                    "title": title,
                }
            
            result = await asyncio.wait_for(
                asyncio.to_thread(_turn),
                timeout=TIMEOUT_LLM,
            )
            
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Completed {operation} in {elapsed:.2f}s")
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"{operation} timed out after {TIMEOUT_LLM}s")
            raise FacadeTimeoutError(operation, TIMEOUT_LLM)
        except FacadeValidationError:
            raise
        except Exception as e:
            logger.exception(f"{operation} unexpected error")
            raise FacadeError(f"Unexpected error in {operation}: {e}", {"operation": operation})

    # ==================== Command Dispatcher ====================

    async def run_command(
        self,
        name: str,
        args: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Generic command dispatcher for GUI use.
        
        Args:
            name: Command name (e.g., "db.check", "index.build", "chat.turn")
            args: Optional dictionary of command arguments
            
        Returns:
            Command result (type depends on command)
            
        Raises:
            FacadeValidationError: If command name is invalid
            FacadeError: If command execution fails
        """
        args = args or {}
        
        # Map command names to methods
        command_map = {
            "db.check": self.db_check,
            "db.init": self.db_init,
            "index.build": self.index_build,
            "index.status": self.index_status,
            "index.search": self.index_search,
            "ai.routes": self.ai_routes,
            "ai.test.summarize": self.ai_test_summarize,
            "ai.test.classify": self.ai_test_classify,
            "ai.test.chat": self.ai_test_chat,
            "chat.start": self.chat_start,
            "chat.resume": self.chat_resume,
            "chat.list": self.chat_list,
            "chat.turn": self.chat_turn,
        }
        
        if name not in command_map:
            raise FacadeValidationError(
                "name",
                name,
                f"Unknown command: {name}. Valid commands: {', '.join(command_map.keys())}",
            )
        
        method = command_map[name]
        
        # Call method with args
        try:
            if args:
                return await method(**args)
            else:
                return await method()
        except (FacadeError, FacadeValidationError, FacadeTimeoutError):
            # Re-raise facade exceptions as-is
            raise
        except Exception as e:
            logger.exception(f"Command {name} failed with unexpected error")
            raise FacadeError(
                f"Command {name} failed: {e}",
                {"command": name, "args": args},
            )


# Global facade instance
_facade_instance: Optional[AppFacade] = None


def get_facade(
    db_path: Optional[Path] = None,
    index_path: Optional[Path] = None,
    ai_client: Optional[AIClient] = None,
) -> AppFacade:
    """
    Get or create global facade instance.
    
    Args:
        db_path: Optional database path override
        index_path: Optional index path override
        ai_client: Optional AI client override
        
    Returns:
        AppFacade instance
    """
    global _facade_instance
    
    if _facade_instance is None or db_path or index_path or ai_client:
        _facade_instance = AppFacade(
            db_path=db_path,
            index_path=index_path,
            ai_client=ai_client,
        )
    
    return _facade_instance

