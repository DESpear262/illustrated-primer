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

