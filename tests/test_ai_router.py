"""
Unit tests for AI router and routing logic.
"""

import pytest

from src.services.ai.router import (
    AITask,
    ModelRouter,
    ModelRoute,
    get_router,
)
from src.config import OPENAI_MODEL_DEFAULT, OPENAI_MODEL_NANO


class TestModelRouter:
    """Tests for ModelRouter."""
    
    def test_router_initialization(self):
        """Test router initializes with default routes."""
        router = ModelRouter()
        
        assert AITask.SUMMARIZE_EVENT in router._routes
        assert AITask.CLASSIFY_TOPICS in router._routes
        assert AITask.CHAT_REPLY in router._routes
    
    def test_get_route(self):
        """Test getting route for a task."""
        router = ModelRouter()
        
        route = router.get_route(AITask.SUMMARIZE_EVENT)
        
        assert isinstance(route, ModelRoute)
        assert route.model_name in [OPENAI_MODEL_DEFAULT, OPENAI_MODEL_NANO]
        assert route.token_budget > 0
    
    def test_get_route_with_override(self):
        """Test getting route with model override."""
        router = ModelRouter()
        
        route = router.get_route(AITask.SUMMARIZE_EVENT, override_model="gpt-4")
        
        assert route.model_name == "gpt-4"
    
    def test_get_fallback_chain(self):
        """Test getting fallback chain for a task."""
        router = ModelRouter()
        
        chain = router.get_fallback_chain(AITask.SUMMARIZE_EVENT)
        
        assert isinstance(chain, list)
        assert len(chain) > 0
        assert all(isinstance(m, str) for m in chain)
    
    def test_set_route(self):
        """Test setting custom route."""
        router = ModelRouter()
        
        new_route = ModelRoute(
            model_name="gpt-4",
            token_budget=8000,
            supports_streaming=True,
        )
        
        router.set_route(AITask.SUMMARIZE_EVENT, new_route)
        
        route = router.get_route(AITask.SUMMARIZE_EVENT)
        assert route.model_name == "gpt-4"
        assert route.token_budget == 8000
    
    def test_get_model_for_task(self):
        """Test convenience method to get model name."""
        router = ModelRouter()
        
        model = router.get_model_for_task(AITask.CLASSIFY_TOPICS)
        
        assert isinstance(model, str)
        assert model in [OPENAI_MODEL_DEFAULT, OPENAI_MODEL_NANO]


class TestGlobalRouter:
    """Tests for global router instance."""
    
    def test_get_router(self):
        """Test getting global router instance."""
        router1 = get_router()
        router2 = get_router()
        
        # Should return same instance
        assert router1 is router2


class TestAITask:
    """Tests for AITask enum."""
    
    def test_task_values(self):
        """Test all task values are defined."""
        tasks = list(AITask)
        
        assert AITask.SUMMARIZE_EVENT in tasks
        assert AITask.CLASSIFY_TOPICS in tasks
        assert AITask.UPDATE_SKILL in tasks
        assert AITask.CHAT_REPLY in tasks

