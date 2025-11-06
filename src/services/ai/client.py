"""
AI client for OpenAI API integration.

Provides high-level interface for AI tasks with retry, rate limiting,
token management, and error handling.
"""

import time
import logging
from typing import Optional, Dict, Any, List, Iterator
from dataclasses import dataclass

from openai import OpenAI
from openai.types.chat import ChatCompletion

from src.config import (
    OPENAI_API_KEY,
    OPENAI_MODEL_DEFAULT,
    OPENAI_MODEL_NANO,
    REQUEST_TIMEOUT,
)
from src.services.ai.router import AITask, ModelRouter, get_router, ModelRoute
from src.services.ai.prompts import (
    get_system_prompt,
    build_summarize_prompt,
    build_classify_prompt,
    build_skill_update_prompt,
    build_chat_prompt,
    parse_json_response,
    SummaryOutput,
    ClassificationOutput,
    SkillUpdateOutput,
)
from src.services.ai.utils import (
    AIError,
    AIClientError,
    AIServerError,
    AITimeoutError,
    retry_with_backoff,
    count_tokens,
    truncate_context,
    log_request,
    RateLimiter,
)

logger = logging.getLogger(__name__)


class AIClient:
    """
    AI client for OpenAI API with retry, rate limiting, and error handling.
    
    Provides high-level interface for all AI tasks with automatic
    routing, retry logic, and structured output parsing.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        router: Optional[ModelRouter] = None,
        rate_limiter: Optional[RateLimiter] = None,
    ):
        """
        Initialize AI client.
        
        Args:
            api_key: OpenAI API key (defaults to config)
            router: Model router (defaults to global router)
            rate_limiter: Rate limiter (defaults to new instance)
        """
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            logger.warning("No OpenAI API key provided - API calls will fail")
        
        self.client = OpenAI(api_key=self.api_key, timeout=REQUEST_TIMEOUT) if self.api_key else None
        self.router = router or get_router()
        self.rate_limiter = rate_limiter or RateLimiter(qps=10.0)
    
    def _call_api(
        self,
        route: ModelRoute,
        system_prompt: str,
        user_prompt: str,
        stream: bool = False,
    ) -> ChatCompletion | Iterator[ChatCompletion]:
        """
        Make OpenAI API call with retry and rate limiting.
        
        Args:
            route: Model route configuration
            system_prompt: System prompt
            user_prompt: User prompt
            stream: Whether to stream response
            
        Returns:
            ChatCompletion or iterator for streaming
            
        Raises:
            AIError: For API errors
        """
        if not self.client:
            raise AIError("OpenAI API key not configured", retryable=False)
        
        # Rate limiting
        if not self.rate_limiter.acquire(timeout=10.0):
            raise AITimeoutError("Rate limiter timeout")
        
        # Token counting and truncation
        prompt_tokens = count_tokens(system_prompt + user_prompt, route.model_name)
        if prompt_tokens > route.token_budget:
            user_prompt = truncate_context(user_prompt, route.token_budget - count_tokens(system_prompt, route.model_name), route.model_name)
            logger.warning(f"Truncated prompt to fit token budget: {route.token_budget}")
        
        # Prepare request
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        request_kwargs: Dict[str, Any] = {
            "model": route.model_name,
            "messages": messages,
            "temperature": 0.7,
        }
        
        # Add JSON mode if supported
        if route.supports_json_mode:
            request_kwargs["response_format"] = {"type": "json_object"}
        
        # Add streaming if requested
        if stream and route.supports_streaming:
            request_kwargs["stream"] = True
        
        # Make API call with retry
        start_time = time.time()
        
        def _make_call():
            try:
                response = self.client.chat.completions.create(**request_kwargs)
                return response
            except Exception as e:
                error_str = str(e).lower()
                
                # Categorize errors
                if "timeout" in error_str or "timed out" in error_str:
                    raise AITimeoutError(f"Request timeout: {e}") from e
                elif "401" in error_str or "unauthorized" in error_str:
                    raise AIClientError(f"API authentication error: {e}") from e
                elif "429" in error_str or "rate limit" in error_str:
                    raise AIServerError(f"Rate limit error: {e}") from e
                elif "500" in error_str or "502" in error_str or "503" in error_str:
                    raise AIServerError(f"Server error: {e}") from e
                elif "400" in error_str or "bad request" in error_str:
                    raise AIClientError(f"Client error: {e}") from e
                else:
                    raise AIServerError(f"API error: {e}") from e
        
        response = retry_with_backoff(_make_call)
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Log request
        response_text = ""
        if not stream and hasattr(response, 'choices'):
            response_text = response.choices[0].message.content or ""
        
        tokens_in = prompt_tokens
        tokens_out = response.usage.completion_tokens if hasattr(response, 'usage') and response.usage else None
        
        log_request(
            route=route.model_name,
            model=route.model_name,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
            prompt=user_prompt if len(user_prompt) < 1000 else user_prompt[:1000] + "...",
            response=response_text[:1000] if response_text else None,
        )
        
        return response
    
    def summarize_event(
        self,
        event_content: str,
        context: Optional[str] = None,
        override_model: Optional[str] = None,
    ) -> SummaryOutput:
        """
        Summarize an event.
        
        Args:
            event_content: Event content to summarize
            context: Optional context from previous events
            override_model: Optional model override
            
        Returns:
            SummaryOutput with parsed results
        """
        route = self.router.get_route(AITask.SUMMARIZE_EVENT, override_model)
        system_prompt = get_system_prompt(AITask.SUMMARIZE_EVENT)
        user_prompt = build_summarize_prompt(event_content, context)
        
        response = self._call_api(route, system_prompt, user_prompt)
        content = response.choices[0].message.content
        
        if not content:
            raise AIError("Empty response from API", retryable=True)
        
        return parse_json_response(content, SummaryOutput)
    
    def classify_topics(
        self,
        text: str,
        override_model: Optional[str] = None,
    ) -> ClassificationOutput:
        """
        Classify topics and skills from text.
        
        Args:
            text: Text to classify
            override_model: Optional model override
            
        Returns:
            ClassificationOutput with parsed results
        """
        route = self.router.get_route(AITask.CLASSIFY_TOPICS, override_model)
        system_prompt = get_system_prompt(AITask.CLASSIFY_TOPICS)
        user_prompt = build_classify_prompt(text)
        
        response = self._call_api(route, system_prompt, user_prompt)
        content = response.choices[0].message.content
        
        if not content:
            raise AIError("Empty response from API", retryable=True)
        
        return parse_json_response(content, ClassificationOutput)
    
    def update_skill_state(
        self,
        skill_id: str,
        current_p_mastery: float,
        evidence: str,
        override_model: Optional[str] = None,
    ) -> SkillUpdateOutput:
        """
        Update skill state based on evidence.
        
        Args:
            skill_id: Skill identifier
            current_p_mastery: Current mastery probability
            evidence: Evidence text
            override_model: Optional model override
            
        Returns:
            SkillUpdateOutput with parsed results
        """
        route = self.router.get_route(AITask.UPDATE_SKILL, override_model)
        system_prompt = get_system_prompt(AITask.UPDATE_SKILL)
        user_prompt = build_skill_update_prompt(skill_id, current_p_mastery, evidence)
        
        response = self._call_api(route, system_prompt, user_prompt)
        content = response.choices[0].message.content
        
        if not content:
            raise AIError("Empty response from API", retryable=True)
        
        return parse_json_response(content, SkillUpdateOutput)
    
    def chat_reply(
        self,
        user_message: str,
        context: Optional[str] = None,
        override_model: Optional[str] = None,
        stream: bool = False,
    ) -> str | Iterator[str]:
        """
        Generate chat reply.
        
        Args:
            user_message: User's message
            context: Optional context from past sessions
            override_model: Optional model override
            stream: Whether to stream response
            
        Returns:
            Response text or iterator for streaming
        """
        route = self.router.get_route(AITask.CHAT_REPLY, override_model)
        system_prompt = get_system_prompt(AITask.CHAT_REPLY)
        user_prompt = build_chat_prompt(user_message, context)
        
        response = self._call_api(route, system_prompt, user_prompt, stream=stream)
        
        if stream:
            def _stream_generator():
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            
            return _stream_generator()
        else:
            content = response.choices[0].message.content
            if not content:
                raise AIError("Empty response from API", retryable=True)
            return content


# Global client instance
_client: Optional[AIClient] = None


def get_client() -> AIClient:
    """Get or create global AI client instance."""
    global _client
    if _client is None:
        _client = AIClient()
    return _client

