"""
Utility functions for AI services: retry, rate limiting, token counting, error handling.
"""

import time
import logging
import threading
from typing import Optional, Callable, Any, TypeVar
from dataclasses import dataclass
from enum import Enum

from src.config import (
    MAX_RETRIES,
    REQUEST_TIMEOUT,
    DEFAULT_CONTEXT_BUDGET,
    USE_TIKTOKEN,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class AIError(Exception):
    """Base exception for AI operations."""
    def __init__(self, message: str, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


class AIClientError(AIError):
    """Client error (4xx) - typically not retryable."""
    def __init__(self, message: str):
        super().__init__(message, retryable=False)


class AIServerError(AIError):
    """Server error (5xx) - typically retryable."""
    def __init__(self, message: str):
        super().__init__(message, retryable=True)


class AITimeoutError(AIError):
    """Timeout error - retryable."""
    def __init__(self, message: str):
        super().__init__(message, retryable=True)


class RateLimiter:
    """Simple token bucket rate limiter."""
    
    def __init__(self, qps: float = 10.0):
        """
        Initialize rate limiter.
        
        Args:
            qps: Queries per second
        """
        self.qps = qps
        self.tokens = qps
        self.last_update = time.time()
        self.lock = threading.Lock()
    
    def acquire(self, timeout: float = 10.0) -> bool:
        """
        Acquire a token, waiting if necessary.
        
        Args:
            timeout: Maximum wait time in seconds
            
        Returns:
            True if token acquired, False if timeout
        """
        start_time = time.time()
        
        with self.lock:
            while self.tokens < 1.0:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False
                
                # Refill tokens based on elapsed time
                now = time.time()
                elapsed_since_last = now - self.last_update
                self.tokens = min(self.qps, self.tokens + elapsed_since_last * self.qps)
                self.last_update = now
                
                if self.tokens < 1.0:
                    wait_time = (1.0 - self.tokens) / self.qps
                    time.sleep(min(wait_time, timeout - elapsed))
                    self.tokens = 0.0
            
            self.tokens -= 1.0
            return True


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """
    Count tokens in text using tiktoken or fallback heuristic.
    
    Args:
        text: Text to count
        model: Model name for encoding
        
    Returns:
        Approximate token count
    """
    if USE_TIKTOKEN:
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except Exception:
            pass
    
    # Fallback: ~4 characters per token
    return len(text) // 4


def truncate_context(text: str, max_tokens: int, model: str = "gpt-4o") -> str:
    """
    Truncate text to fit within token budget.
    
    Args:
        text: Text to truncate
        max_tokens: Maximum tokens
        model: Model name for encoding
        
    Returns:
        Truncated text
    """
    tokens = count_tokens(text, model)
    if tokens <= max_tokens:
        return text
    
    # Truncate from end (simple strategy)
    # In production, could use more sophisticated strategies
    ratio = max_tokens / tokens
    truncated_length = int(len(text) * ratio * 0.9)  # 90% safety margin
    return text[:truncated_length] + "... [truncated]"


def retry_with_backoff(
    func: Callable[[], T],
    max_retries: int = MAX_RETRIES,
    base_delay: float = 0.25,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
) -> T:
    """
    Retry function with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Exponential base for backoff
        jitter: Whether to add jitter
        
    Returns:
        Function result
        
    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except AIError as e:
            last_exception = e
            
            if not e.retryable:
                raise
            
            if attempt < max_retries:
                # Calculate delay
                delay = min(base_delay * (exponential_base ** attempt), max_delay)
                
                if jitter:
                    import random
                    delay = delay * (0.5 + random.random() * 0.5)
                
                logger.warning(f"Retry attempt {attempt + 1}/{max_retries} after {delay:.2f}s: {e}")
                time.sleep(delay)
            else:
                logger.error(f"All {max_retries} retries exhausted")
                raise
        except Exception as e:
            # Non-AIError exceptions are not retried
            raise
    
    if last_exception:
        raise last_exception
    
    raise RuntimeError("Unexpected retry loop exit")


def should_log_payloads() -> bool:
    """Check if payloads should be logged (for debugging)."""
    import os
    return os.getenv("AI_TUTOR_LOG_PAYLOADS", "0") not in ("0", "false", "False")


def log_request(
    route: str,
    model: str,
    tokens_in: Optional[int] = None,
    tokens_out: Optional[int] = None,
    latency_ms: Optional[float] = None,
    prompt: Optional[str] = None,
    response: Optional[str] = None,
) -> None:
    """
    Log AI request metadata.
    
    Args:
        route: Task route
        model: Model used
        tokens_in: Input tokens
        tokens_out: Output tokens
        latency_ms: Latency in milliseconds
        prompt: Prompt text (logged only if AI_TUTOR_LOG_PAYLOADS=1)
        response: Response text (logged only if AI_TUTOR_LOG_PAYLOADS=1)
    """
    log_data = {
        "route": route,
        "model": model,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "latency_ms": latency_ms,
    }
    
    if should_log_payloads():
        log_data["prompt"] = prompt
        log_data["response"] = response
    
    logger.info(f"AI request: {log_data}")

