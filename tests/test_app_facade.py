"""
Unit tests for the GUI-backend facade.

Tests async wrappers for all backend operations, error handling,
timeout guards, and logging hooks.
"""

from __future__ import annotations

import asyncio
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

from src.interface_common.app_facade import AppFacade, get_facade
from src.interface_common.exceptions import (
    FacadeError,
    FacadeTimeoutError,
    FacadeValidationError,
)
from src.storage.db import Database, DatabaseError
from src.config import DB_PATH, FAISS_INDEX_PATH


@pytest.fixture
def facade(tmp_path):
    """Create a facade instance with temporary paths."""
    db_path = tmp_path / "test.db"
    index_path = tmp_path / "test_index.bin"
    return AppFacade(db_path=db_path, index_path=index_path)


@pytest.fixture
def mock_ai_client():
    """Create a mock AI client."""
    client = Mock()
    client.summarize_event = Mock(return_value=Mock(
        summary="Test summary",
        topics=["topic1"],
        skills=["skill1"],
        key_points=["point1"],
        open_questions=["question1"],
    ))
    client.classify_topics = Mock(return_value=Mock(
        topics=["topic1"],
        skills=["skill1"],
        confidence=0.9,
    ))
    client.chat_reply = Mock(return_value="Test reply")
    return client


class TestDatabaseOperations:
    """Tests for database operations."""
    
    @pytest.mark.asyncio
    async def test_db_check_success(self, facade, tmp_path):
        """Test successful database check."""
        # Initialize database first
        from src.storage.db import initialize_database
        initialize_database(facade.db_path)
        
        result = await facade.db_check()
        
        assert result["status"] == "ok"
        assert "tables" in result
        assert "event_count" in result
    
    @pytest.mark.asyncio
    async def test_db_check_timeout(self, facade):
        """Test database check timeout."""
        # Mock a slow operation
        with patch("src.interface_common.app_facade.Database") as mock_db:
            mock_db.return_value.__enter__.return_value.health_check = Mock(
                side_effect=lambda: asyncio.sleep(10)
            )
            
            with pytest.raises(FacadeTimeoutError):
                await facade.db_check()
    
    @pytest.mark.asyncio
    async def test_db_init_success(self, facade, tmp_path):
        """Test successful database initialization."""
        result = await facade.db_init()
        
        assert result["status"] == "ok"
        assert "message" in result
        assert facade.db_path.exists()
    
    @pytest.mark.asyncio
    async def test_db_init_timeout(self, facade):
        """Test database initialization timeout."""
        with patch("src.interface_common.app_facade.initialize_database") as mock_init:
            def slow_init(*args):
                import time
                time.sleep(10)
            mock_init.side_effect = slow_init
            
            with pytest.raises(FacadeTimeoutError):
                await facade.db_init()


class TestIndexOperations:
    """Tests for index operations."""
    
    @pytest.mark.asyncio
    async def test_index_status_success(self, facade, tmp_path):
        """Test successful index status check."""
        result = await facade.index_status()
        
        assert "path" in result
        assert "vector_count" in result
        assert result["vector_count"] == 0  # New index is empty
    
    @pytest.mark.asyncio
    async def test_index_status_timeout(self, facade):
        """Test index status timeout."""
        with patch("src.interface_common.app_facade.load_index") as mock_load:
            def slow_load(*args):
                import time
                time.sleep(10)
            mock_load.side_effect = slow_load
            
            with pytest.raises(FacadeTimeoutError):
                await facade.index_status()
    
    @pytest.mark.asyncio
    async def test_index_search_success(self, facade):
        """Test successful index search."""
        result = await facade.index_search("test query", topk=5)
        
        assert isinstance(result, list)
        # Empty index returns empty results
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_index_search_timeout(self, facade):
        """Test index search timeout."""
        with patch("src.interface_common.app_facade.load_index") as mock_load:
            def slow_load(*args):
                import time
                time.sleep(10)
            mock_load.side_effect = slow_load
            
            with pytest.raises(FacadeTimeoutError):
                await facade.index_search("test query")


