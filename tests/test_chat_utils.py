"""
Tests for chat interface utilities.
"""

from uuid import uuid4
from src.interface.utils import build_history_messages, stitch_transcript, map_actor_to_role
from src.models.base import Event


def _ev(content: str, actor: str = "student") -> Event:
    return Event(event_id=str(uuid4()), content=content, event_type="chat", actor=actor)


def test_map_actor_to_role():
    assert map_actor_to_role("student") == "user"
    assert map_actor_to_role("tutor") == "assistant"
    assert map_actor_to_role("system") == "system"


def test_build_history_messages_budget():
    events = [_ev("hello"), _ev("world", actor="tutor")]
    msgs = build_history_messages(events, token_budget=10)
    assert len(msgs) >= 1
    assert all("role" in m and "content" in m for m in msgs)


def test_stitch_transcript():
    events = [_ev("What is a derivative?", "student"), _ev("It is a rate of change.", "tutor")]
    text = stitch_transcript(events, max_tokens=100)
    assert "Student:" in text and "Tutor:" in text


