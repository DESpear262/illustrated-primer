# System Patterns: AI Tutor Proof of Concept

## Architecture Overview

```
Interface Layer → AI Layer → Retrieval Layer → Data Layer
                    ↓
              Pipelines & Jobs
                    ↓
              External Services
```

## Component Architecture

### Interface Layer
- **Tutor Chat TUI**: Conversational LLM interface for study sessions
- **Command Chat TUI**: Structured command input for administrative operations
- **GUI-Backend Facade**: Unified async API layer between GUI and all backend services
- **Graph Provider**: DAG JSON generation from database for knowledge tree visualization
- **Hover Provider**: Per-node summaries and statistics with caching for knowledge tree visualization
- **UI Models**: Shared Pydantic models (GraphNode, GraphEdge, HoverPayload, ChatMessage, CommandResult) for consistent data structures

### AI Layer
- **AI Orchestration**: Coordinates LLM calls and context management
- **Context Assembler**: Builds task-specific prompts from retrieved context
- **Prompt Templates**: Standardized prompt structures
- **Model Router**: Routes requests to appropriate OpenAI models (nano/4o)

### Retrieval Layer
- **Retrieval Pipeline**: Hybrid retrieval combining SQL and FAISS
- **SQLite FTS5**: Full-text search on event content
- **FAISS Search**: Semantic similarity search on embeddings

### Data Layer
- **SQLite DB**: Structured storage for events, states, summaries
- **FAISS Index Files**: Vector embeddings for semantic search

### Pipelines & Jobs
- **Transcript Ingestion**: Import external transcripts
- **Write-time Summarizers**: Automatic summarization on event creation
- **Spaced Repetition Scheduler**: Review list generation
- **Performance Reports**: Learning progress analysis

## Data Model Patterns

### Event-Driven Architecture
- All interactions stored as `Event` objects
- Events contain: content, metadata, topics, skills, timestamps, embeddings
- Events are immutable once created

### State Derivation
- Raw events → Topic summaries (via AI summarization)
- Events → Skill states (via mastery estimation)
- Derived state updated incrementally, not recomputed from scratch

### Hierarchical Topics
- Topics form a DAG (Directed Acyclic Graph)
- Parent-child relationships via `parent_topic_id`
- Supports subject hierarchies (e.g., calculus → derivatives → chain rule)

## Key Design Patterns

### 1. Context Budget Management
- Configurable token budget per model
- Aggressive summarization to prevent context bloat
- Time-decay weighting for recency
- Semantic similarity for relevance

### 2. Graceful Degradation
- Fallback summaries if AI calls fail
- Cached context for offline operation
- Default priors for cold start scenarios

### 3. Modular AI Routing
- Fast models (nano) for classification tasks
- Powerful models (4o) for reasoning tasks
- Model registry enables easy model swapping

### 4. Local-First Storage
- All data in SQLite (portable, no server required)
- FAISS index stored locally
- Easy backup (copy data directory)

## Data Flow Patterns

### Event Storage Flow
```
User Input → Event Creation → Embedding Generation → Storage → FTS Index Update
```

### Context Retrieval Flow
```
Query → Topic/Skill Filter → Time Filter → Semantic Search → Context Assembly
```

### Summarization Flow
```
New Events → Topic Detection → AI Summarization → Topic Summary Update
```

### Spaced Repetition Flow
```
Skill States → Mastery Decay Calculation → Priority Ranking → Review List Generation
```

## Component Relationships

- **Events** reference **Topics** and **Skills** (many-to-many via JSON arrays)
- **Skills** belong to **Topics** (many-to-one)
- **Topics** have hierarchical relationships (one-to-many parent-child)
- **Goals** and **Commitments** reference **Topics** and **Skills** (many-to-many)
- **NudgeLogs** reference **Topics** and **Commitments** (many-to-one)

## Error Handling Patterns

- Retry logic for API calls (max 3 attempts)
- Validation at model boundaries (Pydantic schemas)
- Transaction safety for database operations
- Graceful fallbacks for AI failures
- Facade pattern for GUI-backend communication with timeout guards and error serialization

