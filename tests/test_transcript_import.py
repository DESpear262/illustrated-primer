"""
Unit and integration tests for transcript import functionality.

Tests transcript parsing, actor inference, timestamp parsing, AI classification,
event creation, summarization, embedding, and topic/skill state updates.
"""

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pytest

from src.config import DB_PATH
from src.ingestion.transcripts import (
    parse_txt_transcript,
    parse_md_transcript,
    parse_json_transcript,
    infer_actor_from_text,
    parse_timestamp,
    create_openai_embed_fn,
    update_topic_summary,
    update_skill_states,
    import_transcript,
)
from src.storage.db import Database
from src.models.base import Event, TopicSummary, SkillState


class TestTranscriptParsers:
    """Tests for transcript parser functions."""
    
    def test_parse_txt_transcript(self, tmp_path: Path):
        """Test parsing plain text transcript."""
        file_path = tmp_path / "test.txt"
        content = "This is a test transcript.\nWith multiple lines."
        file_path.write_text(content)
        
        # Touch file to set mtime
        import time
        test_time = datetime(2024, 1, 15, 10, 30, 0)
        target_timestamp = test_time.timestamp()
        import os
        os.utime(file_path, (target_timestamp, target_timestamp))
        
        parsed_content, recorded_at = parse_txt_transcript(file_path)
        
        assert parsed_content == content
        assert recorded_at is not None
        # Allow some tolerance for timestamp parsing
        assert abs((recorded_at - test_time).total_seconds()) < 60
    
    def test_parse_md_transcript(self, tmp_path: Path):
        """Test parsing markdown transcript."""
        file_path = tmp_path / "test.md"
        content = "# Session Transcript\n\nThis is a test transcript."
        file_path.write_text(content)
        
        parsed_content, recorded_at = parse_md_transcript(file_path)
        
        assert parsed_content == content
        assert recorded_at is not None
    
    def test_parse_json_transcript_simple(self, tmp_path: Path):
        """Test parsing simple JSON transcript."""
        file_path = tmp_path / "test.json"
        data = {
            "content": "This is a test transcript.",
            "timestamp": "2024-01-15T10:30:00Z",
        }
        file_path.write_text(json.dumps(data))
        
        content, recorded_at, metadata = parse_json_transcript(file_path)
        
        assert content == data["content"]
        assert recorded_at is not None
        assert isinstance(metadata, dict)
    
    def test_parse_json_transcript_array(self, tmp_path: Path):
        """Test parsing JSON transcript as array of messages."""
        file_path = tmp_path / "test.json"
        data = [
            {"speaker": "Tutor", "text": "Hello, let's start."},
            {"speaker": "Student", "text": "OK, I'm ready."},
            {"text": "Another message without speaker."},
        ]
        file_path.write_text(json.dumps(data))
        
        content, recorded_at, metadata = parse_json_transcript(file_path)
        
        assert "Tutor" in content
        assert "Hello" in content
        assert "Student" in content
        assert isinstance(metadata, dict)
    
    def test_parse_json_transcript_empty(self, tmp_path: Path):
        """Test parsing empty JSON transcript raises error."""
        file_path = tmp_path / "test.json"
        data = {"other_field": "value"}
        file_path.write_text(json.dumps(data))
        
        with pytest.raises(ValueError, match="No content found"):
            parse_json_transcript(file_path)


class TestActorInference:
    """Tests for actor inference from transcript text."""
    
    def test_infer_actor_tutor(self):
        """Test inferring tutor actor."""
        text = "Tutor: Let's start the lesson.\nStudent: OK."
        actor = infer_actor_from_text(text)
        assert actor == "tutor"
    
    def test_infer_actor_student(self):
        """Test inferring student actor."""
        text = "Student: I have a question.\nTutor: Sure, what is it?"
        actor = infer_actor_from_text(text)
        assert actor == "student"
    
    def test_infer_actor_default(self):
        """Test default actor (tutor) when unclear."""
        text = "This is just plain text without speaker labels."
        actor = infer_actor_from_text(text)
        assert actor == "tutor"  # Default for imported transcripts


class TestTimestampParsing:
    """Tests for timestamp parsing."""
    
    def test_parse_timestamp_iso(self):
        """Test parsing ISO format timestamp."""
        text = "Session recorded at 2024-01-15T10:30:00Z"
        timestamp = parse_timestamp(text)
        assert timestamp is not None
        assert timestamp.year == 2024
        assert timestamp.month == 1
        assert timestamp.day == 15
    
    def test_parse_timestamp_date_only(self):
        """Test parsing date-only timestamp."""
        text = "Date: 2024-01-15"
        timestamp = parse_timestamp(text)
        assert timestamp is not None
        assert timestamp.year == 2024
    
    def test_parse_timestamp_file_mtime(self):
        """Test using file modification time as fallback."""
        file_mtime = datetime(2024, 1, 15, 10, 30, 0)
        text = "No timestamp in this text."
        timestamp = parse_timestamp(text, file_mtime=file_mtime)
        assert timestamp == file_mtime
    
    def test_parse_timestamp_none(self):
        """Test returning None when no timestamp found."""
        text = "No timestamp here."
        timestamp = parse_timestamp(text)
        assert timestamp is None


