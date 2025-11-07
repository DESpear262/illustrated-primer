"""
Chat interface utilities for AI Tutor Proof of Concept.

Provides helpers for building chat history under a token budget,
mapping events to chat messages, and simple session utilities.
"""

from __future__ import annotations

from typing import List, Dict, Any
from uuid import uuid4

from src.config import CHAT_HISTORY_TOKENS
from src.services.ai.utils import count_tokens, truncate_context
from src.models.base import Event


def generate_session_id() -> str:
    """Generate a new session identifier (UUID4)."""
    return str(uuid4())


def map_actor_to_role(actor: str) -> str:
    """
    Map Event.actor to chat role.
    - student -> user
    - tutor -> assistant
    - system -> system
    """
    if actor == "student":
        return "user"
    if actor == "tutor":
        return "assistant"
    return "system"


def build_history_messages(events: List[Event], token_budget: int = CHAT_HISTORY_TOKENS, model: str = "gpt-4o") -> List[Dict[str, str]]:
    """
    Build chat messages from a list of events within a token budget.

    Args:
        events: Ordered events (oldest -> newest)
        token_budget: Max tokens for combined history
        model: Model for token counting

    Returns:
        List of OpenAI-style messages [{role, content}, ...]
    """
    messages: List[Dict[str, str]] = []
    total_tokens = 0

    # Build messages, trimming from the start if we exceed budget
    for event in events:
        role = map_actor_to_role(event.actor)
        content = event.content
        msg = {"role": role, "content": content}
        messages.append(msg)
        total_tokens += count_tokens(content, model)

    # Trim from the start until within budget
    while messages and total_tokens > token_budget:
        removed = messages.pop(0)
        total_tokens -= count_tokens(removed["content"], model)

    return messages


def stitch_transcript(events: List[Event], max_tokens: int = CHAT_HISTORY_TOKENS, model: str = "gpt-4o") -> str:
    """
    Create a stitched plain-text transcript from events, truncated to token budget.
    """
    lines: List[str] = []
    for e in events:
        speaker = "Student" if e.actor == "student" else ("Tutor" if e.actor == "tutor" else "System")
        lines.append(f"{speaker}: {e.content}")
    transcript = "\n".join(lines)
    return truncate_context(transcript, max_tokens, model)


