"""
Integration tests for the GUI-backend facade.

Tests async operations with real backend components, ensuring
GUI can call facade methods successfully and LLM calls run
asynchronously without blocking.
"""

from __future__ import annotations

import asyncio
import pytest
from pathlib import Path
from unittest.mock import patch, Mock
from datetime import datetime

from src.interface_common.app_facade import AppFacade
from src.interface_common.exceptions import FacadeError, FacadeTimeoutError
from src.storage.db import initialize_database, Database
from src.models.base import Event
from uuid import uuid4


@pytest.fixture
def facade_with_db(tmp_path):
    """Create a facade instance with initialized database."""
    db_path = tmp_path / "test.db"
    index_path = tmp_path / "test_index.bin"
    
    # Initialize database
    initialize_database(db_path)
    
    return AppFacade(db_path=db_path, index_path=index_path)


@pytest.mark.asyncio
async def test_facade_chat_turn_integration(facade_with_db):
    """Test that GUI can call chat_turn successfully."""
    # Create a session
    session_result = await facade_with_db.chat_start()
    session_id = session_result["session_id"]
    
    # Mock AI client to avoid real API calls
    mock_client = Mock()
    mock_client.chat_reply = Mock(return_value="This is a test reply from the AI tutor.")
    
    facade_with_db.ai_client = mock_client
    
    # Process a chat turn
    result = await facade_with_db.chat_turn(session_id, "What is a derivative?")
    
    # Verify result structure
    assert "session_id" in result
    assert "turn_index" in result
    assert "user_message" in result
    assert "ai_reply" in result
    assert result["session_id"] == session_id
    assert result["user_message"] == "What is a derivative?"
    assert result["ai_reply"] == "This is a test reply from the AI tutor."
    
    # Verify events were created in database
    from src.interface.tutor_chat import _load_session_events
    events = _load_session_events(session_id, facade_with_db.db_path)
    assert len(events) >= 2  # At least user message and AI reply


@pytest.mark.asyncio
async def test_facade_llm_calls_async(facade_with_db):
    """Test that LLM calls run asynchronously without blocking."""
    # Create a session
    session_result = await facade_with_db.chat_start()
    session_id = session_result["session_id"]
    
    # Mock AI client with a delay to simulate real API call
    def delayed_chat_reply(*args, **kwargs):
        import time
        time.sleep(0.1)  # Simulate 100ms API call
        return "Delayed reply"
    
    mock_client = Mock()
    mock_client.chat_reply = Mock(side_effect=delayed_chat_reply)
    
    facade_with_db.ai_client = mock_client
    
    # Start multiple chat turns concurrently
    start_time = datetime.utcnow()
    
    tasks = [
        facade_with_db.chat_turn(session_id, f"Message {i}")
        for i in range(3)
    ]
    
    results = await asyncio.gather(*tasks)
    
    elapsed = (datetime.utcnow() - start_time).total_seconds()
    
    # Verify all tasks completed
    assert len(results) == 3
    for result in results:
        assert "ai_reply" in result
    
    # Verify operations ran concurrently (should be faster than sequential)
    # Sequential would take ~300ms, concurrent should be ~100ms
    assert elapsed < 0.3


@pytest.mark.asyncio
async def test_facade_db_check_integration(facade_with_db):
    """Test that db.check produces identical results to CLI."""
    # Add some test data
    with Database(facade_with_db.db_path) as db:
        event = Event(
            event_id=str(uuid4()),
            content="Test event",
            event_type="chat",
            actor="student",
        )
        db.insert_event(event)
    
    # Check database via facade
    result = await facade_with_db.db_check()
    
    # Verify structure matches CLI output
    assert result["status"] == "ok"
    assert "tables" in result
    assert "event_count" in result
    assert result["event_count"] >= 1


@pytest.mark.asyncio
async def test_facade_index_build_integration(facade_with_db):
    """Test that index.build produces identical results to CLI."""
    # Add some test events
    with Database(facade_with_db.db_path) as db:
        for i in range(3):
            event = Event(
                event_id=str(uuid4()),
                content=f"Test event {i}",
                event_type="chat",
                actor="student",
            )
            db.insert_event(event)
    
    # Build index via facade
    result = await facade_with_db.index_build(use_stub=True)
    
    # Verify structure matches CLI output
    assert "event_count" in result
    assert "chunk_count" in result
    assert result["event_count"] == 3
    assert result["chunk_count"] > 0


