"""
Command Console View for AI Tutor GUI.

Provides visual interface for all CLI operations with form inputs,
results display, and command history.
"""

from __future__ import annotations

import asyncio
import json
import csv
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from io import StringIO

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QComboBox,
    QGroupBox,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QSplitter,
    QFileDialog,
    QMessageBox,
    QProgressBar,
    QListWidget,
    QListWidgetItem,
    QFormLayout,
)

from src.interface_common import AppFacade, FacadeError, FacadeTimeoutError
from src.config import DB_PATH, FAISS_INDEX_PATH

logger = logging.getLogger(__name__)


class CommandView(QWidget):
    """
    Command Console View widget.
    
    Provides:
    - Grouped command sections (Database, Index, AI, Chat, Review, Import, Refresh, Progress)
    - Form fields for command parameters
    - Results display with tabs (Table/JSON/Text)
    - Command history with re-execution
    - Export functionality (JSON/CSV/Text)
    - Progress bars for long operations
    - Parameter validation
    """
    
    def __init__(
        self,
        facade: AppFacade,
        parent: Optional[QWidget] = None,
    ):
        """
        Initialize command view.
        
        Args:
            facade: AppFacade instance for backend operations
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.facade = facade
        
        # Command history
        self.command_history: List[Dict[str, Any]] = []
        
        # Last used values per command
        self.last_values: Dict[str, Dict[str, Any]] = {}
        
        # Setup UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup UI components."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left side: Command groups
        command_panel = self._create_command_panel()
        splitter.addWidget(command_panel)
        splitter.setStretchFactor(0, 0)
        
        # Right side: Results and history
        results_panel = self._create_results_panel()
        splitter.addWidget(results_panel)
        splitter.setStretchFactor(1, 1)
        
        # Set splitter sizes (30% commands, 70% results)
        splitter.setSizes([300, 700])
        
    def _create_command_panel(self) -> QWidget:
        """Create command groups panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        title_label = QLabel("Commands")
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title_label)
        
        # Scroll area for command groups
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._create_command_groups())
        layout.addWidget(scroll)
        
        return widget
        
    def _create_command_groups(self) -> QWidget:
        """Create collapsible command groups."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Database group
        db_group = self._create_database_group()
        layout.addWidget(db_group)
        
        # Index group
        index_group = self._create_index_group()
        layout.addWidget(index_group)
        
        # AI group
        ai_group = self._create_ai_group()
        layout.addWidget(ai_group)
        
        # Chat group
        chat_group = self._create_chat_group()
        layout.addWidget(chat_group)
        
        # Review group
        review_group = self._create_review_group()
        layout.addWidget(review_group)
        
        # Import group
        import_group = self._create_import_group()
        layout.addWidget(import_group)
        
        # Refresh group
        refresh_group = self._create_refresh_group()
        layout.addWidget(refresh_group)
        
        # Progress group
        progress_group = self._create_progress_group()
        layout.addWidget(progress_group)
        
        layout.addStretch()
        
        return widget
        
    def _create_database_group(self) -> QGroupBox:
        """Create Database command group."""
        group = QGroupBox("Database")
        layout = QVBoxLayout(group)
        
        # DB Check
        check_btn = QPushButton("Check")
        check_btn.clicked.connect(self._on_db_check)
        layout.addWidget(check_btn)
        
        # DB Init
        init_btn = QPushButton("Initialize")
        init_btn.clicked.connect(self._on_db_init)
        layout.addWidget(init_btn)
        
        return group
        
    def _create_index_group(self) -> QGroupBox:
        """Create Index command group."""
        group = QGroupBox("Index")
        layout = QVBoxLayout(group)
        
        # Index Build
        build_layout = QVBoxLayout()
        build_layout.addWidget(QLabel("Build:"))
        
        self.index_build_event_id = QLineEdit()
        self.index_build_event_id.setPlaceholderText("Event ID (optional)")
        build_layout.addWidget(self.index_build_event_id)
        
        self.index_build_use_stub = QCheckBox("Use stub embeddings")
        self.index_build_use_stub.setChecked(True)
        build_layout.addWidget(self.index_build_use_stub)
        
        build_btn = QPushButton("Build")
        build_btn.clicked.connect(self._on_index_build)
        build_layout.addWidget(build_btn)
        
        layout.addLayout(build_layout)
        
        # Index Status
        status_btn = QPushButton("Status")
        status_btn.clicked.connect(self._on_index_status)
        layout.addWidget(status_btn)
        
        # Index Search
        search_layout = QVBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        
        self.index_search_query = QLineEdit()
        self.index_search_query.setPlaceholderText("Search query")
        search_layout.addWidget(self.index_search_query)
        
        topk_layout = QHBoxLayout()
        topk_layout.addWidget(QLabel("Top-K:"))
        self.index_search_topk = QSpinBox()
        self.index_search_topk.setMinimum(1)
        self.index_search_topk.setMaximum(100)
        self.index_search_topk.setValue(5)
        topk_layout.addWidget(self.index_search_topk)
        topk_layout.addStretch()
        search_layout.addLayout(topk_layout)
        
        self.index_search_use_stub = QCheckBox("Use stub embeddings")
        self.index_search_use_stub.setChecked(True)
        search_layout.addWidget(self.index_search_use_stub)
        
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._on_index_search)
        search_layout.addWidget(search_btn)
        
        layout.addLayout(search_layout)
        
        return group
        
    def _create_ai_group(self) -> QGroupBox:
        """Create AI command group."""
        group = QGroupBox("AI")
        layout = QVBoxLayout(group)
        
        # AI Routes
        routes_btn = QPushButton("Routes")
        routes_btn.clicked.connect(self._on_ai_routes)
        layout.addWidget(routes_btn)
        
        # AI Test Summarize
        test_summarize_layout = QVBoxLayout()
        test_summarize_layout.addWidget(QLabel("Test Summarize:"))
        
        self.ai_test_summarize_text = QTextEdit()
        self.ai_test_summarize_text.setPlaceholderText("Event content to summarize")
        self.ai_test_summarize_text.setMaximumHeight(80)
        test_summarize_layout.addWidget(self.ai_test_summarize_text)
        
        test_summarize_btn = QPushButton("Test Summarize")
        test_summarize_btn.clicked.connect(self._on_ai_test_summarize)
        test_summarize_layout.addWidget(test_summarize_btn)
        
        layout.addLayout(test_summarize_layout)
        
        # AI Test Classify
        test_classify_layout = QVBoxLayout()
        test_classify_layout.addWidget(QLabel("Test Classify:"))
        
        self.ai_test_classify_text = QTextEdit()
        self.ai_test_classify_text.setPlaceholderText("Content to classify")
        self.ai_test_classify_text.setMaximumHeight(80)
        test_classify_layout.addWidget(self.ai_test_classify_text)
        
        test_classify_btn = QPushButton("Test Classify")
        test_classify_btn.clicked.connect(self._on_ai_test_classify)
        test_classify_layout.addWidget(test_classify_btn)
        
        layout.addLayout(test_classify_layout)
        
        # AI Test Chat
        test_chat_layout = QVBoxLayout()
        test_chat_layout.addWidget(QLabel("Test Chat:"))
        
        self.ai_test_chat_text = QLineEdit()
        self.ai_test_chat_text.setPlaceholderText("Test message")
        test_chat_layout.addWidget(self.ai_test_chat_text)
        
        test_chat_btn = QPushButton("Test Chat")
        test_chat_btn.clicked.connect(self._on_ai_test_chat)
        test_chat_layout.addWidget(test_chat_btn)
        
        layout.addLayout(test_chat_layout)
        
        return group
        
    def _create_chat_group(self) -> QGroupBox:
        """Create Chat command group."""
        group = QGroupBox("Chat")
        layout = QVBoxLayout(group)
        
        # Chat Start
        start_layout = QVBoxLayout()
        start_layout.addWidget(QLabel("Start:"))
        
        self.chat_start_title = QLineEdit()
        self.chat_start_title.setPlaceholderText("Session title (optional)")
        start_layout.addWidget(self.chat_start_title)
        
        start_btn = QPushButton("Start Session")
        start_btn.clicked.connect(self._on_chat_start)
        start_layout.addWidget(start_btn)
        
        layout.addLayout(start_layout)
        
        # Chat Resume
        resume_layout = QVBoxLayout()
        resume_layout.addWidget(QLabel("Resume:"))
        
        self.chat_resume_session_id = QLineEdit()
        self.chat_resume_session_id.setPlaceholderText("Session ID")
        resume_layout.addWidget(self.chat_resume_session_id)
        
        resume_btn = QPushButton("Resume Session")
        resume_btn.clicked.connect(self._on_chat_resume)
        resume_layout.addWidget(resume_btn)
        
        layout.addLayout(resume_layout)
        
        # Chat List
        list_btn = QPushButton("List Sessions")
        list_btn.clicked.connect(self._on_chat_list)
        layout.addWidget(list_btn)
        
        return group
        
    def _create_review_group(self) -> QGroupBox:
        """Create Review command group."""
        group = QGroupBox("Review")
        layout = QVBoxLayout(group)
        
        # Review Next
        next_layout = QVBoxLayout()
        next_layout.addWidget(QLabel("Next Reviews:"))
        
        limit_layout = QHBoxLayout()
        limit_layout.addWidget(QLabel("Limit:"))
        self.review_next_limit = QSpinBox()
        self.review_next_limit.setMinimum(1)
        self.review_next_limit.setMaximum(100)
        self.review_next_limit.setValue(10)
        limit_layout.addWidget(self.review_next_limit)
        limit_layout.addStretch()
        next_layout.addLayout(limit_layout)
        
        self.review_next_topic = QLineEdit()
        self.review_next_topic.setPlaceholderText("Topic ID (optional)")
        next_layout.addWidget(self.review_next_topic)
        
        mastery_layout = QHBoxLayout()
        mastery_layout.addWidget(QLabel("Mastery:"))
        self.review_next_min_mastery = QDoubleSpinBox()
        self.review_next_min_mastery.setMinimum(0.0)
        self.review_next_min_mastery.setMaximum(1.0)
        self.review_next_min_mastery.setSingleStep(0.1)
        self.review_next_min_mastery.setSpecialValueText("Any")
        mastery_layout.addWidget(self.review_next_min_mastery)
        mastery_layout.addWidget(QLabel("to"))
        self.review_next_max_mastery = QDoubleSpinBox()
        self.review_next_max_mastery.setMinimum(0.0)
        self.review_next_max_mastery.setMaximum(1.0)
        self.review_next_max_mastery.setSingleStep(0.1)
        self.review_next_max_mastery.setValue(1.0)
        self.review_next_max_mastery.setSpecialValueText("Any")
        mastery_layout.addWidget(self.review_next_max_mastery)
        mastery_layout.addStretch()
        next_layout.addLayout(mastery_layout)
        
        next_btn = QPushButton("Get Next Reviews")
        next_btn.clicked.connect(self._on_review_next)
        next_layout.addWidget(next_btn)
        
        layout.addLayout(next_layout)
        
        return group
        
    def _create_import_group(self) -> QGroupBox:
        """Create Import command group."""
        group = QGroupBox("Import")
        layout = QVBoxLayout(group)
        
        # Import Transcript
        transcript_layout = QVBoxLayout()
        transcript_layout.addWidget(QLabel("Import Transcript:"))
        
        file_layout = QHBoxLayout()
        self.import_transcript_file = QLineEdit()
        self.import_transcript_file.setPlaceholderText("File path")
        file_layout.addWidget(self.import_transcript_file)
        
        file_btn = QPushButton("Browse...")
        file_btn.clicked.connect(self._on_import_transcript_browse)
        file_layout.addWidget(file_btn)
        
        transcript_layout.addLayout(file_layout)
        
        self.import_transcript_topics = QLineEdit()
        self.import_transcript_topics.setPlaceholderText("Topics (comma-separated, optional)")
        transcript_layout.addWidget(self.import_transcript_topics)
        
        self.import_transcript_skills = QLineEdit()
        self.import_transcript_skills.setPlaceholderText("Skills (comma-separated, optional)")
        transcript_layout.addWidget(self.import_transcript_skills)
        
        self.import_transcript_use_stub = QCheckBox("Use stub embeddings")
        self.import_transcript_use_stub.setChecked(False)
        transcript_layout.addWidget(self.import_transcript_use_stub)
        
        transcript_btn = QPushButton("Import Transcript")
        transcript_btn.clicked.connect(self._on_import_transcript)
        transcript_layout.addWidget(transcript_btn)
        
        layout.addLayout(transcript_layout)
        
        # Import Batch
        batch_layout = QVBoxLayout()
        batch_layout.addWidget(QLabel("Import Batch:"))
        
        batch_file_layout = QHBoxLayout()
        self.import_batch_dir = QLineEdit()
        self.import_batch_dir.setPlaceholderText("Directory path")
        batch_file_layout.addWidget(self.import_batch_dir)
        
        batch_dir_btn = QPushButton("Browse...")
        batch_dir_btn.clicked.connect(self._on_import_batch_browse)
        batch_file_layout.addWidget(batch_dir_btn)
        
        batch_layout.addLayout(batch_file_layout)
        
        batch_btn = QPushButton("Import Batch")
        batch_btn.clicked.connect(self._on_import_batch)
        batch_layout.addWidget(batch_btn)
        
        layout.addLayout(batch_layout)
        
        return group
        
    def _create_refresh_group(self) -> QGroupBox:
        """Create Refresh command group."""
        group = QGroupBox("Refresh")
        layout = QVBoxLayout(group)
        
        # Refresh Summaries
        summaries_layout = QVBoxLayout()
        summaries_layout.addWidget(QLabel("Refresh Summaries:"))
        
        self.refresh_summaries_topic = QLineEdit()
        self.refresh_summaries_topic.setPlaceholderText("Topic ID (optional)")
        summaries_layout.addWidget(self.refresh_summaries_topic)
        
        self.refresh_summaries_since = QLineEdit()
        self.refresh_summaries_since.setPlaceholderText("Since timestamp (ISO format, optional)")
        summaries_layout.addWidget(self.refresh_summaries_since)
        
        self.refresh_summaries_force = QCheckBox("Force refresh")
        self.refresh_summaries_force.setChecked(False)
        summaries_layout.addWidget(self.refresh_summaries_force)
        
        summaries_btn = QPushButton("Refresh Summaries")
        summaries_btn.clicked.connect(self._on_refresh_summaries)
        summaries_layout.addWidget(summaries_btn)
        
        layout.addLayout(summaries_layout)
        
        # Refresh Status
        status_btn = QPushButton("Status")
        status_btn.clicked.connect(self._on_refresh_status)
        layout.addWidget(status_btn)
        
        return group
        
    def _create_progress_group(self) -> QGroupBox:
        """Create Progress command group."""
        group = QGroupBox("Progress")
        layout = QVBoxLayout(group)
        
        # Progress Summary
        summary_layout = QVBoxLayout()
        summary_layout.addWidget(QLabel("Summary:"))
        
        self.progress_summary_start = QLineEdit()
        self.progress_summary_start.setPlaceholderText("Start timestamp (optional)")
        summary_layout.addWidget(self.progress_summary_start)
        
        self.progress_summary_end = QLineEdit()
        self.progress_summary_end.setPlaceholderText("End timestamp (optional)")
        summary_layout.addWidget(self.progress_summary_end)
        
        days_layout = QHBoxLayout()
        days_layout.addWidget(QLabel("Days:"))
        self.progress_summary_days = QSpinBox()
        self.progress_summary_days.setMinimum(1)
        self.progress_summary_days.setMaximum(365)
        self.progress_summary_days.setSpecialValueText("N/A")
        days_layout.addWidget(self.progress_summary_days)
        days_layout.addStretch()
        summary_layout.addLayout(days_layout)
        
        self.progress_summary_topic = QLineEdit()
        self.progress_summary_topic.setPlaceholderText("Topic ID (optional)")
        summary_layout.addWidget(self.progress_summary_topic)
        
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        self.progress_summary_format = QComboBox()
        self.progress_summary_format.addItems(["table", "json", "markdown"])
        format_layout.addWidget(self.progress_summary_format)
        format_layout.addStretch()
        summary_layout.addLayout(format_layout)
        
        self.progress_summary_chart = QCheckBox("Show chart")
        self.progress_summary_chart.setChecked(False)
        summary_layout.addWidget(self.progress_summary_chart)
        
        summary_btn = QPushButton("Generate Summary")
        summary_btn.clicked.connect(self._on_progress_summary)
        summary_layout.addWidget(summary_btn)
        
        layout.addLayout(summary_layout)
        
        return group
        
    def _create_results_panel(self) -> QWidget:
        """Create results and history panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Results tabs
        self.results_tabs = QTabWidget()
        self.results_tabs.addTab(self._create_table_tab(), "Table")
        self.results_tabs.addTab(self._create_json_tab(), "JSON")
        self.results_tabs.addTab(self._create_text_tab(), "Text")
        layout.addWidget(self.results_tabs)
        
        # Export button
        export_layout = QHBoxLayout()
        export_layout.addStretch()
        
        export_btn = QPushButton("Export...")
        export_btn.clicked.connect(self._on_export)
        export_layout.addWidget(export_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._on_clear_results)
        export_layout.addWidget(clear_btn)
        
        layout.addLayout(export_layout)
        
        # Command history
        history_label = QLabel("Command History")
        history_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        layout.addWidget(history_label)
        
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self._on_history_item_double_clicked)
        layout.addWidget(self.history_list)
        
        return widget
        
    def _create_table_tab(self) -> QWidget:
        """Create table results tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(0)
        self.results_table.setRowCount(0)
        layout.addWidget(self.results_table)
        
        return widget
        
    def _create_json_tab(self) -> QWidget:
        """Create JSON results tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.results_json = QTextEdit()
        self.results_json.setReadOnly(True)
        self.results_json.setFontFamily("Courier")
        layout.addWidget(self.results_json)
        
        return widget
        
    def _create_text_tab(self) -> QWidget:
        """Create text results tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFontFamily("Courier")
        layout.addWidget(self.results_text)
        
        return widget
        
    # ==================== Command Handlers ====================
    
    def _on_db_check(self):
        """Handle DB Check command."""
        self._run_async(self._async_db_check())
    
    async def _async_db_check(self):
        """Async DB check handler."""
        try:
            result = await self.facade.db_check()
            self._add_to_history("db.check", {})
            self._display_result(result, "Database Check")
        except Exception as e:
            self._display_error("Database Check", str(e))
    
    def _on_db_init(self):
        """Handle DB Init command."""
        reply = QMessageBox.question(
            self,
            "Initialize Database",
            "This will initialize a new database. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._run_async(self._async_db_init())
    
    async def _async_db_init(self):
        """Async DB init handler."""
        try:
            result = await self.facade.db_init()
            self._add_to_history("db.init", {})
            self._display_result(result, "Database Initialize")
        except Exception as e:
            self._display_error("Database Initialize", str(e))
    
    def _on_index_build(self):
        """Handle Index Build command."""
        event_id = self.index_build_event_id.text().strip() or None
        use_stub = self.index_build_use_stub.isChecked()
        
        self._run_async(self._async_index_build(event_id, use_stub))
    
    async def _async_index_build(self, event_id: Optional[str], use_stub: bool):
        """Async index build handler."""
        try:
            # Show progress
            progress = QProgressBar()
            progress.setRange(0, 0)  # Indeterminate
            progress.setFormat("Building index...")
            # TODO: Add progress to UI
            
            result = await self.facade.index_build(event_id=event_id, use_stub=use_stub)
            self._add_to_history("index.build", {"event_id": event_id, "use_stub": use_stub})
            self._display_result(result, "Index Build")
        except Exception as e:
            self._display_error("Index Build", str(e))
    
    def _on_index_status(self):
        """Handle Index Status command."""
        self._run_async(self._async_index_status())
    
    async def _async_index_status(self):
        """Async index status handler."""
        try:
            result = await self.facade.index_status()
            self._add_to_history("index.status", {})
            self._display_result(result, "Index Status")
        except Exception as e:
            self._display_error("Index Status", str(e))
    
    def _on_index_search(self):
        """Handle Index Search command."""
        query = self.index_search_query.text().strip()
        if not query:
            QMessageBox.warning(self, "Invalid Input", "Search query is required")
            return
        
        topk = self.index_search_topk.value()
        use_stub = self.index_search_use_stub.isChecked()
        
        self._run_async(self._async_index_search(query, topk, use_stub))
    
    async def _async_index_search(self, query: str, topk: int, use_stub: bool):
        """Async index search handler."""
        try:
            result = await self.facade.index_search(query=query, top_k=topk, use_stub=use_stub)
            self._add_to_history("index.search", {"query": query, "topk": topk, "use_stub": use_stub})
            self._display_result(result, "Index Search")
        except Exception as e:
            self._display_error("Index Search", str(e))
    
    def _on_ai_routes(self):
        """Handle AI Routes command."""
        self._run_async(self._async_ai_routes())
    
    async def _async_ai_routes(self):
        """Async AI routes handler."""
        try:
            result = await self.facade.ai_routes()
            self._add_to_history("ai.routes", {})
            self._display_result(result, "AI Routes")
        except Exception as e:
            self._display_error("AI Routes", str(e))
    
    def _on_ai_test_summarize(self):
        """Handle AI Test Summarize command."""
        text = self.ai_test_summarize_text.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Invalid Input", "Text is required")
            return
        
        self._run_async(self._async_ai_test_summarize(text))
    
    async def _async_ai_test_summarize(self, text: str):
        """Async AI test summarize handler."""
        try:
            result = await self.facade.ai_test_summarize(text)
            self._add_to_history("ai.test.summarize", {"text": text})
            self._display_result(result, "AI Test Summarize")
        except Exception as e:
            self._display_error("AI Test Summarize", str(e))
    
    def _on_ai_test_classify(self):
        """Handle AI Test Classify command."""
        text = self.ai_test_classify_text.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Invalid Input", "Text is required")
            return
        
        self._run_async(self._async_ai_test_classify(text))
    
    async def _async_ai_test_classify(self, text: str):
        """Async AI test classify handler."""
        try:
            result = await self.facade.ai_test_classify(text)
            self._add_to_history("ai.test.classify", {"text": text})
            self._display_result(result, "AI Test Classify")
        except Exception as e:
            self._display_error("AI Test Classify", str(e))
    
    def _on_ai_test_chat(self):
        """Handle AI Test Chat command."""
        text = self.ai_test_chat_text.text().strip()
        if not text:
            QMessageBox.warning(self, "Invalid Input", "Message is required")
            return
        
        self._run_async(self._async_ai_test_chat(text))
    
    async def _async_ai_test_chat(self, text: str):
        """Async AI test chat handler."""
        try:
            result = await self.facade.ai_test_chat(text)
            self._add_to_history("ai.test.chat", {"text": text})
            self._display_result(result, "AI Test Chat")
        except Exception as e:
            self._display_error("AI Test Chat", str(e))
    
    def _on_chat_start(self):
        """Handle Chat Start command."""
        title = self.chat_start_title.text().strip() or None
        self._run_async(self._async_chat_start(title))
    
    async def _async_chat_start(self, title: Optional[str]):
        """Async chat start handler."""
        try:
            result = await self.facade.chat_start(title=title)
            self._add_to_history("chat.start", {"title": title})
            self._display_result(result, "Chat Start")
        except Exception as e:
            self._display_error("Chat Start", str(e))
    
    def _on_chat_resume(self):
        """Handle Chat Resume command."""
        session_id = self.chat_resume_session_id.text().strip()
        if not session_id:
            QMessageBox.warning(self, "Invalid Input", "Session ID is required")
            return
        
        self._run_async(self._async_chat_resume(session_id))
    
    async def _async_chat_resume(self, session_id: str):
        """Async chat resume handler."""
        try:
            result = await self.facade.chat_resume(session_id)
            self._add_to_history("chat.resume", {"session_id": session_id})
            self._display_result(result, "Chat Resume")
        except Exception as e:
            self._display_error("Chat Resume", str(e))
    
    def _on_chat_list(self):
        """Handle Chat List command."""
        self._run_async(self._async_chat_list())
    
    async def _async_chat_list(self):
        """Async chat list handler."""
        try:
            result = await self.facade.chat_list()
            self._add_to_history("chat.list", {})
            self._display_result(result, "Chat List")
        except Exception as e:
            self._display_error("Chat List", str(e))
    
    def _on_review_next(self):
        """Handle Review Next command."""
        limit = self.review_next_limit.value()
        topic = self.review_next_topic.text().strip() or None
        min_mastery = self.review_next_min_mastery.value() if self.review_next_min_mastery.value() > 0 else None
        max_mastery = self.review_next_max_mastery.value() if self.review_next_max_mastery.value() < 1.0 else None
        
        # TODO: Implement when facade method is added
        self._display_error("Review Next", "Review next functionality will be implemented in a future PR.")
    
    def _on_import_transcript_browse(self):
        """Handle Import Transcript Browse button."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Transcript",
            "",
            "Text Files (*.txt);;Markdown Files (*.md);;JSON Files (*.json);;All Files (*.*)"
        )
        if file_path:
            self.import_transcript_file.setText(file_path)
    
    def _on_import_transcript(self):
        """Handle Import Transcript command."""
        file_path = self.import_transcript_file.text().strip()
        if not file_path:
            QMessageBox.warning(self, "Invalid Input", "File path is required")
            return
        
        topics = self.import_transcript_topics.text().strip() or None
        skills = self.import_transcript_skills.text().strip() or None
        use_stub = self.import_transcript_use_stub.isChecked()
        
        # TODO: Implement when facade method is added
        self._display_error("Import Transcript", "Import transcript functionality will be implemented in a future PR.")
    
    def _on_import_batch_browse(self):
        """Handle Import Batch Browse button."""
        dir_path = QFileDialog.getExistingDirectory(self, "Import Batch Transcripts")
        if dir_path:
            self.import_batch_dir.setText(dir_path)
    
    def _on_import_batch(self):
        """Handle Import Batch command."""
        dir_path = self.import_batch_dir.text().strip()
        if not dir_path:
            QMessageBox.warning(self, "Invalid Input", "Directory path is required")
            return
        
        # TODO: Implement when facade method is added
        self._display_error("Import Batch", "Import batch functionality will be implemented in a future PR.")
    
    def _on_refresh_summaries(self):
        """Handle Refresh Summaries command."""
        topic = self.refresh_summaries_topic.text().strip() or None
        since = self.refresh_summaries_since.text().strip() or None
        force = self.refresh_summaries_force.isChecked()
        
        # TODO: Implement when facade method is added
        self._display_error("Refresh Summaries", "Refresh summaries functionality will be implemented in a future PR.")
    
    def _on_refresh_status(self):
        """Handle Refresh Status command."""
        # TODO: Implement when facade method is added
        self._display_error("Refresh Status", "Refresh status functionality will be implemented in a future PR.")
    
    def _on_progress_summary(self):
        """Handle Progress Summary command."""
        start = self.progress_summary_start.text().strip() or None
        end = self.progress_summary_end.text().strip() or None
        days = self.progress_summary_days.value() if self.progress_summary_days.value() > 0 else None
        topic = self.progress_summary_topic.text().strip() or None
        format_type = self.progress_summary_format.currentText()
        chart = self.progress_summary_chart.isChecked()
        
        # TODO: Implement when facade method is added
        self._display_error("Progress Summary", "Progress summary functionality will be implemented in a future PR.")
    
    # ==================== Results Display ====================
    
    def _display_result(self, result: Any, command_name: str):
        """
        Display command result in results panel.
        
        Args:
            result: Command result (dict, list, or other)
            command_name: Name of the command executed
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        # Update text tab
        text_content = f"[{timestamp}] {command_name}\n"
        text_content += "=" * 50 + "\n"
        text_content += str(result) + "\n\n"
        self.results_text.append(text_content)
        
        # Update JSON tab
        try:
            json_content = json.dumps(result, indent=2, default=str)
            self.results_json.append(f"[{timestamp}] {command_name}\n")
            self.results_json.append("=" * 50 + "\n")
            self.results_json.append(json_content + "\n\n")
        except Exception as e:
            self.results_json.append(f"[{timestamp}] {command_name}\n")
            self.results_json.append("=" * 50 + "\n")
            self.results_json.append(f"Error serializing to JSON: {e}\n\n")
        
        # Update table tab
        self._update_table(result, command_name, timestamp)
        
        # Switch to table tab by default
        self.results_tabs.setCurrentIndex(0)
    
    def _display_error(self, command_name: str, error: str):
        """
        Display error in results panel.
        
        Args:
            command_name: Name of the command that failed
            error: Error message
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        error_text = f"[{timestamp}] {command_name} - ERROR\n"
        error_text += "=" * 50 + "\n"
        error_text += f"Error: {error}\n\n"
        
        self.results_text.append(error_text)
        self.results_json.append(error_text)
        
        # Update table with error
        self.results_table.setRowCount(1)
        self.results_table.setColumnCount(2)
        self.results_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.results_table.setItem(0, 0, QTableWidgetItem("Error"))
        self.results_table.setItem(0, 1, QTableWidgetItem(error))
        
        # Switch to text tab for errors
        self.results_tabs.setCurrentIndex(2)
    
    def _update_table(self, result: Any, command_name: str, timestamp: str):
        """
        Update table with result data.
        
        Args:
            result: Command result
            command_name: Name of the command
            timestamp: Timestamp string
        """
        if isinstance(result, dict):
            # Display as key-value pairs
            self.results_table.setRowCount(len(result))
            self.results_table.setColumnCount(2)
            self.results_table.setHorizontalHeaderLabels(["Property", "Value"])
            
            for i, (key, value) in enumerate(result.items()):
                self.results_table.setItem(i, 0, QTableWidgetItem(str(key)))
                self.results_table.setItem(i, 1, QTableWidgetItem(str(value)))
                
        elif isinstance(result, list):
            # Display as table with columns from first item
            if result and isinstance(result[0], dict):
                keys = list(result[0].keys())
                self.results_table.setRowCount(len(result))
                self.results_table.setColumnCount(len(keys))
                self.results_table.setHorizontalHeaderLabels(keys)
                
                for i, item in enumerate(result):
                    for j, key in enumerate(keys):
                        value = item.get(key, "")
                        self.results_table.setItem(i, j, QTableWidgetItem(str(value)))
            else:
                # Simple list
                self.results_table.setRowCount(len(result))
                self.results_table.setColumnCount(1)
                self.results_table.setHorizontalHeaderLabels(["Value"])
                
                for i, item in enumerate(result):
                    self.results_table.setItem(i, 0, QTableWidgetItem(str(item)))
        else:
            # Single value
            self.results_table.setRowCount(1)
            self.results_table.setColumnCount(2)
            self.results_table.setHorizontalHeaderLabels(["Property", "Value"])
            self.results_table.setItem(0, 0, QTableWidgetItem("Result"))
            self.results_table.setItem(0, 1, QTableWidgetItem(str(result)))
        
        # Resize columns to content
        self.results_table.resizeColumnsToContents()
    
    def _add_to_history(self, command: str, args: Dict[str, Any]):
        """
        Add command to history.
        
        Args:
            command: Command name
            args: Command arguments
        """
        timestamp = datetime.utcnow()
        history_item = {
            "timestamp": timestamp,
            "command": command,
            "args": args,
        }
        self.command_history.append(history_item)
        
        # Update history list (keep last 50)
        if len(self.command_history) > 50:
            self.command_history = self.command_history[-50:]
        
        # Add to UI
        item_text = f"[{timestamp.strftime('%H:%M:%S')}] {command}"
        if args:
            item_text += f" {args}"
        item = QListWidgetItem(item_text)
        item.setData(Qt.UserRole, history_item)
        self.history_list.addItem(item)
        self.history_list.scrollToBottom()
    
    def _on_history_item_double_clicked(self, item: QListWidgetItem):
        """Handle history item double-click to re-execute."""
        history_item = item.data(Qt.UserRole)
        if history_item:
            command = history_item["command"]
            args = history_item["args"]
            # TODO: Re-execute command with saved args
            QMessageBox.information(self, "Re-execute", f"Re-executing {command} with args {args}")
    
    def _on_export(self):
        """Handle export button click."""
        if self.results_tabs.currentIndex() == 0:
            # Export table as CSV
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Table",
                "",
                "CSV Files (*.csv);;All Files (*.*)"
            )
            if file_path:
                self._export_table_to_csv(file_path)
        elif self.results_tabs.currentIndex() == 1:
            # Export JSON
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export JSON",
                "",
                "JSON Files (*.json);;All Files (*.*)"
            )
            if file_path:
                self._export_json(file_path)
        else:
            # Export text
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Text",
                "",
                "Text Files (*.txt);;All Files (*.*)"
            )
            if file_path:
                self._export_text(file_path)
    
    def _export_table_to_csv(self, file_path: str):
        """Export table to CSV file."""
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write headers
                headers = []
                for col in range(self.results_table.columnCount()):
                    headers.append(self.results_table.horizontalHeaderItem(col).text())
                writer.writerow(headers)
                
                # Write rows
                for row in range(self.results_table.rowCount()):
                    row_data = []
                    for col in range(self.results_table.columnCount()):
                        item = self.results_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            
            QMessageBox.information(self, "Export", f"Table exported to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to export: {e}")
    
    def _export_json(self, file_path: str):
        """Export JSON results to file."""
        try:
            content = self.results_json.toPlainText()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            QMessageBox.information(self, "Export", f"JSON exported to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to export: {e}")
    
    def _export_text(self, file_path: str):
        """Export text results to file."""
        try:
            content = self.results_text.toPlainText()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            QMessageBox.information(self, "Export", f"Text exported to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to export: {e}")
    
    def _on_clear_results(self):
        """Handle clear all button click."""
        reply = QMessageBox.question(
            self,
            "Clear Results",
            "Clear all results and history?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.results_table.setRowCount(0)
            self.results_table.setColumnCount(0)
            self.results_json.clear()
            self.results_text.clear()
            self.history_list.clear()
            self.command_history.clear()
    
    def _run_async(self, coro):
        """
        Run async coroutine from synchronous context.
        
        Args:
            coro: Coroutine to run
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(coro)
            else:
                loop.run_until_complete(coro)
        except RuntimeError:
            try:
                loop = asyncio.get_running_loop()
                asyncio.ensure_future(coro)
            except RuntimeError:
                asyncio.run(coro)

