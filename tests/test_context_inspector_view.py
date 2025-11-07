"""
Integration tests for Context Inspector View.

Tests tree view, node details, and actions (expand, summarize, recompute).
"""

from __future__ import annotations

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from PySide6.QtWidgets import QApplication

from src.interface_gui.views.context_inspector_view import ContextInspectorView
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
    facade.context_hierarchy = AsyncMock(return_value={
        "roots": [
            {
                "topic_id": "topic-1",
                "parent_topic_id": None,
                "summary": "Test topic 1",
                "open_questions": ["Question 1"],
                "event_count": 5,
                "last_event_at": "2024-01-01T00:00:00",
                "children": [
                    {
                        "topic_id": "topic-1-1",
                        "parent_topic_id": "topic-1",
                        "summary": "Test subtopic 1",
                        "open_questions": [],
                        "event_count": 2,
                        "last_event_at": "2024-01-02T00:00:00",
                        "children": [],
                    },
                ],
            },
        ],
    })
    facade.context_hover = AsyncMock(return_value={
        "title": "topic-1",
        "summary": "Test topic 1 summary",
        "event_count": 5,
        "last_event_at": "2024-01-01T00:00:00",
        "average_mastery": 0.7,
        "child_skills_count": 3,
        "open_questions": ["Question 1"],
    })
    facade.context_expand = AsyncMock(return_value={
        "child_topics": [
            {
                "topic_id": "topic-1-2",
                "parent_topic_id": "topic-1",
                "summary": "Test subtopic 2",
                "event_count": 1,
                "last_event_at": "2024-01-03T00:00:00",
            },
        ],
        "child_skills": [
            {
                "skill_id": "skill-1",
                "topic_id": "topic-1",
                "p_mastery": 0.8,
                "last_evidence_at": "2024-01-01T00:00:00",
                "evidence_count": 2,
            },
        ],
    })
    facade.context_summarize = AsyncMock(return_value={
        "topic_id": "topic-1",
        "summary": "Updated summary",
        "open_questions": ["Question 1", "Question 2"],
        "tokens_used": 100,
    })
    facade.context_recompute = AsyncMock(return_value={
        "topic_id": "topic-1",
        "skills_updated": 3,
        "average_mastery": 0.75,
    })
    return facade


def test_context_inspector_view_creation(qt_app, mock_facade):
    """Test that ContextInspectorView can be created."""
    view = ContextInspectorView(mock_facade)
    
    assert view is not None
    assert view.facade == mock_facade
    assert view.tree is not None
    assert view.details_text is not None
    assert view.refresh_button is not None
    assert view.expand_button is not None
    assert view.summarize_button is not None
    assert view.recompute_button is not None


@pytest.mark.asyncio
async def test_context_inspector_refresh(qt_app, mock_facade):
    """Test context inspector refresh."""
    view = ContextInspectorView(mock_facade)
    
    # Trigger refresh
    view._refresh_hierarchy()
    
    # Wait for async operation
    await asyncio.sleep(0.1)
    
    # Check that facade was called
    mock_facade.context_hierarchy.assert_called_once()
    
    # Check that tree was updated
    assert view.tree.topLevelItemCount() > 0


def test_build_tree_item(qt_app, mock_facade):
    """Test tree item building."""
    view = ContextInspectorView(mock_facade)
    
    topic_dict = {
        "topic_id": "topic-1",
        "parent_topic_id": None,
        "summary": "Test topic",
        "open_questions": [],
        "event_count": 5,
        "last_event_at": "2024-01-01T00:00:00",
        "children": [],
    }
    
    item = view._build_tree_item(topic_dict)
    
    assert item is not None
    assert item.text(0) == "topic-1 (5 events)"
    
    # Check data
    data = item.data(0, view.tree.model().UserRole)
    assert data is not None
    assert data["type"] == "topic"
    assert data["id"] == "topic-1"


def test_selection_changed(qt_app, mock_facade):
    """Test selection change handling."""
    view = ContextInspectorView(mock_facade)
    
    # Build a tree item
    topic_dict = {
        "topic_id": "topic-1",
        "parent_topic_id": None,
        "summary": "Test topic",
        "open_questions": [],
        "event_count": 5,
        "last_event_at": "2024-01-01T00:00:00",
        "children": [],
    }
    item = view._build_tree_item(topic_dict)
    view.tree.addTopLevelItem(item)
    
    # Select item
    view.tree.setCurrentItem(item)
    
    # Trigger selection change
    view._on_selection_changed()
    
    # Check that node ID and type are set
    assert view.selected_node_id == "topic-1"
    assert view.selected_node_type == "topic"


