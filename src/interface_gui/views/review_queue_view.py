"""
Review Queue View for AI Tutor GUI.

Provides table of topics sorted by review priority with filtering,
mark complete dialog, and refresh functionality.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, List, Dict, Any

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QDoubleSpinBox,
    QSpinBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QTextEdit,
    QCheckBox,
    QMessageBox,
    QFormLayout,
    QGroupBox,
)

from src.interface_common import AppFacade, FacadeError, FacadeTimeoutError

logger = logging.getLogger(__name__)


class ReviewCompleteDialog(QDialog):
    """
    Dialog for recording review outcome.
    
    Allows user to mark review as mastered/not mastered
    and optionally add notes.
    """
    
    def __init__(
        self,
        skill_id: str,
        topic_id: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ):
        """
        Initialize review complete dialog.
        
        Args:
            skill_id: Skill identifier being reviewed
            topic_id: Optional topic identifier
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.skill_id = skill_id
        self.topic_id = topic_id
        
        self.setWindowTitle("Mark Review Complete")
        self.setModal(True)
        self.resize(500, 300)
        
        # Setup UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)
        
        # Skill info
        info_label = QLabel(f"Skill: {self.skill_id}")
        if self.topic_id:
            info_label.setText(f"Skill: {self.skill_id}\nTopic: {self.topic_id}")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Outcome selection
        outcome_group = QGroupBox("Review Outcome")
        outcome_layout = QVBoxLayout()
        
        self.mastered_checkbox = QCheckBox("Mastered")
        self.mastered_checkbox.setChecked(True)
        outcome_layout.addWidget(self.mastered_checkbox)
        
        self.not_mastered_checkbox = QCheckBox("Not Mastered")
        outcome_layout.addWidget(self.not_mastered_checkbox)
        
        # Connect checkboxes to be mutually exclusive
        self.mastered_checkbox.toggled.connect(
            lambda checked: self.not_mastered_checkbox.setChecked(not checked) if checked else None
        )
        self.not_mastered_checkbox.toggled.connect(
            lambda checked: self.mastered_checkbox.setChecked(not checked) if checked else None
        )
        
        outcome_group.setLayout(outcome_layout)
        layout.addWidget(outcome_group)
        
        # Notes
        notes_label = QLabel("Notes (optional):")
        layout.addWidget(notes_label)
        
        self.notes_text = QTextEdit()
        self.notes_text.setPlaceholderText("Add any notes about this review...")
        self.notes_text.setMaximumHeight(100)
        layout.addWidget(self.notes_text)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def get_result(self) -> tuple[bool, Optional[str]]:
        """
        Get dialog result.
        
        Returns:
            Tuple of (mastered, notes)
        """
        mastered = self.mastered_checkbox.isChecked()
        notes = self.notes_text.toPlainText().strip() or None
        return mastered, notes


