# Active Context: AI Tutor Proof of Concept

## Current Work Focus

**Interface Development - Block A: Backend Integration Layer - PR #1: Unified GUI–Backend Facade** ✅ **COMPLETED**

## Recent Changes

### Completed (Interface Development - PR #1)
1. ✅ Created `interface_common` module with unified GUI-backend facade
2. ✅ Implemented `AppFacade` class with async wrappers for all backend operations
3. ✅ Created custom exceptions (FacadeError, FacadeTimeoutError, FacadeValidationError)
4. ✅ Implemented DB wrapper methods (check, init) with timeout guards
5. ✅ Implemented Index wrapper methods (build, status, search) with timeout guards
6. ✅ Implemented AI wrapper methods (routes, test summarize/classify/chat) with timeout guards
7. ✅ Implemented Chat wrapper methods (start, resume, list, chat_turn) with full session management
8. ✅ Added `run_command(name, args)` dispatcher for generic command execution
9. ✅ Added timeout guards: LLM (30s), FAISS (10s), DB (5s)
10. ✅ Added error handling and exception serialization for UI display
11. ✅ Added logging hooks for all GUI-initiated operations
12. ✅ Created comprehensive unit tests (30+ tests) for facade methods
13. ✅ Created integration tests (8+ tests) for async operations and session persistence
14. ✅ Updated file index documentation

### Completed (PR #8)
1. ✅ Created summarizers module with update.py for batch processing and aggregation
2. ✅ Refactored update_topic_summary and update_skill_states from transcripts.py to summarizers/update.py
3. ✅ Implemented batch summarization with aggregation logic (aggregates unprocessed events per topic)
4. ✅ Created audit logging system with audit_logs table tracking all summarization operations
5. ✅ Implemented APScheduler background job for write-time summarization (process_summarization_job)
6. ✅ Added summarization configuration constants (SUMMARIZATION_BATCH_SIZE, SUMMARIZATION_INTERVAL_SECONDS, SUMMARIZATION_MAX_CONCURRENT_TOPICS, SUMMARIZATION_ENABLED)
7. ✅ Created CLI commands: `refresh summaries` (with --topic, --since, --force options) and `refresh status`
8. ✅ Integrated write-time summarization into event creation flow via hooks (non-blocking, optional)
9. ✅ Implemented versioning system with summary_version counter and last_summarized_at timestamp
10. ✅ Created comprehensive unit and integration tests (test_summarizers.py)
11. ✅ Updated file index documentation

### Completed (PR #9)
1. ✅ Created ReviewItem class for review items with priority scores
2. ✅ Implemented decay-based mastery model with exponential decay (tau = 30 days, grace period = 7 days)
3. ✅ Implemented review priority computation combining p_mastery and days_since_review
4. ✅ Created get_next_reviews function to retrieve and prioritize skills for review
5. ✅ Created record_review_outcome function to record outcomes as assessment Events and update skill state
6. ✅ Added review scheduler configuration constants (REVIEW_DECAY_TAU_DAYS, REVIEW_GRACE_PERIOD_DAYS, REVIEW_DEFAULT_LIMIT)
7. ✅ Created CLI command: `review next` with rich table output showing skill ID, topic, mastery, decayed mastery, days since review, and priority
8. ✅ Added filtering options (topic, mastery range, limit)
9. ✅ Created comprehensive unit and integration tests (22 tests, all passing)
10. ✅ Updated file index documentation

### Completed (PR #7)
1. ✅ Created transcript parsers for .txt, .md, and .json formats (`src/ingestion/transcripts.py`)
2. ✅ Implemented actor/speaker inference from transcript labels (Tutor/Student patterns)
3. ✅ Implemented timestamp parsing (ISO format, date strings, file modification time fallback)
4. ✅ Created OpenAI embedding function with fallback to stub embeddings
5. ✅ Implemented AI-based topic/skill classification using gpt-4o-mini
6. ✅ Created functions to update topic summaries and skill states after event import
7. ✅ Implemented main import_transcript function with AI classification, summarization, embedding, and state updates
8. ✅ Added comprehensive provenance tracking (source_file_path, import_timestamp, import_method, import_model_version, classification_confidence)
9. ✅ Created CLI commands: `import transcript` (single file) and `import batch` (multiple files)
10. ✅ Created comprehensive unit and integration tests (test_transcript_import.py)
11. ✅ Updated file index documentation

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

### Interface Development - Block A: Backend Integration Layer
- ⏳ PR #2: Graph + Hover Providers (12 hours)
  - Implement graph_provider.py to return DAG JSON from database
  - Implement hover_provider.py for per-node summaries and statistics
  - Integrate networkx DAG traversal utilities
  - Add query filters for scope, depth, and relation
  - Cache hover payloads to minimize repeated lookups

- ⏳ PR #3: UI Model Definitions (8 hours)
  - Create shared Pydantic models for GraphNode, GraphEdge, HoverPayload, ChatMessage, CommandResult
  - Define schema contracts used by both GUI front-ends
  - Add JSON serialization helpers

## Active Decisions

1. **Database Path**: Default to `$PROJECT_ROOT/data/`, configurable via `AI_TUTOR_DATA_DIR`
2. **Embedding Storage**: Embeddings stored as BLOB in SQLite (not just referenced)
3. **Topic Hierarchy**: Implemented as foreign key relationship (parent_topic_id)
4. **JSON Storage**: List and dictionary fields stored as JSON strings in TEXT columns
5. **Testing Framework**: Using pytest for all tests
6. **Python Version**: Using Python 3.14+ with no version pins in requirements.txt

## Current Blockers

None - Interface Development PR #1 complete; proceeding to PR #2: Graph + Hover Providers

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
- ✅ PR #7: Transcript Importer (COMPLETED)
- ✅ PR #8: Update Propagation & Summarization (COMPLETED)

### Block D: Spaced Repetition & Mastery Tracking
- ✅ PR #9: Review Scheduler (COMPLETED)
- ✅ PR #10: Performance Tracking (COMPLETED)

### Interface Development - Block A: Backend Integration Layer
- ✅ PR #1: Unified GUI–Backend Facade (COMPLETED)
- ⏳ PR #2: Graph + Hover Providers
- ⏳ PR #3: UI Model Definitions

## Notes

- All tests passing
- No linter errors (only import warnings for installed dependencies)
- Database schema supports hierarchical topics
- Transcript import fully functional with AI classification, summarization, and state updates
- Write-time summarization fully functional with APScheduler background jobs and audit logging
- Review scheduler fully functional with decay-based mastery model and priority computation
- GUI-backend facade complete with async wrappers, error handling, timeout guards, and logging hooks
- Ready to proceed with Interface Development PR #2: Graph + Hover Providers

