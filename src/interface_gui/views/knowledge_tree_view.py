"""
Knowledge Tree View for AI Tutor GUI.

Provides interactive DAG visualization using Cytoscape.js with QWebEngineView
and QtWebChannel for Python↔JS communication.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtCore import Qt, QObject, Signal, QUrl, Property, Slot
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QMessageBox,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel

from src.interface_common import AppFacade, FacadeError, FacadeTimeoutError

logger = logging.getLogger(__name__)


class GraphBridge(QObject):
    """
    QtWebChannel bridge for Python↔JS communication.
    
    Exposes Python methods to JavaScript for graph operations.
    """
    
    # Signals for JS→Python communication
    nodeClicked = Signal(str, str)  # nodeId, nodeType
    nodeDoubleClicked = Signal(str, str)  # nodeId, nodeType
    hoverRequested = Signal(str, str)  # nodeId, nodeType
    
    def __init__(self, facade: AppFacade, parent: Optional[QObject] = None):
        """
        Initialize graph bridge.
        
        Args:
            facade: AppFacade instance for backend operations
            parent: Optional parent object
        """
        super().__init__(parent)
        self.facade = facade
        
    @Slot(str, int, str, result=str)
    def getGraph(self, scope: str, depth: int, relation: str) -> str:
        """
        Get graph JSON from backend.
        
        Args:
            scope: Graph scope ("all", "root", or "topic:<id>")
            depth: Maximum depth (use -1 for unlimited)
            relation: Edge types ("all", "parent-child", or "topic-skill")
            
        Returns:
            JSON string with nodes and edges
        """
        async def _get():
            try:
                depth_val = None if depth == -1 else depth
                result = await self.facade.graph_get(
                    scope=scope,
                    depth=depth_val,
                    relation=relation,
                )
                return json.dumps(result)
            except Exception as e:
                logger.exception("Error getting graph")
                return json.dumps({"nodes": [], "edges": [], "error": str(e)})
        
        # Run async
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Schedule coroutine
            future = asyncio.run_coroutine_threadsafe(_get(), loop)
            return future.result()
        else:
            return loop.run_until_complete(_get())
    
    @Slot(str, str, result=str)
    def getHoverPayload(self, nodeId: str, nodeType: str) -> str:
        """
        Get hover payload for a node.
        
        Args:
            nodeId: Node identifier
            nodeType: Node type ("topic" or "skill")
            
        Returns:
            JSON string with hover payload
        """
        async def _get():
            try:
                result = await self.facade.context_hover(
                    node_id=nodeId,
                    node_type=nodeType,
                )
                return json.dumps(result)
            except Exception as e:
                logger.exception("Error getting hover payload")
                return json.dumps({"error": str(e)})
        
        # Run async
        loop = asyncio.get_event_loop()
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(_get(), loop)
            return future.result()
        else:
            return loop.run_until_complete(_get())
    
    @Slot(str)
    def onNodeClicked(self, nodeId: str):
        """
        Handle node click from JavaScript.
        
        Args:
            nodeId: Node identifier
        """
        # Get node type from graph data (we'll need to store this)
        # For now, emit with unknown type
        self.nodeClicked.emit(nodeId, "unknown")
    
    @Slot(str, str)
    def onNodeDoubleClicked(self, nodeId: str, nodeType: str):
        """
        Handle node double-click from JavaScript.
        
        Args:
            nodeId: Node identifier
            nodeType: Node type ("topic" or "skill")
        """
        self.nodeDoubleClicked.emit(nodeId, nodeType)
    
    @Slot(str, str)
    def onHoverRequested(self, nodeId: str, nodeType: str):
        """
        Handle hover request from JavaScript.
        
        Args:
            nodeId: Node identifier
            nodeType: Node type ("topic" or "skill")
        """
        self.hoverRequested.emit(nodeId, nodeType)


class KnowledgeTreeView(QWidget):
    """
    Knowledge Tree View widget.
    
    Provides:
    - Interactive DAG visualization using Cytoscape.js
    - Zoom, pan, hover, and node focus
    - Color coding by node type and mastery
    - Search functionality
    - Refresh and fit-to-screen controls
    """
    
    def __init__(
        self,
        facade: AppFacade,
        parent: Optional[QWidget] = None,
    ):
        """
        Initialize knowledge tree view.
        
        Args:
            facade: AppFacade instance for backend operations
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.facade = facade
        
        # Setup UI
        self._setup_ui()
        
        # Setup WebChannel bridge
        self._setup_webchannel()
        
        # Load initial graph
        self._refresh_graph()
        
    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        # Search
        search_label = QLabel("Search:")
        toolbar_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter node ID...")
        self.search_input.returnPressed.connect(self._on_search)
        toolbar_layout.addWidget(self.search_input)
        
        # Scope
        scope_label = QLabel("Scope:")
        toolbar_layout.addWidget(scope_label)
        
        self.scope_combo = QComboBox()
        self.scope_combo.addItems(["Root Topics", "All Nodes", "Topic Subtree"])
        self.scope_combo.setCurrentIndex(0)  # Default to root
        self.scope_combo.currentIndexChanged.connect(self._on_scope_changed)
        toolbar_layout.addWidget(self.scope_combo)
        
        # Depth
        depth_label = QLabel("Depth:")
        toolbar_layout.addWidget(depth_label)
        
        self.depth_spinbox = QSpinBox()
        self.depth_spinbox.setRange(-1, 10)
        self.depth_spinbox.setValue(2)
        self.depth_spinbox.setSpecialValueText("Unlimited")
        self.depth_spinbox.valueChanged.connect(self._on_depth_changed)
        toolbar_layout.addWidget(self.depth_spinbox)
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._refresh_graph)
        toolbar_layout.addWidget(self.refresh_button)
        
        # Fit to screen button
        self.fit_button = QPushButton("Fit to Screen")
        self.fit_button.clicked.connect(self._on_fit_to_screen)
        toolbar_layout.addWidget(self.fit_button)
        
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # WebEngine view
        self.web_view = QWebEngineView()
        
        # Get HTML file path
        html_path = Path(__file__).parent.parent / "web" / "knowledge_tree" / "index.html"
        if html_path.exists():
            self.web_view.setUrl(QUrl.fromLocalFile(str(html_path.absolute())))
        else:
            # Create placeholder HTML if file doesn't exist yet
            self.web_view.setHtml("""
                <html>
                <head><title>Knowledge Tree</title></head>
                <body>
                    <h1>Knowledge Tree</h1>
                    <p>Loading...</p>
                </body>
                </html>
            """)
        
        layout.addWidget(self.web_view)
        
    def _setup_webchannel(self):
        """Setup QtWebChannel bridge."""
        # Create bridge
        self.bridge = GraphBridge(self.facade, self)
        
        # Connect signals
        self.bridge.nodeDoubleClicked.connect(self._on_node_double_clicked)
        
        # Create WebChannel
        channel = QWebChannel(self.web_view.page())
        channel.registerObject("bridge", self.bridge)
        self.web_view.page().setWebChannel(channel)
        
    def _refresh_graph(self):
        """Refresh graph from backend."""
        # Get current scope and depth
        scope_index = self.scope_combo.currentIndex()
        if scope_index == 0:
            scope = "root"
        elif scope_index == 1:
            scope = "all"
        else:
            # Topic subtree - would need topic ID input
            scope = "root"  # Default for now
        
        depth = self.depth_spinbox.value()
        if depth == -1:
            depth = None
        
        # Call JavaScript to refresh graph
        js_code = f"""
        if (typeof refreshGraph === 'function') {{
            refreshGraph('{scope}', {depth if depth is not None else -1}, 'all');
        }}
        """
        self.web_view.page().runJavaScript(js_code)
        
    def _on_search(self):
        """Handle search input."""
        node_id = self.search_input.text().strip()
        if not node_id:
            return
        
        # Call JavaScript to focus node
        js_code = f"""
        if (typeof focusNode === 'function') {{
            focusNode('{node_id}');
        }}
        """
        self.web_view.page().runJavaScript(js_code)
        
    def _on_scope_changed(self, index: int):
        """Handle scope change."""
        self._refresh_graph()
        
    def _on_depth_changed(self, value: int):
        """Handle depth change."""
        self._refresh_graph()
        
    def _on_fit_to_screen(self):
        """Handle fit to screen button."""
        js_code = """
        if (typeof fitToScreen === 'function') {
            fitToScreen();
        }
        """
        self.web_view.page().runJavaScript(js_code)
        
    def _on_node_double_clicked(self, node_id: str, node_type: str):
        """
        Handle node double-click.
        
        Opens Context Inspector tab with node selected.
        
        Args:
            node_id: Node identifier
            node_type: Node type ("topic" or "skill")
        """
        # Emit signal to MainWindow to switch to Context Inspector tab
        # For now, just show a message
        QMessageBox.information(
            self,
            "Node Selected",
            f"Double-clicked node: {node_id} ({node_type})\n\n"
            "This will open the Context Inspector tab in a future update.",
        )
        
    def focus_node(self, node_id: str):
        """
        Focus a specific node in the graph.
        
        Called from MainWindow when navigating from Context Inspector.
        
        Args:
            node_id: Node identifier to focus
        """
        js_code = f"""
        if (typeof focusNode === 'function') {{
            focusNode('{node_id}');
        }}
        """
        self.web_view.page().runJavaScript(js_code)

