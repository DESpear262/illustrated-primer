"""
Message List Widget for Tutor Chat View.

Displays chat messages with styled bubbles and context indicators.
"""

from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
)

from src.interface_common.models import ChatMessage

logger = logging.getLogger(__name__)


class MessageItemWidget(QWidget):
    """
    Custom widget for message items in MessageList.
    
    Displays styled message bubbles with user/tutor styling and
    context indicators for AI messages.
    """
    
    def __init__(
        self,
        message: ChatMessage,
        has_context: bool = False,
        parent: Optional[QWidget] = None,
    ):
        """
        Initialize message item widget.
        
        Args:
            message: ChatMessage to display
            has_context: Whether this message has context chunks
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.message = message
        self.has_context = has_context
        
        # Setup layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)
        
        # Message bubble
        bubble_layout = QHBoxLayout()
        
        # User messages: right-aligned, blue
        # Tutor messages: left-aligned, gray
        if message.role == "user":
            bubble_layout.addStretch()
            bubble_color = QColor(0, 123, 255)  # Blue
            text_color = QColor(255, 255, 255)  # White
            alignment = Qt.AlignRight
        else:
            bubble_color = QColor(240, 240, 240)  # Light gray
            text_color = QColor(0, 0, 0)  # Black
            alignment = Qt.AlignLeft
            if message.role == "tutor" and has_context:
                # Add context indicator
                context_label = QLabel("📎")
                context_label.setToolTip("Click to view context chunks used")
                context_label.setStyleSheet("color: #666; font-size: 12px;")
                bubble_layout.addWidget(context_label)
        
        # Message text
        message_text = QTextEdit()
        message_text.setReadOnly(True)
        message_text.setPlainText(message.content)
        message_text.setMaximumHeight(200)
        message_text.setStyleSheet(
            f"""
            QTextEdit {{
                background-color: {bubble_color.name()};
                color: {text_color.name()};
                border: none;
                border-radius: 10px;
                padding: 8px;
                font-size: 14px;
            }}
            """
        )
        
        bubble_layout.addWidget(message_text)
        
        if message.role == "user":
            bubble_layout.addStretch()
        
        layout.addLayout(bubble_layout)
        
        # Timestamp
        timestamp_label = QLabel(self._format_timestamp(message.timestamp))
        timestamp_label.setStyleSheet("color: #666; font-size: 10px;")
        timestamp_label.setAlignment(
            Qt.AlignRight if message.role == "user" else Qt.AlignLeft
        )
        layout.addWidget(timestamp_label)
        
    def _format_timestamp(self, timestamp: datetime) -> str:
        """Format timestamp for display."""
        return timestamp.strftime("%H:%M:%S")
    
    def sizeHint(self) -> QSize:
        """Return preferred size for the item."""
        return QSize(400, 100)


class MessageList(QListWidget):
    """
    Message list widget for displaying chat messages.
    
    Provides styled message bubbles with user/tutor styling,
    context indicators, and typing indicators.
    """
    
    # Signal emitted when context indicator is clicked
    context_clicked = Signal(int)  # Emits message index
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize message list.
        
        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: none;
            }
            QListWidgetItem {
                border: none;
            }
        """)
        self.setSpacing(5)
        
    def add_message(
        self,
        message: ChatMessage,
        has_context: bool = False,
    ):
        """
        Add a message to the list.
        
        Args:
            message: ChatMessage to add
            has_context: Whether this message has context chunks
        """
        item = QListWidgetItem(self)
        item.setSizeHint(QSize(400, 100))
        
        widget = MessageItemWidget(message, has_context, self)
        self.setItemWidget(item, widget)
        
        # Scroll to bottom
        self.scrollToBottom()
        
    def add_typing_indicator(self):
        """
        Add a typing indicator to show AI is thinking.
        
        Returns:
            QListWidgetItem for the typing indicator
        """
        item = QListWidgetItem(self)
        item.setSizeHint(QSize(400, 50))
        
        typing_widget = QWidget()
        typing_layout = QHBoxLayout(typing_widget)
        typing_layout.setContentsMargins(10, 5, 10, 5)
        
        typing_label = QLabel("AI is thinking...")
        typing_label.setStyleSheet("color: #666; font-style: italic;")
        typing_layout.addWidget(typing_label)
        typing_layout.addStretch()
        
        self.setItemWidget(item, typing_widget)
        self.scrollToBottom()
        
        return item
    
    def remove_typing_indicator(self, item: QListWidgetItem):
        """
        Remove typing indicator.
        
        Args:
            item: QListWidgetItem for the typing indicator
        """
        row = self.row(item)
        if row >= 0:
            self.takeItem(row)
    
    def clear_messages(self):
        """Clear all messages from the list."""
        self.clear()

