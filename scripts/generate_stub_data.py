"""
Stub data generation script for AI Tutor Proof of Concept.

Generates minimal valid records for local testing and development.
Creates sample events, topics, skills, and related entities.
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import DB_PATH, get_data_dir
from src.utils.serialization import serialize_json_list, serialize_json_dict


def init_database(db_path: Path) -> sqlite3.Connection:
    """
    Initialize database with schema.
    
    Args:
        db_path: Path to database file
        
    Returns:
        Database connection
    """
    conn = sqlite3.connect(db_path)
    
    # Read and execute schema
    schema_path = Path(__file__).parent.parent / "src" / "storage" / "schema.sql"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = f.read()
    
    conn.executescript(schema)
    conn.commit()
    
    return conn


def generate_stub_data(conn: sqlite3.Connection, num_events: int = 10) -> None:
    """
    Generate minimal valid stub data for testing.
    
    Args:
        conn: Database connection
        num_events: Number of events to generate
    """
    cursor = conn.cursor()
    now = datetime.utcnow()
    
    # Create sample topics (hierarchical)
    topics = [
        ("calculus", None, "Introduction to calculus concepts"),
        ("derivatives", "calculus", "Understanding derivatives"),
        ("integrals", "calculus", "Understanding integrals"),
        ("linear_algebra", None, "Introduction to linear algebra"),
        ("matrices", "linear_algebra", "Matrix operations"),
    ]
    
    for topic_id, parent_id, summary in topics:
        cursor.execute("""
            INSERT OR IGNORE INTO topics (topic_id, parent_topic_id, summary)
            VALUES (?, ?, ?)
        """, (topic_id, parent_id, summary))
    
    # Create sample skills
    skills = [
        ("derivative_basic", "calculus", 0.6),
        ("derivative_chain", "derivatives", 0.4),
        ("integral_basic", "integrals", 0.5),
        ("matrix_multiply", "matrices", 0.7),
    ]
    
    for skill_id, topic_id, p_mastery in skills:
        cursor.execute("""
            INSERT OR IGNORE INTO skills (skill_id, topic_id, p_mastery, last_evidence_at, evidence_count)
            VALUES (?, ?, ?, ?, ?)
        """, (skill_id, topic_id, p_mastery, now - timedelta(days=1), 3))
    
    # Create sample events
    event_types = ["chat", "chat", "chat", "transcript", "quiz"]
    actors = ["student", "tutor", "student", "tutor", "system"]
    contents = [
        "I'm learning about derivatives",
        "Great! Let's start with the basic definition",
        "Can you explain the chain rule?",
        "Here's a detailed explanation of the chain rule...",
        "Quiz: What is the derivative of x^2?",
    ]
    
    for i in range(num_events):
        event_id = str(uuid4())
        event_type = event_types[i % len(event_types)]
        actor = actors[i % len(actors)]
        content = contents[i % len(contents)]
        topics_json = serialize_json_list(["calculus", "derivatives"])
        skills_json = serialize_json_list(["derivative_basic"])
        metadata_json = serialize_json_dict({"session_id": f"session_{i//5}"})
        
        created_at = now - timedelta(days=num_events - i)
        
        cursor.execute("""
            INSERT INTO events (
                event_id, content, event_type, actor, topics, skills,
                created_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (event_id, content, event_type, actor, topics_json, skills_json, created_at, metadata_json))
    
    # Create sample goal
    goal_id = str(uuid4())
    cursor.execute("""
        INSERT INTO goals (goal_id, title, description, topic_ids, skill_ids)
        VALUES (?, ?, ?, ?, ?)
    """, (
        goal_id,
        "Master calculus basics",
        "Complete derivative and integral basics",
        serialize_json_list(["calculus", "derivatives", "integrals"]),
        serialize_json_list(["derivative_basic", "integral_basic"]),
    ))
    
    # Create sample commitment
    commitment_id = str(uuid4())
    cursor.execute("""
        INSERT INTO commitments (commitment_id, description, frequency, duration_minutes, topic_ids)
        VALUES (?, ?, ?, ?, ?)
    """, (
        commitment_id,
        "Study calculus daily",
        "daily",
        30,
        serialize_json_list(["calculus"]),
    ))
    
    conn.commit()
    print(f"Generated {num_events} events, {len(topics)} topics, {len(skills)} skills, 1 goal, 1 commitment")


def main():
    """Main entry point for stub data generation."""
    # Ensure data directory exists
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize database
    print(f"Initializing database at {DB_PATH}")
    conn = init_database(DB_PATH)
    
    # Generate stub data
    print("Generating stub data...")
    generate_stub_data(conn, num_events=10)
    
    conn.close()
    print("Stub data generation complete!")


if __name__ == "__main__":
    main()