def test_format_node_details_topic(qt_app, mock_facade):
    """Test node details formatting for topic."""
    view = ContextInspectorView(mock_facade)
    view.selected_node_id = "topic-1"
    view.selected_node_type = "topic"
    
    hover_data = {
        "title": "topic-1",
        "summary": "Test topic summary",
        "event_count": 5,
        "last_event_at": "2024-01-01T00:00:00",
        "average_mastery": 0.7,
        "child_skills_count": 3,
        "open_questions": ["Question 1"],
    }
    
    details = view._format_node_details(hover_data)
    
    assert "topic-1" in details
    assert "Test topic summary" in details
    assert "Event Count: 5" in details
    assert "Average Mastery: 0.70" in details
    assert "Child Skills: 3" in details
    assert "Question 1" in details


def test_format_node_details_skill(qt_app, mock_facade):
    """Test node details formatting for skill."""
    view = ContextInspectorView(mock_facade)
    view.selected_node_id = "skill-1"
    view.selected_node_type = "skill"
    
    hover_data = {
        "title": "skill-1",
        "p_mastery": 0.8,
        "last_evidence_at": "2024-01-01T00:00:00",
        "evidence_count": 2,
        "recent_event_snippet": "Test event snippet",
    }
    
    details = view._format_node_details(hover_data)
    
    assert "skill-1" in details
    assert "Mastery: 0.80" in details
    assert "Evidence Count: 2" in details
    assert "Test event snippet" in details


def test_update_button_states(qt_app, mock_facade):
    """Test button state updates."""
    view = ContextInspectorView(mock_facade)
    
    # No selection
    view.selected_node_id = None
    view.selected_node_type = None
    view._update_button_states()
    
    assert view.expand_button.isEnabled() is False
    assert view.summarize_button.isEnabled() is False
    assert view.recompute_button.isEnabled() is False
    
    # Topic selection
    view.selected_node_id = "topic-1"
    view.selected_node_type = "topic"
    view._update_button_states()
    
    assert view.expand_button.isEnabled() is True
    assert view.summarize_button.isEnabled() is True
    assert view.recompute_button.isEnabled() is True
    
    # Skill selection
    view.selected_node_id = "skill-1"
    view.selected_node_type = "skill"
    view._update_button_states()
    
    assert view.expand_button.isEnabled() is False
    assert view.summarize_button.isEnabled() is False
    assert view.recompute_button.isEnabled() is False


@pytest.mark.asyncio
async def test_expand_action(qt_app, mock_facade):
    """Test expand action."""
    view = ContextInspectorView(mock_facade)
    view.selected_node_id = "topic-1"
    view.selected_node_type = "topic"
    
    # Build a tree item
    topic_dict = {
        "topic_id": "topic-1",
        "parent_topic_id": None,
        "summary": "Test topic",
        "open_questions": [],
        "event_count": 5,
        "last_event_at": "2024-01-01T00:00:00",
        "children": [],
    }
    item = view._build_tree_item(topic_dict)
    view.tree.addTopLevelItem(item)
    view.tree.setCurrentItem(item)
    
    # Trigger expand
    view._on_expand()
    
    # Wait for async operation
    await asyncio.sleep(0.1)
    
    # Check that facade was called
    mock_facade.context_expand.assert_called_once_with(topic_id="topic-1")


@pytest.mark.asyncio
async def test_summarize_action(qt_app, mock_facade):
    """Test summarize action."""
    view = ContextInspectorView(mock_facade)
    view.selected_node_id = "topic-1"
    view.selected_node_type = "topic"
    
    # Trigger summarize
    view._on_summarize()
    
    # Wait for async operation
    await asyncio.sleep(0.1)
    
    # Check that facade was called
    mock_facade.context_summarize.assert_called_once_with(
        topic_id="topic-1",
        force=True,
    )


@pytest.mark.asyncio
async def test_recompute_action(qt_app, mock_facade):
    """Test recompute action."""
    view = ContextInspectorView(mock_facade)
    view.selected_node_id = "topic-1"
    view.selected_node_type = "topic"
    
    # Trigger recompute
    view._on_recompute()
    
    # Wait for async operation
    await asyncio.sleep(0.1)
    
    # Check that facade was called
    mock_facade.context_recompute.assert_called_once_with(topic_id="topic-1")

