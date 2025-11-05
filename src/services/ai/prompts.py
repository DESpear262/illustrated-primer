"""
Prompt templates for AI Tutor Proof of Concept.

Provides standardized prompt templates and structured output schemas
for all AI tasks.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from src.services.ai.router import AITask


@dataclass
class SummaryOutput:
    """Structured output schema for event summarization."""
    summary: str
    topics: List[str]
    skills: List[str]
    key_points: List[str]
    open_questions: List[str]


@dataclass
class ClassificationOutput:
    """Structured output schema for topic classification."""
    topics: List[str]
    skills: List[str]
    confidence: float


@dataclass
class SkillUpdateOutput:
    """Structured output schema for skill state updates."""
    p_mastery_delta: float
    evidence_summary: str
    confidence: float


def get_system_prompt(task: AITask) -> str:
    """
    Get system prompt for a task.
    
    Args:
        task: Task type
        
    Returns:
        System prompt string
    """
    prompts = {
        AITask.SUMMARIZE_EVENT: """You are a learning analytics assistant. 
Summarize educational events concisely, extracting topics, skills, key points, and open questions.
Output JSON only.""",
        
        AITask.CLASSIFY_TOPICS: """You are a topic classification assistant.
Analyze text and classify it into educational topics and skills.
Output JSON only.""",
        
        AITask.UPDATE_SKILL: """You are a skill assessment assistant.
Evaluate evidence and update skill mastery estimates.
Output JSON only.""",
        
        AITask.CHAT_REPLY: """You are an AI tutor helping a student learn.
Provide clear, helpful explanations adapted to the student's level.
Reference past learning when relevant.""",
    }
    
    return prompts.get(task, "")


def build_summarize_prompt(event_content: str, context: Optional[str] = None) -> str:
    """
    Build prompt for event summarization.
    
    Args:
        event_content: Event content to summarize
        context: Optional context from previous events
        
    Returns:
        User prompt string
    """
    prompt = f"""Summarize the following educational event:

{event_content}"""
    
    if context:
        prompt += f"\n\nContext from previous sessions:\n{context}"
    
    prompt += "\n\nProvide a JSON response with: summary (string), topics (list), skills (list), key_points (list), open_questions (list)."
    
    return prompt


def build_classify_prompt(text: str) -> str:
    """
    Build prompt for topic classification.
    
    Args:
        text: Text to classify
        
    Returns:
        User prompt string
    """
    return f"""Classify the following text into educational topics and skills:

{text}

Provide a JSON response with: topics (list of strings), skills (list of strings), confidence (float 0-1)."""


def build_skill_update_prompt(
    skill_id: str,
    current_p_mastery: float,
    evidence: str,
) -> str:
    """
    Build prompt for skill state update.
    
    Args:
        skill_id: Skill identifier
        current_p_mastery: Current mastery probability
        evidence: Evidence text
        
    Returns:
        User prompt string
    """
    return f"""Evaluate evidence for skill: {skill_id}

Current mastery: {current_p_mastery:.2f}

Evidence:
{evidence}

Provide a JSON response with: p_mastery_delta (float), evidence_summary (string), confidence (float 0-1)."""


def build_chat_prompt(user_message: str, context: Optional[str] = None) -> str:
    """
    Build prompt for chat reply.
    
    Args:
        user_message: User's message
        context: Optional context from past sessions
        
    Returns:
        User prompt string
    """
    if context:
        return f"""Context from past learning:
{context}

Student: {user_message}

Tutor:"""
    
    return f"""Student: {user_message}

Tutor:"""


def parse_json_response(text: str, schema_type: type) -> Any:
    """
    Parse JSON response from AI output.
    
    Args:
        text: AI response text
        schema_type: Expected schema type (SummaryOutput, ClassificationOutput, etc.)
        
    Returns:
        Parsed schema instance
        
    Raises:
        ValueError: If parsing fails
    """
    import json
    import re
    
    # Try to extract JSON from markdown code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        text = json_match.group(1)
    
    # Try to find JSON object in text
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        text = json_match.group(0)
    
    try:
        data = json.loads(text)
        if schema_type == SummaryOutput:
            return SummaryOutput(
                summary=data.get("summary", ""),
                topics=data.get("topics", []),
                skills=data.get("skills", []),
                key_points=data.get("key_points", []),
                open_questions=data.get("open_questions", []),
            )
        elif schema_type == ClassificationOutput:
            return ClassificationOutput(
                topics=data.get("topics", []),
                skills=data.get("skills", []),
                confidence=data.get("confidence", 0.5),
            )
        elif schema_type == SkillUpdateOutput:
            return SkillUpdateOutput(
                p_mastery_delta=data.get("p_mastery_delta", 0.0),
                evidence_summary=data.get("evidence_summary", ""),
                confidence=data.get("confidence", 0.5),
            )
        else:
            return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON response: {e}") from e

