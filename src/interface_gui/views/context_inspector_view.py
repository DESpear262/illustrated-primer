"""
Context Inspector View for AI Tutor GUI.

Provides tree view of topics/skills with expand/collapse, node details,
and actions (summarize, recompute).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, Dict, Any

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QTextEdit,
    QSplitter,
    QGroupBox,
    QMessageBox,
    QProgressBar,
)

from src.interface_common import AppFacade, FacadeError, FacadeTimeoutError

logger = logging.getLogger(__name__)


class ContextInspectorView(QWidget):
    """
    Context Inspector View widget.
    
    Provides:
    - Tree view of topics/skills with expand/collapse
    - Node details panel (summary, statistics, recent events, related skills)
    - Expand button to load child nodes
    - Summarize button to refresh topic summary
    - Recompute button to recompute skill mastery
    - Manual refresh button
    """
    
    def __init__(
        self,
        facade: AppFacade,
        parent: Optional[QWidget] = None,
    ):
        """
        Initialize context inspector view.
        
        Args:
            facade: AppFacade instance for backend operations
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.facade = facade
        
        # Selected node
        self.selected_node_id: Optional[str] = None
        self.selected_node_type: Optional[str] = None
        
        # Expanded nodes cache
        self.expanded_nodes: set[str] = set()
        
        # Setup UI
        self._setup_ui()
        
        # Load initial hierarchy
        self._refresh_hierarchy()
        
    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._refresh_hierarchy)
        toolbar_layout.addWidget(self.refresh_button)
        
        self.expand_button = QPushButton("Expand")
        self.expand_button.clicked.connect(self._on_expand)
        self.expand_button.setEnabled(False)
        toolbar_layout.addWidget(self.expand_button)
        
        self.summarize_button = QPushButton("Summarize")
        self.summarize_button.clicked.connect(self._on_summarize)
        self.summarize_button.setEnabled(False)
        toolbar_layout.addWidget(self.summarize_button)
        
        self.recompute_button = QPushButton("Recompute")
        self.recompute_button.clicked.connect(self._on_recompute)
        self.recompute_button.setEnabled(False)
        toolbar_layout.addWidget(self.recompute_button)
        
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # Splitter for tree and details
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left: Tree view
        tree_group = QGroupBox("Topic Hierarchy")
        tree_layout = QVBoxLayout()
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Topics & Skills")
        self.tree.setColumnCount(1)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
        self.tree.itemExpanded.connect(self._on_item_expanded)
        self.tree.itemCollapsed.connect(self._on_item_collapsed)
        tree_layout.addWidget(self.tree)
        
        tree_group.setLayout(tree_layout)
        splitter.addWidget(tree_group)
        
        # Right: Details panel
        details_group = QGroupBox("Node Details")
        details_layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setPlaceholderText("Select a node to view details")
        details_layout.addWidget(self.details_text)
        
        details_group.setLayout(details_layout)
        splitter.addWidget(details_group)
        
        # Set splitter proportions (40% tree, 60% details)
        splitter.setSizes([400, 600])
        
    def _refresh_hierarchy(self):
        """Refresh topic hierarchy from backend."""
        async def _load():
            try:
                hierarchy = await self.facade.context_hierarchy()
                
                # Clear tree
                self.tree.clear()
                
                # Build tree from hierarchy
                roots = hierarchy.get("roots", [])
                for root in roots:
                    item = self._build_tree_item(root)
                    self.tree.addTopLevelItem(item)
                
                # Expand previously expanded nodes
                self._restore_expanded_state()
                
            except FacadeError as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to load hierarchy: {e}",
                )
            except Exception as e:
                logger.exception("Unexpected error loading hierarchy")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Unexpected error: {e}",
                )
        
        # Run async
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(_load())
        else:
            loop.run_until_complete(_load())
        
    def _build_tree_item(self, topic_dict: Dict[str, Any]) -> QTreeWidgetItem:
        """
        Build tree item from topic dictionary.
        
        Args:
            topic_dict: Topic dictionary with topic_id, summary, children, etc.
            
        Returns:
            QTreeWidgetItem for the topic
        """
        topic_id = topic_dict.get("topic_id", "")
        summary = topic_dict.get("summary", "")
        event_count = topic_dict.get("event_count", 0)
        
        # Create item
        item = QTreeWidgetItem([f"{topic_id} ({event_count} events)"])
        item.setData(0, Qt.UserRole, {"type": "topic", "id": topic_id, "data": topic_dict})
        
        # Add children
        children = topic_dict.get("children", [])
        for child in children:
            child_item = self._build_tree_item(child)
            item.addChild(child_item)
        
        # Mark as expandable if has children
        if children:
            item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
        
        return item
        
    def _restore_expanded_state(self):
        """Restore expanded state of nodes."""
        def expand_item(item: QTreeWidgetItem):
            data = item.data(0, Qt.UserRole)
            if data and isinstance(data, dict):
                node_id = data.get("id")
                if node_id and node_id in self.expanded_nodes:
                    item.setExpanded(True)
            
            # Recursively expand children
            for i in range(item.childCount()):
                expand_item(item.child(i))
        
        # Expand root items
        for i in range(self.tree.topLevelItemCount()):
            expand_item(self.tree.topLevelItem(i))
        
    def _on_selection_changed(self):
        """Handle tree selection change."""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            self.selected_node_id = None
            self.selected_node_type = None
            self.details_text.clear()
            self._update_button_states()
            return
        
        item = selected_items[0]
        data = item.data(0, Qt.UserRole)
        
        if data and isinstance(data, dict):
            self.selected_node_id = data.get("id")
            self.selected_node_type = data.get("type")
            
            # Load node details
            self._load_node_details()
            self._update_button_states()
        
    def _load_node_details(self):
        """Load details for selected node."""
        if not self.selected_node_id or not self.selected_node_type:
            return
        
        async def _load():
            try:
                hover_data = await self.facade.context_hover(
                    node_id=self.selected_node_id,
                    node_type=self.selected_node_type,
                )
                
                # Format details text
                details = self._format_node_details(hover_data)
                self.details_text.setPlainText(details)
                
            except FacadeError as e:
                self.details_text.setPlainText(f"Error loading details: {e}")
            except Exception as e:
                logger.exception("Unexpected error loading node details")
                self.details_text.setPlainText(f"Unexpected error: {e}")
        
        # Run async
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(_load())
        else:
            loop.run_until_complete(_load())
        
    def _format_node_details(self, hover_data: Dict[str, Any]) -> str:
        """
        Format node details for display.
        
        Args:
            hover_data: Hover payload from backend
            
        Returns:
            Formatted text string
        """
        lines = []
        
        if self.selected_node_type == "topic":
            lines.append(f"Topic: {hover_data.get('title', self.selected_node_id)}")
            lines.append("")
            lines.append("Summary:")
            lines.append(hover_data.get("summary", "No summary available"))
            lines.append("")
            lines.append(f"Event Count: {hover_data.get('event_count', 0)}")
            lines.append(f"Last Event: {hover_data.get('last_event_at', 'Never')}")
            lines.append(f"Average Mastery: {hover_data.get('average_mastery', 0.0):.2f}")
            lines.append(f"Child Skills: {hover_data.get('child_skills_count', 0)}")
            
            open_questions = hover_data.get("open_questions", [])
            if open_questions:
                lines.append("")
                lines.append("Open Questions:")
                for q in open_questions:
                    lines.append(f"  - {q}")
                    
        elif self.selected_node_type == "skill":
            lines.append(f"Skill: {hover_data.get('title', self.selected_node_id)}")
            lines.append("")
            lines.append(f"Mastery: {hover_data.get('p_mastery', 0.0):.2f}")
            lines.append(f"Last Evidence: {hover_data.get('last_evidence_at', 'Never')}")
            lines.append(f"Evidence Count: {hover_data.get('evidence_count', 0)}")
            
            recent_snippet = hover_data.get("recent_event_snippet")
            if recent_snippet:
                lines.append("")
                lines.append("Recent Event:")
                lines.append(recent_snippet)
        
        return "\n".join(lines)
        
    def _update_button_states(self):
        """Update button enabled states based on selection."""
        has_selection = self.selected_node_id is not None
        
        # Expand button: enabled for topics
        self.expand_button.setEnabled(
            has_selection and self.selected_node_type == "topic"
        )
        
        # Summarize button: enabled for topics
        self.summarize_button.setEnabled(
            has_selection and self.selected_node_type == "topic"
        )
        
        # Recompute button: enabled for topics
        self.recompute_button.setEnabled(
            has_selection and self.selected_node_type == "topic"
        )
        
    def _on_item_expanded(self, item: QTreeWidgetItem):
        """Handle item expansion."""
        data = item.data(0, Qt.UserRole)
        if data and isinstance(data, dict):
            node_id = data.get("id")
            if node_id:
                self.expanded_nodes.add(node_id)
        
    def _on_item_collapsed(self, item: QTreeWidgetItem):
        """Handle item collapse."""
        data = item.data(0, Qt.UserRole)
        if data and isinstance(data, dict):
            node_id = data.get("id")
            if node_id:
                self.expanded_nodes.discard(node_id)
        
    def _on_expand(self):
        """Handle expand button click."""
        if not self.selected_node_id or self.selected_node_type != "topic":
            return
        
        async def _expand():
            try:
                expanded = await self.facade.context_expand(
                    topic_id=self.selected_node_id,
                )
                
                # Find selected item
                selected_items = self.tree.selectedItems()
                if not selected_items:
                    return
                
                item = selected_items[0]
                
                # Add child topics
                child_topics = expanded.get("child_topics", [])
                for topic_dict in child_topics:
                    child_item = self._build_tree_item(topic_dict)
                    item.addChild(child_item)
                
                # Add child skills
                child_skills = expanded.get("child_skills", [])
                for skill_dict in child_skills:
                    skill_id = skill_dict.get("skill_id", "")
                    skill_item = QTreeWidgetItem([f"{skill_id} (skill)"])
                    skill_item.setData(0, Qt.UserRole, {
                        "type": "skill",
                        "id": skill_id,
                        "data": skill_dict,
                    })
                    item.addChild(skill_item)
                
                # Expand item
                item.setExpanded(True)
                self.expanded_nodes.add(self.selected_node_id)
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Expanded {len(child_topics)} topics and {len(child_skills)} skills",
                )
                
            except FacadeError as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to expand topic: {e}",
                )
            except Exception as e:
                logger.exception("Unexpected error expanding topic")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Unexpected error: {e}",
                )
        
        # Run async
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(_expand())
        else:
            loop.run_until_complete(_expand())
        
    def _on_summarize(self):
        """Handle summarize button click."""
        if not self.selected_node_id or self.selected_node_type != "topic":
            return
        
        async def _summarize():
            try:
                result = await self.facade.context_summarize(
                    topic_id=self.selected_node_id,
                    force=True,
                )
                
                # Refresh node details
                self._load_node_details()
                
                # Refresh hierarchy to update summary in tree
                self._refresh_hierarchy()
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Topic summarized successfully.\n"
                    f"Tokens used: {result.get('tokens_used', 'N/A')}",
                )
                
            except FacadeError as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to summarize topic: {e}",
                )
            except Exception as e:
                logger.exception("Unexpected error summarizing topic")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Unexpected error: {e}",
                )
        
        # Run async
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(_summarize())
        else:
            loop.run_until_complete(_summarize())
        
    def _on_recompute(self):
        """Handle recompute button click."""
        if not self.selected_node_id or self.selected_node_type != "topic":
            return
        
        async def _recompute():
            try:
                result = await self.facade.context_recompute(
                    topic_id=self.selected_node_id,
                )
                
                # Refresh node details
                self._load_node_details()
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Recomputed {result.get('skills_updated', 0)} skills.\n"
                    f"Average mastery: {result.get('average_mastery', 0.0):.2f}",
                )
                
            except FacadeError as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to recompute skills: {e}",
                )
            except Exception as e:
                logger.exception("Unexpected error recomputing skills")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Unexpected error: {e}",
                )
        
        # Run async
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(_recompute())
        else:
            loop.run_until_complete(_recompute())

