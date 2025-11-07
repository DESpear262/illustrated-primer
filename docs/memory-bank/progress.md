# Progress: AI Tutor Proof of Concept

## What Works

### ✅ Block A (Interface), PR #1: Unified GUI–Backend Facade (COMPLETED)

1. **Interface Common Module** (`src/interface_common/`)
   - `exceptions.py` - Custom exception classes with JSON serialization (FacadeError, FacadeTimeoutError, FacadeDatabaseError, FacadeIndexError, FacadeAIError, FacadeChatError)
   - `app_facade.py` - Unified facade with async wrappers for all CLI commands
   - `__init__.py` - Package initialization and exports

2. **AppFacade Class** (`src/interface_common/app_facade.py`)
   - Async wrappers for all CLI commands:
     - Database: `db_check()`, `db_init()`
     - Index: `index_build()`, `index_status()`, `index_search()`
     - AI: `ai_routes()`, `ai_test()`
     - Chat: `chat_start()`, `chat_resume()`, `chat_list()`, `chat_turn()`
     - Review: `review_next()`
     - Import: `import_transcript()`
     - Refresh: `refresh_summaries()`
     - Progress: `progress_summary()`
   - Error handling with timeout guards (LLM: 60s, FAISS/DB: 30s)
   - Logging hooks for all GUI-initiated operations with structured logging
   - `run_command(name, args)` dispatcher for GUI use

3. **Configuration Updates** (`src/config.py`)
   - Added summarization configuration constants (SUMMARIZATION_BATCH_SIZE, SUMMARIZATION_INTERVAL_SECONDS, SUMMARIZATION_MAX_CONCURRENT_TOPICS, SUMMARIZATION_ENABLED)

4. **Testing** (`tests/test_facade.py`)
   - Unit tests for exception classes (8 tests)
   - Unit tests for database commands (4 tests)
   - Unit tests for index commands (3 tests)
   - Unit tests for AI commands (4 tests)
   - Unit tests for chat commands (5 tests)
   - Unit tests for review, import, refresh, and progress commands (4 tests)
   - Unit tests for command dispatcher (4 tests)
   - Unit tests for error handling (2 tests)
   - Integration tests (2 tests)
   - All 36 tests passing

5. **Documentation**
   - Updated `docs/index/index.md` with new interface_common module files
   - Added pytest-asyncio to requirements.txt and pytest.ini

### ✅ Block A (Interface), PR #2: Graph + Hover Providers (COMPLETED)

1. **Graph Provider** (`src/context/graph_provider.py`)
   - `get_graph_json()` function for DAG JSON generation from database
   - Cytoscape.js format output (nodes/edges)
   - Networkx DAG traversal utilities for topic hierarchy
   - Filtering by scope (topic ID), depth (hierarchy level), and relation type
   - Support for topics, skills, and optional event nodes
   - Edge types: parent-child, belongs-to, evidence
   - Node IDs use unified format: "type:id" (e.g., "topic:math", "skill:derivative")

2. **Hover Provider** (`src/context/hover_provider.py`)
   - `get_hover_payload()` function for per-node summaries and statistics
   - Support for topic, skill, and event node types
   - Hover payload includes:
     - Topics: title, summary, event_count, last_event_at, open_questions, event_snippet, statistics
     - Skills: title, mastery, evidence_count, last_evidence_at, topic_id, event_snippet, statistics
     - Events: title, content, event_type, actor, topics, skills, created_at, recorded_at, statistics
   - LRU cache with TTL (5 minutes) for performance optimization
   - Cache invalidation support via `invalidate_hover_cache()`
   - Cache trimming to max size (1000 entries)

3. **Context Module Updates** (`src/context/__init__.py`)
   - Exported `get_graph_json`, `get_hover_payload`, and `invalidate_hover_cache`

4. **Testing**
   - Unit tests (`tests/test_graph_provider.py`) - 17 tests, all passing
     - Graph JSON format validation
     - Node and edge format validation
     - Depth filtering (0, 1, 2 levels)
     - Scope filtering (topic ID)
     - Relation filtering (parent-child, belongs-to)
     - Content accuracy (summaries, mastery, edges)
     - Edge cases (empty database, invalid scope, depth zero)
   - Unit tests (`tests/test_hover_provider.py`) - 15 tests, all passing
     - Hover payload structure validation
     - Caching (cache hit, invalidation, clear all)
     - Content accuracy (event snippets, truncation, statistics)
     - Error handling (invalid node ID, unknown type, nonexistent entities)
     - Performance (single node, multiple nodes)
   - Integration tests (`tests/test_graph_hover_integration.py`) - 6 tests, all passing
     - Combined graph and hover operations
     - Hover latency requirement validation (<200ms for 500 nodes)
     - Graph with events integration
     - Filtered graph and hover
     - Cache performance improvement
     - Graph JSON schema validation

