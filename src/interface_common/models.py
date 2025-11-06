"""
UI Model Definitions for AI Tutor Proof of Concept.

Provides shared Pydantic models for consistent data structures between
CLI outputs and GUI responses. Ensures schema contracts for all GUI front-ends.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any, List, Literal, Union
from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    """
    Graph node model for knowledge tree visualization.
    
    Represents a node in the DAG (topic, skill, or event) in Cytoscape.js format.
    This models the 'data' object within the Cytoscape.js node structure.
    """
    
    # Core fields (required for all node types)
    id: str = Field(..., description="Node ID in format 'type:id' (e.g., 'topic:math')")
    type: Literal["topic", "skill", "event"] = Field(..., description="Node type")
    label: str = Field(..., description="Display label for the node")
    
    # Topic-specific fields (optional)
    summary: Optional[str] = Field(None, description="Topic summary text")
    event_count: Optional[int] = Field(None, description="Number of events associated with topic")
    last_event_at: Optional[str] = Field(None, description="ISO timestamp of last event")
    
    # Skill-specific fields (optional)
    mastery: Optional[float] = Field(None, ge=0.0, le=1.0, description="Mastery probability (0.0-1.0)")
    evidence_count: Optional[int] = Field(None, description="Number of evidence events")
    last_evidence_at: Optional[str] = Field(None, description="ISO timestamp of last evidence")
    
    # Event-specific fields (optional)
    content: Optional[str] = Field(None, description="Event content (truncated)")
    event_type: Optional[Literal["chat", "transcript", "quiz", "assessment"]] = Field(
        None, description="Event type"
    )
    actor: Optional[Literal["student", "tutor", "system"]] = Field(None, description="Event actor")
    created_at: Optional[str] = Field(None, description="ISO timestamp of event creation")
    
    model_config = {
        "json_encoders": {datetime: lambda v: v.isoformat()},
    }


class GraphEdge(BaseModel):
    """
    Graph edge model for knowledge tree visualization.
    
    Represents an edge in the DAG (relationship between nodes) in Cytoscape.js format.
    This models the 'data' object within the Cytoscape.js edge structure.
    """
    
    id: str = Field(..., description="Edge ID (e.g., 'e1', 'e2')")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    type: str = Field(..., description="Edge type (e.g., 'parent-child', 'belongs-to', 'evidence')")
    label: str = Field(..., description="Edge label (e.g., 'parent-of', 'has-skill')")


class EventSnippet(BaseModel):
    """Event snippet model for hover payloads."""
    
    content: str = Field(..., description="Event content snippet (truncated)")
    actor: Literal["student", "tutor", "system"] = Field(..., description="Event actor")
    created_at: str = Field(..., description="ISO timestamp of event creation")


class HoverStatistics(BaseModel):
    """Statistics model for hover payloads."""
    
    created_at: Optional[str] = Field(None, description="ISO timestamp of creation")
    updated_at: Optional[str] = Field(None, description="ISO timestamp of last update")
    content_length: Optional[int] = Field(None, description="Content length (for events)")


class TopicHoverPayload(BaseModel):
    """Hover payload for topic nodes."""
    
    title: str = Field(..., description="Topic title/ID")
    type: Literal["topic"] = Field("topic", description="Node type")
    summary: str = Field(..., description="Topic summary text")
    event_count: int = Field(..., description="Number of events associated with topic")
    last_event_at: Optional[str] = Field(None, description="ISO timestamp of last event")
    open_questions: List[str] = Field(default_factory=list, description="List of open questions")
    event_snippet: Optional[EventSnippet] = Field(None, description="Recent event snippet")
    statistics: HoverStatistics = Field(..., description="Topic statistics")


class SkillHoverPayload(BaseModel):
    """Hover payload for skill nodes."""
    
    title: str = Field(..., description="Skill title/ID")
    type: Literal["skill"] = Field("skill", description="Node type")
    mastery: float = Field(..., ge=0.0, le=1.0, description="Mastery probability (0.0-1.0)")
    evidence_count: int = Field(..., description="Number of evidence events")
    last_evidence_at: Optional[str] = Field(None, description="ISO timestamp of last evidence")
    topic_id: Optional[str] = Field(None, description="Parent topic ID")
    event_snippet: Optional[EventSnippet] = Field(None, description="Recent event snippet")
    statistics: HoverStatistics = Field(..., description="Skill statistics")


class EventHoverPayload(BaseModel):
    """Hover payload for event nodes."""
    
    title: str = Field(..., description="Event title (short ID)")
    type: Literal["event"] = Field("event", description="Node type")
    content: str = Field(..., description="Event content (truncated)")
    event_type: Literal["chat", "transcript", "quiz", "assessment"] = Field(
        ..., description="Event type"
    )
    actor: Literal["student", "tutor", "system"] = Field(..., description="Event actor")
    topics: List[str] = Field(default_factory=list, description="List of topic IDs")
    skills: List[str] = Field(default_factory=list, description="List of skill IDs")
    created_at: str = Field(..., description="ISO timestamp of event creation")
    recorded_at: Optional[str] = Field(None, description="ISO timestamp of original recording")
    statistics: HoverStatistics = Field(..., description="Event statistics")


# Discriminated union for hover payloads
HoverPayload = Union[TopicHoverPayload, SkillHoverPayload, EventHoverPayload]


class ChatMessage(BaseModel):
    """
    Chat message model for tutor chat interface.
    
    Represents a single message in a chat session, used for both
    student and tutor messages.
    """
    
    role: Literal["student", "tutor", "system"] = Field(..., description="Message role")
    content: str = Field(..., description="Message content text")
    timestamp: datetime = Field(..., description="Message timestamp")
    session_id: str = Field(..., description="Chat session ID")
    event_id: Optional[str] = Field(None, description="Associated event ID (if stored)")
    
    model_config = {
        "json_encoders": {datetime: lambda v: v.isoformat()},
    }


class CommandResult(BaseModel):
    """
    Command result model for facade operations.
    
    Represents the result of a facade command execution, including
    success status, result data, error information, and duration.
    """
    
    success: bool = Field(..., description="Whether the command succeeded")
    result: Optional[Dict[str, Any]] = Field(None, description="Command result data (if successful)")
    error: Optional[Dict[str, Any]] = Field(None, description="Error information (if failed)")
    duration_seconds: float = Field(..., ge=0.0, description="Command execution duration in seconds")
    
    @classmethod
    def from_facade_response(cls, response: Dict[str, Any]) -> CommandResult:
        """
        Create CommandResult from facade response dictionary.
        
        Args:
            response: Dictionary from facade method (e.g., {"success": True, "result": {...}, "duration_seconds": 0.5})
            
        Returns:
            CommandResult instance
        """
        # Extract error if present
        error = None
        if not response.get("success", False):
            error = {
                "error_type": response.get("error", {}).get("error_type", "UnknownError"),
                "message": response.get("error", {}).get("message", "Unknown error"),
                "details": response.get("error", {}).get("details", {}),
            }
        
        return cls(
            success=response.get("success", False),
            result=response.get("result"),
            error=error,
            duration_seconds=response.get("duration_seconds", 0.0),
        )

