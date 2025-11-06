"""
Database I/O layer for AI Tutor Proof of Concept.

Provides context manager for database connections, initialization,
and CRUD operations for all entities.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from src.config import DB_PATH, get_data_dir
from src.models.base import (
    Event,
    SkillState,
    TopicSummary,
    Goal,
    Commitment,
    NudgeLog,
)
from src.utils.serialization import (
    serialize_json_list,
    deserialize_json_list,
    serialize_json_dict,
    deserialize_json_dict,
    serialize_datetime,
    deserialize_datetime,
)


class DatabaseError(Exception):
    """Base exception for database operations."""
    pass


class DatabaseNotFoundError(DatabaseError):
    """Raised when database file is not found."""
    pass


class ConstraintViolationError(DatabaseError):
    """Raised when a database constraint is violated."""
    pass


class Database:
    """
    Database context manager for SQLite operations.
    
    Provides connection management, initialization, and CRUD operations
    for all entities. Uses context manager pattern for transaction safety.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to database file (defaults to config.DB_PATH)
        """
        self.db_path = db_path or DB_PATH
        self.conn: Optional[sqlite3.Connection] = None
    
    def __enter__(self):
        """Enter context manager and return self."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and close connection."""
        if self.conn:
            if exc_type:
                self.conn.rollback()
            else:
                self.conn.commit()
            self.conn.close()
        return False
    
    def initialize(self) -> None:
        """
        Initialize database with schema.
        
        Creates all tables, indexes, and triggers if they don't exist.
        Safe to call multiple times (uses IF NOT EXISTS).
        
        Raises:
            DatabaseError: If schema file cannot be read or executed
        """
        if not self.conn:
            raise DatabaseError("Database connection not established")
        
        schema_file = Path(__file__).parent / "schema.sql"
        if not schema_file.exists():
            raise DatabaseNotFoundError(f"Schema file not found: {schema_file}")
        
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = f.read()
        
        try:
            self.conn.executescript(schema)
            self.conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to initialize database: {e}") from e
    
    def _execute_insert(self, table: str, data: Dict[str, Any]) -> int:
        """
        Execute INSERT statement and return inserted row ID.
        
        Args:
            table: Table name
            data: Dictionary of column: value pairs
            
        Returns:
            Inserted row ID
            
        Raises:
            ConstraintViolationError: If constraint is violated
            DatabaseError: For other database errors
        """
        if not self.conn:
            raise DatabaseError("Database connection not established")
        
        columns = ", ".join(data.keys())
        placeholders = ", ".join("?" * len(data))
        values = tuple(data.values())
        
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, values)
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            raise ConstraintViolationError(f"Constraint violation: {e}") from e
        except sqlite3.Error as e:
            raise DatabaseError(f"Database error: {e}") from e
    
    def _execute_update(self, table: str, data: Dict[str, Any], where_clause: str, where_values: tuple) -> int:
        """
        Execute UPDATE statement and return number of affected rows.
        
        Args:
            table: Table name
            data: Dictionary of column: value pairs to update
            where_clause: WHERE clause (e.g., "id = ?")
            where_values: Values for WHERE clause placeholders
            
        Returns:
            Number of affected rows
            
        Raises:
            ConstraintViolationError: If constraint is violated
            DatabaseError: For other database errors
        """
        if not self.conn:
            raise DatabaseError("Database connection not established")
        
        set_clause = ", ".join(f"{k} = ?" for k in data.keys())
        values = tuple(data.values()) + where_values
        
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, values)
            self.conn.commit()
            return cursor.rowcount
        except sqlite3.IntegrityError as e:
            raise ConstraintViolationError(f"Constraint violation: {e}") from e
        except sqlite3.Error as e:
            raise DatabaseError(f"Database error: {e}") from e
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert sqlite3.Row to dictionary."""
        return dict(row)
    
    # Event operations
    def insert_event(self, event: Event) -> Event:
        """
        Insert an event into the database.
        
        Args:
            event: Event model instance
            
        Returns:
            Event with database ID populated
        """
        data = {
            "event_id": event.event_id,
            "content": event.content,
            "event_type": event.event_type,
            "actor": event.actor,
            "topics": serialize_json_list(event.topics),
            "skills": serialize_json_list(event.skills),
            "created_at": serialize_datetime(event.created_at),
            "recorded_at": serialize_datetime(event.recorded_at) if event.recorded_at else None,
            "embedding": event.embedding,
            "embedding_id": event.embedding_id,
            "metadata": serialize_json_dict(event.metadata),
            "source": event.source,
        }
        
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        
        row_id = self._execute_insert("events", data)
        
        # Return event with ID populated
        inserted_event = Event(**{**event.model_dump(), "id": row_id})
        
        # Queue summarization job if enabled (non-blocking)
        try:
            from src.summarizers.hooks import on_event_created
            on_event_created(inserted_event, db_path=self.db_path)
        except Exception as e:
            # Don't fail event insertion if summarization hook fails
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Summarization hook failed (non-critical): {e}")
        except ImportError:
            # Summarizers module may not be available in all contexts
            pass
        
        return inserted_event
    
    def update_event(self, event: Event) -> Event:
        """
        Update an existing event in the database.
        
        Args:
            event: Event model instance with ID set
            
        Returns:
            Updated event
            
        Raises:
            DatabaseError: If event ID is not set or event not found
        """
        if not event.id:
            raise DatabaseError("Event ID must be set for update")
        
        data = {
            "content": event.content,
            "event_type": event.event_type,
            "actor": event.actor,
            "topics": serialize_json_list(event.topics),
            "skills": serialize_json_list(event.skills),
            "created_at": serialize_datetime(event.created_at),
            "recorded_at": serialize_datetime(event.recorded_at) if event.recorded_at else None,
            "embedding": event.embedding,
            "embedding_id": event.embedding_id,
            "metadata": serialize_json_dict(event.metadata),
            "source": event.source,
        }
        
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        
        self._execute_update("events", data, "id = ?", (event.id,))
        return event
    
    def get_event_by_id(self, event_id: str) -> Optional[Event]:
        """
        Get event by event_id (UUID).
        
        Args:
            event_id: Event UUID
            
        Returns:
            Event if found, None otherwise
        """
        if not self.conn:
            raise DatabaseError("Database connection not established")
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM events WHERE event_id = ?", (event_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_event(row)
    
    def get_event_by_db_id(self, db_id: int) -> Optional[Event]:
        """
        Get event by database ID.
        
        Args:
            db_id: Database primary key ID
            
        Returns:
            Event if found, None otherwise
        """
        if not self.conn:
            raise DatabaseError("Database connection not established")
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM events WHERE id = ?", (db_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_event(row)
    
    def _row_to_event(self, row: sqlite3.Row) -> Event:
        """Convert database row to Event model."""
        row_dict = self._row_to_dict(row)
        
        # Deserialize JSON fields
        row_dict["topics"] = deserialize_json_list(row_dict["topics"])
        row_dict["skills"] = deserialize_json_list(row_dict["skills"])
        row_dict["metadata"] = deserialize_json_dict(row_dict["metadata"])
        
        # Deserialize datetime fields
        if row_dict.get("created_at"):
            row_dict["created_at"] = deserialize_datetime(row_dict["created_at"])
        if row_dict.get("recorded_at"):
            row_dict["recorded_at"] = deserialize_datetime(row_dict["recorded_at"])
        
        return Event.model_validate(row_dict)
    
    # SkillState operations
    def insert_skill_state(self, skill: SkillState) -> SkillState:
        """Insert a skill state into the database."""
        data = {
            "skill_id": skill.skill_id,
            "p_mastery": skill.p_mastery,
            "last_evidence_at": serialize_datetime(skill.last_evidence_at) if skill.last_evidence_at else None,
            "evidence_count": skill.evidence_count,
            "topic_id": skill.topic_id,
            "created_at": serialize_datetime(skill.created_at),
            "updated_at": serialize_datetime(skill.updated_at),
            "metadata": serialize_json_dict(skill.metadata),
        }
        
        data = {k: v for k, v in data.items() if v is not None}
        
        row_id = self._execute_insert("skills", data)
        return SkillState(**{**skill.model_dump(), "id": row_id})
    
    def update_skill_state(self, skill: SkillState) -> SkillState:
        """Update an existing skill state."""
        if not skill.id:
            raise DatabaseError("SkillState ID must be set for update")
        
        data = {
            "p_mastery": skill.p_mastery,
            "last_evidence_at": serialize_datetime(skill.last_evidence_at) if skill.last_evidence_at else None,
            "evidence_count": skill.evidence_count,
            "topic_id": skill.topic_id,
            "updated_at": serialize_datetime(skill.updated_at),
            "metadata": serialize_json_dict(skill.metadata),
        }
        
        data = {k: v for k, v in data.items() if v is not None}
        
        self._execute_update("skills", data, "id = ?", (skill.id,))
        return skill
    
    def get_skill_state_by_id(self, skill_id: str) -> Optional[SkillState]:
        """Get skill state by skill_id."""
        if not self.conn:
            raise DatabaseError("Database connection not established")
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM skills WHERE skill_id = ?", (skill_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_skill_state(row)
    
    def _row_to_skill_state(self, row: sqlite3.Row) -> SkillState:
        """Convert database row to SkillState model."""
        row_dict = self._row_to_dict(row)
        
        row_dict["metadata"] = deserialize_json_dict(row_dict["metadata"])
        
        if row_dict.get("last_evidence_at"):
            row_dict["last_evidence_at"] = deserialize_datetime(row_dict["last_evidence_at"])
        if row_dict.get("created_at"):
            row_dict["created_at"] = deserialize_datetime(row_dict["created_at"])
        if row_dict.get("updated_at"):
            row_dict["updated_at"] = deserialize_datetime(row_dict["updated_at"])
        
        return SkillState.model_validate(row_dict)
    
    # TopicSummary operations
    def insert_topic_summary(self, topic: TopicSummary) -> TopicSummary:
        """Insert a topic summary into the database."""
        data = {
            "topic_id": topic.topic_id,
            "parent_topic_id": topic.parent_topic_id,
            "summary": topic.summary,
            "open_questions": serialize_json_list(topic.open_questions),
            "event_count": topic.event_count,
            "last_event_at": serialize_datetime(topic.last_event_at) if topic.last_event_at else None,
            "created_at": serialize_datetime(topic.created_at),
            "updated_at": serialize_datetime(topic.updated_at),
            "metadata": serialize_json_dict(topic.metadata),
        }
        
        data = {k: v for k, v in data.items() if v is not None}
        
        row_id = self._execute_insert("topics", data)
        return TopicSummary(**{**topic.model_dump(), "id": row_id})
    
    def update_topic_summary(self, topic: TopicSummary) -> TopicSummary:
        """Update an existing topic summary."""
        if not topic.id:
            raise DatabaseError("TopicSummary ID must be set for update")
        
        data = {
            "parent_topic_id": topic.parent_topic_id,
            "summary": topic.summary,
            "open_questions": serialize_json_list(topic.open_questions),
            "event_count": topic.event_count,
            "last_event_at": serialize_datetime(topic.last_event_at) if topic.last_event_at else None,
            "updated_at": serialize_datetime(topic.updated_at),
            "metadata": serialize_json_dict(topic.metadata),
        }
        
        data = {k: v for k, v in data.items() if v is not None}
        
        self._execute_update("topics", data, "id = ?", (topic.id,))
        return topic
    
    def get_topic_summary_by_id(self, topic_id: str) -> Optional[TopicSummary]:
        """Get topic summary by topic_id."""
        if not self.conn:
            raise DatabaseError("Database connection not established")
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM topics WHERE topic_id = ?", (topic_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_topic_summary(row)
    
    def _row_to_topic_summary(self, row: sqlite3.Row) -> TopicSummary:
        """Convert database row to TopicSummary model."""
        row_dict = self._row_to_dict(row)
        
        row_dict["open_questions"] = deserialize_json_list(row_dict["open_questions"])
        row_dict["metadata"] = deserialize_json_dict(row_dict["metadata"])
        
        if row_dict.get("last_event_at"):
            row_dict["last_event_at"] = deserialize_datetime(row_dict["last_event_at"])
        if row_dict.get("created_at"):
            row_dict["created_at"] = deserialize_datetime(row_dict["created_at"])
        if row_dict.get("updated_at"):
            row_dict["updated_at"] = deserialize_datetime(row_dict["updated_at"])
        
        return TopicSummary.model_validate(row_dict)
    
    # Goal operations
    def insert_goal(self, goal: Goal) -> Goal:
        """Insert a goal into the database."""
        data = {
            "goal_id": goal.goal_id,
            "title": goal.title,
            "description": goal.description,
            "topic_ids": serialize_json_list(goal.topic_ids),
            "skill_ids": serialize_json_list(goal.skill_ids),
            "status": goal.status,
            "created_at": serialize_datetime(goal.created_at),
            "target_date": serialize_datetime(goal.target_date) if goal.target_date else None,
            "completed_at": serialize_datetime(goal.completed_at) if goal.completed_at else None,
            "metadata": serialize_json_dict(goal.metadata),
        }
        
        data = {k: v for k, v in data.items() if v is not None}
        
        row_id = self._execute_insert("goals", data)
        return Goal(**{**goal.model_dump(), "id": row_id})
    
    def update_goal(self, goal: Goal) -> Goal:
        """Update an existing goal."""
        if not goal.id:
            raise DatabaseError("Goal ID must be set for update")
        
        data = {
            "title": goal.title,
            "description": goal.description,
            "topic_ids": serialize_json_list(goal.topic_ids),
            "skill_ids": serialize_json_list(goal.skill_ids),
            "status": goal.status,
            "target_date": serialize_datetime(goal.target_date) if goal.target_date else None,
            "completed_at": serialize_datetime(goal.completed_at) if goal.completed_at else None,
            "metadata": serialize_json_dict(goal.metadata),
        }
        
        data = {k: v for k, v in data.items() if v is not None}
        
        self._execute_update("goals", data, "id = ?", (goal.id,))
        return goal
    
    def get_goal_by_id(self, goal_id: str) -> Optional[Goal]:
        """Get goal by goal_id."""
        if not self.conn:
            raise DatabaseError("Database connection not established")
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM goals WHERE goal_id = ?", (goal_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_goal(row)
    
    def _row_to_goal(self, row: sqlite3.Row) -> Goal:
        """Convert database row to Goal model."""
        row_dict = self._row_to_dict(row)
        
        row_dict["topic_ids"] = deserialize_json_list(row_dict["topic_ids"])
        row_dict["skill_ids"] = deserialize_json_list(row_dict["skill_ids"])
        row_dict["metadata"] = deserialize_json_dict(row_dict["metadata"])
        
        if row_dict.get("created_at"):
            row_dict["created_at"] = deserialize_datetime(row_dict["created_at"])
        if row_dict.get("target_date"):
            row_dict["target_date"] = deserialize_datetime(row_dict["target_date"])
        if row_dict.get("completed_at"):
            row_dict["completed_at"] = deserialize_datetime(row_dict["completed_at"])
        
        return Goal.model_validate(row_dict)
    
    # Commitment operations
    def insert_commitment(self, commitment: Commitment) -> Commitment:
        """Insert a commitment into the database."""
        data = {
            "commitment_id": commitment.commitment_id,
            "description": commitment.description,
            "frequency": commitment.frequency,
            "duration_minutes": commitment.duration_minutes,
            "topic_ids": serialize_json_list(commitment.topic_ids),
            "status": commitment.status,
            "created_at": serialize_datetime(commitment.created_at),
            "start_date": serialize_datetime(commitment.start_date) if commitment.start_date else None,
            "end_date": serialize_datetime(commitment.end_date) if commitment.end_date else None,
            "metadata": serialize_json_dict(commitment.metadata),
        }
        
        data = {k: v for k, v in data.items() if v is not None}
        
        row_id = self._execute_insert("commitments", data)
        return Commitment(**{**commitment.model_dump(), "id": row_id})
    
    def update_commitment(self, commitment: Commitment) -> Commitment:
        """Update an existing commitment."""
        if not commitment.id:
            raise DatabaseError("Commitment ID must be set for update")
        
        data = {
            "description": commitment.description,
            "frequency": commitment.frequency,
            "duration_minutes": commitment.duration_minutes,
            "topic_ids": serialize_json_list(commitment.topic_ids),
            "status": commitment.status,
            "start_date": serialize_datetime(commitment.start_date) if commitment.start_date else None,
            "end_date": serialize_datetime(commitment.end_date) if commitment.end_date else None,
            "metadata": serialize_json_dict(commitment.metadata),
        }
        
        data = {k: v for k, v in data.items() if v is not None}
        
        self._execute_update("commitments", data, "id = ?", (commitment.id,))
        return commitment
    
    def get_commitment_by_id(self, commitment_id: str) -> Optional[Commitment]:
        """Get commitment by commitment_id."""
        if not self.conn:
            raise DatabaseError("Database connection not established")
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM commitments WHERE commitment_id = ?", (commitment_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_commitment(row)
    
    def _row_to_commitment(self, row: sqlite3.Row) -> Commitment:
        """Convert database row to Commitment model."""
        row_dict = self._row_to_dict(row)
        
        row_dict["topic_ids"] = deserialize_json_list(row_dict["topic_ids"])
        row_dict["metadata"] = deserialize_json_dict(row_dict["metadata"])
        
        if row_dict.get("created_at"):
            row_dict["created_at"] = deserialize_datetime(row_dict["created_at"])
        if row_dict.get("start_date"):
            row_dict["start_date"] = deserialize_datetime(row_dict["start_date"])
        if row_dict.get("end_date"):
            row_dict["end_date"] = deserialize_datetime(row_dict["end_date"])
        
        return Commitment.model_validate(row_dict)
    
    # NudgeLog operations
    def insert_nudge_log(self, nudge: NudgeLog) -> NudgeLog:
        """Insert a nudge log into the database."""
        data = {
            "nudge_id": nudge.nudge_id,
            "nudge_type": nudge.nudge_type,
            "message": nudge.message,
            "topic_ids": serialize_json_list(nudge.topic_ids),
            "commitment_id": nudge.commitment_id,
            "status": nudge.status,
            "created_at": serialize_datetime(nudge.created_at),
            "acknowledged_at": serialize_datetime(nudge.acknowledged_at) if nudge.acknowledged_at else None,
            "metadata": serialize_json_dict(nudge.metadata),
        }
        
        data = {k: v for k, v in data.items() if v is not None}
        
        row_id = self._execute_insert("nudge_logs", data)
        return NudgeLog(**{**nudge.model_dump(), "id": row_id})
    
    def update_nudge_log(self, nudge: NudgeLog) -> NudgeLog:
        """Update an existing nudge log."""
        if not nudge.id:
            raise DatabaseError("NudgeLog ID must be set for update")
        
        data = {
            "nudge_type": nudge.nudge_type,
            "message": nudge.message,
            "topic_ids": serialize_json_list(nudge.topic_ids),
            "commitment_id": nudge.commitment_id,
            "status": nudge.status,
            "acknowledged_at": serialize_datetime(nudge.acknowledged_at) if nudge.acknowledged_at else None,
            "metadata": serialize_json_dict(nudge.metadata),
        }
        
        data = {k: v for k, v in data.items() if v is not None}
        
        self._execute_update("nudge_logs", data, "id = ?", (nudge.id,))
        return nudge
    
    def get_nudge_log_by_id(self, nudge_id: str) -> Optional[NudgeLog]:
        """Get nudge log by nudge_id."""
        if not self.conn:
            raise DatabaseError("Database connection not established")
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM nudge_logs WHERE nudge_id = ?", (nudge_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_nudge_log(row)
    
    def _row_to_nudge_log(self, row: sqlite3.Row) -> NudgeLog:
        """Convert database row to NudgeLog model."""
        row_dict = self._row_to_dict(row)
        
        row_dict["topic_ids"] = deserialize_json_list(row_dict["topic_ids"])
        row_dict["metadata"] = deserialize_json_dict(row_dict["metadata"])
        
        if row_dict.get("created_at"):
            row_dict["created_at"] = deserialize_datetime(row_dict["created_at"])
        if row_dict.get("acknowledged_at"):
            row_dict["acknowledged_at"] = deserialize_datetime(row_dict["acknowledged_at"])
        
        return NudgeLog.model_validate(row_dict)
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform database health check.
        
        Checks:
        - Connection is valid
        - Required tables exist
        - Can perform basic queries
        
        Returns:
            Dictionary with health check results
        """
        if not self.conn:
            return {"status": "error", "message": "Database connection not established"}
        
        try:
            cursor = self.conn.cursor()
            
            # Check required tables exist
            required_tables = [
                "events", "skills", "topics", "goals", "commitments", "nudge_logs"
            ]
            
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            existing_tables = {row[0] for row in cursor.fetchall()}
            
            missing_tables = [t for t in required_tables if t not in existing_tables]
            
            if missing_tables:
                return {
                    "status": "error",
                    "message": f"Missing tables: {', '.join(missing_tables)}",
                    "missing_tables": missing_tables,
                }
            
            # Test basic query
            cursor.execute("SELECT COUNT(*) FROM events")
            event_count = cursor.fetchone()[0]
            
            return {
                "status": "ok",
                "message": "Database is healthy",
                "tables": list(existing_tables),
                "event_count": event_count,
            }
        except sqlite3.Error as e:
            return {
                "status": "error",
                "message": f"Database error: {e}",
            }


def initialize_database(db_path: Optional[Path] = None) -> None:
    """
    Initialize database with schema.
    
    Convenience function to initialize database without context manager.
    Creates database file and schema if they don't exist.
    
    Args:
        db_path: Path to database file (defaults to config.DB_PATH)
    """
    db_path = db_path or DB_PATH
    data_dir = db_path.parent
    data_dir.mkdir(parents=True, exist_ok=True)
    
    with Database(db_path) as db:
        db.initialize()