5. **Documentation**
   - Updated `docs/index/index.md` with new graph and hover provider files

### ✅ Block A (Interface), PR #3: UI Model Definitions (COMPLETED)

1. **UI Models** (`src/interface_common/models.py`)
   - `GraphNode` - Graph node model for knowledge tree visualization
     - Supports topic, skill, and event node types
     - Type-specific fields (summary, mastery, content, etc.)
     - Validation for node types and mastery values (0.0-1.0)
   - `GraphEdge` - Graph edge model for relationships between nodes
     - Source, target, type, and label fields
   - `HoverPayload` - Discriminated union for hover payloads
     - `TopicHoverPayload` - Topic hover payload with summary, event_count, open_questions, event_snippet, statistics
     - `SkillHoverPayload` - Skill hover payload with mastery, evidence_count, topic_id, event_snippet, statistics
     - `EventHoverPayload` - Event hover payload with content, event_type, actor, topics, skills, timestamps, statistics
   - `ChatMessage` - Chat message model for tutor chat interface
     - Role (student/tutor/system), content, timestamp, session_id, event_id
   - `CommandResult` - Command result model for facade operations
     - Success status, result data, error information, duration
     - `from_facade_response()` class method for creating from facade responses
   - Supporting models: `EventSnippet`, `HoverStatistics`

2. **Interface Common Module Updates** (`src/interface_common/__init__.py`)
   - Exported all new models for use by GUI front-ends

3. **Testing** (`tests/test_interface_models.py`)
   - Unit tests for GraphNode (8 tests)
     - Topic, skill, and event node creation
     - Serialization, deserialization, round-trip
     - Validation error handling (invalid types, invalid mastery values)
   - Unit tests for GraphEdge (3 tests)
     - Edge creation, serialization, round-trip
   - Unit tests for HoverPayload (6 tests)
     - Topic, skill, and event hover payload creation
     - Serialization, round-trip
     - Validation error handling (invalid mastery values)
   - Unit tests for ChatMessage (3 tests)
     - Message creation, serialization, round-trip
   - Unit tests for CommandResult (6 tests)
     - Success and failure result creation
     - `from_facade_response()` method testing
     - Serialization, round-trip
   - Model validation tests (4 tests)
     - Graph provider output matches GraphNode
     - Graph provider output matches GraphEdge
     - Hover provider output matches HoverPayload
     - Facade output matches CommandResult
   - All 30 tests passing

4. **Documentation**
   - Updated `docs/index/index.md` with new models file

### ✅ Block C (GUI Framework), PR #10: Frontend Scaffolding (COMPLETED)

1. **React + TypeScript + Vite Project** (`frontend/`)
   - Initialized React + TypeScript + Vite project structure
   - Configured build tooling with Vite
   - Set up TypeScript configuration files

2. **Tailwind CSS Configuration**
   - Set up Tailwind CSS with PostCSS
   - Updated global CSS with Tailwind directives
   - Configured Tailwind for React components

3. **React Router Setup**
   - Configured React Router with routes for Chat, Console, Review, Context, KnowledgeTree
   - Default redirect from `/` to `/chat`
   - Navigation preserves app state

4. **Layout Components** (`frontend/src/components/`)
   - `Layout.tsx` - Main layout wrapper with header, sidebar, content area, and footer
   - `Header.tsx` - Top menu bar with navigation links
   - `Sidebar.tsx` - Collapsible navigation shortcuts
   - `StatusFooter.tsx` - API health, database path, and index state

