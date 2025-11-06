"""
UI Model Definitions for AI Tutor Proof of Concept.

Provides shared Pydantic models for GUI interfaces, ensuring consistent
data models across both GUI front-ends. These models define schema
contracts used by the facade and providers.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from src.utils.serialization import model_to_json, model_from_json, models_to_json, models_from_json


class GraphNode(BaseModel):
    """
    Represents a node in the knowledge tree graph.
    
    Can represent either a topic or a skill node, with type-specific
    fields populated based on the node type.
    """
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        from_attributes=True,
    )
    
    # Core identifiers
    id: str = Field(..., description="Node identifier (topic_id or skill_id)")
    type: Literal["topic", "skill"] = Field(..., description="Node type: 'topic' or 'skill'")
    label: str = Field(..., description="Node label for display")
    
    # Topic-specific fields (optional, populated for topic nodes)
    summary: Optional[str] = Field(None, description="Topic summary text")
    event_count: Optional[int] = Field(None, description="Number of events associated with topic")
    parent_topic_id: Optional[str] = Field(None, description="Parent topic in DAG hierarchy")
    
    # Skill-specific fields (optional, populated for skill nodes)
    p_mastery: Optional[float] = Field(None, ge=0.0, le=1.0, description="Probability of mastery (0.0 to 1.0)")
    topic_id: Optional[str] = Field(None, description="Parent topic identifier")
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional node metadata")


class GraphEdge(BaseModel):
    """
    Represents an edge in the knowledge tree graph.
    
    Can represent parent-child relationships (topic→topic) or
    belongs-to relationships (topic→skill).
    """
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        from_attributes=True,
    )
    
    # Core identifiers
    id: str = Field(..., description="Edge identifier (source-target)")
    source: str = Field(..., description="Source node identifier")
    target: str = Field(..., description="Target node identifier")
    type: Literal["parent-child", "topic-skill"] = Field(..., description="Edge type: 'parent-child' or 'topic-skill'")
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional edge metadata")


class HoverPayload(BaseModel):
    """
    Represents hover payload for a node in the knowledge tree.
    
    Contains per-node summaries and statistics. Fields are optional
    and populated based on node type (topic or skill).
    """
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        from_attributes=True,
    )
    
    # Core identifiers
    title: str = Field(..., description="Node title (topic_id or skill_id)")
    node_type: Literal["topic", "skill"] = Field(..., description="Node type: 'topic' or 'skill'")
    
    # Topic-specific fields (optional, populated for topic nodes)
    summary: Optional[str] = Field(None, description="Topic summary text")
    event_count: Optional[int] = Field(None, description="Number of events associated with topic")
    last_event_at: Optional[datetime] = Field(None, description="Most recent event timestamp")
    average_mastery: Optional[float] = Field(None, ge=0.0, le=1.0, description="Average mastery from child skills")
    child_skills_count: Optional[int] = Field(None, description="Number of child skills")
    open_questions: Optional[List[str]] = Field(None, description="List of open questions or gaps")
    
    # Skill-specific fields (optional, populated for skill nodes)
    p_mastery: Optional[float] = Field(None, ge=0.0, le=1.0, description="Probability of mastery (0.0 to 1.0)")
    last_evidence_at: Optional[datetime] = Field(None, description="Most recent evidence timestamp")
    evidence_count: Optional[int] = Field(None, description="Total number of evidence events")
    topic_id: Optional[str] = Field(None, description="Parent topic identifier")
    recent_event_snippet: Optional[Dict[str, Any]] = Field(None, description="Recent event snippet (content, created_at, event_type)")


class ChatMessage(BaseModel):
    """
    Represents a chat message in a tutoring session.
    
    Can represent either a user message or an AI tutor reply.
    """
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        from_attributes=True,
    )
    
    # Core identifiers
    role: Literal["user", "tutor"] = Field(..., description="Message role: 'user' or 'tutor'")
    content: str = Field(..., description="Message content text")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    
    # Session context
    session_id: str = Field(..., description="Session identifier")
    turn_index: int = Field(..., description="Turn index in session")
    
    # Additional context
    context_used: Optional[List[str]] = Field(None, description="List of context chunk IDs used for this message")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional message metadata")


class CommandResult(BaseModel):
    """
    Represents the result of a command execution from the facade.
    
    Used to standardize command responses across all facade operations.
    """
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        from_attributes=True,
    )
    
    # Core identifiers
    command_name: str = Field(..., description="Command name (e.g., 'db.check', 'chat.turn')")
    success: bool = Field(..., description="Whether command executed successfully")
    
    # Result data
    result_data: Optional[Dict[str, Any]] = Field(None, description="Command result data (if successful)")
    error_message: Optional[str] = Field(None, description="Error message (if failed)")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Additional error details (if failed)")
    
    # Execution metadata
    execution_time: Optional[float] = Field(None, ge=0.0, description="Execution time in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Command execution timestamp")
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional command metadata")


# JSON serialization helpers

def graph_node_to_json(node: GraphNode, exclude_none: bool = False) -> Dict[str, Any]:
    """
    Convert GraphNode to JSON-serializable dictionary.
    
    Args:
        node: GraphNode instance
        exclude_none: Whether to exclude None values from output
        
    Returns:
        Dictionary representation of the node
    """
    return model_to_json(node, exclude_none=exclude_none)


def graph_node_from_json(data: Dict[str, Any]) -> GraphNode:
    """
    Create GraphNode from JSON dictionary.
    
    Args:
        data: Dictionary containing node data
        
    Returns:
        GraphNode instance
    """
    return model_from_json(data, GraphNode)


def graph_nodes_to_json(nodes: List[GraphNode], exclude_none: bool = False) -> List[Dict[str, Any]]:
    """
    Convert list of GraphNodes to JSON-serializable dictionaries.
    
    Args:
        nodes: List of GraphNode instances
        exclude_none: Whether to exclude None values from output
        
    Returns:
        List of dictionary representations
    """
    return models_to_json(nodes, exclude_none=exclude_none)


def graph_nodes_from_json(data: List[Dict[str, Any]]) -> List[GraphNode]:
    """
    Create list of GraphNodes from JSON dictionaries.
    
    Args:
        data: List of dictionaries containing node data
        
    Returns:
        List of GraphNode instances
    """
    return [graph_node_from_json(item) for item in data]


def graph_edge_to_json(edge: GraphEdge, exclude_none: bool = False) -> Dict[str, Any]:
    """
    Convert GraphEdge to JSON-serializable dictionary.
    
    Args:
        edge: GraphEdge instance
        exclude_none: Whether to exclude None values from output
        
    Returns:
        Dictionary representation of the edge
    """
    return model_to_json(edge, exclude_none=exclude_none)


def graph_edge_from_json(data: Dict[str, Any]) -> GraphEdge:
    """
    Create GraphEdge from JSON dictionary.
    
    Args:
        data: Dictionary containing edge data
        
    Returns:
        GraphEdge instance
    """
    return model_from_json(data, GraphEdge)


def graph_edges_to_json(edges: List[GraphEdge], exclude_none: bool = False) -> List[Dict[str, Any]]:
    """
    Convert list of GraphEdges to JSON-serializable dictionaries.
    
    Args:
        edges: List of GraphEdge instances
        exclude_none: Whether to exclude None values from output
        
    Returns:
        List of dictionary representations
    """
    return models_to_json(edges, exclude_none=exclude_none)


def graph_edges_from_json(data: List[Dict[str, Any]]) -> List[GraphEdge]:
    """
    Create list of GraphEdges from JSON dictionaries.
    
    Args:
        data: List of dictionaries containing edge data
        
    Returns:
        List of GraphEdge instances
    """
    return [graph_edge_from_json(item) for item in data]


def hover_payload_to_json(payload: HoverPayload, exclude_none: bool = False) -> Dict[str, Any]:
    """
    Convert HoverPayload to JSON-serializable dictionary.
    
    Args:
        payload: HoverPayload instance
        exclude_none: Whether to exclude None values from output
        
    Returns:
        Dictionary representation of the payload
    """
    return model_to_json(payload, exclude_none=exclude_none)


def hover_payload_from_json(data: Dict[str, Any]) -> HoverPayload:
    """
    Create HoverPayload from JSON dictionary.
    
    Args:
        data: Dictionary containing payload data
        
    Returns:
        HoverPayload instance
    """
    return model_from_json(data, HoverPayload)


def chat_message_to_json(message: ChatMessage, exclude_none: bool = False) -> Dict[str, Any]:
    """
    Convert ChatMessage to JSON-serializable dictionary.
    
    Args:
        message: ChatMessage instance
        exclude_none: Whether to exclude None values from output
        
    Returns:
        Dictionary representation of the message
    """
    return model_to_json(message, exclude_none=exclude_none)


def chat_message_from_json(data: Dict[str, Any]) -> ChatMessage:
    """
    Create ChatMessage from JSON dictionary.
    
    Args:
        data: Dictionary containing message data
        
    Returns:
        ChatMessage instance
    """
    return model_from_json(data, ChatMessage)


def chat_messages_to_json(messages: List[ChatMessage], exclude_none: bool = False) -> List[Dict[str, Any]]:
    """
    Convert list of ChatMessages to JSON-serializable dictionaries.
    
    Args:
        messages: List of ChatMessage instances
        exclude_none: Whether to exclude None values from output
        
    Returns:
        List of dictionary representations
    """
    return models_to_json(messages, exclude_none=exclude_none)


def chat_messages_from_json(data: List[Dict[str, Any]]) -> List[ChatMessage]:
    """
    Create list of ChatMessages from JSON dictionaries.
    
    Args:
        data: List of dictionaries containing message data
        
    Returns:
        List of ChatMessage instances
    """
    return [chat_message_from_json(item) for item in data]


def command_result_to_json(result: CommandResult, exclude_none: bool = False) -> Dict[str, Any]:
    """
    Convert CommandResult to JSON-serializable dictionary.
    
    Args:
        result: CommandResult instance
        exclude_none: Whether to exclude None values from output
        
    Returns:
        Dictionary representation of the result
    """
    return model_to_json(result, exclude_none=exclude_none)


def command_result_from_json(data: Dict[str, Any]) -> CommandResult:
    """
    Create CommandResult from JSON dictionary.
    
    Args:
        data: Dictionary containing result data
        
    Returns:
        CommandResult instance
    """
    return model_from_json(data, CommandResult)

