"""
Interface Common module for AI Tutor Proof of Concept.

Provides shared backend interface for GUI applications, including async wrappers
for CLI commands and a unified facade API.
"""

from src.interface_common.app_facade import AppFacade, run_command
from src.interface_common.exceptions import (
    FacadeError,
    FacadeTimeoutError,
    FacadeDatabaseError,
    FacadeIndexError,
    FacadeAIError,
    FacadeChatError,
)
from src.interface_common.models import (
    GraphNode,
    GraphEdge,
    HoverPayload,
    TopicHoverPayload,
    SkillHoverPayload,
    EventHoverPayload,
    EventSnippet,
    HoverStatistics,
    ChatMessage,
    CommandResult,
)

__all__ = [
    "AppFacade",
    "run_command",
    "FacadeError",
    "FacadeTimeoutError",
    "FacadeDatabaseError",
    "FacadeIndexError",
    "FacadeAIError",
    "FacadeChatError",
    "GraphNode",
    "GraphEdge",
    "HoverPayload",
    "TopicHoverPayload",
    "SkillHoverPayload",
    "EventHoverPayload",
    "EventSnippet",
    "HoverStatistics",
    "ChatMessage",
    "CommandResult",
]

