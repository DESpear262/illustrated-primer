"""
Integration tests for AI client with mocked API responses.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from src.services.ai.client import AIClient
from src.services.ai.router import AITask, ModelRouter
from src.services.ai.prompts import SummaryOutput, ClassificationOutput
from src.services.ai.utils import AIError, AIClientError, AIServerError


class TestAIClient:
    """Tests for AIClient with mocked API."""
    
    @patch('src.services.ai.client.OpenAI')
    def test_summarize_event(self, mock_openai_class):
        """Test summarize_event with mocked API."""
        # Setup mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "summary": "Test summary",
            "topics": ["calculus"],
            "skills": ["derivative_basic"],
            "key_points": ["Point 1"],
            "open_questions": ["Question 1"],
        })
        mock_response.usage = Mock()
        mock_response.usage.completion_tokens = 100
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        client = AIClient(api_key="test-key")
        result = client.summarize_event("Test content")
        
        assert isinstance(result, SummaryOutput)
        assert result.summary == "Test summary"
        assert result.topics == ["calculus"]
        
        # Verify API was called
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('src.services.ai.client.OpenAI')
    def test_classify_topics(self, mock_openai_class):
        """Test classify_topics with mocked API."""
        # Setup mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "topics": ["calculus", "derivatives"],
            "skills": ["derivative_basic"],
            "confidence": 0.85,
        })
        mock_response.usage = Mock()
        mock_response.usage.completion_tokens = 50
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        client = AIClient(api_key="test-key")
        result = client.classify_topics("Learning about derivatives")
        
        assert isinstance(result, ClassificationOutput)
        assert result.topics == ["calculus", "derivatives"]
        assert result.confidence == 0.85
    
    @patch('src.services.ai.client.OpenAI')
    def test_chat_reply(self, mock_openai_class):
        """Test chat_reply with mocked API."""
        # Setup mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "A derivative is the rate of change."
        mock_response.usage = Mock()
        mock_response.usage.completion_tokens = 20
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        client = AIClient(api_key="test-key")
        result = client.chat_reply("What is a derivative?")
        
        assert isinstance(result, str)
        assert "derivative" in result.lower()
    
    @patch('src.services.ai.client.OpenAI')
    def test_retry_on_server_error(self, mock_openai_class):
        """Test retry logic on server error."""
        from src.services.ai.utils import AIServerError
        
        mock_client = Mock()
        
        # First call fails with server error, second succeeds
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "summary": "Success",
            "topics": [],
            "skills": [],
            "key_points": [],
            "open_questions": [],
        })
        mock_response.usage = Mock()
        mock_response.usage.completion_tokens = 10
        
        # Simulate server error (500) on first call - use string error that will be caught
        mock_client.chat.completions.create.side_effect = [
            Exception("500 Internal Server Error"),
            mock_response,
        ]
        mock_openai_class.return_value = mock_client
        
        client = AIClient(api_key="test-key")
        
        # Should retry and succeed
        result = client.summarize_event("Test", override_model="gpt-4o-mini")
        
        assert isinstance(result, SummaryOutput)
        assert mock_client.chat.completions.create.call_count == 2
    
    @patch('src.services.ai.client.OpenAI')
    def test_no_retry_on_client_error(self, mock_openai_class):
        """Test no retry on client error."""
        mock_client = Mock()
        # Simulate client error (400) - should not retry
        # Use string error that will be caught by error categorization
        mock_client.chat.completions.create.side_effect = Exception("400 Bad Request")
        mock_openai_class.return_value = mock_client
        
        client = AIClient(api_key="test-key")
        
        # Should not retry
        with pytest.raises(AIClientError):
            client.summarize_event("Test")
        
        assert mock_client.chat.completions.create.call_count == 1
    
    def test_no_api_key(self):
        """Test client without API key."""
        client = AIClient(api_key=None)
        
        with pytest.raises(AIError) as exc_info:
            client.summarize_event("Test")
        
        assert "not configured" in str(exc_info.value).lower()
    
    @patch('src.services.ai.client.OpenAI')
    def test_token_budget_respected(self, mock_openai_class):
        """Test token budget is respected."""
        from src.services.ai.router import ModelRoute
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "summary": "Test",
            "topics": [],
            "skills": [],
            "key_points": [],
            "open_questions": [],
        })
        mock_response.usage = Mock()
        mock_response.usage.completion_tokens = 50
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        router = ModelRouter()
        router.set_route(
            AITask.SUMMARIZE_EVENT,
            ModelRoute(
                model_name="gpt-4o",
                token_budget=100,
                supports_json_mode=True,
                supports_streaming=False,
            ),
        )
        
        client = AIClient(api_key="test-key", router=router)
        
        # Long text that exceeds budget
        long_text = "This is a test. " * 10000
        
        client.summarize_event(long_text)
        
        # Verify API was called (prompt should be truncated)
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        user_message = messages[1]["content"]
        
        # Should be truncated
        assert len(user_message) < len(long_text)

