"""
Unit tests for prompt templates and parsing.
"""

import pytest
import json

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
    AITask,
)


class TestSystemPrompts:
    """Tests for system prompts."""
    
    def test_get_system_prompt_all_tasks(self):
        """Test system prompts exist for all tasks."""
        for task in AITask:
            prompt = get_system_prompt(task)
            assert isinstance(prompt, str)
            assert len(prompt) > 0


class TestPromptBuilding:
    """Tests for prompt building functions."""
    
    def test_build_summarize_prompt(self):
        """Test building summarize prompt."""
        content = "Learning about derivatives and integrals"
        
        prompt = build_summarize_prompt(content)
        
        assert content in prompt
        assert "JSON" in prompt or "json" in prompt
    
    def test_build_summarize_prompt_with_context(self):
        """Test building summarize prompt with context."""
        content = "Learning about derivatives"
        context = "Previous session covered limits"
        
        prompt = build_summarize_prompt(content, context)
        
        assert content in prompt
        assert context in prompt
    
    def test_build_classify_prompt(self):
        """Test building classify prompt."""
        text = "This is about calculus and derivatives"
        
        prompt = build_classify_prompt(text)
        
        assert text in prompt
        assert "topics" in prompt.lower()
    
    def test_build_skill_update_prompt(self):
        """Test building skill update prompt."""
        skill_id = "derivative_basic"
        p_mastery = 0.6
        evidence = "Student correctly solved derivative problems"
        
        prompt = build_skill_update_prompt(skill_id, p_mastery, evidence)
        
        assert skill_id in prompt
        assert str(p_mastery) in prompt
        assert evidence in prompt
    
    def test_build_chat_prompt(self):
        """Test building chat prompt."""
        message = "What is a derivative?"
        
        prompt = build_chat_prompt(message)
        
        assert message in prompt
    
    def test_build_chat_prompt_with_context(self):
        """Test building chat prompt with context."""
        message = "Can you explain more?"
        context = "Previous discussion about limits"
        
        prompt = build_chat_prompt(message, context)
        
        assert message in prompt
        assert context in prompt


class TestJSONParsing:
    """Tests for JSON response parsing."""
    
    def test_parse_summary_output(self):
        """Test parsing SummaryOutput."""
        json_text = json.dumps({
            "summary": "Test summary",
            "topics": ["calculus"],
            "skills": ["derivative_basic"],
            "key_points": ["Point 1", "Point 2"],
            "open_questions": ["Question 1"],
        })
        
        result = parse_json_response(json_text, SummaryOutput)
        
        assert isinstance(result, SummaryOutput)
        assert result.summary == "Test summary"
        assert result.topics == ["calculus"]
        assert result.skills == ["derivative_basic"]
    
    def test_parse_summary_output_in_markdown(self):
        """Test parsing SummaryOutput from markdown code block."""
        json_text = "```json\n" + json.dumps({
            "summary": "Test",
            "topics": [],
            "skills": [],
            "key_points": [],
            "open_questions": [],
        }) + "\n```"
        
        result = parse_json_response(json_text, SummaryOutput)
        
        assert isinstance(result, SummaryOutput)
    
    def test_parse_classification_output(self):
        """Test parsing ClassificationOutput."""
        json_text = json.dumps({
            "topics": ["calculus"],
            "skills": ["derivative_basic"],
            "confidence": 0.85,
        })
        
        result = parse_json_response(json_text, ClassificationOutput)
        
        assert isinstance(result, ClassificationOutput)
        assert result.topics == ["calculus"]
        assert result.confidence == 0.85
    
    def test_parse_skill_update_output(self):
        """Test parsing SkillUpdateOutput."""
        json_text = json.dumps({
            "p_mastery_delta": 0.1,
            "evidence_summary": "Good progress",
            "confidence": 0.8,
        })
        
        result = parse_json_response(json_text, SkillUpdateOutput)
        
        assert isinstance(result, SkillUpdateOutput)
        assert result.p_mastery_delta == 0.1
        assert result.confidence == 0.8
    
    def test_parse_invalid_json(self):
        """Test parsing invalid JSON raises error."""
        invalid_json = "not json"
        
        with pytest.raises(ValueError):
            parse_json_response(invalid_json, SummaryOutput)

