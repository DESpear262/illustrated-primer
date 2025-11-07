# AI Tutor Proof of Concept — Local Context Manager

> **Purpose:** Build a self-contained prototype demonstrating persistent, context-aware AI tutoring and spaced repetition, powered by local storage and modular context management.

**Deadline:** TBD (Target: 4 weeks from kickoff)  
**Success Criteria:** AI agent demonstrates context persistence, topic-based summarization, adaptive retrieval, and multi-turn reasoning across sessions.  
**Architecture Principle:** All state and memory remain local; modular design enables later expansion to multi-user or cloud modes.

---

## Project Overview

This proof of concept builds a **local AI tutoring engine** capable of:
- Persisting study sessions as structured events (chats, transcripts, assessments).  
- Dynamically retrieving relevant context for continued discussion.  
- Generating summaries, progress tracking, and spaced repetition schedules.  
- Integrating external “session recordings” from human tutors into the same context model.  

The system operates entirely **offline except for OpenAI API calls**, with a **CLI/TUI interface** providing two primary modes:
1. **Tutor Chat** — conversational study sessions.
2. **Command Chat** — administrative queries and context operations (e.g., “summarize all calculus sessions since last week”).

---

## Current State

### What Exists (Pre-Prototype)
- Conceptual schema for event- and state-based context storage.
- Agreed separation between *Events* (raw logs) and *Derived State* (summaries, mastery estimates).
- Preliminary stack choice: Python + SQLite + FAISS + OpenAI API.

### What We’re Building
- Local storage layer with retrieval, summarization, and spaced repetition.
- Two chat UIs (Tutor / Command) using shared memory.
- Ingestion pipeline for transcripts and summaries.
- Automated topic rollups and mastery estimation.
- Minimal spaced repetition scheduler and progress reporting.
- Modular AI layer for flexible model routing (nano / 4o / etc.).

---

## User Stories

### Primary User: Student with AI Tutor
- As a student, I want to continue a tutoring session and have the AI recall my past work without re-uploading context.  
- As a student, I want to ask, “Show me what I last studied in calculus,” and get a summary.  
- As a student, I want the AI to quiz me on concepts I haven’t reviewed recently.  
- As a student, I want to see how my understanding has improved over time.  

### Secondary User: Human Tutor
- As a tutor, I want to import a session transcript and have it reflected in the student’s learning record.  
- As a tutor, I want to review what the student has practiced before our next meeting.

### System
- As the system, I must retrieve relevant session fragments efficiently and compose a prompt that fits the LLM context window.  
- As the system, I must summarize new sessions into persistent long-term memory without duplicating content.  
- As the system, I must handle multiple subjects, each with hierarchical relationships and timestamps.

---

## Core Feature Requirements

### 1. Context Storage & Retrieval (Critical)
- **Event Storage:**  
  - Each chat or imported session stored as an `Event` with metadata (topics, skills, actors, timestamps, embeddings).  
- **State Derivation:**  
  - Derived summaries at topic and skill level (`TopicSummary`, `SkillState`).
- **Retrieval Policy:**  
  - Time-decay weighting, semantic similarity, and topic matching.  
  - Configurable context budget for prompt composition.

### 2. AI-Orchestrated Context Manager (Critical)
- **Responsibilities:**  
  - Summarize new events, update mastery probabilities, and refresh topic summaries.  
  - Retrieve and merge relevant slices into working context for chat interactions.  
  - Route OpenAI requests through model registry (nano for fast classification, 4o for reasoning).  
- **Functions:**  
  - `summarize_event(event_id)`  
  - `update_skill_state(skill_id, evidence)`  
  - `get_context(topics, time_range)`  
  - `compose_prompt(task, context_window)`

### 3. Dual Chat Interfaces (Critical)
- **Tutor Chat:**  
  - Conversational LLM interface for study sessions.  
  - Automatically records interactions as events.  
- **Command Chat (TUI):**  
  - Structured command input: “summarize topic X,” “show progress Y,” “import transcript Z.”  
  - Displays formatted JSON/log output and metrics.

