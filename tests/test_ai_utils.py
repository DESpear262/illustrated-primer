"""
Unit tests for AI utilities: retry, rate limiting, token counting.
"""

import pytest
import time
import threading

from src.services.ai.utils import (
    retry_with_backoff,
    count_tokens,
    truncate_context,
    RateLimiter,
    AIError,
    AIClientError,
    AIServerError,
    AITimeoutError,
)


class TestRetryLogic:
    """Tests for retry with backoff."""
    
    def test_retry_succeeds_first_try(self):
        """Test retry succeeds on first attempt."""
        def func():
            return "success"
        
        result = retry_with_backoff(func, max_retries=3)
        
        assert result == "success"
    
    def test_retry_succeeds_after_retries(self):
        """Test retry succeeds after some failures."""
        attempts = [0]
        
        def func():
            attempts[0] += 1
            if attempts[0] < 3:
                raise AIServerError("Temporary error")
            return "success"
        
        result = retry_with_backoff(func, max_retries=3, base_delay=0.01)
        
        assert result == "success"
        assert attempts[0] == 3
    
    def test_retry_stops_on_non_retryable_error(self):
        """Test retry stops immediately on non-retryable error."""
        attempts = [0]
        
        def func():
            attempts[0] += 1
            raise AIClientError("Client error")
        
        with pytest.raises(AIClientError):
            retry_with_backoff(func, max_retries=3, base_delay=0.01)
        
        assert attempts[0] == 1
    
    def test_retry_exhausts_retries(self):
        """Test retry exhausts all retries before failing."""
        attempts = [0]
        
        def func():
            attempts[0] += 1
            raise AIServerError("Persistent error")
        
        with pytest.raises(AIServerError):
            retry_with_backoff(func, max_retries=2, base_delay=0.01)
        
        assert attempts[0] == 3  # Initial + 2 retries


class TestTokenCounting:
    """Tests for token counting."""
    
    def test_count_tokens_basic(self):
        """Test basic token counting."""
        text = "This is a test"
        
        count = count_tokens(text)
        
        assert count > 0
        assert isinstance(count, int)
    
    def test_count_tokens_empty(self):
        """Test counting tokens in empty text."""
        count = count_tokens("")
        
        assert count == 0
    
    def test_count_tokens_long_text(self):
        """Test counting tokens in long text."""
        text = "This is a test. " * 100
        
        count = count_tokens(text)
        
        assert count > 0
    
    def test_truncate_context(self):
        """Test truncating context to fit token budget."""
        text = "This is a test. " * 1000
        max_tokens = 10
        
        truncated = truncate_context(text, max_tokens)
        
        assert len(truncated) < len(text)
        assert "[truncated]" in truncated or truncated.endswith("...")


class TestRateLimiter:
    """Tests for rate limiter."""
    
    def test_rate_limiter_acquires_token(self):
        """Test rate limiter acquires token."""
        limiter = RateLimiter(qps=10.0)
        
        result = limiter.acquire()
        
        assert result is True
    
    def test_rate_limiter_limits_rate(self):
        """Test rate limiter enforces rate limit."""
        limiter = RateLimiter(qps=1.0)  # 1 per second
        
        # Acquire first token
        assert limiter.acquire() is True
        
        # Second token should wait
        start = time.time()
        result = limiter.acquire(timeout=2.0)
        elapsed = time.time() - start
        
        assert result is True
        assert elapsed >= 0.9  # Should wait ~1 second
    
    def test_rate_limiter_timeout(self):
        """Test rate limiter times out if unable to acquire."""
        limiter = RateLimiter(qps=0.1)  # Very slow
        
        # Acquire first token
        limiter.acquire()
        
        # Second should timeout
        result = limiter.acquire(timeout=0.1)
        
        assert result is False


class TestAIErrors:
    """Tests for AI error types."""
    
    def test_ai_error_retryable(self):
        """Test AIError with retryable flag."""
        error = AIError("Test", retryable=True)
        
        assert error.retryable is True
    
    def test_client_error_not_retryable(self):
        """Test AIClientError is not retryable."""
        error = AIClientError("Client error")
        
        assert error.retryable is False
    
    def test_server_error_retryable(self):
        """Test AIServerError is retryable."""
        error = AIServerError("Server error")
        
        assert error.retryable is True
    
    def test_timeout_error_retryable(self):
        """Test AITimeoutError is retryable."""
        error = AITimeoutError("Timeout")
        
        assert error.retryable is True

