"""
Model routing registry for AI Tutor Proof of Concept.

Provides task-based routing to appropriate OpenAI models with
configurable defaults and fallback strategies.
"""

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass

from src.config import (
    OPENAI_MODEL_DEFAULT,
    OPENAI_MODEL_NANO,
    OPENAI_EMBEDDING_MODEL,
    DEFAULT_CONTEXT_BUDGET,
    MAX_CONTEXT_TOKENS,
)


class AITask(Enum):
    """Task types for AI routing."""
    SUMMARIZE_EVENT = "summarize_event"
    CLASSIFY_TOPICS = "classify_topics"
    UPDATE_SKILL = "update_skill"
    CHAT_REPLY = "chat_reply"


@dataclass
class ModelRoute:
    """Configuration for a model route."""
    model_name: str
    token_budget: int
    supports_streaming: bool = False
    supports_json_mode: bool = False


class ModelRouter:
    """
    Model routing registry with task-based defaults and fallback.
    
    Routes tasks to appropriate models based on complexity and requirements.
    Supports configurable overrides and graceful degradation.
    """
    
    def __init__(self):
        """Initialize router with default routes."""
        # Default routes for each task
        self._routes: Dict[AITask, ModelRoute] = {
            AITask.SUMMARIZE_EVENT: ModelRoute(
                model_name=OPENAI_MODEL_DEFAULT,
                token_budget=DEFAULT_CONTEXT_BUDGET,
                supports_json_mode=True,
            ),
            AITask.CLASSIFY_TOPICS: ModelRoute(
                model_name=OPENAI_MODEL_NANO,
                token_budget=4000,  # Smaller budget for classification
                supports_json_mode=True,
            ),
            AITask.UPDATE_SKILL: ModelRoute(
                model_name=OPENAI_MODEL_NANO,
                token_budget=4000,
                supports_json_mode=True,
            ),
            AITask.CHAT_REPLY: ModelRoute(
                model_name=OPENAI_MODEL_DEFAULT,
                token_budget=DEFAULT_CONTEXT_BUDGET,
                supports_streaming=True,
            ),
        }
        
        # Fallback chain for each task
        self._fallbacks: Dict[AITask, list[str]] = {
            AITask.SUMMARIZE_EVENT: [OPENAI_MODEL_DEFAULT, OPENAI_MODEL_NANO],
            AITask.CLASSIFY_TOPICS: [OPENAI_MODEL_NANO, OPENAI_MODEL_DEFAULT],
            AITask.UPDATE_SKILL: [OPENAI_MODEL_NANO, OPENAI_MODEL_DEFAULT],
            AITask.CHAT_REPLY: [OPENAI_MODEL_DEFAULT, OPENAI_MODEL_NANO],
        }
    
    def get_route(self, task: AITask, override_model: Optional[str] = None) -> ModelRoute:
        """
        Get model route for a task.
        
        Args:
            task: Task type
            override_model: Optional model name override
            
        Returns:
            ModelRoute configuration
        """
        if override_model:
            # Use override with task's default budget
            base_route = self._routes[task]
            return ModelRoute(
                model_name=override_model,
                token_budget=base_route.token_budget,
                supports_streaming=base_route.supports_streaming,
                supports_json_mode=base_route.supports_json_mode,
            )
        
        return self._routes[task]
    
    def get_fallback_chain(self, task: AITask) -> list[str]:
        """
        Get fallback model chain for a task.
        
        Args:
            task: Task type
            
        Returns:
            List of model names in fallback order
        """
        return self._fallbacks[task].copy()
    
    def set_route(self, task: AITask, route: ModelRoute) -> None:
        """
        Override default route for a task.
        
        Args:
            task: Task type
            route: New route configuration
        """
        self._routes[task] = route
    
    def get_model_for_task(self, task: AITask, override_model: Optional[str] = None) -> str:
        """
        Get model name for a task (convenience method).
        
        Args:
            task: Task type
            override_model: Optional model name override
            
        Returns:
            Model name string
        """
        return self.get_route(task, override_model).model_name


# Global router instance
_router: Optional[ModelRouter] = None


def get_router() -> ModelRouter:
    """Get or create global router instance."""
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router

