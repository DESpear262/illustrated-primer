"""
Unit tests for context filters: hybrid scoring, recency decay, filtering.
"""

import pytest
from datetime import datetime, timedelta

from src.context.filters import (
    recency_decay,
    normalize_scores,
    compute_hybrid_score,
    filter_by_score_threshold,
    filter_by_topic_overlap,
    apply_max_per_event,
    apply_max_per_topic,
)
from src.models.base import ChunkRecord


class TestRecencyDecay:
    """Tests for recency decay function."""
    
    def test_recency_decay_recent(self):
        """Test recency decay for recent timestamp."""
        now = datetime.utcnow()
        weight = recency_decay(now, tau_days=7.0)
        assert 0.9 <= weight <= 1.0  # Very recent should have high weight
    
    def test_recency_decay_old(self):
        """Test recency decay for old timestamp."""
        old = datetime.utcnow() - timedelta(days=30)
        weight = recency_decay(old, tau_days=7.0)
        assert 0.0 <= weight < 0.3  # Old should have low weight
    
    def test_recency_decay_half_life(self):
        """Test recency decay at half-life."""
        half_life = datetime.utcnow() - timedelta(days=7.0)
        weight = recency_decay(half_life, tau_days=7.0)
        # At half-life, weight should be approximately exp(-1) ≈ 0.368
        assert 0.3 <= weight <= 0.4


class TestNormalizeScores:
    """Tests for score normalization."""
    
    def test_normalize_scores_basic(self):
        """Test basic score normalization."""
        scores = [0.1, 0.5, 0.9]
        normalized = normalize_scores(scores)
        assert normalized[0] == 0.0
        assert normalized[-1] == 1.0
        assert all(0.0 <= s <= 1.0 for s in normalized)
    
    def test_normalize_scores_empty(self):
        """Test normalization of empty list."""
        assert normalize_scores([]) == []
    
    def test_normalize_scores_single(self):
        """Test normalization of single score."""
        assert normalize_scores([0.5]) == [1.0]
    
    def test_normalize_scores_identical(self):
        """Test normalization of identical scores."""
        normalized = normalize_scores([0.5, 0.5, 0.5])
        assert all(s == 1.0 for s in normalized)


class TestHybridScore:
    """Tests for hybrid score computation."""
    
    def test_hybrid_score_basic(self):
        """Test basic hybrid score."""
        score = compute_hybrid_score(
            faiss_score=0.8,
            recency_score=0.6,
            fts_score=0.4,
        )
        assert 0.0 <= score <= 1.0
    
    def test_hybrid_score_weights(self):
        """Test hybrid score with custom weights."""
        score = compute_hybrid_score(
            faiss_score=1.0,
            recency_score=0.0,
            fts_score=0.0,
            weight_faiss=1.0,
            weight_recency=0.0,
            weight_fts=0.0,
        )
        assert score == 1.0


class TestFilterByScoreThreshold:
    """Tests for score threshold filtering."""
    
    def test_filter_by_threshold(self):
        """Test filtering by score threshold."""
        items = [("a", 0.3), ("b", 0.5), ("c", 0.2)]
        filtered = filter_by_score_threshold(items, threshold=0.25)
        assert len(filtered) == 2
        assert all(score >= 0.25 for _, score in filtered)


class TestFilterByTopicOverlap:
    """Tests for topic overlap filtering."""
    
    def test_filter_by_topic_overlap(self):
        """Test filtering by topic overlap."""
        chunks = [
            ChunkRecord(
                chunk_id="1",
                event_id="e1",
                chunk_index=0,
                text="test",
                topics=["calculus"],
                skills=[],
            ),
            ChunkRecord(
                chunk_id="2",
                event_id="e2",
                chunk_index=0,
                text="test",
                topics=["linear_algebra"],
                skills=[],
            ),
        ]
        
        filtered = filter_by_topic_overlap(chunks, session_topics=["calculus"], min_overlap_ratio=0.0)
        assert len(filtered) == 2  # min_overlap_ratio=0.0 allows all
        
        filtered = filter_by_topic_overlap(chunks, session_topics=["calculus"], min_overlap_ratio=1.0)
        assert len(filtered) == 1
        assert filtered[0].topics == ["calculus"]


class TestMaxPerEvent:
    """Tests for max per event filtering."""
    
    def test_apply_max_per_event(self):
        """Test applying max per event limit."""
        items = [
            ({"event_id": "e1", "id": 1}, 0.9),
            ({"event_id": "e1", "id": 2}, 0.8),
            ({"event_id": "e1", "id": 3}, 0.7),
            ({"event_id": "e2", "id": 4}, 0.6),
        ]
        
        filtered = apply_max_per_event(items, get_event_id=lambda x: x["event_id"], max_per_event=2)
        assert len(filtered) == 3  # 2 from e1, 1 from e2
        assert all(item["id"] in [1, 2, 4] for item, _ in filtered)


class TestMaxPerTopic:
    """Tests for max per topic filtering."""
    
    def test_apply_max_per_topic(self):
        """Test applying max per topic limit."""
        items = [
            ({"topics": ["calculus"], "id": 1}, 0.9),
            ({"topics": ["calculus"], "id": 2}, 0.8),
            ({"topics": ["calculus"], "id": 3}, 0.7),
            ({"topics": ["linear_algebra"], "id": 4}, 0.6),
        ]
        
        filtered = apply_max_per_topic(items, get_topics=lambda x: x["topics"], max_per_topic=2)
        assert len(filtered) == 3  # 2 from calculus, 1 from linear_algebra
        assert all(item["id"] in [1, 2, 4] for item, _ in filtered)