5. **Placeholder Pages** (`frontend/src/pages/`)
   - `Home.tsx` - Redirects to Chat
   - `Chat.tsx` - Placeholder for Tutor Chat (PR #11)
   - `Console.tsx` - Placeholder for Command Console (PR #11)
   - `Review.tsx` - Placeholder for Review Queue
   - `Context.tsx` - Placeholder for Context Inspector
   - `KnowledgeTree.tsx` - Placeholder for Knowledge Tree (PR #12)
   - Each page includes minimal API calls for validation

6. **API Client** (`frontend/src/lib/api.ts`)
   - Centralized API client with base URL configuration
   - Environment variable support (`VITE_API_BASE_URL`)
   - Defaults to `http://localhost:8000/api`
   - Error handling for API requests

7. **Testing Infrastructure** (`frontend/src/test/`)
   - Vitest + React Testing Library setup
   - Test setup file with jest-dom matchers
   - Tests for App component (2 tests)
   - Tests for Layout component (1 test)
   - Tests for API client (4 tests)
   - All 7 tests passing

8. **Documentation**
   - Updated `docs/index/index.md` with all frontend files
   - Inline documentation in all components

### ✅ Block C (GUI Framework), PR #9: FastAPI Backend for Tauri (COMPLETED)

1. **FastAPI Application** (`backend/api/main.py`)
   - FastAPI app with lifespan management for facade initialization
   - CORS middleware configured for localhost-only policy (localhost, 127.0.0.1)
   - WebSocket support for live updates
   - Router registration for all endpoints
   - Root and health check endpoints

2. **Facade Access** (`backend/api/facade.py`)
   - Facade instance access module to avoid circular imports
   - `set_facade()` and `get_facade()` functions for facade management

3. **API Routes** (`backend/api/routes/`)
   - `db.py` - Database endpoints: GET `/api/db/check`, POST `/api/db/init`
   - `index.py` - Index endpoints: POST `/api/index/build`, GET `/api/index/status`, POST `/api/index/search`
   - `ai.py` - AI endpoints: GET `/api/ai/routes`, POST `/api/ai/test`
   - `chat.py` - Chat endpoints: POST `/api/chat/start`, POST `/api/chat/resume`, GET `/api/chat/list`, POST `/api/chat/turn`
   - `graph.py` - Graph endpoint: GET `/api/graph` (with scope, depth, relation, include_events filters)
   - `hover.py` - Hover endpoint: GET `/api/hover/{node_id}`
   - `review.py` - Review endpoint: GET `/api/review/next` (with limit, topic, mastery filters)
   - `import_route.py` - Import endpoints: POST `/api/import/transcript`, POST `/api/import/transcript/upload`
   - `refresh.py` - Refresh endpoint: POST `/api/refresh/summaries` (with topic, since, force filters)
   - `progress.py` - Progress endpoint: GET `/api/progress/summary` (with start, end, days, topic, format filters)
   - `websocket.py` - WebSocket endpoint: `/ws` (supports ping/pong, subscribe, error handling)

4. **Response Models**
   - All endpoints return Pydantic models (CommandResult, HoverPayload, etc.)
   - Error handling with proper HTTP status codes (400 for validation, 500 for server errors)
   - Facade exceptions caught and converted to HTTP exceptions

5. **Dependencies** (`requirements.txt`)
   - Added fastapi, uvicorn[standard], websockets, python-multipart

6. **Testing** (`tests/test_api.py`)
   - Unit and integration tests for all endpoints (23 tests, all passing)
   - Tests for root endpoints (root, health)
   - Tests for database endpoints (check, init)
   - Tests for index endpoints (status, build)
   - Tests for AI endpoints (routes, test)
   - Tests for chat endpoints (start, list)
   - Tests for graph endpoints (get, with filters)
   - Tests for hover endpoints (topic, invalid node ID)
   - Tests for review endpoints (next)
   - Tests for import endpoints (invalid path)
   - Tests for refresh endpoints (summaries)
   - Tests for progress endpoints (summary)
   - Tests for WebSocket endpoints (connection, subscribe, invalid message)
   - Tests for error handling (invalid endpoint, CORS)

7. **Documentation**
   - Updated `docs/index/index.md` with all new backend API files

### ✅ Block D, PR #10: Performance Tracking (COMPLETED)

1. **Performance Analysis** (`src/analysis/performance.py`)
   - SkillDelta and TopicDelta dataclasses for structured delta representation
   - ProgressReport dataclass with summary statistics, skill deltas, and topic deltas
   - reconstruct_skill_state_at_time function to reconstruct historical skill states by replaying events
   - calculate_skill_deltas function to compute mastery deltas between two timestamps
   - aggregate_topic_deltas function to aggregate skill deltas by topic
   - generate_progress_report function to generate comprehensive progress reports
   - report_to_json function for JSON report formatting
   - report_to_markdown function for Markdown report formatting
   - create_chart_data function for chart visualization data preparation

2. **CLI Commands** (`src/cli/progress.py`)
   - `progress summary` - Generate performance report with delta calculations
   - Flexible timestamp parsing (ISO format, relative times like "7 days ago", "30 days ago")
   - Multiple output formats (json, markdown, table)
   - Chart visualization option with --chart flag showing top skills by delta
   - Filtering options (topic, time range)
   - Rich table output showing summary statistics, topic summaries, and top skills by delta

3. **Testing** (`tests/test_analysis.py`)
   - Unit tests for state reconstruction (3 tests)
   - Unit tests for delta calculation (3 tests)
   - Unit tests for topic aggregation (1 test)
   - Unit tests for report generation (2 tests)
   - Unit tests for report formatting (2 tests)
   - Unit tests for chart data (1 test)
   - Unit tests for dataclass creation (2 tests)
   - All 14 tests passing

### ✅ Block D, PR #9: Review Scheduler (COMPLETED)

1. **Review Scheduler** (`src/scheduler/review.py`)
   - ReviewItem class for review items with priority scores
   - Decay-based mastery model with exponential decay (tau = 30 days, grace period = 7 days)
   - Review priority computation combining p_mastery and days_since_review
   - get_next_reviews function to retrieve and prioritize skills for review
   - record_review_outcome function to record outcomes as assessment Events and update skill state

2. **Configuration** (`src/config.py`)
   - REVIEW_DECAY_TAU_DAYS (default: 30.0)
   - REVIEW_GRACE_PERIOD_DAYS (default: 7.0)
   - REVIEW_DEFAULT_LIMIT (default: 10)

3. **CLI Commands** (`src/cli/review.py`)
   - `review next` - Get prioritized review list with rich table output
   - Filtering options (topic, mastery range, limit)
   - Shows: Skill ID, Topic, Current Mastery, Decayed Mastery, Days Since Review, Priority Score

4. **Testing** (`tests/test_scheduler.py`)
   - Unit tests for decay model (6 tests)
   - Unit tests for priority computation (5 tests)
   - Integration tests for review retrieval (6 tests)
   - Integration tests for outcome recording (4 tests)
   - Unit test for ReviewItem class (1 test)
   - All 22 tests passing

### ✅ Block C, PR #8: Update Propagation & Summarization (COMPLETED)

1. **Summarizers Module** (`src/summarizers/update.py`)
   - Batch summarization with aggregation logic
   - Versioning system with summary_version counter and last_summarized_at timestamp
   - Unprocessed event detection using last_summarized_at
   - Topic summary and skill state updates with audit logging

2. **Audit Logging** (`src/storage/schema.sql`)
   - audit_logs table tracking all summarization operations
   - Tracks: log_type, topic_id, skill_id, event_ids, summary_version, model_version, tokens_used, status, error_message
   - Queryable by topic, date range, status

3. **APScheduler Background Job** (`src/summarizers/scheduler.py`)
   - Background scheduler for write-time summarization
   - Configurable interval (default: 300 seconds / 5 minutes)
   - Processes topics with unprocessed events in batches
   - Respects max concurrent topics limit

4. **Write-time Hooks** (`src/summarizers/hooks.py`)
   - Hooks to trigger summarization after event creation
   - Non-blocking, optional via configuration
   - Integrated into Database.insert_event()

5. **Configuration** (`src/config.py`)
   - SUMMARIZATION_BATCH_SIZE (default: 10)
   - SUMMARIZATION_INTERVAL_SECONDS (default: 300)
   - SUMMARIZATION_MAX_CONCURRENT_TOPICS (default: 3)
   - SUMMARIZATION_ENABLED (default: true)

6. **CLI Commands** (`src/cli/refresh.py`)
   - `refresh summaries` - Refresh topic summaries with filtering options (--topic, --since, --force)
   - `refresh status` - Show topics needing refresh
   - Rich table output showing results and statistics

7. **Testing** (`tests/test_summarizers.py`)
   - Unit tests for audit logging, versioning, batch processing
   - Integration tests for scheduler and refresh functions
   - Tests for 100-event batch processing (one summarization per topic)
   - All tests passing

### ✅ Block C, PR #7: Transcript Importer (COMPLETED)

1. **Transcript Parsers** (`src/ingestion/transcripts.py`)
   - Parsers for .txt, .md, and .json formats
   - Actor/speaker inference from transcript labels
   - Timestamp parsing (ISO format, date strings, file modification time fallback)
   - Flexible JSON structure support (simple objects, arrays of messages)

2. **AI Classification & Summarization**
   - AI-based topic/skill classification using gpt-4o-mini
   - Manual tagging support (topics/skills via CLI)
   - Event summarization with context from recent events
   - Topic summaries updated/created automatically
   - Skill states updated/created automatically

3. **Embedding & Indexing**
   - OpenAI embedding function with fallback to stub
   - Integration with existing chunking and FAISS indexing pipeline
   - Chunks stored in event_chunks table with embeddings

4. **Provenance Tracking**
   - Comprehensive metadata: source_file_path, import_timestamp, import_method, import_model_version, classification_confidence

5. **CLI Commands** (`src/cli/import_cmd.py`)
   - `import transcript <file>` - Import single transcript file
   - `import batch <directory>` - Batch import multiple files
   - Options for manual topics/skills, database path, stub embeddings

6. **Testing** (`tests/test_transcript_import.py`)
   - Unit tests for parsers, actor inference, timestamp parsing
   - Integration tests for full import flow
   - Tests for topic/skill state updates
   - All tests passing

### ✅ Block A, PR #1: Define Data Models and Schemas (COMPLETED)

### ✅ Block A, PR #2: Database I/O Layer (COMPLETED)

### ✅ Block A, PR #3: Vector Store & Embedding Pipeline (COMPLETED)

1. **Schema Update** (`src/storage/schema.sql`)
   - Added `event_chunks` table for multi-chunk events and embeddings

2. **FAISS Index** (`src/retrieval/faiss_index.py`)
   - Flat IP index with cosine via normalization
   - Add/search/persist utilities

3. **Embedding Pipeline** (`src/retrieval/pipeline.py`)
   - Token-aware (tiktoken) or char-heuristic chunking with overlap
   - Batched embedding pipeline and SQLite upsert for chunks
   - Index persistence to disk

4. **CLI** (`src/cli/index.py`, `src/cli/main.py`)
   - `index build`, `index status`, `index search`

5. **Config** (`src/config.py`)
   - Added CHUNK_TOKENS/OVERLAP, BATCH_EMBED_SIZE, USE_TIKTOKEN flags

6. **Tests** (`tests/`)
   - Unit tests for FAISS and chunking
   - Integration tests for pipeline and hybrid retrieval
   - All tests passing

1. **Database I/O Layer** (`src/storage/db.py`)
   - Database context manager with transaction safety
   - CRUD operations for all entities
   - Custom exception classes (DatabaseError, ConstraintViolationError)
   - Database initialization function
   - Health check utilities

2. **Query Wrappers** (`src/storage/queries.py`)
   - Event filtering by topic, time, skill, and event type
   - FTS5 full-text search API
   - Skill filtering by topic and mastery range
   - Topic hierarchy queries
   - SkillState persistence helpers with evidence updates

3. **CLI Structure** (`src/cli/`)
   - Minimal CLI with typer and rich
   - `db check` command for health checks
   - `db init` command for database initialization

4. **Testing** (`tests/`)
   - Unit tests for database I/O operations
   - Integration tests for query operations
   - All tests passing

### ✅ Block A, PR #1: Define Data Models and Schemas (COMPLETED)

1. **Pydantic Models** (`src/models/base.py`)
   - All 6 core models implemented and validated
   - Proper type hints and validation rules
   - JSON serialization support

2. **SQLite Schema** (`src/storage/schema.sql`)
   - All tables created with proper constraints
   - Hierarchical topic support via foreign keys
   - FTS5 full-text search table with triggers
   - Comprehensive indexes for performance
   - Embedding storage as BLOB

3. **Serialization Utilities** (`src/utils/serialization.py`)
   - Model-to-JSON conversion
   - JSON list/dict serialization
   - Datetime serialization
   - Embedding binary serialization

4. **Configuration** (`src/config.py`)
   - Environment variable support
   - Database path configuration
   - OpenAI API configuration
   - Default paths and constants

5. **Testing** (`tests/`)
   - Unit tests for models, serialization, database
   - Integration tests for database operations
   - All tests passing

6. **Stub Data Generator** (`scripts/generate_stub_data.py`)
   - Generates minimal valid test data
   - Creates sample events, topics, skills, goals, commitments

7. **Documentation** (`README.md`)
   - Schema documentation
   - Setup instructions
   - Project structure

## What's Left to Build

### 🔴 Block A (Interface): Backend Integration Layer

#### PR #1: Unified GUI–Backend Facade ✅
- [x] Implement `app_facade.py` with async wrappers for CLI-equivalent commands
- [x] Wrap DB, Index, AI, and Chat functions from CLI
- [x] Add error handling and timeout guards for LLM and FAISS operations
- [x] Expose async `run_command(name, args)` dispatcher for GUI use
- [x] Add logging hooks for all GUI-initiated operations
- [x] Unit tests - all facade methods execute CLI-equivalent functions
- [x] Unit tests - exceptions correctly caught and serialized for UI display
- [x] Integration tests - GUI prototype can call `app_facade.chat_turn()` successfully
- [x] Integration tests - LLM calls run asynchronously without blocking

#### PR #2: Graph + Hover Providers
- [ ] Implement `graph_provider.py` to return DAG JSON from database
- [ ] Implement `hover_provider.py` for per-node summaries and statistics
- [ ] Integrate `networkx` DAG traversal utilities
- [ ] Add query filters for `scope`, `depth`, and `relation`
- [ ] Cache hover payloads to minimize repeated lookups
- [ ] Unit and integration tests

#### PR #3: UI Model Definitions
- [ ] Create shared Pydantic models for `GraphNode`, `GraphEdge`, `HoverPayload`, `ChatMessage`, and `CommandResult`
- [ ] Define schema contracts used by both GUI front-ends
- [ ] Add JSON serialization helpers
- [ ] Unit tests

### ✅ Block B, PR #6: Context Composition Engine (COMPLETED)

1. **Context Assembler** (`src/context/assembler.py`)
   - Dynamic token allocation (new chat: all to memory; grows to 60% history cap)
   - Hybrid retrieval (FAISS + recency + FTS) with configurable weights
   - MMR (Maximal Marginal Relevance) for diversity
   - Retrieval decision logging for auditability

2. **Context Filters** (`src/context/filters.py`)
   - Recency decay with exponential decay (tau = 7 days)
   - Hybrid score computation (FAISS 0.6, recency 0.3, FTS 0.1)
   - Filtering by score threshold, topic overlap, max per event/topic

3. **Integration** (`src/interface/tutor_chat.py`)
   - Integrated assembler into chat flow
   - Extracts session topics for filtering
   - Composes context before each tutor reply

4. **ChunkRecord Model** (`src/models/base.py`)
   - Added ChunkRecord Pydantic model for chunk storage

5. **Testing** (`tests/`)
   - Unit tests for filters (13 tests)
   - Unit tests for assembler (6 tests)
   - All tests passing

### ✅ Block B, PR #5: Tutor Chat Interface (TUI) (COMPLETED)

1. **Chat Interface** (`src/interface/tutor_chat.py`)
   - Interactive TUI with typer + rich
   - Session management (start, resume, list)
   - Upload handling with immediate summarization
   - LLM-suggested session titles

2. **Chat Utilities** (`src/interface/utils.py`)
   - History building with token budgeting
   - Transcript stitching for summarization

3. **CLI** (`src/cli/chat.py`)
   - `chat start` - Start new session
   - `chat resume` - Resume existing session
   - `chat list` - List recent sessions

### ✅ Block B, PR #4: AI Orchestration Layer (COMPLETED)

1. **Model Router** (`src/services/ai/router.py`)
   - Task-based routing (SUMMARIZE_EVENT, CLASSIFY_TOPICS, UPDATE_SKILL, CHAT_REPLY)
   - Configurable routes with fallback chains
   - ModelRoute with token budgets and capabilities

2. **AI Client** (`src/services/ai/client.py`)
   - OpenAI API integration with retry and rate limiting
   - Token counting and truncation
   - Error categorization and handling
   - Structured output parsing

3. **Prompt Templates** (`src/services/ai/prompts.py`)
   - System prompts for all tasks
   - Prompt building functions
   - JSON response parsing with schema validation

4. **Utilities** (`src/services/ai/utils.py`)
   - Retry with exponential backoff
   - Rate limiter (token bucket)
   - Token counting (tiktoken or heuristic)
   - Context truncation utilities

5. **CLI** (`src/cli/ai.py`)
   - `ai routes` - Show routing configuration
   - `ai test` - Test AI functionality (summarize, classify, chat)

6. **Testing** (`tests/`)
   - Unit tests for router, prompts, utils (35 tests)
   - Integration tests with mocked API (7 tests)
   - All tests passing

### 🔴 Block A: Core Data Infrastructure (COMPLETED)

### 🟢 Block B: AI Tutor Chat System

#### PR #4: AI Orchestration Layer
- [ ] Model routing registry (nano/classifier/4o)
- [ ] Standardized prompt interface
- [ ] Retry, rate limiting, error handling
- [ ] Summarization and classification functions
- [ ] Unit and integration tests

#### PR #5: Tutor Chat Interface (TUI)
- [ ] Text-based TUI using typer + rich
- [ ] Conversational history buffer
- [ ] Event logging for each turn
- [ ] Loading indicators and summaries
- [ ] Session save/resume
- [ ] Unit and integration tests

#### PR #6: Context Composition Engine
- [ ] Retrieval pipeline (SQL + FAISS)
- [ ] Relevance scoring and recency decay
- [ ] Dynamic context slice and prompt assembly
- [ ] Token budget management
- [ ] Retrieval decision logging
- [ ] Unit and integration tests

### 🔵 Block C: Transcript Ingestion Pipeline

#### PR #7: Transcript Importer ✅
- [x] Parse .txt/.md/.json transcripts
- [x] Tag with topics, skills, timestamps
- [x] Auto-summarize and embed events
- [x] Update skill and topic summaries
- [x] Log provenance and model version
- [x] Unit and integration tests

#### PR #8: Update Propagation & Summarization ✅
- [x] Write-time summarization job
- [x] TopicSummary and SkillState delta updates
- [x] Background job via APScheduler
- [x] Summarization audit logs
- [x] CLI command: `refresh summaries`
- [x] Unit and integration tests

### 🟡 Block D: Spaced Repetition & Mastery Tracking

#### PR #9: Review Scheduler ✅
- [x] Decay-based mastery model
- [x] Review priority computation (recency + p_mastery)
- [x] CLI: `review next`
- [x] Outcome recording to Event objects
- [x] Mastery delta updates
- [x] Unit and integration tests

#### PR #10: Performance Tracking ✅
- [x] Delta calculator (p_mastery between timestamps)
- [x] CLI: `progress summary`
- [x] JSON and markdown report generation
- [x] Plotting option using rich charts
- [x] Reports aggregate all skills (single-student model)
- [x] Unit and integration tests

## Current Status

### Overall Progress
- **Block A (Core)**: 3/3 PRs complete (100%)
- **Block B**: 3/3 PRs complete (100%)
- **Block C**: 2/2 PRs complete (100%)
- **Block D**: 2/2 PRs complete (100%)
- **Block A (Interface)**: 3/3 PRs complete (100%)
- **Block C (GUI Framework)**: 2/4 PRs complete (50%)
- **Total**: 13/17 PRs complete (76%)

### Timeline
- **Block A**: ~30/30 hours complete (100%)
- **Block B**: ~40/40 hours complete (100%)
- **Block C**: ~25/25 hours complete (100%)
- **Block D**: ~25/25 hours complete (100%)
- **Total**: ~120/120 hours complete (100%)

## Known Issues

None currently - PR #1 is complete and tested

## Validation Status

### PR #1 Validation ✅
- [x] Local database initializes on fresh clone
- [x] Sample data populates without error
- [x] All models pass Pydantic validation
- [x] All unit tests pass
- [x] All integration tests pass
- [x] No linter errors

## Next Milestones

1. **Complete Block A** (PR #2 and #3) - Foundation for all other blocks
2. **Complete Block B** (PR #4, #5, #6) - Enable user interaction
3. **Complete Blocks C and D** (can run in parallel after Block B)

## Success Metrics Progress

### Primary Goals
- [ ] AI can retrieve and summarize sessions across ≥5 topics
- [ ] Context persistence verified across ≥3 restarts
- [x] Spaced repetition algorithm generates review lists accurately
- [x] Transcripts integrate into topic summaries automatically
- [x] User can query performance deltas between timestamps

### Secondary Goals
- [ ] Mastery tracking via lightweight Bayesian update or Elo model
- [ ] Context visualizer (CLI heatmap of reviewed topics)
- [ ] Plugin-style API for external data ingestion

