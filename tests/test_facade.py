"""
Unit and integration tests for GUI–Backend Facade.

Tests exception classes, AppFacade methods, run_command dispatcher,
error handling, timeout guards, and logging hooks.
"""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
from uuid import uuid4

from src.interface_common.exceptions import (
    FacadeError,
    FacadeTimeoutError,
    FacadeDatabaseError,
    FacadeIndexError,
    FacadeAIError,
    FacadeChatError,
)
from src.interface_common.app_facade import AppFacade, run_command
from src.storage.db import Database, initialize_database
from src.models.base import Event


# ==================== Exception Tests ====================

class TestFacadeExceptions:
    """Tests for facade exception classes."""
    
    def test_facade_error_basic(self):
        """Test basic FacadeError creation."""
        error = FacadeError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.error_type == "FacadeError"
        assert error.details == {}
    
    def test_facade_error_with_details(self):
        """Test FacadeError with details."""
        details = {"key": "value"}
        error = FacadeError("Test error", error_type="CustomError", details=details)
        assert error.error_type == "CustomError"
        assert error.details == details
    
    def test_facade_error_to_dict(self):
        """Test FacadeError serialization."""
        error = FacadeError("Test error", details={"key": "value"})
        error_dict = error.to_dict()
        assert error_dict["error_type"] == "FacadeError"
        assert error_dict["message"] == "Test error"
        assert error_dict["details"] == {"key": "value"}
    
    def test_facade_timeout_error(self):
        """Test FacadeTimeoutError."""
        error = FacadeTimeoutError("Timeout", operation="test", timeout_seconds=30.0)
        assert error.operation == "test"
        assert error.timeout_seconds == 30.0
        assert error.error_type == "TimeoutError"
        assert error.details["operation"] == "test"
        assert error.details["timeout_seconds"] == 30.0
    
    def test_facade_database_error(self):
        """Test FacadeDatabaseError."""
        error = FacadeDatabaseError("DB error", operation="check", db_path="/path/to/db")
        assert error.operation == "check"
        assert error.db_path == "/path/to/db"
        assert error.error_type == "DatabaseError"
    
    def test_facade_index_error(self):
        """Test FacadeIndexError."""
        error = FacadeIndexError("Index error", operation="build", index_path="/path/to/index")
        assert error.operation == "build"
        assert error.index_path == "/path/to/index"
        assert error.error_type == "IndexError"
    
    def test_facade_ai_error(self):
        """Test FacadeAIError."""
        error = FacadeAIError("AI error", operation="test", model="gpt-4o")
        assert error.operation == "test"
        assert error.model == "gpt-4o"
        assert error.error_type == "AIError"
    
    def test_facade_chat_error(self):
        """Test FacadeChatError."""
        error = FacadeChatError("Chat error", operation="start", session_id="session-123")
        assert error.operation == "start"
        assert error.session_id == "session-123"
        assert error.error_type == "ChatError"


# ==================== Database Command Tests ====================

class TestFacadeDatabaseCommands:
    """Tests for database facade commands."""
    
    @pytest.fixture
    def db_path(self, tmp_path):
        """Create test database."""
        db_path = tmp_path / "test.db"
        initialize_database(db_path)
        return db_path
    
    @pytest.fixture
    def facade(self, db_path):
        """Create facade instance."""
        return AppFacade(db_path=db_path)
    
    @pytest.mark.asyncio
    async def test_db_check_success(self, facade, db_path):
        """Test successful database check."""
        result = await facade.db_check()
        
        assert result["success"] is True
        assert "result" in result
        assert "duration_seconds" in result
        assert result["result"]["status"] == "ok"
    
    @pytest.mark.asyncio
    async def test_db_check_custom_path(self, facade, tmp_path):
        """Test database check with custom path."""
        custom_db = tmp_path / "custom.db"
        initialize_database(custom_db)
        
        result = await facade.db_check(db_path=custom_db)
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_db_init_success(self, facade, tmp_path):
        """Test successful database initialization."""
        new_db = tmp_path / "new.db"
        result = await facade.db_init(db_path=new_db)
        
        assert result["success"] is True
        assert new_db.exists()
    
    @pytest.mark.asyncio
    async def test_db_check_invalid_path(self, facade):
        """Test database check with invalid path."""
        invalid_path = Path("/nonexistent/path.db")
        
        with pytest.raises(FacadeDatabaseError):
            await facade.db_check(db_path=invalid_path)


