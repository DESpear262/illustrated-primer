"""
Context filters for AI Tutor Proof of Concept.

Provides hybrid scoring, recency decay, and filtering utilities
for retrieved chunks and events.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import math

from src.config import (
    CONTEXT_RECENCY_TAU_DAYS,
    CONTEXT_HYBRID_WEIGHT_FAISS,
    CONTEXT_HYBRID_WEIGHT_RECENCY,
    CONTEXT_HYBRID_WEIGHT_FTS,
    CONTEXT_MIN_SCORE_THRESHOLD,
)
from src.models.base import Event, ChunkRecord


def recency_decay(timestamp: datetime, tau_days: float = CONTEXT_RECENCY_TAU_DAYS) -> float:
    """
    Compute recency decay weight using exponential decay.
    
    Args:
        timestamp: Event timestamp
        tau_days: Half-life in days (default from config)
        
    Returns:
        Decay weight between 0.0 and 1.0 (newer = higher)
    """
    now = datetime.utcnow()
    delta = now - timestamp
    days = delta.total_seconds() / (24 * 3600)
    
    # Exponential decay: w = exp(-days / tau)
    weight = math.exp(-days / tau_days)
    return max(0.0, min(1.0, weight))


def normalize_scores(scores: List[float]) -> List[float]:
    """
    Normalize scores to [0, 1] range using min-max normalization.
    
    Args:
        scores: List of raw scores
        
    Returns:
        Normalized scores
    """
    if not scores:
        return []
    
    min_score = min(scores)
    max_score = max(scores)
    
    if max_score == min_score:
        return [1.0] * len(scores)
    
    return [(s - min_score) / (max_score - min_score) for s in scores]


def compute_hybrid_score(
    faiss_score: float,
    recency_score: float,
    fts_score: float = 0.0,
    weight_faiss: float = CONTEXT_HYBRID_WEIGHT_FAISS,
    weight_recency: float = CONTEXT_HYBRID_WEIGHT_RECENCY,
    weight_fts: float = CONTEXT_HYBRID_WEIGHT_FTS,
) -> float:
    """
    Compute hybrid retrieval score from multiple sources.
    
    Args:
        faiss_score: Semantic similarity score (0-1)
        recency_score: Recency decay score (0-1)
        fts_score: Full-text search score (0-1)
        weight_faiss: Weight for FAISS score
        weight_recency: Weight for recency score
        weight_fts: Weight for FTS score
        
    Returns:
        Combined hybrid score (0-1)
    """
    # Normalize weights to sum to 1.0
    total_weight = weight_faiss + weight_recency + weight_fts
    if total_weight == 0:
        return 0.0
    
    weight_faiss /= total_weight
    weight_recency /= total_weight
    weight_fts /= total_weight
    
    hybrid_score = (
        weight_faiss * faiss_score +
        weight_recency * recency_score +
        weight_fts * fts_score
    )
    
    return max(0.0, min(1.0, hybrid_score))


def filter_by_score_threshold(
    items: List[Tuple[Any, float]],
    threshold: float = CONTEXT_MIN_SCORE_THRESHOLD,
) -> List[Tuple[Any, float]]:
    """
    Filter items by score threshold.
    
    Args:
        items: List of (item, score) tuples
        threshold: Minimum score threshold
        
    Returns:
        Filtered items with scores >= threshold
    """
    return [(item, score) for item, score in items if score >= threshold]


def filter_by_topic_overlap(
    chunks: List[ChunkRecord],
    session_topics: List[str],
    min_overlap_ratio: float = 0.0,
) -> List[ChunkRecord]:
    """
    Filter chunks by topic overlap with session topics.
    
    Args:
        chunks: List of chunks to filter
        session_topics: Topics from current session
        min_overlap_ratio: Minimum overlap ratio (0.0 = allow all)
        
    Returns:
        Filtered chunks
    """
    if not session_topics:
        return chunks
    
    filtered = []
    for chunk in chunks:
        chunk_topics = set(chunk.topics)
        session_topics_set = set(session_topics)
        
        if not chunk_topics:
            # No topics in chunk - allow if min_overlap_ratio is 0
            if min_overlap_ratio == 0.0:
                filtered.append(chunk)
            continue
        
        overlap = len(chunk_topics & session_topics_set)
        overlap_ratio = overlap / len(chunk_topics)
        
        if overlap_ratio >= min_overlap_ratio:
            filtered.append(chunk)
    
    return filtered


def apply_max_per_event(
    items: List[Tuple[Any, float]],
    get_event_id: callable,
    max_per_event: int = 3,
) -> List[Tuple[Any, float]]:
    """
    Limit number of items per event.
    
    Args:
        items: List of (item, score) tuples, sorted by score descending
        get_event_id: Function to extract event_id from item
        max_per_event: Maximum items per event
        
    Returns:
        Filtered items with max_per_event per event
    """
    event_counts: Dict[str, int] = {}
    filtered = []
    
    for item, score in items:
        event_id = get_event_id(item)
        count = event_counts.get(event_id, 0)
        
        if count < max_per_event:
            filtered.append((item, score))
            event_counts[event_id] = count + 1
    
    return filtered


def apply_max_per_topic(
    items: List[Tuple[Any, float]],
    get_topics: callable,
    max_per_topic: int = 5,
) -> List[Tuple[Any, float]]:
    """
    Limit number of items per topic.
    
    Args:
        items: List of (item, score) tuples, sorted by score descending
        get_topics: Function to extract topics from item
        max_per_topic: Maximum items per topic
        
    Returns:
        Filtered items with max_per_topic per topic
    """
    topic_counts: Dict[str, int] = {}
    filtered = []
    
    for item, score in items:
        topics = get_topics(item)
        can_add = True
        
        for topic in topics:
            count = topic_counts.get(topic, 0)
            if count >= max_per_topic:
                can_add = False
                break
        
        if can_add:
            filtered.append((item, score))
            for topic in topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
    
    return filtered

