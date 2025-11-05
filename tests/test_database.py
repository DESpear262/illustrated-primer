"""
Unit tests for database initialization and schema.

Tests database creation, schema loading, and basic operations.
"""

import pytest
import sqlite3
from pathlib import Path
import tempfile

from src.config import get_data_dir


def test_database_initialization():
    """Test that database can be initialized with schema."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Read and execute schema
        schema_file = Path(__file__).parent.parent / "src" / "storage" / "schema.sql"
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = f.read()
        
        conn.executescript(schema)
        conn.commit()
        
        # Verify tables exist
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            "commitments",
            "events",
            "goals",
            "nudge_logs",
            "skills",
            "topics",
        ]
        
        for table in expected_tables:
            assert table in tables, f"Table {table} not found"
        
        conn.close()
    finally:
        db_path.unlink()


def test_database_indexes():
    """Test that indexes are created correctly."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Read and execute schema
        schema_file = Path(__file__).parent.parent / "src" / "storage" / "schema.sql"
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = f.read()
        
        conn.executescript(schema)
        conn.commit()
        
        # Verify indexes exist
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        
        # Check for key indexes
        assert "idx_events_created_at" in indexes
        assert "idx_events_event_type" in indexes
        assert "idx_skills_skill_id" in indexes
        assert "idx_topics_topic_id" in indexes
        assert "idx_topics_parent_topic_id" in indexes
        
        conn.close()
    finally:
        db_path.unlink()


def test_database_fts_table():
    """Test that FTS5 table is created."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Read and execute schema
        schema_file = Path(__file__).parent.parent / "src" / "storage" / "schema.sql"
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = f.read()
        
        conn.executescript(schema)
        conn.commit()
        
        # Verify FTS table exists
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='events_fts'
        """)
        result = cursor.fetchone()
        assert result is not None, "FTS table not found"
        
        conn.close()
    finally:
        db_path.unlink()


def test_database_triggers():
    """Test that triggers are created."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Read and execute schema
        schema_file = Path(__file__).parent.parent / "src" / "storage" / "schema.sql"
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = f.read()
        
        conn.executescript(schema)
        conn.commit()
        
        # Verify triggers exist
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='trigger'
            ORDER BY name
        """)
        triggers = [row[0] for row in cursor.fetchall()]
        
        assert "events_fts_delete" in triggers
        assert "events_fts_insert" in triggers
        assert "events_fts_update" in triggers
        assert "skills_update_timestamp" in triggers
        assert "topics_update_timestamp" in triggers
        
        conn.close()
    finally:
        db_path.unlink()