# ==================== Index Command Tests ====================

class TestFacadeIndexCommands:
    """Tests for index facade commands."""
    
    @pytest.fixture
    def db_path(self, tmp_path):
        """Create test database with events."""
        db_path = tmp_path / "test.db"
        initialize_database(db_path)
        
        # Add test event
        with Database(db_path) as db:
            event = Event(
                event_id=str(uuid4()),
                content="Test content for indexing",
                event_type="chat",
                actor="student",
                topics=["test"],
                skills=["test_skill"],
            )
            db.insert_event(event)
        
        return db_path
    
    @pytest.fixture
    def facade(self, db_path, tmp_path):
        """Create facade instance."""
        index_path = tmp_path / "index.bin"
        return AppFacade(db_path=db_path, index_path=index_path)
    
    @pytest.mark.asyncio
    async def test_index_build_success(self, facade):
        """Test successful index build."""
        result = await facade.index_build(use_stub=True)
        
        assert result["success"] is True
        assert "result" in result
        assert result["result"]["events_indexed"] >= 0
    
    @pytest.mark.asyncio
    async def test_index_status_success(self, facade):
        """Test successful index status check."""
        # Build index first
        await facade.index_build(use_stub=True)
        
        result = await facade.index_status()
        
        assert result["success"] is True
        assert "result" in result
        assert "vectors" in result["result"]
    
    @pytest.mark.asyncio
    async def test_index_search_success(self, facade):
        """Test successful index search."""
        # Build index first
        await facade.index_build(use_stub=True)
        
        result = await facade.index_search(query="test", topk=5, use_stub=True)
        
        assert result["success"] is True
        assert "result" in result
        assert "results" in result["result"]


# ==================== AI Command Tests ====================

class TestFacadeAICommands:
    """Tests for AI facade commands."""
    
    @pytest.fixture
    def facade(self, tmp_path):
        """Create facade instance."""
        db_path = tmp_path / "test.db"
        initialize_database(db_path)
        return AppFacade(db_path=db_path)
    
    @pytest.mark.asyncio
    @patch('src.services.ai.client.OpenAI')
    async def test_ai_routes_success(self, mock_openai_class, facade):
        """Test successful AI routes command."""
        result = await facade.ai_routes()
        
        assert result["success"] is True
        assert "result" in result
        assert "routes" in result["result"]
        assert len(result["result"]["routes"]) > 0
    
    @pytest.mark.asyncio
    @patch('src.interface_common.app_facade.get_client')
    async def test_ai_test_summarize(self, mock_get_client, facade):
        """Test AI test summarize command."""
        # Mock client
        mock_client = Mock()
        mock_client.summarize_event.return_value = Mock(
            summary="Test summary",
            topics=["test"],
            skills=["test_skill"],
            key_points=["Point 1"],
            open_questions=["Question 1"],
        )
        mock_get_client.return_value = mock_client
        
        result = await facade.ai_test(task="summarize", text="Test content")
        
        assert result["success"] is True
        assert "result" in result
        assert result["result"]["task"] == "summarize"
        assert result["result"]["summary"] == "Test summary"
    
    @pytest.mark.asyncio
    @patch('src.interface_common.app_facade.get_client')
    async def test_ai_test_classify(self, mock_get_client, facade):
        """Test AI test classify command."""
        # Mock client
        mock_client = Mock()
        mock_client.classify_topics.return_value = Mock(
            topics=["test"],
            skills=["test_skill"],
            confidence=0.9,
        )
        mock_get_client.return_value = mock_client
        
        result = await facade.ai_test(task="classify", text="Test content")
        
        assert result["success"] is True
        assert result["result"]["task"] == "classify"
        assert result["result"]["topics"] == ["test"]
    
    @pytest.mark.asyncio
    @patch('src.interface_common.app_facade.get_client')
    async def test_ai_test_chat(self, mock_get_client, facade):
        """Test AI test chat command."""
        # Mock client
        mock_client = Mock()
        mock_client.chat_reply.return_value = "Test response"
        mock_get_client.return_value = mock_client
        
        result = await facade.ai_test(task="chat", text="Hello")
        
        assert result["success"] is True
        assert result["result"]["task"] == "chat"
        assert result["result"]["response"] == "Test response"


