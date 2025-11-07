"""
Integration tests for GUI application.

Tests app launch, menu actions, and basic functionality.
"""

from __future__ import annotations

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from PySide6.QtWidgets import QApplication
from qasync import QEventLoop

from src.interface_gui.app import create_app, async_main
from src.interface_gui.views.main_window import MainWindow
from src.interface_common import get_facade


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
    facade = Mock()
    facade.db_check = AsyncMock(return_value={"status": "ok", "tables": 10, "event_count": 5})
    facade.index_status = AsyncMock(return_value={"path": "/test/index.bin", "vector_count": 100})
    facade.ai_routes = AsyncMock(return_value=[])
    facade.chat_list = AsyncMock(return_value=[])
    return facade


@pytest.mark.asyncio
async def test_app_launch(qt_app, mock_facade):
    """Test that app can launch successfully."""
    with patch('src.interface_gui.app.get_facade', return_value=mock_facade):
        with patch('src.interface_gui.views.main_window.get_facade', return_value=mock_facade):
            # Create app and loop
            app, loop = create_app()
            
            # Run async main
            exit_code = await async_main()
            
            # Should return 0 for success
            assert exit_code == 0


def test_main_window_creation(qt_app, mock_facade):
    """Test that MainWindow can be created."""
    window = MainWindow(mock_facade)
    
    # Check window properties
    assert window.windowTitle() == "AI Tutor"
    assert window.facade == mock_facade
    
    # Check tabs exist
    assert window.tab_widget.count() == 5
    assert window.tab_widget.tabText(0) == "Tutor Chat"
    assert window.tab_widget.tabText(1) == "Command Console"
    assert window.tab_widget.tabText(2) == "Review Queue"
    assert window.tab_widget.tabText(3) == "Knowledge Tree"
    assert window.tab_widget.tabText(4) == "Context Inspector"


def test_menu_bar_exists(qt_app, mock_facade):
    """Test that menu bar is created with all menus."""
    window = MainWindow(mock_facade)
    menubar = window.menuBar()
    
    # Get menu titles
    menu_titles = []
    for action in menubar.actions():
        if action.menu():
            menu_titles.append(action.menu().title())
    
    # Check for key menu items (File, Database, Index, AI, Chat, Review, Refresh, Progress, Help)
    assert "&File" in menu_titles
    assert "&Database" in menu_titles
    assert "&Index" in menu_titles
    assert "&AI" in menu_titles
    assert "&Chat" in menu_titles
    assert "&Review" in menu_titles
    assert "Re&fresh" in menu_titles
    assert "&Progress" in menu_titles
    assert "&Help" in menu_titles


def test_status_bar_exists(qt_app, mock_facade):
    """Test that status bar is created with health indicators."""
    window = MainWindow(mock_facade)
    status_bar = window.statusBar()
    
    # Check that status bar exists
    assert status_bar is not None
    
    # Check that health indicators exist
    assert hasattr(window, 'db_status_label')
    assert hasattr(window, 'faiss_status_label')
    assert hasattr(window, 'api_status_label')


@pytest.mark.asyncio
async def test_startup_health_check(qt_app, mock_facade):
    """Test that startup health check runs successfully."""
    window = MainWindow(mock_facade)
    
    # Run startup health check
    await window.check_startup_health()
    
    # Check that health status was updated
    assert window.db_health is not None
    assert window.faiss_health is not None
    assert window.api_health is not None


def test_loading_overlay(qt_app, mock_facade):
    """Test that loading overlay can be shown and hidden."""
    window = MainWindow(mock_facade)
    
    # Initially hidden
    assert not window.loading_overlay.isVisible()
    
    # Show loading
    window.show_loading("Test message")
    assert window.loading_overlay.isVisible()
    assert window.loading_label.text() == "Test message"
    
    # Hide loading
    window.hide_loading()
    assert not window.loading_overlay.isVisible()


@pytest.mark.asyncio
async def test_db_check_menu_action(qt_app, mock_facade):
    """Test that DB check menu action works."""
    window = MainWindow(mock_facade)
    
    # Trigger DB check
    await window._async_db_check()
    
    # Check that facade was called
    mock_facade.db_check.assert_called_once()
    
    # Check that health status was updated
    assert window.db_health is True


@pytest.mark.asyncio
async def test_index_status_menu_action(qt_app, mock_facade):
    """Test that Index status menu action works."""
    window = MainWindow(mock_facade)
    
    # Trigger index status
    await window._async_index_status()
    
    # Check that facade was called
    mock_facade.index_status.assert_called_once()
    
    # Check that health status was updated
    assert window.faiss_health is True

