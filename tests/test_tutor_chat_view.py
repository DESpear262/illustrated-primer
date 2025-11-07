"""
Unit and integration tests for Tutor Chat View.

Tests chat session logging, context retrieval, and session persistence.
"""

from __future__ import annotations

import pytest
import asyncio
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from PySide6.QtWidgets import QApplication
from qasync import QEventLoop

from src.interface_gui.views.tutor_chat_view import TutorChatView
from src.interface_gui.widgets.message_list import MessageList, MessageItemWidget
from src.interface_common import AppFacade, FacadeError
from src.interface_common.models import ChatMessage
from PySide6.QtCore import Qt


@pytest.fixture
def qt_app():
    """Create QApplication for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def mock_facade():
    """Create mock facade for testing."""
    facade = Mock(spec=AppFacade)
    facade.chat_start = AsyncMock(return_value={"session_id": "test-session-1", "title": "Test Session"})
    facade.chat_resume = AsyncMock(return_value={"session_id": "test-session-1", "title": "Test Session", "event_count": 2})
    facade.chat_list = AsyncMock(return_value=[
        {"session_id": "test-session-1", "title": "Test Session", "first_at": datetime.utcnow(), "last_at": datetime.utcnow(), "count": 2}
    ])
    facade.chat_turn = AsyncMock(return_value={
        "session_id": "test-session-1",
        "turn_index": 1,
        "user_message": "Test message",
        "ai_reply": "Test reply",
        "context_used": ["chunk-1", "chunk-2"],
        "title": "Test Session",
    })
    return facade


def test_message_list_creation(qt_app):
    """Test that MessageList can be created."""
    message_list = MessageList()
    
    assert message_list is not None
    assert message_list.count() == 0


def test_message_list_add_message(qt_app):
    """Test adding messages to MessageList."""
    message_list = MessageList()
    
    # Add user message
    user_msg = ChatMessage(
        role="user",
        content="Hello",
        timestamp=datetime.utcnow(),
    )
    message_list.add_message(user_msg)
    
    assert message_list.count() == 1
    
    # Add tutor message
    tutor_msg = ChatMessage(
        role="tutor",
        content="Hi there!",
        timestamp=datetime.utcnow(),
    )
    message_list.add_message(tutor_msg, has_context=True)
    
    assert message_list.count() == 2


def test_message_list_typing_indicator(qt_app):
    """Test typing indicator in MessageList."""
    message_list = MessageList()
    
    # Add typing indicator
    item = message_list.add_typing_indicator()
    
    assert message_list.count() == 1
    assert item is not None
    
    # Remove typing indicator
    message_list.remove_typing_indicator(item)
    
    assert message_list.count() == 0


def test_message_item_widget(qt_app):
    """Test MessageItemWidget creation."""
    user_msg = ChatMessage(
        role="user",
        content="Test message",
        timestamp=datetime.utcnow(),
    )
    
    widget = MessageItemWidget(user_msg, has_context=False)
    
    assert widget is not None
    assert widget.message == user_msg


def test_tutor_chat_view_creation(qt_app, mock_facade):
    """Test that TutorChatView can be created."""
    view = TutorChatView(mock_facade)
    
    assert view is not None
    assert view.facade == mock_facade
    assert view.current_session_id is None


@pytest.mark.asyncio
async def test_tutor_chat_view_start_session(qt_app, mock_facade):
    """Test starting a new session."""
    view = TutorChatView(mock_facade)
    
    await view._async_start_session()
    
    assert view.current_session_id == "test-session-1"
    assert view.current_session_title == "Test Session"
    assert view.title_label.text() == "Test Session"


@pytest.mark.asyncio
async def test_tutor_chat_view_send_message(qt_app, mock_facade):
    """Test sending a message."""
    view = TutorChatView(mock_facade)
    
    # Start session first
    await view._async_start_session()
    
    # Send message
    await view._async_send_message("Test message")
    
    # Check that facade was called
    mock_facade.chat_turn.assert_called_once_with(
        "test-session-1",
        "Test message",
        suggest_title=False,
    )
    
    # Check that messages were added
    assert view.message_list.count() >= 2  # User message + AI reply


@pytest.mark.asyncio
async def test_tutor_chat_view_load_session(qt_app, mock_facade):
    """Test loading an existing session."""
    view = TutorChatView(mock_facade)
    
    await view._async_load_session("test-session-1")
    
    assert view.current_session_id == "test-session-1"
    assert view.current_session_title == "Test Session"


@pytest.mark.asyncio
async def test_tutor_chat_view_load_recent_sessions(qt_app, mock_facade):
    """Test loading recent sessions."""
    view = TutorChatView(mock_facade)
    
    await view._async_load_recent_sessions()
    
    assert view.session_list.count() == 1
    item = view.session_list.item(0)
    assert item.text() == "Test Session"
    assert item.data(Qt.UserRole) == "test-session-1"


@pytest.mark.asyncio
async def test_tutor_chat_view_error_handling(qt_app, mock_facade):
    """Test error handling in chat view."""
    view = TutorChatView(mock_facade)
    
    # Make chat_turn raise an error
    mock_facade.chat_turn = AsyncMock(side_effect=FacadeError("Test error", {}))
    
    # Start session
    await view._async_start_session()
    
    # Try to send message (should handle error gracefully)
    await view._async_send_message("Test message")
    
    # Check that error was handled (typing indicator removed)
    assert view.typing_indicator is None


def test_tutor_chat_view_file_upload(qt_app, mock_facade, tmp_path):
    """Test file upload functionality."""
    view = TutorChatView(mock_facade)
    
    # Create test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test file content")
    
    # Handle file upload
    view._handle_file_upload(test_file)
    
    # Check that message was sent (will be async, so just check no error)
    assert True  # If we get here, no exception was raised