# ==================== Chat Command Tests ====================

class TestFacadeChatCommands:
    """Tests for chat facade commands."""
    
    @pytest.fixture
    def db_path(self, tmp_path):
        """Create test database."""
        db_path = tmp_path / "test.db"
        initialize_database(db_path)
        return db_path
    
    @pytest.fixture
    def facade(self, db_path):
        """Create facade instance."""
        return AppFacade(db_path=db_path)
    
    @pytest.mark.asyncio
    async def test_chat_start_success(self, facade):
        """Test successful chat start."""
        result = await facade.chat_start(title="Test Session")
        
        assert result["success"] is True
        assert "result" in result
        assert "session_id" in result["result"]
        assert result["result"]["title"] == "Test Session"
    
    @pytest.mark.asyncio
    async def test_chat_list_success(self, facade, db_path):
        """Test successful chat list."""
        # Create a test session
        session_id = str(uuid4())
        with Database(db_path) as db:
            event = Event(
                event_id=str(uuid4()),
                content="Test message",
                event_type="chat",
                actor="student",
                metadata={"session_id": session_id, "session_title": "Test"},
            )
            db.insert_event(event)
        
        result = await facade.chat_list(limit=10)
        
        assert result["success"] is True
        assert "result" in result
        assert "sessions" in result["result"]
    
    @pytest.mark.asyncio
    async def test_chat_resume_success(self, facade, db_path):
        """Test successful chat resume."""
        # Create a test session
        session_id = str(uuid4())
        with Database(db_path) as db:
            event = Event(
                event_id=str(uuid4()),
                content="Test message",
                event_type="chat",
                actor="student",
                metadata={"session_id": session_id, "session_title": "Test"},
            )
            db.insert_event(event)
        
        result = await facade.chat_resume(session_id=session_id)
        
        assert result["success"] is True
        assert "result" in result
        assert result["result"]["session_id"] == session_id
        assert "messages" in result["result"]
    
    @pytest.mark.asyncio
    async def test_chat_resume_not_found(self, facade):
        """Test chat resume with non-existent session."""
        with pytest.raises(FacadeChatError):
            await facade.chat_resume(session_id="nonexistent")
    
    @pytest.mark.asyncio
    @patch('src.interface_common.app_facade.get_client')
    async def test_chat_turn_success(self, mock_get_client, facade, db_path):
        """Test successful chat turn."""
        # Mock client
        mock_client = Mock()
        mock_client.chat_reply.return_value = "Test reply"
        mock_get_client.return_value = mock_client
        
        # Start a session
        start_result = await facade.chat_start()
        session_id = start_result["result"]["session_id"]
        
        # Process a turn
        result = await facade.chat_turn(session_id=session_id, user_message="Hello")
        
        assert result["success"] is True
        assert "result" in result
        assert result["result"]["tutor_reply"] == "Test reply"
        assert result["result"]["user_message"] == "Hello"


# ==================== Review Command Tests ====================

class TestFacadeReviewCommands:
    """Tests for review facade commands."""
    
    @pytest.fixture
    def db_path(self, tmp_path):
        """Create test database with skills."""
        db_path = tmp_path / "test.db"
        initialize_database(db_path)
        
        # Add test skill
        with Database(db_path) as db:
            from src.models.base import SkillState
            skill = SkillState(
                skill_id="test_skill",
                topic_id="test_topic",
                p_mastery=0.5,
            )
            db.insert_skill_state(skill)
        
        return db_path
    
    @pytest.fixture
    def facade(self, db_path):
        """Create facade instance."""
        return AppFacade(db_path=db_path)
    
    @pytest.mark.asyncio
    async def test_review_next_success(self, facade):
        """Test successful review next."""
        result = await facade.review_next(limit=10)
        
        assert result["success"] is True
        assert "result" in result
        assert "items" in result["result"]


# ==================== Import Command Tests ====================

