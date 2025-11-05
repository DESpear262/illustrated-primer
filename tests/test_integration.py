"""
Integration tests for database operations.

Tests end-to-end database operations including inserts, queries,
and topic hierarchy reconstruction.
"""

import pytest
import sqlite3
from pathlib import Path
import tempfile
from datetime import datetime, timedelta
from uuid import uuid4

from src.utils.serialization import serialize_json_list, serialize_json_dict


def create_test_database():
    """Create a test database with schema."""
    db_path = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path.close()
    db_path = Path(db_path.name)
    
    conn = sqlite3.connect(db_path)
    
    # Read and execute schema
    schema_file = Path(__file__).parent.parent / "src" / "storage" / "schema.sql"
    with open(schema_file, "r", encoding="utf-8") as f:
        schema = f.read()
    
    conn.executescript(schema)
    conn.commit()
    
    return conn, db_path


def test_event_insert_and_retrieve():
    """Test inserting and retrieving events."""
    conn, db_path = create_test_database()
    
    try:
        cursor = conn.cursor()
        
        # Insert event
        event_id = str(uuid4())
        topics_json = serialize_json_list(["calculus", "derivatives"])
        skills_json = serialize_json_list(["derivative_basic"])
        metadata_json = serialize_json_dict({"session_id": "test_session"})
        
        cursor.execute("""
            INSERT INTO events (
                event_id, content, event_type, actor, topics, skills,
                created_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id,
            "Test content",
            "chat",
            "student",
            topics_json,
            skills_json,
            datetime.utcnow(),
            metadata_json,
        ))
        conn.commit()
        
        # Retrieve event
        cursor.execute("SELECT * FROM events WHERE event_id = ?", (event_id,))
        row = cursor.fetchone()
        
        assert row is not None
        assert row[1] == event_id  # event_id is second column
        assert row[2] == "Test content"
        assert row[3] == "chat"
        assert row[4] == "student"
        
    finally:
        conn.close()
        db_path.unlink()


def test_topic_hierarchy():
    """Test topic hierarchy reconstruction."""
    conn, db_path = create_test_database()
    
    try:
        cursor = conn.cursor()
        
        # Insert parent topic
        cursor.execute("""
            INSERT INTO topics (topic_id, parent_topic_id, summary)
            VALUES (?, ?, ?)
        """, ("calculus", None, "Introduction to calculus"))
        
        # Insert child topic
        cursor.execute("""
            INSERT INTO topics (topic_id, parent_topic_id, summary)
            VALUES (?, ?, ?)
        """, ("derivatives", "calculus", "Understanding derivatives"))
        
        conn.commit()
        
        # Query parent-child relationship
        cursor.execute("""
            SELECT t1.topic_id, t1.parent_topic_id, t2.topic_id as parent_name
            FROM topics t1
            LEFT JOIN topics t2 ON t1.parent_topic_id = t2.topic_id
            WHERE t1.topic_id = 'derivatives'
        """)
        row = cursor.fetchone()
        
        assert row is not None
        assert row[0] == "derivatives"
        assert row[1] == "calculus"
        assert row[2] == "calculus"  # Parent topic name
        
    finally:
        conn.close()
        db_path.unlink()


def test_skill_state_update():
    """Test updating skill state."""
    conn, db_path = create_test_database()
    
    try:
        cursor = conn.cursor()
        
        # Insert skill
        skill_id = "test_skill"
        cursor.execute("""
            INSERT INTO skills (skill_id, p_mastery, topic_id, evidence_count)
            VALUES (?, ?, ?, ?)
        """, (skill_id, 0.5, "calculus", 1))
        conn.commit()
        
        # Update skill
        new_p_mastery = 0.75
        cursor.execute("""
            UPDATE skills
            SET p_mastery = ?, evidence_count = evidence_count + 1,
                last_evidence_at = ?, updated_at = CURRENT_TIMESTAMP
            WHERE skill_id = ?
        """, (new_p_mastery, datetime.utcnow(), skill_id))
        conn.commit()
        
        # Verify update
        cursor.execute("SELECT p_mastery, evidence_count FROM skills WHERE skill_id = ?", (skill_id,))
        row = cursor.fetchone()
        
        assert row is not None
        assert row[0] == new_p_mastery
        assert row[1] == 2
        
    finally:
        conn.close()
        db_path.unlink()


def test_context_loader_multiple_sessions():
    """Test loading context from multiple sessions."""
    conn, db_path = create_test_database()
    
    try:
        cursor = conn.cursor()
        
        # Insert multiple events across different sessions
        now = datetime.utcnow()
        for i in range(5):
            event_id = str(uuid4())
            topics_json = serialize_json_list(["calculus"])
            skills_json = serialize_json_list(["derivative_basic"])
            metadata_json = serialize_json_dict({"session_id": f"session_{i//3}"})
            
            cursor.execute("""
                INSERT INTO events (
                    event_id, content, event_type, actor, topics, skills,
                    created_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id,
                f"Content {i}",
                "chat",
                "student",
                topics_json,
                skills_json,
                now - timedelta(days=5-i),
                metadata_json,
            ))
        
        conn.commit()
        
        # Query events by topic
        cursor.execute("""
            SELECT event_id, content, created_at
            FROM events
            WHERE topics LIKE '%calculus%'
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        
        assert len(rows) == 5
        # Verify ordering (most recent first)
        for i in range(len(rows) - 1):
            assert rows[i][2] >= rows[i+1][2]
        
    finally:
        conn.close()
        db_path.unlink()


def test_fts_search():
    """Test full-text search on events."""
    conn, db_path = create_test_database()
    
    try:
        cursor = conn.cursor()
        
        # Insert events
        for i in range(3):
            event_id = str(uuid4())
            topics_json = serialize_json_list(["calculus"])
            skills_json = serialize_json_list(["derivative_basic"])
            
            cursor.execute("""
                INSERT INTO events (
                    event_id, content, event_type, actor, topics, skills
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                event_id,
                f"Learning about derivatives and integrals",
                "chat",
                "student",
                topics_json,
                skills_json,
            ))
        
        conn.commit()
        
        # Search using FTS
        cursor.execute("""
            SELECT e.event_id, e.content
            FROM events e
            JOIN events_fts ON e.id = events_fts.rowid
            WHERE events_fts MATCH 'derivatives'
        """)
        rows = cursor.fetchall()
        
        assert len(rows) > 0
        assert all("derivatives" in row[1].lower() for row in rows)
        
    finally:
        conn.close()
        db_path.unlink()

