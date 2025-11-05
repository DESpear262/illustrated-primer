# Project Brief: AI Tutor Proof of Concept

## Core Purpose

Build a self-contained prototype demonstrating persistent, context-aware AI tutoring and spaced repetition, powered by local storage and modular context management.

## Primary Goals

1. **Context Persistence**: AI agent demonstrates context persistence, topic-based summarization, adaptive retrieval, and multi-turn reasoning across sessions
2. **Local-First Architecture**: All state and memory remain local; modular design enables later expansion to multi-user or cloud modes
3. **Dual Interface**: Two chat UIs (Tutor Chat and Command Chat) using shared memory
4. **Spaced Repetition**: Generate review lists and track mastery over time
5. **Transcript Integration**: Import human tutor sessions and external transcripts

## Success Criteria

**Primary (Proof of Concept Minimum Viable Goals):**
- AI can retrieve and summarize sessions across ≥5 topics
- Context persistence verified across ≥3 restarts
- Spaced repetition algorithm generates review lists accurately
- Transcripts integrate into topic summaries automatically
- User can query performance deltas (learning improvement) between timestamps

**Secondary (Stretch Goals):**
- Mastery tracking via lightweight Bayesian update or Elo model
- Context visualizer (CLI heatmap of reviewed topics)
- Plugin-style API for external data ingestion (e.g., quiz apps)

## Key Principles

1. **Context First** — Persistence and retrieval reliability precede pedagogy
2. **Local by Default** — All state and storage remain offline
3. **Modular AI** — Any OpenAI-compatible model can serve specific sub-tasks
4. **Transparent Operation** — Logs and summaries visible and inspectable
5. **Graceful Degradation** — If AI calls fail, fallback summaries or cached context used

## Timeline

- **Deadline**: TBD (Target: 4 weeks from kickoff)
- **Total Implementation Time**: ~140 hours
- **Implementation Blocks**: 
  - Block A: Core Data Infrastructure (~30 hours) - **IN PROGRESS**
  - Block B: AI Tutor Chat System (~40 hours)
  - Block C: Transcript Ingestion Pipeline (~25 hours)
  - Block D: Spaced Repetition & Mastery Tracking (~25 hours)

