"""
Pydantic models for AI Tutor Proof of Concept.

Defines core data structures for events, skills, topics, and related entities.
All models support JSON serialization and validation.
"""

from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class Event(BaseModel):
    """
    Represents a single interaction event (chat turn, transcript, quiz, etc.).
    
    Events are the atomic units of learning history. Each event contains
    content, metadata, and optional embeddings for retrieval.
    """
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        from_attributes=True,
    )
    
    # Core identifiers
    id: Optional[int] = Field(None, description="Database primary key")
    event_id: str = Field(..., description="Unique event identifier (UUID)")
    
    # Content and metadata
    content: str = Field(..., description="Raw content text (chat, transcript, etc.)")
    event_type: Literal['chat', 'transcript', 'quiz', 'assessment'] = Field(..., description="Type: 'chat', 'transcript', 'quiz', 'assessment'")
    actor: Literal['student', 'tutor', 'system'] = Field(..., description="Actor: 'student', 'tutor', 'system'")
    
    # Topics and skills
    topics: List[str] = Field(default_factory=list, description="List of topic identifiers")
    skills: List[str] = Field(default_factory=list, description="List of skill identifiers")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Event creation timestamp")
    recorded_at: Optional[datetime] = Field(None, description="Original recording timestamp (for imports)")
    
    # Embedding and retrieval
    embedding: Optional[bytes] = Field(None, description="Serialized embedding vector (FAISS format)")
    embedding_id: Optional[int] = Field(None, description="FAISS index ID for this embedding")
    
    # Additional metadata
    metadata: dict = Field(default_factory=dict, description="Additional JSON metadata")
    source: Optional[str] = Field(None, description="Source identifier (e.g., 'imported_transcript_v1')")


class SkillState(BaseModel):
    """
    Represents the mastery state of a specific skill.
    
    Tracks probability of mastery (p_mastery) and evidence history
    for spaced repetition and adaptive learning.
    """
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        from_attributes=True,
    )
    
    # Core identifiers
    id: Optional[int] = Field(None, description="Database primary key")
    skill_id: str = Field(..., description="Unique skill identifier")
    
    # Mastery tracking
    p_mastery: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Probability of mastery (0.0 to 1.0)"
    )
    
    # Evidence tracking
    last_evidence_at: Optional[datetime] = Field(None, description="Most recent evidence timestamp")
    evidence_count: int = Field(default=0, description="Total number of evidence events")
    
    # Topic association
    topic_id: Optional[str] = Field(None, description="Parent topic identifier")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="State creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    # Metadata
    metadata: dict = Field(default_factory=dict, description="Additional JSON metadata")


class TopicSummary(BaseModel):
    """
    Represents a high-level summary of a topic across multiple sessions.
    
    Topics form a hierarchical DAG (Directed Acyclic Graph) where
    topics can have parent-child relationships. Summaries are derived
    from events and updated incrementally.
    """
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        from_attributes=True,
    )
    
    # Core identifiers
    id: Optional[int] = Field(None, description="Database primary key")
    topic_id: str = Field(..., description="Unique topic identifier")
    
    # Hierarchy
    parent_topic_id: Optional[str] = Field(None, description="Parent topic in DAG hierarchy")
    
    # Summary content
    summary: str = Field(..., description="AI-generated summary text")
    open_questions: List[str] = Field(default_factory=list, description="List of open questions or gaps")
    
    # Statistics
    event_count: int = Field(default=0, description="Number of events associated with this topic")
    last_event_at: Optional[datetime] = Field(None, description="Most recent event timestamp")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Summary creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    # Metadata
    metadata: dict = Field(default_factory=dict, description="Additional JSON metadata")


class Goal(BaseModel):
    """
    Represents a learning goal or objective.
    
    Goals track student intentions and can be linked to topics/skills
    for progress tracking and motivation.
    """
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        from_attributes=True,
    )
    
    # Core identifiers
    id: Optional[int] = Field(None, description="Database primary key")
    goal_id: str = Field(..., description="Unique goal identifier")
    
    # Goal content
    title: str = Field(..., description="Goal title")
    description: Optional[str] = Field(None, description="Detailed goal description")
    
    # Associations
    topic_ids: List[str] = Field(default_factory=list, description="Related topic identifiers")
    skill_ids: List[str] = Field(default_factory=list, description="Related skill identifiers")
    
    # Status
    status: Literal['active', 'completed', 'archived'] = Field(default="active", description="Status: 'active', 'completed', 'archived'")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Goal creation timestamp")
    target_date: Optional[datetime] = Field(None, description="Target completion date")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    
    # Metadata
    metadata: dict = Field(default_factory=dict, description="Additional JSON metadata")


class Commitment(BaseModel):
    """
    Represents a student commitment or study plan.
    
    Commitments track intended study schedules and can be used
    for accountability and reminder generation.
    """
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        from_attributes=True,
    )
    
    # Core identifiers
    id: Optional[int] = Field(None, description="Database primary key")
    commitment_id: str = Field(..., description="Unique commitment identifier")
    
    # Commitment content
    description: str = Field(..., description="Commitment description")
    
    # Schedule
    frequency: Literal['daily', 'weekly', 'custom'] = Field(..., description="Frequency: 'daily', 'weekly', 'custom'")
    duration_minutes: Optional[int] = Field(None, description="Intended duration in minutes")
    
    # Associations
    topic_ids: List[str] = Field(default_factory=list, description="Related topic identifiers")
    
    # Status
    status: Literal['active', 'completed', 'paused'] = Field(default="active", description="Status: 'active', 'completed', 'paused'")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Commitment creation timestamp")
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")
    
    # Metadata
    metadata: dict = Field(default_factory=dict, description="Additional JSON metadata")


class NudgeLog(BaseModel):
    """
    Represents a log entry for system nudges or reminders.
    
    Tracks when the system sends reminders, prompts, or motivational
    messages to the student.
    """
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        from_attributes=True,
    )
    
    # Core identifiers
    id: Optional[int] = Field(None, description="Database primary key")
    nudge_id: str = Field(..., description="Unique nudge identifier")
    
    # Nudge content
    nudge_type: Literal['reminder', 'motivation', 'review_prompt'] = Field(..., description="Type: 'reminder', 'motivation', 'review_prompt'")
    message: str = Field(..., description="Nudge message text")
    
    # Associations
    topic_ids: List[str] = Field(default_factory=list, description="Related topic identifiers")
    commitment_id: Optional[str] = Field(None, description="Related commitment identifier")
    
    # Status
    status: Literal['sent', 'acknowledged', 'dismissed'] = Field(default="sent", description="Status: 'sent', 'acknowledged', 'dismissed'")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Nudge creation timestamp")
    acknowledged_at: Optional[datetime] = Field(None, description="Acknowledgment timestamp")
    
    # Metadata
    metadata: dict = Field(default_factory=dict, description="Additional JSON metadata")

