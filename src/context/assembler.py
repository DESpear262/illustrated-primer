"""
Context assembler for AI Tutor Proof of Concept.

Builds task-specific prompts from retrieved and summarized memory
using dynamic token allocation, hybrid retrieval, and MMR diversity.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json

import numpy as np

from src.config import (
    DB_PATH,
    FAISS_INDEX_PATH,
    CONTEXT_MAX_HISTORY_SHARE,
    CONTEXT_MIN_MEMORY_TOKENS,
    CONTEXT_TOP_K,
    CONTEXT_MAX_CHUNKS_PER_EVENT,
    CONTEXT_MMR_LAMBDA,
    CONTEXT_RECENCY_TAU_DAYS,
    CONTEXT_HYBRID_WEIGHT_FAISS,
    CONTEXT_HYBRID_WEIGHT_RECENCY,
    CONTEXT_HYBRID_WEIGHT_FTS,
    CONTEXT_MIN_SCORE_THRESHOLD,
)
from src.models.base import Event, ChunkRecord
from src.storage.db import Database
from src.retrieval.faiss_index import load_index, search_vectors
from src.retrieval.pipeline import default_stub_embed
from src.services.ai.utils import count_tokens, truncate_context
from src.services.ai.router import ModelRoute
from src.context.filters import (
    recency_decay,
    normalize_scores,
    compute_hybrid_score,
    filter_by_score_threshold,
    filter_by_topic_overlap,
    apply_max_per_event,
    apply_max_per_topic,
)


@dataclass
class RetrievalDecision:
    """Log of retrieval decisions for auditability."""
    selected_chunk_ids: List[str]
    scores: List[float]
    weights: Dict[str, float]
    truncation_counts: Dict[str, int]
    final_token_allocation: Dict[str, int]
    timestamp: datetime


class ContextAssembler:
    """
    Assembles context from retrieved memory and conversation history.
    
    Uses dynamic token allocation, hybrid retrieval, and MMR diversity.
    """
    
    def __init__(
        self,
        db_path: Optional[Any] = None,
        faiss_index_path: Optional[Any] = None,
    ):
        """
        Initialize context assembler.
        
        Args:
            db_path: Path to database (defaults to config)
            faiss_index_path: Path to FAISS index (defaults to config)
        """
        self.db_path = db_path or DB_PATH
        self.faiss_index_path = faiss_index_path or FAISS_INDEX_PATH
    
    def _get_faiss_index(self):
        """Get or load FAISS index."""
        return load_index(self.faiss_index_path)
    
    def allocate_tokens(
        self,
        total_budget: int,
        system_tokens: int,
        history_tokens: int,
        max_history_share: float = CONTEXT_MAX_HISTORY_SHARE,
        min_memory_tokens: int = CONTEXT_MIN_MEMORY_TOKENS,
    ) -> Tuple[int, int]:
        """
        Dynamically allocate tokens between history and memory.
        
        For new chats: allocate all non-system to memory.
        As chat grows: history expands up to max_history_share (default 60%).
        
        Args:
            total_budget: Total token budget (route.token_budget)
            system_tokens: System prompt tokens
            history_tokens: Actual history tokens
            max_history_share: Maximum fraction for history (0-1)
            min_memory_tokens: Minimum tokens reserved for memory
            
        Returns:
            (history_budget, memory_budget) tuple
        """
        available = total_budget - system_tokens
        
        if available <= 0:
            return (0, 0)
        
        # For new chat (no history), allocate all to memory
        if history_tokens == 0:
            memory_budget = available
            history_budget = 0
        else:
            # Compute dynamic history share (grows with history, capped at max_history_share)
            # Smooth growth: h = min(max_share, history / (history + memory_target))
            # We estimate memory_target as a fraction of available
            memory_target_estimate = max(min_memory_tokens, available * 0.5)
            history_share = min(
                max_history_share,
                history_tokens / (history_tokens + memory_target_estimate)
            )
            
            # Allocate based on share
            history_budget = min(int(history_share * available), history_tokens)
            memory_budget = available - history_budget
            
            # Ensure minimum memory budget
            if memory_budget < min_memory_tokens:
                memory_budget = min_memory_tokens
                history_budget = available - memory_budget
        
        return (history_budget, memory_budget)
    
    def retrieve_chunks(
        self,
        query_text: str,
        session_topics: Optional[List[str]] = None,
        top_k: int = CONTEXT_TOP_K,
        query_embedding: Optional[np.ndarray] = None,
    ) -> List[Tuple[ChunkRecord, float]]:
        """
        Retrieve relevant chunks using hybrid retrieval (FAISS + recency + FTS).
        
        Args:
            query_text: Query text for semantic search
            session_topics: Topics from current session (for filtering)
            top_k: Maximum number of chunks to retrieve
            query_embedding: Optional pre-computed query embedding
            
        Returns:
            List of (chunk, score) tuples sorted by score descending
        """
        # Generate query embedding if not provided
        if query_embedding is None:
            from src.config import OPENAI_API_KEY
            if OPENAI_API_KEY:
                from openai import OpenAI
                client = OpenAI(api_key=OPENAI_API_KEY)
                response = client.embeddings.create(
                    input=[query_text],
                    model="text-embedding-3-small"
                )
                query_embedding = np.array(response.data[0].embedding, dtype=np.float32)
            else:
                # Use stub for testing
                query_embedding = default_stub_embed([query_text])[0]
        
        # FAISS search
        faiss_index = self._get_faiss_index()
        if faiss_index.ntotal == 0:
            return []
        
        # Reshape query for search_vectors (expects 2D array)
        query_reshaped = query_embedding.reshape(1, -1)
        faiss_ids, faiss_distances = search_vectors(faiss_index, query_reshaped, top_k=top_k * 2)
        
        # Extract from batch results (first query)
        faiss_ids = faiss_ids[0]
        faiss_distances = faiss_distances[0]
        
        # Normalize FAISS scores (cosine similarity already normalized)
        faiss_scores = normalize_scores(faiss_distances.tolist())
        
        # Load chunks from database
        with Database(self.db_path) as db:
            if not db.conn:
                raise ValueError("Database connection not established")
            
            cursor = db.conn.cursor()
            chunks_with_scores = []
            
            for i, (chunk_id, faiss_score) in enumerate(zip(faiss_ids, faiss_scores)):
                # Get chunk by database ID
                cursor.execute("SELECT * FROM event_chunks WHERE id = ?", (int(chunk_id),))
                chunk_row = cursor.fetchone()
                if not chunk_row:
                    continue
                
                # Convert row to ChunkRecord
                chunk_dict = dict(chunk_row)
                from src.utils.serialization import deserialize_json_list, deserialize_json_dict, deserialize_datetime
                chunk_dict["topics"] = deserialize_json_list(chunk_dict.get("topics", "[]"))
                chunk_dict["skills"] = deserialize_json_list(chunk_dict.get("skills", "[]"))
                if chunk_dict.get("created_at"):
                    chunk_dict["created_at"] = deserialize_datetime(chunk_dict["created_at"])
                # Metadata column doesn't exist in schema - use empty dict
                chunk_dict["metadata"] = {}
                
                # Create ChunkRecord
                chunk = ChunkRecord(
                    id=chunk_dict.get("id"),
                    chunk_id=chunk_dict["chunk_id"],
                    event_id=chunk_dict["event_id"],
                    chunk_index=chunk_dict["chunk_index"],
                    text=chunk_dict["text"],
                    topics=chunk_dict["topics"],
                    skills=chunk_dict["skills"],
                    embedding=chunk_dict.get("embedding"),
                    embedding_id=chunk_dict.get("embedding_id"),
                    created_at=chunk_dict.get("created_at"),
                    metadata=chunk_dict["metadata"],
                )
                
                # Get parent event for recency
                event = db.get_event_by_id(chunk.event_id)
                if not event:
                    continue
                
                # Compute recency score
                recency_score = recency_decay(event.created_at, CONTEXT_RECENCY_TAU_DAYS)
                
                # Compute FTS score (simplified - could use actual FTS ranking)
                fts_score = 0.0  # TODO: integrate with FTS5 ranking if needed
                
                # Compute hybrid score
                hybrid_score = compute_hybrid_score(
                    faiss_score,
                    recency_score,
                    fts_score,
                    CONTEXT_HYBRID_WEIGHT_FAISS,
                    CONTEXT_HYBRID_WEIGHT_RECENCY,
                    CONTEXT_HYBRID_WEIGHT_FTS,
                )
                
                chunks_with_scores.append((chunk, hybrid_score))
        
        # Sort by score descending
        chunks_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Apply topic filtering if session topics provided
        if session_topics:
            chunks = [c for c, _ in chunks_with_scores]
            filtered_chunks = filter_by_topic_overlap(chunks, session_topics, min_overlap_ratio=0.0)
            # Rebuild with scores
            chunk_dict = {c.chunk_id: s for c, s in chunks_with_scores}
            chunks_with_scores = [(c, chunk_dict.get(c.chunk_id, 0.0)) for c in filtered_chunks]
            chunks_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Apply max per event
        chunks_with_scores = apply_max_per_event(
            chunks_with_scores,
            get_event_id=lambda c: c[0].event_id,
            max_per_event=CONTEXT_MAX_CHUNKS_PER_EVENT,
        )
        
        # Apply max per topic
        chunks_with_scores = apply_max_per_topic(
            chunks_with_scores,
            get_topics=lambda c: c[0].topics,
            max_per_topic=5,  # Configurable if needed
        )
        
        # Filter by score threshold
        chunks_with_scores = filter_by_score_threshold(
            chunks_with_scores,
            threshold=CONTEXT_MIN_SCORE_THRESHOLD,
        )
        
        # Take top_k
        return chunks_with_scores[:top_k]
    
    def apply_mmr(
        self,
        chunks_with_scores: List[Tuple[ChunkRecord, float]],
        query_embedding: np.ndarray,
        lambda_param: float = CONTEXT_MMR_LAMBDA,
        max_chunks: int = CONTEXT_TOP_K,
    ) -> List[Tuple[ChunkRecord, float]]:
        """
        Apply Maximal Marginal Relevance (MMR) for diversity.
        
        Args:
            chunks_with_scores: List of (chunk, score) tuples
            query_embedding: Query embedding vector
            lambda_param: MMR lambda (0.0 = pure relevance, 1.0 = pure diversity)
            max_chunks: Maximum chunks to return
            
        Returns:
            Re-ranked chunks with MMR scores
        """
        if not chunks_with_scores:
            return []
        
        # Deserialize embeddings for similarity computation
        selected = []
        remaining = list(chunks_with_scores)
        
        # Initialize with top-scoring chunk
        if remaining:
            selected.append(remaining.pop(0))
        
        # Greedily select chunks maximizing MMR
        while len(selected) < max_chunks and remaining:
            best_mmr = -1.0
            best_idx = -1
            
            for i, (chunk, relevance_score) in enumerate(remaining):
                # Compute diversity (min similarity to selected chunks)
                chunk_embedding = None
                try:
                    from src.utils.serialization import deserialize_embedding
                    chunk_embedding = deserialize_embedding(chunk.embedding)
                except Exception:
                    continue
                
                if chunk_embedding is None:
                    continue
                
                # Normalize chunk embedding
                chunk_embedding = chunk_embedding / np.linalg.norm(chunk_embedding)
                
                max_similarity = 0.0
                for selected_chunk, _ in selected:
                    try:
                        sel_embedding = deserialize_embedding(selected_chunk.embedding)
                        sel_embedding = sel_embedding / np.linalg.norm(sel_embedding)
                        similarity = np.dot(chunk_embedding, sel_embedding)
                        max_similarity = max(max_similarity, similarity)
                    except Exception:
                        continue
                
                diversity = 1.0 - max_similarity
                
                # MMR score: lambda * relevance + (1 - lambda) * diversity
                mmr_score = lambda_param * relevance_score + (1 - lambda_param) * diversity
                
                if mmr_score > best_mmr:
                    best_mmr = mmr_score
                    best_idx = i
            
            if best_idx >= 0:
                selected.append(remaining.pop(best_idx))
            else:
                break
        
        return selected
    
    def compose_context(
        self,
        query_text: str,
        history_messages: List[Dict[str, str]],
        system_prompt: str,
        route: ModelRoute,
        session_topics: Optional[List[str]] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Compose full context from retrieved memory and history.
        
        Args:
            query_text: Current query text
            history_messages: Conversation history (OpenAI format)
            system_prompt: System prompt
            route: Model route configuration
            session_topics: Topics from current session
            
        Returns:
            (composed_context, retrieval_decision) tuple
        """
        # Count tokens
        system_tokens = count_tokens(system_prompt, route.model_name)
        history_tokens = sum(count_tokens(m["content"], route.model_name) for m in history_messages)
        
        # Allocate tokens dynamically
        history_budget, memory_budget = self.allocate_tokens(
            route.token_budget,
            system_tokens,
            history_tokens,
        )
        
        # Generate query embedding once
        from src.config import OPENAI_API_KEY
        if OPENAI_API_KEY:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.embeddings.create(
                input=[query_text],
                model="text-embedding-3-small"
            )
            query_embedding = np.array(response.data[0].embedding, dtype=np.float32)
        else:
            query_embedding = default_stub_embed([query_text])[0]
        
        # Retrieve chunks (pass query_embedding to avoid regenerating)
        chunks_with_scores = self.retrieve_chunks(
            query_text,
            session_topics=session_topics,
            top_k=CONTEXT_TOP_K,
            query_embedding=query_embedding,
        )
        
        # Apply MMR for diversity
        chunks_with_scores = self.apply_mmr(
            chunks_with_scores,
            query_embedding,
            lambda_param=CONTEXT_MMR_LAMBDA,
        )
        
        # Build memory context from chunks (within budget)
        memory_texts = []
        memory_tokens_used = 0
        
        for chunk, score in chunks_with_scores:
            chunk_text = chunk.text
            chunk_tokens = count_tokens(chunk_text, route.model_name)
            
            if memory_tokens_used + chunk_tokens > memory_budget:
                # Truncate last chunk if needed
                remaining = memory_budget - memory_tokens_used
                if remaining > 100:  # Only add if meaningful
                    chunk_text = truncate_context(chunk_text, remaining, route.model_name)
                    memory_texts.append(chunk_text)
                break
            
            memory_texts.append(chunk_text)
            memory_tokens_used += chunk_tokens
        
        # Truncate history if needed
        history_texts = []
        history_tokens_used = 0
        
        for msg in reversed(history_messages):  # Process oldest first
            msg_text = msg["content"]
            msg_tokens = count_tokens(msg_text, route.model_name)
            
            if history_tokens_used + msg_tokens > history_budget:
                remaining = history_budget - history_tokens_used
                if remaining > 100:
                    msg_text = truncate_context(msg_text, remaining, route.model_name)
                    history_texts.insert(0, msg_text)
                break
            
            history_texts.insert(0, msg_text)
            history_tokens_used += msg_tokens
        
        # Compose final context
        memory_context = "\n\n".join(memory_texts) if memory_texts else ""
        history_context = "\n\n".join(f"{m['role']}: {m['content']}" for m in history_messages[-len(history_texts):]) if history_texts else ""
        
        # Build retrieval decision log
        decision = RetrievalDecision(
            selected_chunk_ids=[c.chunk_id for c, _ in chunks_with_scores[:len(memory_texts)]],
            scores=[s for _, s in chunks_with_scores[:len(memory_texts)]],
            weights={
                "faiss": CONTEXT_HYBRID_WEIGHT_FAISS,
                "recency": CONTEXT_HYBRID_WEIGHT_RECENCY,
                "fts": CONTEXT_HYBRID_WEIGHT_FTS,
            },
            truncation_counts={
                "memory": len(chunks_with_scores) - len(memory_texts),
                "history": len(history_messages) - len(history_texts),
            },
            final_token_allocation={
                "system": system_tokens,
                "history": history_tokens_used,
                "memory": memory_tokens_used,
                "total": system_tokens + history_tokens_used + memory_tokens_used,
            },
            timestamp=datetime.utcnow(),
        )
        
        # Combine context (memory first, then history)
        composed = f"{memory_context}\n\n{history_context}" if memory_context and history_context else (memory_context or history_context)
        
        return composed, decision

