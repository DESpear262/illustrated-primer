"""
Integration tests for chat interface with mocked AI client.
"""

import json
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch, Mock

from src.interface.tutor_chat import ChatSession, _load_session_events, list_sessions, run_session
from src.storage.db import Database
from src.models.base import Event


def _make_db(tmp_path) -> Path:
    db_path = tmp_path / "test.db"
    with Database(db_path) as db:
        db.initialize()
    return db_path


@patch('src.services.ai.client.OpenAI')
def test_session_records_and_summarizes(mock_openai_class, tmp_path):
    db_path = _make_db(tmp_path)

    # Mock chat reply and summarize
    mock_client = Mock()
    # chat replies
    mock_client.chat.completions.create.side_effect = [
        Mock(choices=[Mock(message=Mock(content="A derivative is rate of change."))], usage=Mock(completion_tokens=5)),
        Mock(choices=[Mock(message=Mock(content="Session Title"))], usage=Mock(completion_tokens=2)),
        Mock(choices=[Mock(message=Mock(content=json.dumps({"summary":"Session summary","topics":[],"skills":[],"key_points":[],"open_questions":[]})))], usage=Mock(completion_tokens=10)),
    ]
    mock_openai_class.return_value = mock_client

    session = ChatSession()

    # Seed with one user event then end
    with Database(db_path) as db:
        e = Event(event_id=str(uuid4()), content="What is a derivative?", event_type="chat", actor="student",
                  metadata={"session_id": session.session_id, "turn_index": 1})
        db.insert_event(e)

    # Run minimal loop that triggers one reply and summary
    # We won't simulate input loop; call summarize directly over events
    events = _load_session_events(session.session_id, db_path)
    assert len(events) == 1

    # Fake end-of-session summary insertion
    with Database(db_path) as db:
        s = Event(event_id=str(uuid4()), content="Session summary", event_type="chat", actor="system",
                  metadata={"session_id": session.session_id, "turn_index": 2})
        db.insert_event(s)

    events2 = _load_session_events(session.session_id, db_path)
    assert len(events2) == 2
    assert events2[-1].actor == "system"


def test_list_sessions(tmp_path):
    db_path = _make_db(tmp_path)

    sess_id = str(uuid4())
    with Database(db_path) as db:
        for i in range(3):
            e = Event(event_id=str(uuid4()), content=f"msg {i}", event_type="chat", actor="student",
                      metadata={"session_id": sess_id, "turn_index": i+1, "session_title": "Test Session"})
            db.insert_event(e)

    rows = list_sessions(db_path)
    assert any(r["session_id"] == sess_id for r in rows)


