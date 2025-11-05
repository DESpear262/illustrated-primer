# Product Context: AI Tutor Proof of Concept

## Why This Project Exists

This project addresses the need for a persistent, context-aware AI tutoring system that can:
- Remember past learning sessions without requiring users to re-upload context
- Provide personalized learning experiences based on historical performance
- Integrate external learning materials (human tutor transcripts) seamlessly
- Support spaced repetition for improved retention

## Problems It Solves

1. **Context Loss**: Traditional AI tutors don't remember past conversations
2. **No Personalization**: Generic responses don't adapt to individual learning patterns
3. **Disconnected Learning**: External learning materials (tutor sessions) aren't integrated
4. **No Retention Strategy**: Missing systematic review and spaced repetition
5. **Lack of Progress Tracking**: No visibility into learning improvement over time

## How It Should Work

### Core Workflow

```
User chats → Event stored → AI summarizes → State updated
                           ↓
               Retrieval manager builds context
                           ↓
            AI composes prompt for next interaction
```

### User Experience

**Tutor Chat Mode:**
- Conversational LLM interface for study sessions
- Automatically records interactions as events
- AI recalls past work and adapts to student's knowledge level

**Command Chat Mode:**
- Structured command input: "summarize topic X," "show progress Y," "import transcript Z"
- Displays formatted JSON/log output and metrics
- Administrative queries and context operations

### Key Features

1. **Context Storage & Retrieval**
   - Events stored with metadata (topics, skills, actors, timestamps, embeddings)
   - Derived summaries at topic and skill level
   - Time-decay weighting, semantic similarity, and topic matching

2. **AI-Orchestrated Context Manager**
   - Summarize new events
   - Update mastery probabilities
   - Refresh topic summaries
   - Retrieve and merge relevant slices into working context

3. **Spaced Repetition Engine**
   - Compute review priority based on `last_evidence_at` + mastery decay
   - Generate review lists
   - Track outcomes to refine mastery estimates

## User Stories

### Primary User: Student with AI Tutor
- As a student, I want to continue a tutoring session and have the AI recall my past work without re-uploading context
- As a student, I want to ask, "Show me what I last studied in calculus," and get a summary
- As a student, I want the AI to quiz me on concepts I haven't reviewed recently
- As a student, I want to see how my understanding has improved over time

### Secondary User: Human Tutor
- As a tutor, I want to import a session transcript and have it reflected in the student's learning record
- As a tutor, I want to review what the student has practiced before our next meeting

### System
- As the system, I must retrieve relevant session fragments efficiently and compose a prompt that fits the LLM context window
- As the system, I must summarize new sessions into persistent long-term memory without duplicating content
- As the system, I must handle multiple subjects, each with hierarchical relationships and timestamps

