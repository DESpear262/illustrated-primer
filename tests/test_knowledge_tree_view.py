"""
Integration tests for Knowledge Tree View.

Tests graph rendering, WebChannel communication, and node interactions.
"""

from __future__ import annotations

import json
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from PySide6.QtWidgets import QApplication

from src.interface_gui.views.knowledge_tree_view import KnowledgeTreeView, GraphBridge
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
    facade.graph_get = AsyncMock(return_value={
        "nodes": [
            {
                "data": {
                    "id": "topic-1",
                    "type": "topic",
                    "label": "Topic 1",
                    "summary": "Test topic 1",
                    "event_count": 5,
                }
            },
            {
                "data": {
                    "id": "skill-1",
                    "type": "skill",
                    "label": "Skill 1",
                    "p_mastery": 0.7,
                    "topic_id": "topic-1",
                }
            },
        ],
        "edges": [
            {
                "data": {
                    "id": "topic-1-skill-1",
                    "source": "topic-1",
                    "target": "skill-1",
                    "type": "topic-skill",
                }
            },
        ],
    })
    facade.context_hover = AsyncMock(return_value={
        "title": "topic-1",
        "summary": "Test topic 1 summary",
        "event_count": 5,
        "last_event_at": "2024-01-01T00:00:00",
        "average_mastery": 0.7,
        "child_skills_count": 1,
        "open_questions": ["Question 1"],
    })
    return facade


def test_knowledge_tree_view_creation(qt_app, mock_facade):
    """Test that KnowledgeTreeView can be created."""
    view = KnowledgeTreeView(mock_facade)
    
    assert view is not None
    assert view.facade == mock_facade
    assert view.web_view is not None
    assert view.bridge is not None
    assert view.search_input is not None
    assert view.scope_combo is not None
    assert view.depth_spinbox is not None
    assert view.refresh_button is not None
    assert view.fit_button is not None


def test_graph_bridge_creation(qt_app, mock_facade):
    """Test that GraphBridge can be created."""
    bridge = GraphBridge(mock_facade)
    
    assert bridge is not None
    assert bridge.facade == mock_facade


@pytest.mark.asyncio
async def test_graph_bridge_get_graph(qt_app, mock_facade):
    """Test GraphBridge.getGraph method."""
    bridge = GraphBridge(mock_facade)
    
    # Call getGraph
    result_json = bridge.getGraph("root", 2, "all")
    result = json.loads(result_json)
    
    # Check that facade was called
    mock_facade.graph_get.assert_called_once_with(
        scope="root",
        depth=2,
        relation="all",
    )
    
    # Check result structure
    assert "nodes" in result
    assert "edges" in result


@pytest.mark.asyncio
async def test_graph_bridge_get_hover_payload(qt_app, mock_facade):
    """Test GraphBridge.getHoverPayload method."""
    bridge = GraphBridge(mock_facade)
    
    # Call getHoverPayload
    result_json = bridge.getHoverPayload("topic-1", "topic")
    result = json.loads(result_json)
    
    # Check that facade was called
    mock_facade.context_hover.assert_called_once_with(
        node_id="topic-1",
        node_type="topic",
    )
    
    # Check result structure
    assert "title" in result
    assert "summary" in result


def test_search_functionality(qt_app, mock_facade):
    """Test search input functionality."""
    view = KnowledgeTreeView(mock_facade)
    
    # Set search text
    view.search_input.setText("topic-1")
    
    # Trigger search (this will call JavaScript, which we can't easily test)
    view._on_search()
    
    # Just verify the method exists and doesn't crash
    assert hasattr(view, "_on_search")


def test_scope_change(qt_app, mock_facade):
    """Test scope change functionality."""
    view = KnowledgeTreeView(mock_facade)
    
    # Change scope
    view.scope_combo.setCurrentIndex(1)  # "All Nodes"
    
    # Trigger scope change
    view._on_scope_changed(1)
    
    # Just verify the method exists and doesn't crash
    assert hasattr(view, "_on_scope_changed")


def test_depth_change(qt_app, mock_facade):
    """Test depth change functionality."""
    view = KnowledgeTreeView(mock_facade)
    
    # Change depth
    view.depth_spinbox.setValue(3)
    
    # Trigger depth change
    view._on_depth_changed(3)
    
    # Just verify the method exists and doesn't crash
    assert hasattr(view, "_on_depth_changed")


def test_fit_to_screen(qt_app, mock_facade):
    """Test fit to screen functionality."""
    view = KnowledgeTreeView(mock_facade)
    
    # Trigger fit to screen
    view._on_fit_to_screen()
    
    # Just verify the method exists and doesn't crash
    assert hasattr(view, "_on_fit_to_screen")


def test_focus_node(qt_app, mock_facade):
    """Test focus node functionality."""
    view = KnowledgeTreeView(mock_facade)
    
    # Focus a node
    view.focus_node("topic-1")
    
    # Just verify the method exists and doesn't crash
    assert hasattr(view, "focus_node")


def test_node_double_clicked(qt_app, mock_facade):
    """Test node double-click handling."""
    view = KnowledgeTreeView(mock_facade)
    
    # Trigger double-click
    view._on_node_double_clicked("topic-1", "topic")
    
    # Just verify the method exists and doesn't crash
    assert hasattr(view, "_on_node_double_clicked")


def test_refresh_graph(qt_app, mock_facade):
    """Test graph refresh functionality."""
    view = KnowledgeTreeView(mock_facade)
    
    # Trigger refresh
    view._refresh_graph()
    
    # Just verify the method exists and doesn't crash
    assert hasattr(view, "_refresh_graph")