class ReviewQueueView(QWidget):
    """
    Review Queue View widget.
    
    Provides:
    - Table of review items sorted by priority
    - Filtering controls (topic, mastery range, limit)
    - Mark complete dialog
    - Refresh functionality
    - Empty state message
    """
    
    def __init__(
        self,
        facade: AppFacade,
        parent: Optional[QWidget] = None,
    ):
        """
        Initialize review queue view.
        
        Args:
            facade: AppFacade instance for backend operations
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.facade = facade
        
        # Review data
        self.review_items: List[Dict[str, Any]] = []
        
        # Setup UI
        self._setup_ui()
        
        # Load initial data
        self._refresh_reviews()
        
    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Filter controls
        filter_group = QGroupBox("Filters")
        filter_layout = QHBoxLayout()
        
        # Topic filter
        topic_label = QLabel("Topic:")
        filter_layout.addWidget(topic_label)
        
        self.topic_filter = QLineEdit()
        self.topic_filter.setPlaceholderText("Filter by topic ID (optional)")
        filter_layout.addWidget(self.topic_filter)
        
        # Mastery range
        mastery_label = QLabel("Mastery Range:")
        filter_layout.addWidget(mastery_label)
        
        self.min_mastery = QDoubleSpinBox()
        self.min_mastery.setRange(0.0, 1.0)
        self.min_mastery.setSingleStep(0.1)
        self.min_mastery.setValue(0.0)
        self.min_mastery.setSpecialValueText("Any")
        filter_layout.addWidget(self.min_mastery)
        
        self.max_mastery = QDoubleSpinBox()
        self.max_mastery.setRange(0.0, 1.0)
        self.max_mastery.setSingleStep(0.1)
        self.max_mastery.setValue(1.0)
        self.max_mastery.setSpecialValueText("Any")
        filter_layout.addWidget(self.max_mastery)
        
        # Limit
        limit_label = QLabel("Limit:")
        filter_layout.addWidget(limit_label)
        
        self.limit_spinbox = QSpinBox()
        self.limit_spinbox.setRange(1, 100)
        self.limit_spinbox.setValue(10)
        filter_layout.addWidget(self.limit_spinbox)
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._refresh_reviews)
        filter_layout.addWidget(self.refresh_button)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Skill ID",
            "Topic ID",
            "Current Mastery",
            "Decayed Mastery",
            "Days Since Review",
            "Priority Score",
            "Last Evidence",
            "Evidence Count",
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setSortingEnabled(True)
        self.table.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.table)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.mark_complete_button = QPushButton("Mark Complete")
        self.mark_complete_button.clicked.connect(self._on_mark_complete)
        self.mark_complete_button.setEnabled(False)
        button_layout.addWidget(self.mark_complete_button)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Connect table selection to button state
        self.table.selectionModel().selectionChanged.connect(
            lambda: self.mark_complete_button.setEnabled(
                len(self.table.selectedItems()) > 0
            )
        )
        
    def _refresh_reviews(self):
        """Refresh review list from backend."""
        # Get filter values
        topic_id = self.topic_filter.text().strip() or None
        min_mastery = self.min_mastery.value() if self.min_mastery.value() > 0.0 else None
        max_mastery = self.max_mastery.value() if self.max_mastery.value() < 1.0 else None
        limit = self.limit_spinbox.value()
        
        # Call facade
        async def _load():
            try:
                items = await self.facade.review_next(
                    limit=limit,
                    min_mastery=min_mastery,
                    max_mastery=max_mastery,
                    topic_id=topic_id,
                )
                self.review_items = items
                self._update_table()
            except FacadeError as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to load reviews: {e}",
                )
            except Exception as e:
                logger.exception("Unexpected error loading reviews")
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
        
    def _update_table(self):
        """Update table with current review items."""
        self.table.setRowCount(len(self.review_items))
        
        for row, item in enumerate(self.review_items):
            # Skill ID
            skill_id_item = QTableWidgetItem(item.get("skill_id", ""))
            skill_id_item.setData(Qt.UserRole, item)  # Store full item data
            self.table.setItem(row, 0, skill_id_item)
            
            # Topic ID
            topic_id_item = QTableWidgetItem(item.get("topic_id", "") or "")
            self.table.setItem(row, 1, topic_id_item)
            
            # Current Mastery
            current_mastery = item.get("current_mastery", 0.0)
            mastery_item = QTableWidgetItem(f"{current_mastery:.2f}")
            mastery_item.setData(Qt.UserRole, current_mastery)
            self.table.setItem(row, 2, mastery_item)
            
            # Decayed Mastery
            decayed_mastery = item.get("decayed_mastery", 0.0)
            decayed_item = QTableWidgetItem(f"{decayed_mastery:.2f}")
            decayed_item.setData(Qt.UserRole, decayed_mastery)
            self.table.setItem(row, 3, decayed_item)
            
            # Days Since Review
            days = item.get("days_since_review", 0.0)
            days_item = QTableWidgetItem(f"{days:.1f}")
            days_item.setData(Qt.UserRole, days)
            self.table.setItem(row, 4, days_item)
            
            # Priority Score
            priority = item.get("priority_score", 0.0)
            priority_item = QTableWidgetItem(f"{priority:.3f}")
            priority_item.setData(Qt.UserRole, priority)
            self.table.setItem(row, 5, priority_item)
            
            # Last Evidence
            last_evidence = item.get("last_evidence_at", "")
            last_evidence_item = QTableWidgetItem(last_evidence or "Never")
            self.table.setItem(row, 6, last_evidence_item)
            
            # Evidence Count
            evidence_count = item.get("evidence_count", 0)
            count_item = QTableWidgetItem(str(evidence_count))
            count_item.setData(Qt.UserRole, evidence_count)
            self.table.setItem(row, 7, count_item)
        
        # Resize columns to content
        self.table.resizeColumnsToContents()
        
        # Show empty state if no items
        if len(self.review_items) == 0:
            self.table.setRowCount(1)
            empty_item = QTableWidgetItem("No reviews needed")
            empty_item.setFlags(Qt.NoItemFlags)
            self.table.setItem(0, 0, empty_item)
            self.table.setSpan(0, 0, 1, 8)
        
    def _on_item_double_clicked(self, item: QTableWidgetItem):
        """Handle double-click on table item."""
        self._on_mark_complete()
        
    def _on_mark_complete(self):
        """Handle mark complete button click."""
        # Get selected row
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        if row >= len(self.review_items):
            return
        
        item = self.review_items[row]
        skill_id = item.get("skill_id")
        topic_id = item.get("topic_id")
        
        if not skill_id:
            return
        
        # Show dialog
        dialog = ReviewCompleteDialog(skill_id, topic_id, self)
        if dialog.exec() == QDialog.Accepted:
            mastered, notes = dialog.get_result()
            
            # Record review
            async def _record():
                try:
                    await self.facade.review_record(
                        skill_id=skill_id,
                        mastered=mastered,
                        review_content=notes,
                    )
                    
                    # Refresh list
                    self._refresh_reviews()
                    
                    QMessageBox.information(
                        self,
                        "Success",
                        f"Review recorded successfully.\n"
                        f"Skill: {skill_id}\n"
                        f"Outcome: {'Mastered' if mastered else 'Not Mastered'}",
                    )
                except FacadeError as e:
                    QMessageBox.warning(
                        self,
                        "Error",
                        f"Failed to record review: {e}",
                    )
                except Exception as e:
                    logger.exception("Unexpected error recording review")
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Unexpected error: {e}",
                    )
            
            # Run async
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(_record())
            else:
                loop.run_until_complete(_record())

