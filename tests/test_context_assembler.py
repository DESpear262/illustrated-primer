"""
Unit and integration tests for context assembler.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4

import numpy as np

from src.context.assembler import ContextAssembler, RetrievalDecision
from src.services.ai.router import ModelRoute, AITask, get_router
from src.storage.db import Database
from src.models.base import Event, ChunkRecord
from src.utils.serialization import serialize_json_list, serialize_embedding, serialize_datetime


def _make_db(tmp_path) -> Path:
    db_path = tmp_path / "test.db"
    with Database(db_path) as db:
        db.initialize()
    return db_path


def _make_faiss_index(tmp_path) -> Path:
    faiss_path = tmp_path / "faiss_index.bin"
    from src.retrieval.faiss_index import create_flat_ip_index, save_index
    index = create_flat_ip_index(dimension=1536)
    save_index(index, faiss_path)
    return faiss_path


class TestTokenAllocation:
    """Tests for dynamic token allocation."""
    
    def test_allocate_tokens_new_chat(self):
        """Test token allocation for new chat (no history)."""
        assembler = ContextAssembler()
        
        history_budget, memory_budget = assembler.allocate_tokens(
            total_budget=10000,
            system_tokens=1000,
            history_tokens=0,
        )
        
        assert history_budget == 0
        assert memory_budget == 9000  # All available to memory
    
    def test_allocate_tokens_with_history(self):
        """Test token allocation with history."""
        assembler = ContextAssembler()
        
        history_budget, memory_budget = assembler.allocate_tokens(
            total_budget=10000,
            system_tokens=1000,
            history_tokens=5000,
            max_history_share=0.6,
        )
        
        assert history_budget <= 5400  # 60% of 9000
        assert memory_budget >= 3600  # At least 40% of 9000
        assert history_budget + memory_budget == 9000
    
    def test_allocate_tokens_min_memory(self):
        """Test token allocation respects minimum memory budget."""
        assembler = ContextAssembler()
        
        history_budget, memory_budget = assembler.allocate_tokens(
            total_budget=10000,
            system_tokens=1000,
            history_tokens=10000,  # Very large history
            max_history_share=0.6,
            min_memory_tokens=3000,
        )
        
        assert memory_budget >= 3000
        assert history_budget + memory_budget == 9000


class TestContextComposition:
    """Integration tests for context composition."""
    
    @pytest.mark.skip(reason="Requires FAISS index and embeddings - complex setup")
    def test_compose_context_basic(self):
        """Test basic context composition."""
        # This test would require:
        # 1. FAISS index with chunks
        # 2. Proper embeddings
        # 3. Mock AI client
        # Skipping for now - can be added with proper fixtures
        pass
    
    def test_compose_context_empty_index(self, tmp_path):
        """Test context composition with empty FAISS index."""
        db_path = _make_db(tmp_path)
        faiss_path = _make_faiss_index(tmp_path)
        
        assembler = ContextAssembler(db_path=db_path, faiss_index_path=faiss_path)
        router = get_router()
        route = router.get_route(AITask.CHAT_REPLY)
        
        context, decision = assembler.compose_context(
            query_text="test",
            history_messages=[],
            system_prompt="You are a tutor.",
            route=route,
        )
        
        # Should return empty or minimal context
        assert isinstance(context, str)
        assert isinstance(decision, RetrievalDecision)


@pytest.fixture
def sample_events():
    """Create sample events for testing."""
    now = datetime.utcnow()
    return [
        Event(
            event_id=str(uuid4()),
            content="Learning about derivatives",
            event_type="chat",
            actor="student",
            topics=["calculus"],
            created_at=now - timedelta(days=1),
        ),
        Event(
            event_id=str(uuid4()),
            content="Derivatives are rates of change",
            event_type="chat",
            actor="tutor",
            topics=["calculus"],
            created_at=now - timedelta(days=1),
        ),
    ]


def test_retrieval_decision_structure():
    """Test that RetrievalDecision has correct structure."""
    decision = RetrievalDecision(
        selected_chunk_ids=["1", "2"],
        scores=[0.8, 0.7],
        weights={"faiss": 0.6, "recency": 0.3, "fts": 0.1},
        truncation_counts={"memory": 0, "history": 0},
        final_token_allocation={"system": 100, "history": 200, "memory": 300, "total": 600},
        timestamp=datetime.utcnow(),
    )
    
    assert len(decision.selected_chunk_ids) == 2
    assert decision.weights["faiss"] == 0.6
    assert decision.final_token_allocation["total"] == 600

