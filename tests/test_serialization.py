"""
Unit tests for serialization utilities.

Tests JSON serialization/deserialization and binary encoding.
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import json

from src.models.base import Event
from src.utils.serialization import (
    model_to_json,
    model_from_json,
    models_to_json,
    models_from_json,
    save_model_to_file,
    load_model_from_file,
    serialize_json_list,
    deserialize_json_list,
    serialize_json_dict,
    deserialize_json_dict,
    serialize_datetime,
    deserialize_datetime,
    serialize_embedding,
    deserialize_embedding,
)


class TestModelSerialization:
    """Tests for model serialization utilities."""
    
    def test_model_to_json(self):
        """Test converting model to JSON dictionary."""
        event = Event(
            event_id="test-id",
            content="Test content",
            event_type="chat",
            actor="student",
        )
        data = model_to_json(event)
        assert isinstance(data, dict)
        assert data["event_id"] == "test-id"
        assert data["content"] == "Test content"
    
    def test_model_from_json(self):
        """Test creating model from JSON dictionary."""
        data = {
            "event_id": "test-id",
            "content": "Test content",
            "event_type": "chat",
            "actor": "student",
        }
        event = model_from_json(data, Event)
        assert isinstance(event, Event)
        assert event.event_id == "test-id"
        assert event.content == "Test content"
    
    def test_models_to_json(self):
        """Test converting list of models to JSON."""
        events = [
            Event(event_id=f"id-{i}", content=f"Content {i}", event_type="chat", actor="student")
            for i in range(3)
        ]
        data = models_to_json(events)
        assert len(data) == 3
        assert all(isinstance(item, dict) for item in data)
    
    def test_save_and_load_model(self):
        """Test saving and loading model from file."""
        event = Event(
            event_id="test-id",
            content="Test content",
            event_type="chat",
            actor="student",
        )
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            save_model_to_file(event, temp_path)
            loaded_event = load_model_from_file(temp_path, Event)
            assert loaded_event.event_id == event.event_id
            assert loaded_event.content == event.content
        finally:
            temp_path.unlink()


class TestJSONSerialization:
    """Tests for JSON list/dict serialization."""
    
    def test_serialize_json_list(self):
        """Test serializing list to JSON string."""
        items = ["item1", "item2", "item3"]
        json_str = serialize_json_list(items)
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed == items
    
    def test_deserialize_json_list(self):
        """Test deserializing JSON string to list."""
        json_str = '["item1", "item2", "item3"]'
        items = deserialize_json_list(json_str)
        assert items == ["item1", "item2", "item3"]
    
    def test_deserialize_empty_json_list(self):
        """Test deserializing empty JSON list."""
        assert deserialize_json_list("") == []
        assert deserialize_json_list("[]") == []
    
    def test_serialize_json_dict(self):
        """Test serializing dictionary to JSON string."""
        data = {"key1": "value1", "key2": 42}
        json_str = serialize_json_dict(data)
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed == data
    
    def test_deserialize_json_dict(self):
        """Test deserializing JSON string to dictionary."""
        json_str = '{"key1": "value1", "key2": 42}'
        data = deserialize_json_dict(json_str)
        assert data == {"key1": "value1", "key2": 42}
    
    def test_deserialize_empty_json_dict(self):
        """Test deserializing empty JSON dict."""
        assert deserialize_json_dict("") == {}
        assert deserialize_json_dict("{}") == {}


class TestDatetimeSerialization:
    """Tests for datetime serialization."""
    
    def test_serialize_datetime(self):
        """Test serializing datetime to ISO string."""
        dt = datetime(2024, 1, 15, 12, 30, 45)
        iso_str = serialize_datetime(dt)
        assert isinstance(iso_str, str)
        assert "2024-01-15" in iso_str
    
    def test_deserialize_datetime(self):
        """Test deserializing ISO string to datetime."""
        iso_str = "2024-01-15T12:30:45"
        dt = deserialize_datetime(iso_str)
        assert isinstance(dt, datetime)
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15


class TestEmbeddingSerialization:
    """Tests for embedding serialization."""
    
    def test_serialize_embedding(self):
        """Test serializing embedding vector to bytes."""
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        data = serialize_embedding(embedding)
        assert isinstance(data, bytes)
        assert len(data) > 0
    
    def test_deserialize_embedding(self):
        """Test deserializing bytes to embedding vector."""
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        data = serialize_embedding(embedding)
        deserialized = deserialize_embedding(data)
        assert len(deserialized) == len(embedding)
        assert all(abs(a - b) < 1e-6 for a, b in zip(embedding, deserialized))
    
    def test_deserialize_empty_embedding(self):
        """Test deserializing empty embedding."""
        assert deserialize_embedding(b"") == []