@pytest.mark.asyncio
async def test_facade_ai_test_integration(facade_with_db):
    """Test that ai.test commands produce identical results to CLI."""
    # Mock AI client
    mock_client = Mock()
    mock_client.summarize_event = Mock(return_value=Mock(
        summary="Test summary",
        topics=["math", "calculus"],
        skills=["derivatives"],
        key_points=["point1", "point2"],
        open_questions=["question1"],
    ))
    mock_client.classify_topics = Mock(return_value=Mock(
        topics=["math"],
        skills=["derivatives"],
        confidence=0.95,
    ))
    mock_client.chat_reply = Mock(return_value="Test chat reply")
    
    facade_with_db.ai_client = mock_client
    
    # Test summarize
    summarize_result = await facade_with_db.ai_test_summarize(text="Learning about derivatives")
    assert "summary" in summarize_result
    assert "topics" in summarize_result
    assert summarize_result["topics"] == ["math", "calculus"]
    
    # Test classify
    classify_result = await facade_with_db.ai_test_classify("Learning about derivatives")
    assert "topics" in classify_result
    assert "skills" in classify_result
    assert classify_result["topics"] == ["math"]
    
    # Test chat
    chat_result = await facade_with_db.ai_test_chat("What is a derivative?")
    assert isinstance(chat_result, str)
    assert chat_result == "Test chat reply"


@pytest.mark.asyncio
async def test_facade_run_command_integration(facade_with_db):
    """Test that run_command dispatcher works correctly."""
    # Test db.check via dispatcher
    result = await facade_with_db.run_command("db.check")
    assert result["status"] == "ok"
    
    # Test index.status via dispatcher
    result = await facade_with_db.run_command("index.status")
    assert "path" in result
    assert "vector_count" in result
    
    # Test chat.start via dispatcher
    result = await facade_with_db.run_command("chat.start", {"title": "Test Session"})
    assert "session_id" in result
    assert result["title"] == "Test Session"
    
    # Test chat.turn via dispatcher
    session_id = result["session_id"]
    
    # Mock AI client
    mock_client = Mock()
    mock_client.chat_reply = Mock(return_value="Test reply")
    facade_with_db.ai_client = mock_client
    
    result = await facade_with_db.run_command("chat.turn", {
        "session_id": session_id,
        "user_message": "Hello",
    })
    assert "ai_reply" in result
    assert result["ai_reply"] == "Test reply"


@pytest.mark.asyncio
async def test_facade_error_handling_integration(facade_with_db):
    """Test that errors are properly caught and serialized for UI display."""
    # Test validation error
    with pytest.raises(FacadeError) as exc_info:
        await facade_with_db.ai_test_classify("")
    
    error = exc_info.value
    assert hasattr(error, "message")
    assert hasattr(error, "details")
    
    # Test timeout error
    with patch("src.interface_common.app_facade.load_index") as mock_load:
        def slow_load(*args):
            import time
            time.sleep(10)
        mock_load.side_effect = slow_load
        
        with pytest.raises(FacadeTimeoutError) as exc_info:
            await facade_with_db.index_status()
        
        error = exc_info.value
        assert hasattr(error, "operation")
        assert hasattr(error, "timeout_seconds")
        assert error.operation == "index.status"


@pytest.mark.asyncio
async def test_facade_chat_session_persistence(facade_with_db):
    """Test that chat sessions persist across facade calls."""
    # Create session
    session_result = await facade_with_db.chat_start(title="Test Session")
    session_id = session_result["session_id"]
    
    # Mock AI client
    mock_client = Mock()
    mock_client.chat_reply = Mock(return_value="Reply 1")
    facade_with_db.ai_client = mock_client
    
    # Process first turn
    result1 = await facade_with_db.chat_turn(session_id, "Message 1")
    assert result1["turn_index"] == 1
    
    # Process second turn
    mock_client.chat_reply = Mock(return_value="Reply 2")
    result2 = await facade_with_db.chat_turn(session_id, "Message 2")
    assert result2["turn_index"] == 2
    
    # Resume session
    resume_result = await facade_with_db.chat_resume(session_id)
    assert resume_result["session_id"] == session_id
    assert resume_result["event_count"] >= 4  # At least 2 user + 2 AI messages
    
    # List sessions
    list_result = await facade_with_db.chat_list(limit=10)
    assert len(list_result) >= 1
    assert any(s["session_id"] == session_id for s in list_result)