class TestAIOperations:
    """Tests for AI operations."""
    
    @pytest.mark.asyncio
    async def test_ai_routes_success(self, facade):
        """Test successful AI routes retrieval."""
        result = await facade.ai_routes()
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert "task" in result[0]
        assert "model" in result[0]
        assert "token_budget" in result[0]
    
    @pytest.mark.asyncio
    async def test_ai_test_summarize_with_text(self, facade, mock_ai_client):
        """Test AI summarization with text."""
        facade.ai_client = mock_ai_client
        
        result = await facade.ai_test_summarize(text="Test content")
        
        assert "summary" in result
        assert "topics" in result
        assert "skills" in result
        assert result["summary"] == "Test summary"
    
    @pytest.mark.asyncio
    async def test_ai_test_summarize_with_event_id(self, facade, mock_ai_client, tmp_path):
        """Test AI summarization with event ID."""
        from src.storage.db import initialize_database, Database
        from src.models.base import Event
        from uuid import uuid4
        
        initialize_database(facade.db_path)
        
        # Create test event
        with Database(facade.db_path) as db:
            event = Event(
                event_id=str(uuid4()),
                content="Test content",
                event_type="chat",
                actor="student",
            )
            db.insert_event(event)
            event_id = event.event_id
        
        facade.ai_client = mock_ai_client
        
        result = await facade.ai_test_summarize(event_id=event_id)
        
        assert "summary" in result
        assert result["summary"] == "Test summary"
    
    @pytest.mark.asyncio
    async def test_ai_test_summarize_validation_error(self, facade):
        """Test AI summarization validation error."""
        with pytest.raises(FacadeValidationError):
            await facade.ai_test_summarize()
    
    @pytest.mark.asyncio
    async def test_ai_test_classify_success(self, facade, mock_ai_client):
        """Test successful AI classification."""
        facade.ai_client = mock_ai_client
        
        result = await facade.ai_test_classify("Test text")
        
        assert "topics" in result
        assert "skills" in result
        assert "confidence" in result
        assert result["topics"] == ["topic1"]
    
    @pytest.mark.asyncio
    async def test_ai_test_classify_validation_error(self, facade):
        """Test AI classification validation error."""
        with pytest.raises(FacadeValidationError):
            await facade.ai_test_classify("")
    
    @pytest.mark.asyncio
    async def test_ai_test_chat_success(self, facade, mock_ai_client):
        """Test successful AI chat."""
        facade.ai_client = mock_ai_client
        
        result = await facade.ai_test_chat("Hello")
        
        assert isinstance(result, str)
        assert result == "Test reply"
    
    @pytest.mark.asyncio
    async def test_ai_test_chat_validation_error(self, facade):
        """Test AI chat validation error."""
        with pytest.raises(FacadeValidationError):
            await facade.ai_test_chat("")


class TestChatOperations:
    """Tests for chat operations."""
    
    @pytest.mark.asyncio
    async def test_chat_start_success(self, facade):
        """Test successful chat start."""
        result = await facade.chat_start()
        
        assert "session_id" in result
        assert "title" in result
        assert result["title"] is None
    
    @pytest.mark.asyncio
    async def test_chat_start_with_title(self, facade):
        """Test chat start with title."""
        result = await facade.chat_start(title="Test Session")
        
        assert result["title"] == "Test Session"
    
    @pytest.mark.asyncio
    async def test_chat_list_success(self, facade, tmp_path):
        """Test successful chat list."""
        from src.storage.db import initialize_database
        
        initialize_database(facade.db_path)
        
        result = await facade.chat_list(limit=10)
        
        assert isinstance(result, list)
        # Empty database returns empty list
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_chat_resume_not_found(self, facade, tmp_path):
        """Test chat resume with non-existent session."""
        from src.storage.db import initialize_database
        
        initialize_database(facade.db_path)
        
        with pytest.raises(FacadeValidationError):
            await facade.chat_resume("nonexistent-session-id")
    
    @pytest.mark.asyncio
    async def test_chat_turn_success(self, facade, mock_ai_client, tmp_path):
        """Test successful chat turn."""
        from src.storage.db import initialize_database, Database
        from src.models.base import Event
        from uuid import uuid4
        
        initialize_database(facade.db_path)
        
        # Create session with one event
        session_id = str(uuid4())
        with Database(facade.db_path) as db:
            event = Event(
                event_id=str(uuid4()),
                content="Previous message",
                event_type="chat",
                actor="student",
                metadata={"session_id": session_id, "turn_index": 1},
            )
            db.insert_event(event)
        
        facade.ai_client = mock_ai_client
        
        result = await facade.chat_turn(session_id, "New message")
        
        assert "session_id" in result
        assert "turn_index" in result
        assert "user_message" in result
        assert "ai_reply" in result
        assert result["user_message"] == "New message"
        assert result["ai_reply"] == "Test reply"
    
    @pytest.mark.asyncio
    async def test_chat_turn_validation_error(self, facade):
        """Test chat turn validation error."""
        with pytest.raises(FacadeValidationError):
            await facade.chat_turn("", "message")
        
        with pytest.raises(FacadeValidationError):
            await facade.chat_turn("session-id", "")


