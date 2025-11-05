# Active Context: AI Tutor Proof of Concept

## Current Work Focus

**Block B: AI Tutor Chat System - PR #6: Context Composition Engine** ✅ **COMPLETED**

## Recent Changes

### Completed (PR #6)
1. ✅ Created ContextAssembler with dynamic token allocation (new chat: all to memory; grows to 60% history cap)
2. ✅ Implemented hybrid retrieval (FAISS + recency + FTS) with configurable weights
3. ✅ Added recency decay with exponential decay (tau = 7 days, configurable)
4. ✅ Implemented MMR (Maximal Marginal Relevance) for diversity (lambda = 0.7, configurable)
5. ✅ Added filtering by score threshold, topic overlap, max per event/topic
6. ✅ Integrated assembler into chat flow for context composition
7. ✅ Added ChunkRecord model to base.py
8. ✅ Created comprehensive unit tests for filters and assembler (19 new tests, all passing)

### Completed (PR #5)
1. ✅ Implemented text-based TUI using typer + rich (`src/cli/chat.py`, `src/interface/tutor_chat.py`)
2. ✅ Added conversational history buffer with token budgeting (`src/interface/utils.py`)
3. ✅ Logged each turn as `Event` with `metadata.session_id` and `turn_index`
4. ✅ Displayed loading indicators and summaries; summarize on exit and on upload
5. ✅ Implemented session list and resume
6. ✅ LLM-suggested session title based on first interaction

### Completed (PR #4)
1. ✅ Created ModelRouter with task-based routing (SUMMARIZE_EVENT, CLASSIFY_TOPICS, UPDATE_SKILL, CHAT_REPLY)
2. ✅ Implemented AIClient with retry, rate limiting, token counting, and error handling
3. ✅ Created prompt templates and structured output schemas (SummaryOutput, ClassificationOutput, SkillUpdateOutput)
4. ✅ Implemented summarization, classification, and skill update functions
5. ✅ Added error categorization (AIClientError, AIServerError, AITimeoutError) with retry logic
6. ✅ Added CLI commands: `ai routes` and `ai test` for testing and configuration
7. ✅ Created comprehensive unit and integration tests (49 new tests, all passing)

### Completed (PR #3)
1. ✅ Added `event_chunks` table for chunk storage and embeddings
2. ✅ Implemented FAISS index ops (build/search/persist) with cosine similarity
3. ✅ Implemented chunking and embedding pipeline with batching and overlap
4. ✅ Added CLI commands: `index build`, `index status`, `index search`
5. ✅ Added tiktoken support and config flags; sensible defaults applied
6. ✅ Added unit/integration tests for FAISS, pipeline, and hybrid retrieval
7. ✅ Adjusted validation and FTS query aliasing for test reliability

### Completed (PR #1)
1. ✅ Created Pydantic schemas for all entities:
   - `Event` - chat/transcript/quiz interactions
   - `SkillState` - mastery tracking with p_mastery (0.0-1.0)
   - `TopicSummary` - hierarchical topic summaries
   - `Goal` - learning objectives
   - `Commitment` - study plans
   - `NudgeLog` - system reminders

2. ✅ Created SQLite schema with:
   - All tables with proper constraints
   - Hierarchical topic support (foreign key on parent_topic_id)
   - FTS5 full-text search table with triggers
   - Indexes on timestamps, topics, and embeddings
   - Embedding storage as BLOB in SQLite

3. ✅ Created serialization utilities:
   - Model-to-JSON conversion
   - JSON list/dict serialization
   - Datetime serialization
   - Embedding binary serialization

4. ✅ Created comprehensive test suite:
   - Unit tests for models, serialization, database initialization
   - Integration tests for database operations, topic hierarchy, FTS search

5. ✅ Created stub data generation script
6. ✅ Created README with schema documentation
7. ✅ Created configuration module with environment variable support

## Next Steps

### Completed (PR #5)
1. ✅ Implemented text-based TUI using typer + rich (`src/cli/chat.py`, `src/interface/tutor_chat.py`)
2. ✅ Added conversational history buffer with token budgeting (`src/interface/utils.py`)
3. ✅ Logged each turn as `Event` with `metadata.session_id` and `turn_index`
4. ✅ Displayed loading indicators and summaries; summarize on exit and on upload
5. ✅ Implemented session list and resume
6. ✅ LLM-suggested session title based on first interaction

## Active Decisions

1. **Database Path**: Default to `$PROJECT_ROOT/data/`, configurable via `AI_TUTOR_DATA_DIR`
2. **Embedding Storage**: Embeddings stored as BLOB in SQLite (not just referenced)
3. **Topic Hierarchy**: Implemented as foreign key relationship (parent_topic_id)
4. **JSON Storage**: List and dictionary fields stored as JSON strings in TEXT columns
5. **Testing Framework**: Using pytest for all tests
6. **Python Version**: Using Python 3.14+ with no version pins in requirements.txt

## Current Blockers

None - Block A complete; proceeding to Block B

## Implementation Status

### Block A: Core Data Infrastructure
- ✅ PR #1: Define Data Models and Schemas (COMPLETED)
- ✅ PR #2: Database I/O Layer (COMPLETED)
- ✅ PR #3: Vector Store & Embedding Pipeline (COMPLETED)

### Block B: AI Tutor Chat System
- ✅ PR #4: AI Orchestration Layer (COMPLETED)
- ✅ PR #5: Tutor Chat Interface (TUI) (COMPLETED)
- ✅ PR #6: Context Composition Engine (COMPLETED)

### Block C: Transcript Ingestion Pipeline
- ⏳ PR #7: Transcript Importer
- ⏳ PR #8: Update Propagation & Summarization

### Block D: Spaced Repetition & Mastery Tracking
- ⏳ PR #9: Review Scheduler
- ⏳ PR #10: Performance Tracking

## Notes

- All tests passing
- No linter errors
- Database schema supports hierarchical topics
- Ready to proceed with database I/O layer implementation

