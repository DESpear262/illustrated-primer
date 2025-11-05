"""
JSON serialization/deserialization utilities for AI Tutor Proof of Concept.

Handles conversion between Pydantic models and JSON, with special
handling for datetime objects, embedded JSON fields, and binary data.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar
from pathlib import Path

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def model_to_json(model: BaseModel, exclude_none: bool = False) -> Dict[str, Any]:
    """
    Convert a Pydantic model to a JSON-serializable dictionary.
    
    Args:
        model: Pydantic model instance
        exclude_none: Whether to exclude None values from output
        
    Returns:
        Dictionary representation of the model
    """
    return model.model_dump(exclude_none=exclude_none, mode="json")


def model_from_json(data: Dict[str, Any], model_class: Type[T]) -> T:
    """
    Create a Pydantic model instance from a JSON dictionary.
    
    Args:
        data: Dictionary containing model data
        model_class: Pydantic model class to instantiate
        
    Returns:
        Model instance
    """
    return model_class.model_validate(data)


def models_to_json(models: List[BaseModel], exclude_none: bool = False) -> List[Dict[str, Any]]:
    """
    Convert a list of Pydantic models to JSON-serializable dictionaries.
    
    Args:
        models: List of Pydantic model instances
        exclude_none: Whether to exclude None values from output
        
    Returns:
        List of dictionary representations
    """
    return [model_to_json(model, exclude_none=exclude_none) for model in models]


def models_from_json(data: List[Dict[str, Any]], model_class: Type[T]) -> List[T]:
    """
    Create a list of Pydantic model instances from JSON dictionaries.
    
    Args:
        data: List of dictionaries containing model data
        model_class: Pydantic model class to instantiate
        
    Returns:
        List of model instances
    """
    return [model_from_json(item, model_class) for item in data]


def save_model_to_file(model: BaseModel, file_path: Path, exclude_none: bool = False) -> None:
    """
    Save a Pydantic model to a JSON file.
    
    Args:
        model: Pydantic model instance
        file_path: Path to output JSON file
        exclude_none: Whether to exclude None values from output
    """
    data = model_to_json(model, exclude_none=exclude_none)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_model_from_file(file_path: Path, model_class: Type[T]) -> T:
    """
    Load a Pydantic model from a JSON file.
    
    Args:
        file_path: Path to input JSON file
        model_class: Pydantic model class to instantiate
        
    Returns:
        Model instance
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return model_from_json(data, model_class)


def serialize_json_list(items: List[str]) -> str:
    """
    Serialize a list of strings to a JSON array string.
    
    Used for storing list fields in SQLite TEXT columns.
    
    Args:
        items: List of strings to serialize
        
    Returns:
        JSON string representation
    """
    return json.dumps(items, ensure_ascii=False)


def deserialize_json_list(json_str: str) -> List[str]:
    """
    Deserialize a JSON array string to a list of strings.
    
    Used for loading list fields from SQLite TEXT columns.
    
    Args:
        json_str: JSON string representation
        
    Returns:
        List of strings
    """
    if not json_str or json_str.strip() == "":
        return []
    return json.loads(json_str)


def serialize_json_dict(data: Dict[str, Any]) -> str:
    """
    Serialize a dictionary to a JSON string.
    
    Used for storing metadata dictionaries in SQLite TEXT columns.
    
    Args:
        data: Dictionary to serialize
        
    Returns:
        JSON string representation
    """
    return json.dumps(data, ensure_ascii=False, default=str)


def deserialize_json_dict(json_str: str) -> Dict[str, Any]:
    """
    Deserialize a JSON string to a dictionary.
    
    Used for loading metadata dictionaries from SQLite TEXT columns.
    
    Args:
        json_str: JSON string representation
        
    Returns:
        Dictionary
    """
    if not json_str or json_str.strip() == "":
        return {}
    return json.loads(json_str)


def serialize_datetime(dt: datetime) -> str:
    """
    Serialize a datetime to ISO format string.
    
    Args:
        dt: Datetime object to serialize
        
    Returns:
        ISO format string
    """
    return dt.isoformat()


def deserialize_datetime(iso_str: str) -> datetime:
    """
    Deserialize an ISO format string to a datetime.
    
    Args:
        iso_str: ISO format string
        
    Returns:
        Datetime object
    """
    return datetime.fromisoformat(iso_str)


def serialize_embedding(embedding: List[float]) -> bytes:
    """
    Serialize an embedding vector to bytes for storage.
    
    Uses a simple binary format: 4-byte float count followed by floats.
    
    Args:
        embedding: List of float values representing the embedding
        
    Returns:
        Serialized bytes
    """
    import struct
    
    count = len(embedding)
    fmt = f"<I{count}f"  # Little-endian: uint32 count, then count floats
    return struct.pack(fmt, count, *embedding)


def deserialize_embedding(data: bytes) -> List[float]:
    """
    Deserialize bytes to an embedding vector.
    
    Args:
        data: Serialized bytes
        
    Returns:
        List of float values representing the embedding
    """
    import struct
    
    if not data:
        return []
    
    # Read count (first 4 bytes)
    count = struct.unpack("<I", data[:4])[0]
    
    # Read floats
    fmt = f"<{count}f"
    return list(struct.unpack(fmt, data[4:4 + count * 4]))