class TestCommandDispatcher:
    """Tests for command dispatcher."""
    
    @pytest.mark.asyncio
    async def test_run_command_db_check(self, facade, tmp_path):
        """Test run_command with db.check."""
        from src.storage.db import initialize_database
        
        initialize_database(facade.db_path)
        
        result = await facade.run_command("db.check")
        
        assert result["status"] == "ok"
    
    @pytest.mark.asyncio
    async def test_run_command_index_status(self, facade):
        """Test run_command with index.status."""
        result = await facade.run_command("index.status")
        
        assert "path" in result
        assert "vector_count" in result
    
    @pytest.mark.asyncio
    async def test_run_command_with_args(self, facade, mock_ai_client):
        """Test run_command with arguments."""
        facade.ai_client = mock_ai_client
        
        result = await facade.run_command("ai.test.chat", {"text": "Hello"})
        
        assert isinstance(result, str)
        assert result == "Test reply"
    
    @pytest.mark.asyncio
    async def test_run_command_invalid_name(self, facade):
        """Test run_command with invalid command name."""
        with pytest.raises(FacadeValidationError):
            await facade.run_command("invalid.command")
    
    @pytest.mark.asyncio
    async def test_run_command_error_propagation(self, facade):
        """Test run_command error propagation."""
        with pytest.raises(FacadeValidationError):
            await facade.run_command("ai.test.classify", {"text": ""})


class TestGetFacade:
    """Tests for get_facade function."""
    
    def test_get_facade_default(self):
        """Test get_facade with default parameters."""
        facade = get_facade()
        
        assert isinstance(facade, AppFacade)
        assert facade.db_path == DB_PATH
        assert facade.index_path == FAISS_INDEX_PATH
    
    def test_get_facade_custom_paths(self, tmp_path):
        """Test get_facade with custom paths."""
        db_path = tmp_path / "custom.db"
        index_path = tmp_path / "custom_index.bin"
        
        facade = get_facade(db_path=db_path, index_path=index_path)
        
        assert facade.db_path == db_path
        assert facade.index_path == index_path
    
    def test_get_facade_singleton(self):
        """Test get_facade returns singleton."""
        facade1 = get_facade()
        facade2 = get_facade()
        
        assert facade1 is facade2


class TestErrorHandling:
    """Tests for error handling."""
    
    @pytest.mark.asyncio
    async def test_database_error_propagation(self, facade):
        """Test database errors are properly propagated."""
        # Use non-existent database path
        facade.db_path = Path("/nonexistent/path.db")
        
        with pytest.raises(FacadeError):
            await facade.db_check()
    
    @pytest.mark.asyncio
    async def test_timeout_error_propagation(self, facade):
        """Test timeout errors are properly propagated."""
        with patch("src.interface_common.app_facade.load_index") as mock_load:
            mock_load.side_effect = lambda *args: asyncio.sleep(10)
            
            with pytest.raises(FacadeTimeoutError) as exc_info:
                await facade.index_status()
            
            assert exc_info.value.operation == "index.status"
            assert exc_info.value.timeout_seconds == 10.0
    
    @pytest.mark.asyncio
    async def test_validation_error_propagation(self, facade):
        """Test validation errors are properly propagated."""
        with pytest.raises(FacadeValidationError) as exc_info:
            await facade.ai_test_classify("")
        
        assert exc_info.value.field == "text"
        assert "must be provided" in exc_info.value.reason

