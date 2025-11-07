"""
Integration tests for Command Console View.

Tests command execution, results display, and history.
"""

from __future__ import annotations

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from PySide6.QtWidgets import QApplication

from src.interface_gui.views.command_view import CommandView
from src.interface_common import AppFacade


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
    facade.db_check = AsyncMock(return_value={"status": "ok", "tables": 10, "event_count": 5})
    facade.db_init = AsyncMock(return_value={"status": "ok", "message": "Database initialized"})
    facade.index_build = AsyncMock(return_value={"vector_count": 100, "event_count": 10})
    facade.index_status = AsyncMock(return_value={"path": "/test/index.bin", "vector_count": 100})
    facade.index_search = AsyncMock(return_value={"results": [{"id": 1, "score": 0.9}]})
    facade.ai_routes = AsyncMock(return_value=[{"task": "CHAT_REPLY", "model": "gpt-4o"}])
    facade.ai_test_summarize = AsyncMock(return_value={"summary": "Test summary"})
    facade.ai_test_classify = AsyncMock(return_value={"topics": ["topic1"], "skills": ["skill1"]})
    facade.ai_test_chat = AsyncMock(return_value={"reply": "Test reply"})
    facade.chat_start = AsyncMock(return_value={"session_id": "test-1", "title": "Test"})
    facade.chat_resume = AsyncMock(return_value={"session_id": "test-1", "title": "Test", "event_count": 2})
    facade.chat_list = AsyncMock(return_value=[{"session_id": "test-1", "title": "Test"}])
    return facade


def test_command_view_creation(qt_app, mock_facade):
    """Test that CommandView can be created."""
    view = CommandView(mock_facade)
    
    assert view is not None
    assert view.facade == mock_facade
    assert len(view.command_history) == 0


@pytest.mark.asyncio
async def test_db_check_command(qt_app, mock_facade):
    """Test DB Check command execution."""
    view = CommandView(mock_facade)
    
    await view._async_db_check()
    
    # Check that facade was called
    mock_facade.db_check.assert_called_once()
    
    # Check that result was displayed
    assert view.results_text.toPlainText() != ""
    assert len(view.command_history) == 1
    assert view.command_history[0]["command"] == "db.check"


@pytest.mark.asyncio
async def test_index_build_command(qt_app, mock_facade):
    """Test Index Build command execution."""
    view = CommandView(mock_facade)
    
    # Set form values
    view.index_build_event_id.setText("test-event-1")
    view.index_build_use_stub.setChecked(True)
    
    await view._async_index_build("test-event-1", True)
    
    # Check that facade was called
    mock_facade.index_build.assert_called_once_with(event_id="test-event-1", use_stub=True)
    
    # Check that result was displayed
    assert view.results_text.toPlainText() != ""
    assert len(view.command_history) == 1


@pytest.mark.asyncio
async def test_index_search_command(qt_app, mock_facade):
    """Test Index Search command execution."""
    view = CommandView(mock_facade)
    
    # Set form values
    view.index_search_query.setText("test query")
    view.index_search_topk.setValue(10)
    view.index_search_use_stub.setChecked(True)
    
    await view._async_index_search("test query", 10, True)
    
    # Check that facade was called
    mock_facade.index_search.assert_called_once_with(query="test query", top_k=10, use_stub=True)
    
    # Check that result was displayed
    assert view.results_text.toPlainText() != ""


@pytest.mark.asyncio
async def test_ai_routes_command(qt_app, mock_facade):
    """Test AI Routes command execution."""
    view = CommandView(mock_facade)
    
    await view._async_ai_routes()
    
    # Check that facade was called
    mock_facade.ai_routes.assert_called_once()
    
    # Check that result was displayed
    assert view.results_text.toPlainText() != ""


@pytest.mark.asyncio
async def test_chat_list_command(qt_app, mock_facade):
    """Test Chat List command execution."""
    view = CommandView(mock_facade)
    
    await view._async_chat_list()
    
    # Check that facade was called
    mock_facade.chat_list.assert_called_once()
    
    # Check that result was displayed
    assert view.results_text.toPlainText() != ""


def test_command_history(qt_app, mock_facade):
    """Test command history tracking."""
    view = CommandView(mock_facade)
    
    # Add command to history
    view._add_to_history("db.check", {})
    
    assert len(view.command_history) == 1
    assert view.command_history[0]["command"] == "db.check"
    assert view.history_list.count() == 1


def test_results_display(qt_app, mock_facade):
    """Test results display in different formats."""
    view = CommandView(mock_facade)
    
    # Display result
    result = {"status": "ok", "tables": 10}
    view._display_result(result, "Test Command")
    
    # Check that all tabs were updated
    assert view.results_text.toPlainText() != ""
    assert view.results_json.toPlainText() != ""
    assert view.results_table.rowCount() > 0


def test_error_display(qt_app, mock_facade):
    """Test error display."""
    view = CommandView(mock_facade)
    
    # Display error
    view._display_error("Test Command", "Test error message")
    
    # Check that error was displayed
    assert "ERROR" in view.results_text.toPlainText()
    assert "Test error message" in view.results_text.toPlainText()


def test_table_update(qt_app, mock_facade):
    """Test table update with different result types."""
    view = CommandView(mock_facade)
    
    # Test with dict
    result_dict = {"key1": "value1", "key2": "value2"}
    view._update_table(result_dict, "Test", "2024-01-01 00:00:00")
    assert view.results_table.rowCount() == 2
    assert view.results_table.columnCount() == 2
    
    # Test with list of dicts
    result_list = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
    view._update_table(result_list, "Test", "2024-01-01 00:00:00")
    assert view.results_table.rowCount() == 2
    assert view.results_table.columnCount() == 2
    
    # Test with simple list
    result_simple = ["item1", "item2", "item3"]
    view._update_table(result_simple, "Test", "2024-01-01 00:00:00")
    assert view.results_table.rowCount() == 3
    assert view.results_table.columnCount() == 1