### 4. Transcript Integration (High)
- **Input:** human tutor transcripts (plain text, JSON, or markdown).  
- **Process:** chunk, embed, summarize → create new events + update state.  
- **Output:** visible in student summaries and spaced repetition scheduler.

### 5. Spaced Repetition Engine (High)
- **Core Logic:** compute review priority based on `last_evidence_at` + mastery decay.  
- **Interface:**  
  - “Show me what I should review today.”  
  - “Generate 5 quick questions from my weak topics.”  
- **Evaluation Loop:** store outcomes as new evidence to refine mastery estimates.

---

## Success Metrics

**Primary (Proof of Concept Minimum Viable Goals):**
- AI can retrieve and summarize sessions across ≥5 topics.  
- Context persistence verified across ≥3 restarts.  
- Spaced repetition algorithm generates review lists accurately.  
- Transcripts integrate into topic summaries automatically.  
- User can query performance deltas (learning improvement) between timestamps.  

**Secondary (Stretch Goals):**
- Mastery tracking via lightweight Bayesian update or Elo model.  
- Context visualizer (CLI heatmap of reviewed topics).  
- Plugin-style API for external data ingestion (e.g., quiz apps).  

---

## Technical Architecture

### Stack Summary
| Component | Choice | Purpose |
|------------|---------|----------|
| **Core Language** | Python 3.11+ | Rapid prototyping |
| **Database** | SQLite (FTS5) | Events, states, metadata |
| **Vector Search** | FAISS | Semantic retrieval |
| **Graph Handling** | networkx | Topic/skill DAG |
| **Model Integration** | OpenAI API | LLM + embeddings |
| **Validation** | Pydantic | Schema enforcement |
| **Interface** | typer + rich | CLI / TUI command pages |
| **Scheduling** | APScheduler | Spaced repetition + maintenance tasks |

### Data Entities
- `Event`: raw chat, quiz, or transcript segment.  
- `SkillState`: mastery probability + last evidence.  
- `TopicSummary`: high-level recap and open questions.  
- `Goal`, `Commitment`, `NudgeLog`: for future retention logic.  

### Flow Overview
```
User chats → Event stored → AI summarizes → State updated
                           ↓
               Retrieval manager builds context
                           ↓
            AI composes prompt for next interaction
```

---

## Risks & Mitigation

| Risk | Description | Mitigation |
|------|--------------|-------------|
| **Context bloat** | Overlong prompts exceed LLM window | Aggressive summarization + embedding filtering |
| **Cold start** | Sparse data leads to weak personalization | Default priors + guided diagnostic |
| **Hallucinated summaries** | LLM invents details during summarization | Validation via keyword/entity cross-check |
| **Performance drift** | Retrieval slows as data grows | Index rotation + periodic pruning |
| **Integration ambiguity** | Tutor transcripts vary in format | Require minimal JSON schema wrapper |

---

## Implementation Timeline (30 Days)

| Week | Milestone | Deliverables |
|------|------------|--------------|
| 1 | Core data model & ingestion | SQLite schema, event logging, transcript importer |
| 2 | Retrieval & summarization | FAISS search, summarizer pipeline, context composer |
| 3 | Chat interfaces | Tutor and Command TUIs, prompt assembly |
| 4 | Spaced repetition & metrics | Review scheduler, delta tracking, demo + logs |

---

## Success Criteria (Definition of Done)

- [ ] Local database operational with events, state, summaries  
- [ ] Retrieval works by topic and time  
- [ ] Summarizer updates topic summaries automatically  
- [ ] Spaced repetition produces review list  
- [ ] Transcript ingestion pipeline functional  
- [ ] Tutor chat and Command chat UIs operational  
- [ ] Context persisted between runs and validated manually  

---

## Key Principles

1. **Context First** — Persistence and retrieval reliability precede pedagogy.  
2. **Local by Default** — All state and storage remain offline.  
3. **Modular AI** — Any OpenAI-compatible model can serve specific sub-tasks.  
4. **Transparent Operation** — Logs and summaries visible and inspectable.  
5. **Graceful Degradation** — If AI calls fail, fallback summaries or cached context used.  
