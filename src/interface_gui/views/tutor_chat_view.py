"""
Tutor Chat View for AI Tutor GUI.

Provides chat interface with message display, input, context sidebar,
and session management.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from PySide6.QtCore import Qt, Signal, QTimer, QMimeData, QEvent
from PySide6.QtGui import QKeySequence, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QSplitter,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QMessageBox,
    QFileDialog,
    QTreeWidget,
    QTreeWidgetItem,
    QScrollArea,
)

from src.interface_common import AppFacade, FacadeError, FacadeTimeoutError
from src.interface_common.models import ChatMessage
from src.interface_gui.widgets.message_list import MessageList
from src.config import DB_PATH

logger = logging.getLogger(__name__)


class TutorChatView(QWidget):
    """
    Tutor Chat View widget.
    
    Provides:
    - Chat message display with styled bubbles
    - Multi-line input with Enter+Shift for newlines, Enter to send
    - Context sidebar showing last-used context chunks
    - Session list sidebar with recent sessions
    - Session title editing with AI suggestion
    - Upload functionality (file dialog + drag-and-drop)
    - Auto-save after each turn
    - Loading indicators
    - Error handling with retry
    """
    
    # Signal emitted when session changes
    session_changed = Signal(str)  # Emits session_id
    
    def __init__(
        self,
        facade: AppFacade,
        parent: Optional[QWidget] = None,
    ):
        """
        Initialize tutor chat view.
        
        Args:
            facade: AppFacade instance for backend operations
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.facade = facade
        
        # Current session state
        self.current_session_id: Optional[str] = None
        self.current_session_title: Optional[str] = None
        self.typing_indicator: Optional[QListWidgetItem] = None
        
        # Context chunks for current session
        self.context_chunks: List[Dict[str, Any]] = []
        
        # Setup UI
        self._setup_ui()
        
        # Load recent sessions
        self._load_recent_sessions()
        
    def eventFilter(self, obj, event):
        """Event filter for input text edit."""
        if obj == self.input_text:
            if event.type() == QEvent.KeyPress:
                handled = self._on_input_key_press(event)
                if handled:
                    return True
            elif event.type() == QEvent.DragEnter:
                handled = self._on_drag_enter(event)
                if handled:
                    return True
            elif event.type() == QEvent.Drop:
                handled = self._on_drop(event)
                if handled:
                    return True
        return super().eventFilter(obj, event)
        
    def _setup_ui(self):
        """Setup UI components."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter for sidebars
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Session list sidebar (left)
        self.session_list_widget = self._create_session_list()
        splitter.addWidget(self.session_list_widget)
        splitter.setStretchFactor(0, 0)
        
        # Main chat area
        chat_widget = self._create_chat_area()
        splitter.addWidget(chat_widget)
        splitter.setStretchFactor(1, 1)
        
        # Context sidebar (right)
        self.context_widget = self._create_context_sidebar()
        splitter.addWidget(self.context_widget)
        splitter.setStretchFactor(2, 0)
        
        # Set splitter sizes (20% session, 60% chat, 20% context)
        splitter.setSizes([200, 600, 200])
        
    def _create_session_list(self) -> QWidget:
        """Create session list sidebar."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        title_label = QLabel("Recent Sessions")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)
        
        # Session list
        self.session_list = QListWidget()
        self.session_list.itemClicked.connect(self._on_session_selected)
        layout.addWidget(self.session_list)
        
        # New session button
        new_session_btn = QPushButton("New Session")
        new_session_btn.clicked.connect(self._on_new_session)
        layout.addWidget(new_session_btn)
        
        return widget
        
    def _create_chat_area(self) -> QWidget:
        """Create main chat area."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Session title bar
        title_layout = QHBoxLayout()
        
        self.title_label = QLabel("No session")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        title_layout.addWidget(self.title_label)
        
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Session title...")
        self.title_edit.setVisible(False)
        self.title_edit.editingFinished.connect(self._on_title_edited)
        title_layout.addWidget(self.title_edit)
        
        title_layout.addStretch()
        
        edit_title_btn = QPushButton("Edit")
        edit_title_btn.clicked.connect(self._on_edit_title)
        title_layout.addWidget(edit_title_btn)
        
        layout.addLayout(title_layout)
        
        # Message list
        self.message_list = MessageList()
        self.message_list.context_clicked.connect(self._on_context_clicked)
        layout.addWidget(self.message_list)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Type your message... (Enter to send, Shift+Enter for newline)")
        self.input_text.setMaximumHeight(100)
        self.input_text.setAcceptDrops(True)
        # Store original keyPressEvent
        self._original_key_press = self.input_text.keyPressEvent
        # Install event filter for key press
        self.input_text.installEventFilter(self)
        input_layout.addWidget(self.input_text)
        
        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self._on_send_message)
        input_layout.addWidget(send_btn)
        
        upload_btn = QPushButton("Upload")
        upload_btn.clicked.connect(self._on_upload_file)
        input_layout.addWidget(upload_btn)
        
        layout.addLayout(input_layout)
        
        return widget
        
    def _create_context_sidebar(self) -> QWidget:
        """Create context sidebar."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        title_label = QLabel("Context Used")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)
        
        # Context tree
        self.context_tree = QTreeWidget()
        self.context_tree.setHeaderLabel("Context Chunks")
        self.context_tree.setColumnCount(1)
        layout.addWidget(self.context_tree)
        
        # Session topics summary
        topics_label = QLabel("Session Topics")
        topics_label.setStyleSheet("font-weight: bold; font-size: 12px; margin-top: 10px;")
        layout.addWidget(topics_label)
        
        self.topics_list = QListWidget()
        layout.addWidget(self.topics_list)
        
        return widget
        
    def _on_input_key_press(self, event):
        """Handle key press in input text edit."""
        # Enter to send, Shift+Enter for newline
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if event.modifiers() & Qt.ShiftModifier:
                # Shift+Enter: insert newline - let default handler process
                return False
            else:
                # Enter: send message
                self._on_send_message()
                return True
        return False
    
    def _on_drag_enter(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return True
        return False
    
    def _on_drop(self, event: QDropEvent):
        """Handle drop event for file upload."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = Path(urls[0].toLocalFile())
                self._handle_file_upload(file_path)
            event.acceptProposedAction()
            return True
        return False
    
    def _on_send_message(self):
        """Handle send message button click."""
        text = self.input_text.toPlainText().strip()
        if not text:
            return
        
        if not self.current_session_id:
            # Start new session
            self._start_new_session()
        
        # Clear input
        self.input_text.clear()
        
        # Send message
        self._run_async(self._async_send_message(text))
    
    def _on_upload_file(self):
        """Handle upload file button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Upload File",
            "",
            "Text Files (*.txt);;Markdown Files (*.md);;JSON Files (*.json);;All Files (*.*)"
        )
        if file_path:
            self._handle_file_upload(Path(file_path))
    
    def _handle_file_upload(self, file_path: Path):
        """Handle file upload."""
        try:
            # Read file content
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            
            # Add as user message
            if not self.current_session_id:
                self._start_new_session()
            
            # Prepend file info to content
            message = f"[Uploaded: {file_path.name}]\n\n{content}"
            
            # Send message
            self._run_async(self._async_send_message(message))
            
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            QMessageBox.warning(self, "Upload Failed", f"Failed to upload file: {e}")
    
    def _on_new_session(self):
        """Handle new session button click."""
        self._start_new_session()
    
    def _on_session_selected(self, item: QListWidgetItem):
        """Handle session selection."""
        session_id = item.data(Qt.UserRole)
        if session_id:
            self._run_async(self._async_load_session(session_id))
    
    def _on_edit_title(self):
        """Handle edit title button click."""
        if self.title_edit.isVisible():
            # Save title
            self._on_title_edited()
        else:
            # Show edit field
            self.title_label.setVisible(False)
            self.title_edit.setText(self.current_session_title or "")
            self.title_edit.setVisible(True)
            self.title_edit.setFocus()
    
    def _on_title_edited(self):
        """Handle title edit finished."""
        new_title = self.title_edit.text().strip()
        if new_title and new_title != self.current_session_title:
            self.current_session_title = new_title
            self.title_label.setText(new_title)
            # TODO: Update session title in database
        self.title_edit.setVisible(False)
        self.title_label.setVisible(True)
    
    def _on_context_clicked(self, message_index: int):
        """Handle context indicator click."""
        # Highlight context chunks in sidebar
        self._update_context_display()
    
    def _start_new_session(self):
        """Start a new chat session."""
        self._run_async(self._async_start_session())
    
    async def _async_start_session(self):
        """Async start new session."""
        try:
            result = await self.facade.chat_start()
            self.current_session_id = result["session_id"]
            self.current_session_title = result.get("title")
            
            # Update UI
            self.title_label.setText(self.current_session_title or "New Session")
            self.message_list.clear_messages()
            self.context_chunks = []
            self._update_context_display()
            
            # Emit signal
            self.session_changed.emit(self.current_session_id)
            
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            QMessageBox.critical(self, "Session Start Failed", str(e))
    
    async def _async_load_session(self, session_id: str):
        """Async load existing session."""
        try:
            result = await self.facade.chat_resume(session_id)
            self.current_session_id = session_id
            self.current_session_title = result.get("title")
            
            # Update UI
            self.title_label.setText(self.current_session_title or "Untitled")
            self.message_list.clear_messages()
            
            # Load messages
            # TODO: Load messages from database
            # For now, just update title
            
            # Emit signal
            self.session_changed.emit(self.current_session_id)
            
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            QMessageBox.critical(self, "Session Load Failed", str(e))
    
    async def _async_send_message(self, user_message: str):
        """Async send message and get AI reply."""
        if not self.current_session_id:
            await self._async_start_session()
        
        # Add user message to display
        user_msg = ChatMessage(
            role="user",
            content=user_message,
            timestamp=datetime.utcnow(),
        )
        self.message_list.add_message(user_msg)
        
        # Show typing indicator
        self.typing_indicator = self.message_list.add_typing_indicator()
        
        try:
            # Send message via facade
            result = await self.facade.chat_turn(
                self.current_session_id,
                user_message,
                suggest_title=(not self.current_session_title),
            )
            
            # Remove typing indicator
            if self.typing_indicator:
                self.message_list.remove_typing_indicator(self.typing_indicator)
                self.typing_indicator = None
            
            # Update session title if suggested
            if result.get("title") and not self.current_session_title:
                self.current_session_title = result["title"]
                self.title_label.setText(self.current_session_title)
            
            # Add AI reply to display
            ai_reply = result.get("ai_reply", "")
            ai_msg = ChatMessage(
                role="tutor",
                content=ai_reply,
                timestamp=datetime.utcnow(),
            )
            has_context = bool(result.get("context_used"))
            self.message_list.add_message(ai_msg, has_context=has_context)
            
            # Update context chunks
            context_used = result.get("context_used", [])
            if context_used:
                # TODO: Load context chunk details from database
                self.context_chunks = [{"chunk_id": cid} for cid in context_used]
                self._update_context_display()
            
        except FacadeTimeoutError as e:
            # Remove typing indicator
            if self.typing_indicator:
                self.message_list.remove_typing_indicator(self.typing_indicator)
                self.typing_indicator = None
            
            # Show error with retry option
            reply = QMessageBox.critical(
                self,
                "Request Timeout",
                f"Request timed out: {e}\n\nRetry?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply == QMessageBox.Yes:
                # Retry
                self._run_async(self._async_send_message(user_message))
            else:
                # Show error message in chat
                error_msg = ChatMessage(
                    role="system",
                    content=f"Error: Request timed out. Please try again.",
                    timestamp=datetime.utcnow(),
                )
                self.message_list.add_message(error_msg)
                
        except FacadeError as e:
            # Remove typing indicator
            if self.typing_indicator:
                self.message_list.remove_typing_indicator(self.typing_indicator)
                self.typing_indicator = None
            
            # Show error with retry option
            reply = QMessageBox.critical(
                self,
                "Error",
                f"Failed to send message: {e}\n\nRetry?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply == QMessageBox.Yes:
                # Retry
                self._run_async(self._async_send_message(user_message))
            else:
                # Show error message in chat
                error_msg = ChatMessage(
                    role="system",
                    content=f"Error: {e}",
                    timestamp=datetime.utcnow(),
                )
                self.message_list.add_message(error_msg)
    
    def _update_context_display(self):
        """Update context sidebar display."""
        self.context_tree.clear()
        
        for chunk in self.context_chunks:
            item = QTreeWidgetItem(self.context_tree)
            item.setText(0, f"Chunk: {chunk.get('chunk_id', 'unknown')}")
            # TODO: Add expandable details (source event, topic, score)
    
    def _load_recent_sessions(self):
        """Load recent sessions into sidebar."""
        self._run_async(self._async_load_recent_sessions())
    
    async def _async_load_recent_sessions(self):
        """Async load recent sessions."""
        try:
            sessions = await self.facade.chat_list(limit=20)
            
            self.session_list.clear()
            for session in sessions:
                item = QListWidgetItem(session.get("title", "Untitled"))
                item.setData(Qt.UserRole, session.get("session_id"))
                self.session_list.addItem(item)
                
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
    
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

