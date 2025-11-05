"""
Configuration module for AI Tutor Proof of Concept.

Handles environment variables, database paths, and global constants.
All configuration is local-first with environment variable overrides.
"""

import os
from pathlib import Path
from typing import Optional


def get_project_root() -> Path:
    """Get the project root directory."""
    # Assume config.py is in src/, so project root is parent
    return Path(__file__).parent.parent


def get_data_dir() -> Path:
    """
    Get the data directory path.
    
    Defaults to $PROJECT_ROOT/data, but can be overridden via
    AI_TUTOR_DATA_DIR environment variable.
    """
    env_data_dir = os.getenv("AI_TUTOR_DATA_DIR")
    if env_data_dir:
        return Path(env_data_dir)
    return get_project_root() / "data"


def get_database_path() -> Path:
    """
    Get the SQLite database file path.
    
    Database is stored in the data directory as 'ai_tutor.db'.
    """
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "ai_tutor.db"


def get_faiss_index_path() -> Path:
    """
    Get the FAISS index file path.
    
    Index is stored in the data directory as 'faiss_index.bin'.
    """
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "faiss_index.bin"


# OpenAI API configuration
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL_DEFAULT: str = "gpt-4o"
OPENAI_MODEL_NANO: str = "gpt-4o-mini"
OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

# Database configuration
DB_PATH: Path = get_database_path()
FAISS_INDEX_PATH: Path = get_faiss_index_path()

# Embedding configuration
EMBEDDING_DIMENSION: int = int(os.getenv("AI_TUTOR_EMBED_DIM", "1536"))  # default matches text-embedding-3-small
USE_TIKTOKEN: bool = os.getenv("AI_TUTOR_USE_TIKTOKEN", "1") not in ("0", "false", "False")
CHUNK_TOKENS: int = int(os.getenv("AI_TUTOR_CHUNK_TOKENS", "200"))
CHUNK_OVERLAP_TOKENS: int = int(os.getenv("AI_TUTOR_CHUNK_OVERLAP", "50"))
BATCH_EMBED_SIZE: int = int(os.getenv("AI_TUTOR_BATCH_EMBED_SIZE", "64"))

# Context window configuration
MAX_CONTEXT_TOKENS: int = 128000  # gpt-4o context window
DEFAULT_CONTEXT_BUDGET: int = 32000  # Conservative default

# Retry and timeout configuration
MAX_RETRIES: int = 3
REQUEST_TIMEOUT: int = 60  # seconds

# Chat configuration
CHAT_HISTORY_TOKENS: int = int(os.getenv("AI_TUTOR_CHAT_HISTORY_TOKENS", "4000"))
CHAT_MAX_TURNS: int = int(os.getenv("AI_TUTOR_CHAT_MAX_TURNS", "200"))
CHAT_AUTOSUMMARIZE: bool = os.getenv("AI_TUTOR_CHAT_AUTOSUMMARIZE", "1") not in ("0", "false", "False")
CHAT_STREAM: bool = os.getenv("AI_TUTOR_CHAT_STREAM", "1") not in ("0", "false", "False")
CHAT_SPINNER_STYLE: str = os.getenv("AI_TUTOR_CHAT_SPINNER_STYLE", "dots")
CHAT_AUTOSAVE_INTERVAL_S: int = int(os.getenv("AI_TUTOR_CHAT_AUTOSAVE_INTERVAL_S", "30"))

# Context composition configuration
CONTEXT_MAX_HISTORY_SHARE: float = float(os.getenv("AI_TUTOR_CONTEXT_MAX_HISTORY_SHARE", "0.60"))
CONTEXT_MIN_MEMORY_TOKENS: int = int(os.getenv("AI_TUTOR_CONTEXT_MIN_MEMORY_TOKENS", "3000"))
CONTEXT_TOP_K: int = int(os.getenv("AI_TUTOR_CONTEXT_TOP_K", "24"))
CONTEXT_MAX_CHUNKS_PER_EVENT: int = int(os.getenv("AI_TUTOR_CONTEXT_MAX_CHUNKS_PER_EVENT", "3"))
CONTEXT_MMR_LAMBDA: float = float(os.getenv("AI_TUTOR_CONTEXT_MMR_LAMBDA", "0.7"))
CONTEXT_RECENCY_TAU_DAYS: float = float(os.getenv("AI_TUTOR_RECENCY_TAU_DAYS", "7.0"))
CONTEXT_HYBRID_WEIGHT_FAISS: float = float(os.getenv("AI_TUTOR_HYBRID_WEIGHT_FAISS", "0.6"))
CONTEXT_HYBRID_WEIGHT_RECENCY: float = float(os.getenv("AI_TUTOR_HYBRID_WEIGHT_RECENCY", "0.3"))
CONTEXT_HYBRID_WEIGHT_FTS: float = float(os.getenv("AI_TUTOR_HYBRID_WEIGHT_FTS", "0.1"))
CONTEXT_MIN_SCORE_THRESHOLD: float = float(os.getenv("AI_TUTOR_CONTEXT_MIN_SCORE_THRESHOLD", "0.25"))
CONTEXT_RERANK: bool = os.getenv("AI_TUTOR_RERANK", "0") not in ("0", "false", "False")
CONTEXT_REDACT: bool = os.getenv("AI_TUTOR_REDACT", "0") not in ("0", "false", "False")