class TestTopicSummaryUpdates:
    """Tests for topic summary updates."""
    
    def test_update_topic_summary_new(self, tmp_path: Path):
        """Test creating new topic summary."""
        db_path = tmp_path / "test.db"
        
        # Create database
        with Database(db_path) as db:
            db.initialize()
        
        # Create topic summary
        event_content = "Learning about derivatives and chain rule."
        summary = update_topic_summary("calculus", event_content, db_path=db_path)
        
        assert summary.topic_id == "calculus"
        assert summary.summary
        assert summary.event_count == 1
        assert summary.last_event_at is not None
    
    def test_update_topic_summary_existing(self, tmp_path: Path):
        """Test updating existing topic summary."""
        db_path = tmp_path / "test.db"
        
        # Create database and initial topic
        with Database(db_path) as db:
            db.initialize()
            initial_topic = TopicSummary(
                topic_id="calculus",
                summary="Initial summary",
                open_questions=["Question 1"],
                event_count=1,
            )
            db.insert_topic_summary(initial_topic)
        
        # Update topic
        event_content = "More content about derivatives."
        updated = update_topic_summary("calculus", event_content, db_path=db_path)
        
        assert updated.event_count == 2
        assert "Initial summary" in updated.summary
        assert "New content" in updated.summary


class TestSkillStateUpdates:
    """Tests for skill state updates."""
    
    def test_update_skill_states_new(self, tmp_path: Path):
        """Test creating new skill states."""
        db_path = tmp_path / "test.db"
        
        # Create database
        with Database(db_path) as db:
            db.initialize()
        
        # Create skill states
        skills = ["derivative_basic", "chain_rule"]
        updated = update_skill_states(skills, "Event content", db_path=db_path)
        
        assert len(updated) == 2
        for skill in updated:
            assert skill.skill_id in skills
            assert skill.evidence_count == 1
            assert skill.p_mastery == 0.5  # Default initial
    
    def test_update_skill_states_existing(self, tmp_path: Path):
        """Test updating existing skill states."""
        db_path = tmp_path / "test.db"
        
        # Create database and initial skill
        with Database(db_path) as db:
            db.initialize()
            initial_skill = SkillState(
                skill_id="derivative_basic",
                p_mastery=0.6,
                evidence_count=2,
            )
            db.insert_skill_state(initial_skill)
        
        # Update skill
        updated = update_skill_states(["derivative_basic"], "Event content", db_path=db_path)
        
        assert len(updated) == 1
        assert updated[0].evidence_count == 3
        assert updated[0].p_mastery > 0.6  # Should increase with positive evidence


class TestImportTranscript:
    """Integration tests for full transcript import."""
    
    def test_import_txt_transcript(self, tmp_path: Path):
        """Test importing a plain text transcript."""
        db_path = tmp_path / "test.db"
        file_path = tmp_path / "transcript.txt"
        
        content = "Tutor: Let's learn about calculus.\nStudent: Great!"
        file_path.write_text(content)
        
        # Create database
        with Database(db_path) as db:
            db.initialize()
        
        # Import transcript (use stub embeddings for testing)
        event = import_transcript(
            file_path=file_path,
            db_path=db_path,
            use_real_embeddings=False,
        )
        
        assert event.event_type == "transcript"
        assert event.content == content
        assert event.actor in ("student", "tutor", "system")
        assert "imported_transcript" == event.source
        assert "source_file_path" in event.metadata
    
    def test_import_json_transcript(self, tmp_path: Path):
        """Test importing a JSON transcript."""
        db_path = tmp_path / "test.db"
        file_path = tmp_path / "transcript.json"
        
        data = {
            "content": "This is a JSON transcript about algebra.",
            "timestamp": "2024-01-15T10:30:00Z",
        }
        file_path.write_text(json.dumps(data))
        
        # Create database
        with Database(db_path) as db:
            db.initialize()
        
        # Import transcript
        event = import_transcript(
            file_path=file_path,
            db_path=db_path,
            use_real_embeddings=False,
        )
        
        assert event.event_type == "transcript"
        assert data["content"] in event.content
        assert event.recorded_at is not None
    
    def test_import_with_manual_tags(self, tmp_path: Path):
        """Test importing with manual topic/skill tags."""
        db_path = tmp_path / "test.db"
        file_path = tmp_path / "transcript.txt"
        
        content = "Learning session content."
        file_path.write_text(content)
        
        # Create database
        with Database(db_path) as db:
            db.initialize()
        
        # Import with manual tags
        event = import_transcript(
            file_path=file_path,
            manual_topics=["calculus", "derivatives"],
            manual_skills=["derivative_basic"],
            db_path=db_path,
            use_real_embeddings=False,
        )
        
        # Manual tags should be included (AI classification may add more)
        assert "calculus" in event.topics or "derivatives" in event.topics
        # Note: AI classification might add topics, so we check if manual ones are present
    
    def test_import_invalid_file(self, tmp_path: Path):
        """Test importing invalid file raises error."""
        db_path = tmp_path / "test.db"
        file_path = tmp_path / "nonexistent.txt"
        
        with Database(db_path) as db:
            db.initialize()
        
        with pytest.raises(IOError, match="File not found"):
            import_transcript(file_path=file_path, db_path=db_path)
    
    def test_import_unsupported_format(self, tmp_path: Path):
        """Test importing unsupported format raises error."""
        db_path = tmp_path / "test.db"
        file_path = tmp_path / "transcript.pdf"
        file_path.write_text("Content")
        
        with Database(db_path) as db:
            db.initialize()
        
        with pytest.raises(ValueError, match="Unsupported file format"):
            import_transcript(file_path=file_path, db_path=db_path)

