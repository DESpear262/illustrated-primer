"""
Main Window for AI Tutor GUI.

Provides multi-tab layout with menu bar, status bar, and all CLI command equivalents.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QMessageBox,
    QStatusBar,
    QMenuBar,
    QMenu,
    QFileDialog,
    QProgressDialog,
    QFrame,
)

from src.interface_common import AppFacade, FacadeError, FacadeTimeoutError
from src.config import DB_PATH, FAISS_INDEX_PATH, OPENAI_API_KEY

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main window for AI Tutor GUI.
    
    Provides:
    - Multi-tab layout (Tutor Chat, Command Console, Review Queue, Knowledge Tree, Context Inspector)
    - Menu bar with all CLI command equivalents
    - Status bar with DB, FAISS, and API health indicators
    - Startup health checks
    - Global loading overlay for async operations
    """
    
    def __init__(self, facade: AppFacade, parent: Optional[QWidget] = None):
        """
        Initialize main window.
        
        Args:
            facade: AppFacade instance for backend operations
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.facade = facade
        
        # Health status indicators
        self.db_health: Optional[bool] = None
        self.faiss_health: Optional[bool] = None
        self.api_health: Optional[bool] = None
        
        # Setup UI
        self._setup_ui()
        self._setup_menu_bar()
        self._setup_status_bar()
        self._setup_tabs()
        
        # Set window properties
        self.setWindowTitle("AI Tutor")
        self.resize(1200, 800)
        
        # Setup health check timer (check every 30 seconds)
        self.health_check_timer = QTimer(self)
        self.health_check_timer.timeout.connect(self._check_health_status)
        self.health_check_timer.start(30000)  # 30 seconds
        
        # Setup loading overlay
        self._setup_loading_overlay()
        
    def _setup_ui(self):
        """Setup main UI components."""
        # Central widget with tabs
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        
        # Main layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Tab widget
        self.tab_widget = QTabWidget(self)
        self.main_layout.addWidget(self.tab_widget)
        
    def _setup_menu_bar(self):
        """Setup menu bar with all CLI command equivalents."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Import actions
        import_transcript_action = QAction("&Import Transcript...", self)
        import_transcript_action.setShortcut(QKeySequence("Ctrl+I"))
        import_transcript_action.triggered.connect(self._on_import_transcript)
        file_menu.addAction(import_transcript_action)
        
        import_batch_action = QAction("Import &Batch...", self)
        import_batch_action.triggered.connect(self._on_import_batch)
        file_menu.addAction(import_batch_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Database menu
        db_menu = menubar.addMenu("&Database")
        
        db_check_action = QAction("&Check", self)
        db_check_action.triggered.connect(self._on_db_check)
        db_menu.addAction(db_check_action)
        
        db_init_action = QAction("&Initialize", self)
        db_init_action.triggered.connect(self._on_db_init)
        db_menu.addAction(db_init_action)
        
        # Index menu
        index_menu = menubar.addMenu("&Index")
        
        index_build_action = QAction("&Build", self)
        index_build_action.triggered.connect(self._on_index_build)
        index_menu.addAction(index_build_action)
        
        index_status_action = QAction("&Status", self)
        index_status_action.triggered.connect(self._on_index_status)
        index_menu.addAction(index_status_action)
        
        index_search_action = QAction("&Search...", self)
        index_search_action.triggered.connect(self._on_index_search)
        index_menu.addAction(index_search_action)
        
        # AI menu
        ai_menu = menubar.addMenu("&AI")
        
        ai_routes_action = QAction("&Routes", self)
        ai_routes_action.triggered.connect(self._on_ai_routes)
        ai_menu.addAction(ai_routes_action)
        
        ai_menu.addSeparator()
        
        ai_test_summarize_action = QAction("Test &Summarize", self)
        ai_test_summarize_action.triggered.connect(self._on_ai_test_summarize)
        ai_menu.addAction(ai_test_summarize_action)
        
        ai_test_classify_action = QAction("Test &Classify", self)
        ai_test_classify_action.triggered.connect(self._on_ai_test_classify)
        ai_menu.addAction(ai_test_classify_action)
        
        ai_test_chat_action = QAction("Test &Chat", self)
        ai_test_chat_action.triggered.connect(self._on_ai_test_chat)
        ai_menu.addAction(ai_test_chat_action)
        
        # Chat menu
        chat_menu = menubar.addMenu("&Chat")
        
        chat_start_action = QAction("&Start Session", self)
        chat_start_action.setShortcut(QKeySequence("Ctrl+N"))
        chat_start_action.triggered.connect(self._on_chat_start)
        chat_menu.addAction(chat_start_action)
        
        chat_resume_action = QAction("&Resume Session...", self)
        chat_resume_action.setShortcut(QKeySequence("Ctrl+R"))
        chat_resume_action.triggered.connect(self._on_chat_resume)
        chat_menu.addAction(chat_resume_action)
        
        chat_list_action = QAction("&List Sessions", self)
        chat_list_action.triggered.connect(self._on_chat_list)
        chat_menu.addAction(chat_list_action)
        
        # Review menu
        review_menu = menubar.addMenu("&Review")
        
        review_next_action = QAction("&Next Reviews", self)
        review_next_action.triggered.connect(self._on_review_next)
        review_menu.addAction(review_next_action)
        
        # Refresh menu
        refresh_menu = menubar.addMenu("Re&fresh")
        
        refresh_summaries_action = QAction("&Summaries...", self)
        refresh_summaries_action.triggered.connect(self._on_refresh_summaries)
        refresh_menu.addAction(refresh_summaries_action)
        
        refresh_status_action = QAction("&Status", self)
        refresh_status_action.triggered.connect(self._on_refresh_status)
        refresh_menu.addAction(refresh_status_action)
        
        # Progress menu
        progress_menu = menubar.addMenu("&Progress")
        
        progress_summary_action = QAction("&Summary...", self)
        progress_summary_action.triggered.connect(self._on_progress_summary)
        progress_menu.addAction(progress_summary_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
        
    def _setup_status_bar(self):
        """Setup status bar with health indicators."""
        status_bar = self.statusBar()
        
        # DB health indicator
        self.db_status_label = QLabel("DB: ?")
        status_bar.addPermanentWidget(self.db_status_label)
        
        # FAISS health indicator
        self.faiss_status_label = QLabel("FAISS: ?")
        status_bar.addPermanentWidget(self.faiss_status_label)
        
        # API health indicator
        self.api_status_label = QLabel("API: ?")
        status_bar.addPermanentWidget(self.api_status_label)
        
        # Database path
        self.db_path_label = QLabel(f"DB: {DB_PATH}")
        status_bar.addPermanentWidget(self.db_path_label)
        
        # Initial status message
        status_bar.showMessage("Ready")
        
    def _setup_tabs(self):
        """Setup tab widgets with basic structures."""
        # Tutor Chat tab
        from src.interface_gui.views.tutor_chat_view import TutorChatView
        self.tutor_chat_view = TutorChatView(self.facade)
        self.tab_widget.addTab(self.tutor_chat_view, "Tutor Chat")
        
        # Command Console tab
        from src.interface_gui.views.command_view import CommandView
        self.command_view = CommandView(self.facade)
        self.tab_widget.addTab(self.command_view, "Command Console")
        
        # Review Queue tab
        from src.interface_gui.views.review_queue_view import ReviewQueueView
        self.review_queue_view = ReviewQueueView(self.facade)
        self.tab_widget.addTab(self.review_queue_view, "Review Queue")
        
        # Knowledge Tree tab
        self.knowledge_tree_tab = QWidget()
        knowledge_tree_layout = QVBoxLayout(self.knowledge_tree_tab)
        knowledge_tree_label = QLabel("Knowledge Tree - Coming in PR #8")
        knowledge_tree_label.setAlignment(Qt.AlignCenter)
        knowledge_tree_layout.addWidget(knowledge_tree_label)
        self.tab_widget.addTab(self.knowledge_tree_tab, "Knowledge Tree")
        
        # Context Inspector tab
        from src.interface_gui.views.context_inspector_view import ContextInspectorView
        self.context_inspector_view = ContextInspectorView(self.facade)
        self.tab_widget.addTab(self.context_inspector_view, "Context Inspector")
        
    def _setup_loading_overlay(self):
        """Setup global loading overlay for async operations."""
        # Create overlay frame
        self.loading_overlay = QFrame(self)
        self.loading_overlay.setFrameShape(QFrame.StyledPanel)
        self.loading_overlay.setStyleSheet("background-color: rgba(0, 0, 0, 128);")
        self.loading_overlay.hide()
        
        # Create layout for overlay
        overlay_layout = QVBoxLayout(self.loading_overlay)
        overlay_layout.setAlignment(Qt.AlignCenter)
        
        # Loading label
        self.loading_label = QLabel("Loading...", self.loading_overlay)
        self.loading_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        self.loading_label.setAlignment(Qt.AlignCenter)
        overlay_layout.addWidget(self.loading_label)
        
        # Resize overlay to match window
        self.loading_overlay.resize(self.size())
        
    def show_loading(self, message: str = "Loading..."):
        """
        Show loading overlay.
        
        Args:
            message: Loading message to display
        """
        self.loading_label.setText(message)
        self.loading_overlay.resize(self.size())
        self.loading_overlay.show()
        self.loading_overlay.raise_()
        
    def hide_loading(self):
        """Hide loading overlay."""
        self.loading_overlay.hide()
        
    def resizeEvent(self, event):
        """Handle window resize to update loading overlay."""
        super().resizeEvent(event)
        if hasattr(self, 'loading_overlay'):
            self.loading_overlay.resize(self.size())
        
    def _run_async(self, coro):
        """
        Run async coroutine from synchronous context.
        
        Args:
            coro: Coroutine to run
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Event loop is running, schedule the coroutine
                asyncio.ensure_future(coro)
            else:
                # No event loop running, this shouldn't happen with qasync
                loop.run_until_complete(coro)
        except RuntimeError:
            # No event loop available, try to get the default one
            try:
                loop = asyncio.get_running_loop()
                asyncio.ensure_future(coro)
            except RuntimeError:
                # Fallback: create new event loop
                asyncio.run(coro)
        
    async def check_startup_health(self):
        """
        Check database and FAISS health on startup.
        
        Shows non-blocking warnings if health checks fail.
        """
        try:
            # Check database health
            db_result = await self.facade.db_check()
            self.db_health = db_result.get("status") == "ok"
            self._update_db_status()
            
            # Auto-initialize database if it doesn't exist
            if not self.db_health:
                logger.warning("Database not found, initializing...")
                try:
                    await self.facade.db_init()
                    self.db_health = True
                    self._update_db_status()
                    self.statusBar().showMessage("Database initialized successfully", 5000)
                except Exception as e:
                    logger.error(f"Failed to initialize database: {e}")
                    self._show_warning("Database Initialization Failed", 
                                     f"Failed to initialize database: {e}\n\n"
                                     "You can try initializing manually from the Database menu.")
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            self.db_health = False
            self._update_db_status()
            self._show_warning("Database Health Check Failed", 
                             f"Could not check database health: {e}\n\n"
                             "Some features may not work correctly.")
        
        try:
            # Check FAISS index health
            faiss_result = await self.facade.index_status()
            self.faiss_health = faiss_result.get("vector_count", 0) >= 0
            self._update_faiss_status()
        except Exception as e:
            logger.warning(f"FAISS index not found or invalid: {e}")
            self.faiss_health = False
            self._update_faiss_status()
            # Don't show warning for missing FAISS index - it's optional
        
        # Check API health
        self.api_health = OPENAI_API_KEY is not None
        self._update_api_status()
        
    def _check_health_status(self):
        """Periodically check health status (called by timer)."""
        self._run_async(self._async_check_health())
        
    async def _async_check_health(self):
        """Async health check for timer."""
        try:
            db_result = await self.facade.db_check()
            self.db_health = db_result.get("status") == "ok"
            self._update_db_status()
        except Exception:
            self.db_health = False
            self._update_db_status()
        
        try:
            faiss_result = await self.facade.index_status()
            self.faiss_health = faiss_result.get("vector_count", 0) >= 0
            self._update_faiss_status()
        except Exception:
            self.faiss_health = False
            self._update_faiss_status()
        
        self.api_health = OPENAI_API_KEY is not None
        self._update_api_status()
        
    def _update_db_status(self):
        """Update DB status indicator."""
        if self.db_health is True:
            self.db_status_label.setText("DB: ✓")
            self.db_status_label.setStyleSheet("color: green;")
        elif self.db_health is False:
            self.db_status_label.setText("DB: ✗")
            self.db_status_label.setStyleSheet("color: red;")
        else:
            self.db_status_label.setText("DB: ?")
            self.db_status_label.setStyleSheet("color: gray;")
            
    def _update_faiss_status(self):
        """Update FAISS status indicator."""
        if self.faiss_health is True:
            self.faiss_status_label.setText("FAISS: ✓")
            self.faiss_status_label.setStyleSheet("color: green;")
        elif self.faiss_health is False:
            self.faiss_status_label.setText("FAISS: ✗")
            self.faiss_status_label.setStyleSheet("color: yellow;")
        else:
            self.faiss_status_label.setText("FAISS: ?")
            self.faiss_status_label.setStyleSheet("color: gray;")
            
    def _update_api_status(self):
        """Update API status indicator."""
        if self.api_health is True:
            self.api_status_label.setText("API: ✓")
            self.api_status_label.setStyleSheet("color: green;")
        else:
            self.api_status_label.setText("API: ✗")
            self.api_status_label.setStyleSheet("color: red;")
    
    def _show_warning(self, title: str, message: str):
        """Show warning dialog."""
        QMessageBox.warning(self, title, message)
    
    def _show_error(self, title: str, message: str):
        """Show error dialog."""
        QMessageBox.critical(self, title, message)
    
    def _show_info(self, title: str, message: str):
        """Show info dialog."""
        QMessageBox.information(self, title, message)
    
    # ==================== Menu Action Handlers ====================
    
    def _on_import_transcript(self):
        """Handle Import Transcript menu action."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Transcript",
            "",
            "Text Files (*.txt);;Markdown Files (*.md);;JSON Files (*.json);;All Files (*.*)"
        )
        if file_path:
            self._run_async(self._async_import_transcript(Path(file_path)))
    
    async def _async_import_transcript(self, file_path: Path):
        """Async import transcript handler."""
        # TODO: Implement when facade method is added
        self._show_info("Import Transcript", 
                      f"Import transcript functionality will be implemented in a future PR.\n\n"
                      f"Selected file: {file_path}")
    
    def _on_import_batch(self):
        """Handle Import Batch menu action."""
        dir_path = QFileDialog.getExistingDirectory(self, "Import Batch Transcripts")
        if dir_path:
            self._run_async(self._async_import_batch(Path(dir_path)))
    
    async def _async_import_batch(self, dir_path: Path):
        """Async import batch handler."""
        # TODO: Implement when facade method is added
        self._show_info("Import Batch", 
                      f"Import batch functionality will be implemented in a future PR.\n\n"
                      f"Selected directory: {dir_path}")
    
    def _on_db_check(self):
        """Handle Database Check menu action."""
        self._run_async(self._async_db_check())
    
    async def _async_db_check(self):
        """Async database check handler."""
        self.show_loading("Checking database...")
        try:
            result = await self.facade.db_check()
            self.db_health = result.get("status") == "ok"
            self._update_db_status()
            
            message = f"Database Status: {result.get('status', 'unknown')}\n"
            message += f"Tables: {result.get('tables', 0)}\n"
            message += f"Events: {result.get('event_count', 0)}"
            self._show_info("Database Check", message)
            self.statusBar().showMessage("Database check completed", 3000)
        except Exception as e:
            logger.error(f"Database check failed: {e}")
            self._show_error("Database Check Failed", str(e))
        finally:
            self.hide_loading()
    
    def _on_db_init(self):
        """Handle Database Initialize menu action."""
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
        """Async database init handler."""
        self.show_loading("Initializing database...")
        try:
            result = await self.facade.db_init()
            self.db_health = True
            self._update_db_status()
            self._show_info("Database Initialize", result.get("message", "Database initialized successfully"))
            self.statusBar().showMessage("Database initialized", 3000)
        except Exception as e:
            logger.error(f"Database init failed: {e}")
            self._show_error("Database Initialize Failed", str(e))
        finally:
            self.hide_loading()
    
    def _on_index_build(self):
        """Handle Index Build menu action."""
        reply = QMessageBox.question(
            self,
            "Build Index",
            "This may take a while. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._run_async(self._async_index_build())
    
    async def _async_index_build(self):
        """Async index build handler."""
        progress = QProgressDialog("Building index...", "Cancel", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        try:
            result = await self.facade.index_build()
            progress.close()
            self.faiss_health = True
            self._update_faiss_status()
            message = f"Index built successfully\n"
            message += f"Vectors: {result.get('vector_count', 0)}"
            self._show_info("Index Build", message)
            self.statusBar().showMessage("Index built successfully", 3000)
        except Exception as e:
            progress.close()
            logger.error(f"Index build failed: {e}")
            self._show_error("Index Build Failed", str(e))
    
    def _on_index_status(self):
        """Handle Index Status menu action."""
        self._run_async(self._async_index_status())
    
    async def _async_index_status(self):
        """Async index status handler."""
        self.show_loading("Checking index status...")
        try:
            result = await self.facade.index_status()
            self.faiss_health = result.get("vector_count", 0) >= 0
            self._update_faiss_status()
            message = f"Index Path: {result.get('path', 'unknown')}\n"
            message += f"Vectors: {result.get('vector_count', 0)}"
            self._show_info("Index Status", message)
            self.statusBar().showMessage("Index status retrieved", 3000)
        except Exception as e:
            logger.error(f"Index status failed: {e}")
            self.faiss_health = False
            self._update_faiss_status()
            self._show_error("Index Status Failed", str(e))
        finally:
            self.hide_loading()
    
    def _on_index_search(self):
        """Handle Index Search menu action."""
        # TODO: Implement search dialog
        self._show_info("Index Search", "Index search functionality will be implemented in a future PR.")
    
    def _on_ai_routes(self):
        """Handle AI Routes menu action."""
        self._run_async(self._async_ai_routes())
    
    async def _async_ai_routes(self):
        """Async AI routes handler."""
        self.show_loading("Loading AI routes...")
        try:
            routes = await self.facade.ai_routes()
            message = "AI Routes:\n\n"
            for route in routes:
                message += f"Task: {route.get('task', 'unknown')}\n"
                message += f"Model: {route.get('model', 'unknown')}\n"
                message += f"Tokens: {route.get('max_tokens', 'unknown')}\n\n"
            self._show_info("AI Routes", message)
        except Exception as e:
            logger.error(f"AI routes failed: {e}")
            self._show_error("AI Routes Failed", str(e))
        finally:
            self.hide_loading()
    
    def _on_ai_test_summarize(self):
        """Handle AI Test Summarize menu action."""
        self._run_async(self._async_ai_test_summarize())
    
    async def _async_ai_test_summarize(self):
        """Async AI test summarize handler."""
        try:
            result = await self.facade.ai_test_summarize("Test event content for summarization.")
            message = f"Summary: {result.get('summary', 'N/A')}\n"
            message += f"Topics: {', '.join(result.get('topics', []))}"
            self._show_info("AI Test Summarize", message)
        except Exception as e:
            logger.error(f"AI test summarize failed: {e}")
            self._show_error("AI Test Summarize Failed", str(e))
    
    def _on_ai_test_classify(self):
        """Handle AI Test Classify menu action."""
        self._run_async(self._async_ai_test_classify())
    
    async def _async_ai_test_classify(self):
        """Async AI test classify handler."""
        try:
            result = await self.facade.ai_test_classify("Test content for topic classification.")
            message = f"Topics: {', '.join(result.get('topics', []))}\n"
            message += f"Skills: {', '.join(result.get('skills', []))}"
            self._show_info("AI Test Classify", message)
        except Exception as e:
            logger.error(f"AI test classify failed: {e}")
            self._show_error("AI Test Classify Failed", str(e))
    
    def _on_ai_test_chat(self):
        """Handle AI Test Chat menu action."""
        self._run_async(self._async_ai_test_chat())
    
    async def _async_ai_test_chat(self):
        """Async AI test chat handler."""
        try:
            result = await self.facade.ai_test_chat("Hello, this is a test message.")
            message = f"Response: {result.get('reply', 'N/A')}"
            self._show_info("AI Test Chat", message)
        except Exception as e:
            logger.error(f"AI test chat failed: {e}")
            self._show_error("AI Test Chat Failed", str(e))
    
    def _on_chat_start(self):
        """Handle Chat Start menu action."""
        # Switch to Tutor Chat tab
        self.tab_widget.setCurrentIndex(0)
        # Start new session in chat view
        if hasattr(self, 'tutor_chat_view'):
            self.tutor_chat_view._start_new_session()
    
    def _on_chat_resume(self):
        """Handle Chat Resume menu action."""
        # Switch to Tutor Chat tab
        self.tab_widget.setCurrentIndex(0)
        # Show session list in chat view
        if hasattr(self, 'tutor_chat_view'):
            # Session list is already visible in sidebar
            self.statusBar().showMessage("Select a session from the sidebar to resume", 3000)
    
    def _on_chat_list(self):
        """Handle Chat List menu action."""
        self._run_async(self._async_chat_list())
    
    async def _async_chat_list(self):
        """Async chat list handler."""
        self.show_loading("Loading chat sessions...")
        try:
            sessions = await self.facade.chat_list()
            message = f"Found {len(sessions)} sessions:\n\n"
            for session in sessions[:10]:  # Show first 10
                message += f"- {session.get('session_id', 'unknown')}: {session.get('title', 'Untitled')}\n"
            if len(sessions) > 10:
                message += f"\n... and {len(sessions) - 10} more"
            self._show_info("Chat Sessions", message)
        except Exception as e:
            logger.error(f"Chat list failed: {e}")
            self._show_error("Chat List Failed", str(e))
        finally:
            self.hide_loading()
    
    def _on_review_next(self):
        """Handle Review Next menu action."""
        # TODO: Implement when facade method is added
        self._show_info("Review Next", "Review next functionality will be implemented in a future PR.")
    
    def _on_refresh_summaries(self):
        """Handle Refresh Summaries menu action."""
        # TODO: Implement when facade method is added
        self._show_info("Refresh Summaries", "Refresh summaries functionality will be implemented in a future PR.")
    
    def _on_refresh_status(self):
        """Handle Refresh Status menu action."""
        # TODO: Implement when facade method is added
        self._show_info("Refresh Status", "Refresh status functionality will be implemented in a future PR.")
    
    def _on_progress_summary(self):
        """Handle Progress Summary menu action."""
        # TODO: Implement when facade method is added
        self._show_info("Progress Summary", "Progress summary functionality will be implemented in a future PR.")
    
    def _on_about(self):
        """Handle About menu action."""
        message = "AI Tutor Proof of Concept\n\n"
        message += "Version: 0.1.0\n\n"
        message += "A graphical interface for AI-powered tutoring with knowledge tree visualization."
        self._show_info("About", message)