class TestFacadeImportCommands:
    """Tests for import facade commands."""
    
    @pytest.fixture
    def db_path(self, tmp_path):
        """Create test database."""
        db_path = tmp_path / "test.db"
        initialize_database(db_path)
        return db_path
    
    @pytest.fixture
    def facade(self, db_path):
        """Create facade instance."""
        return AppFacade(db_path=db_path)
    
    @pytest.fixture
    def transcript_file(self, tmp_path):
        """Create test transcript file."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Student: Hello\nTutor: Hi there!")
        return file_path
    
    @pytest.mark.asyncio
    @patch('src.services.ai.client.OpenAI')
    async def test_import_transcript_success(self, mock_openai_class, facade, transcript_file):
        """Test successful transcript import."""
        # Mock API responses
        mock_response_classify = Mock()
        mock_response_classify.choices = [Mock()]
        mock_response_classify.choices[0].message.content = json.dumps({
            "topics": ["test"],
            "skills": ["test_skill"],
            "confidence": 0.9,
        })
        mock_response_classify.usage = Mock()
        mock_response_classify.usage.completion_tokens = 50
        
        mock_response_summarize = Mock()
        mock_response_summarize.choices = [Mock()]
        mock_response_summarize.choices[0].message.content = json.dumps({
            "summary": "Test summary",
            "topics": ["test"],
            "skills": ["test_skill"],
            "key_points": [],
            "open_questions": [],
        })
        mock_response_summarize.usage = Mock()
        mock_response_summarize.usage.completion_tokens = 100
        
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = [
            mock_response_classify,
            mock_response_summarize,
        ]
        mock_openai_class.return_value = mock_client
        
        result = await facade.import_transcript(
            file_path=transcript_file,
            use_stub_embeddings=True,
        )
        
        assert result["success"] is True
        assert "result" in result
        assert "event_id" in result["result"]


# ==================== Refresh Command Tests ====================

class TestFacadeRefreshCommands:
    """Tests for refresh facade commands."""
    
    @pytest.fixture
    def db_path(self, tmp_path):
        """Create test database with topics."""
        db_path = tmp_path / "test.db"
        initialize_database(db_path)
        
        # Add test topic and event
        with Database(db_path) as db:
            from src.models.base import TopicSummary
            topic = TopicSummary(
                topic_id="test_topic",
                summary="Test summary",
            )
            db.insert_topic_summary(topic)
            
            event = Event(
                event_id=str(uuid4()),
                content="Test content",
                event_type="chat",
                actor="student",
                topics=["test_topic"],
            )
            db.insert_event(event)
        
        return db_path
    
    @pytest.fixture
    def facade(self, db_path):
        """Create facade instance."""
        return AppFacade(db_path=db_path)
    
    @pytest.mark.asyncio
    @patch('src.services.ai.client.OpenAI')
    async def test_refresh_summaries_success(self, mock_openai_class, facade):
        """Test successful refresh summaries."""
        # Mock API response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "summary": "Updated summary",
            "topics": ["test_topic"],
            "skills": [],
            "key_points": [],
            "open_questions": [],
        })
        mock_response.usage = Mock()
        mock_response.usage.completion_tokens = 100
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        result = await facade.refresh_summaries()
        
        assert result["success"] is True
        assert "result" in result
        assert "topics_refreshed" in result["result"]


# ==================== Progress Command Tests ====================

class TestFacadeProgressCommands:
    """Tests for progress facade commands."""
    
    @pytest.fixture
    def db_path(self, tmp_path):
        """Create test database with skills."""
        db_path = tmp_path / "test.db"
        initialize_database(db_path)
        
        # Add test skills with different timestamps
        with Database(db_path) as db:
            from src.models.base import SkillState
            skill1 = SkillState(
                skill_id="skill1",
                p_mastery=0.5,
            )
            skill2 = SkillState(
                skill_id="skill2",
                p_mastery=0.7,
            )
            db.insert_skill_state(skill1)
            db.insert_skill_state(skill2)
        
        return db_path
    
    @pytest.fixture
    def facade(self, db_path):
        """Create facade instance."""
        return AppFacade(db_path=db_path)
    
    @pytest.mark.asyncio
    async def test_progress_summary_success(self, facade):
        """Test successful progress summary."""
        result = await facade.progress_summary(days=30, format="json")
        
        assert result["success"] is True
        assert "result" in result
        assert "summary" in result["result"]


# ==================== Command Dispatcher Tests ====================

class TestCommandDispatcher:
    """Tests for run_command dispatcher."""
    
    @pytest.fixture
    def db_path(self, tmp_path):
        """Create test database."""
        db_path = tmp_path / "test.db"
        initialize_database(db_path)
        return db_path
    
    @pytest.mark.asyncio
    async def test_run_command_db_check(self, db_path):
        """Test run_command with db.check."""
        result = await run_command("db.check", db_path=db_path)
        
        assert result["success"] is True
        assert "result" in result
    
    @pytest.mark.asyncio
    async def test_run_command_invalid_name(self):
        """Test run_command with invalid command name."""
        with pytest.raises(FacadeError) as exc_info:
            await run_command("invalid.command")
        
        assert "Unknown command" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_run_command_malformed_name(self):
        """Test run_command with malformed command name."""
        with pytest.raises(FacadeError) as exc_info:
            await run_command("invalid")
        
        assert "Invalid command name" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_run_command_chat_start(self, db_path):
        """Test run_command with chat.start."""
        result = await run_command("chat.start", db_path=db_path, title="Test")
        
        assert result["success"] is True
        assert "result" in result
        assert "session_id" in result["result"]


# ==================== Error Handling Tests ====================

class TestFacadeErrorHandling:
    """Tests for error handling in facade."""
    
    @pytest.fixture
    def facade(self, tmp_path):
        """Create facade instance."""
        db_path = tmp_path / "test.db"
        initialize_database(db_path)
        return AppFacade(db_path=db_path)
    
    @pytest.mark.asyncio
    async def test_error_serialization(self, facade):
        """Test that errors are properly serialized."""
        try:
            await facade.chat_resume(session_id="nonexistent")
        except FacadeChatError as e:
            error_dict = e.to_dict()
            assert "error_type" in error_dict
            assert "message" in error_dict
            assert "details" in error_dict
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, facade):
        """Test timeout handling."""
        # Create a slow operation
        async def slow_operation():
            await asyncio.sleep(0.1)  # Very short delay for test
            return {"result": "done"}
        
        # Test with very short timeout
        from src.interface_common.app_facade import _with_timeout
        
        with pytest.raises(FacadeTimeoutError):
            await _with_timeout(slow_operation(), timeout_seconds=0.01, operation="test")


# ==================== Integration Tests ====================

class TestFacadeIntegration:
    """Integration tests for facade."""
    
    @pytest.fixture
    def db_path(self, tmp_path):
        """Create test database."""
        db_path = tmp_path / "test.db"
        initialize_database(db_path)
        return db_path
    
    @pytest.fixture
    def facade(self, db_path):
        """Create facade instance."""
        return AppFacade(db_path=db_path)
    
    @pytest.mark.asyncio
    @patch('src.interface_common.app_facade.get_client')
    async def test_full_chat_flow(self, mock_get_client, facade):
        """Test full chat flow: start -> turn -> resume."""
        # Mock client
        mock_client = Mock()
        mock_client.chat_reply.return_value = "Test reply"
        mock_get_client.return_value = mock_client
        
        # Start session
        start_result = await facade.chat_start(title="Integration Test")
        session_id = start_result["result"]["session_id"]
        
        # Process turn
        turn_result = await facade.chat_turn(session_id=session_id, user_message="Hello")
        assert turn_result["success"] is True
        
        # Resume session
        resume_result = await facade.chat_resume(session_id=session_id)
        assert resume_result["success"] is True
        assert len(resume_result["result"]["messages"]) >= 2  # User + Tutor
    
    @pytest.mark.asyncio
    async def test_db_and_index_flow(self, facade, tmp_path):
        """Test database and index operations flow."""
        # Check database
        check_result = await facade.db_check()
        assert check_result["success"] is True
        
        # Build index
        build_result = await facade.index_build(use_stub=True)
        assert build_result["success"] is True
        
        # Check index status
        status_result = await facade.index_status()
        assert status_result["success"] is True
        
        # Search index
        search_result = await facade.index_search(query="test", topk=5, use_stub=True)
        assert search_result["success"] is True

