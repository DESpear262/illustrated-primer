# Active Context: AI Tutor Proof of Concept

## Current Work Focus

### Completed (Desktop Packaging & Distribution)
1. ✅ Established repeatable desktop build pipeline:
   - `scripts/build_backend.spec` revised to include FastAPI, Rich, Typer, and other runtime deps.
   - `scripts/build_python_backend.ps1` and `scripts/build_all.ps1` now clean previous artifacts, rebuild the backend, copy it into `frontend/src-tauri/resources`, and run `npm run tauri:build`.
2. ✅ Hardened backend bundle startup:
   - `backend/api/main.py` auto-initializes the SQLite/FAISS data directory, adds custom CORS handling for `tauri://` origins, and keeps the FastAPI facade wiring intact.
   - `frontend/src-tauri/src/commands.rs` launches the bundled backend with `AI_TUTOR_DATA_DIR` + logging-friendly stdout/stderr capture.
3. ✅ Added desktop logging + config awareness:
   - `frontend/src-tauri/src/lib.rs` configures `tauri-plugin-log` to mirror output to `%APPDATA%\AI Tutor\logs\app.log`, stdout, and the webview console.
   - `src/config.py` detects bundled execution and points data paths to `%APPDATA%\AI Tutor\data`.
4. ✅ Verified end-to-end build artifacts:
   - `frontend\src-tauri\target\release\ai-tutor.exe`
   - `frontend\src-tauri\target\release\bundle\nsis\AI Tutor_0.1.0_x64-setup.exe`
   - `frontend\src-tauri\target\release\bundle\msi\AI Tutor_0.1.0_x64_en-US.msi`

**Block C (GUI Framework): UI Style Guide Implementation** ✅ **COMPLETED**

## Recent Changes

### Completed (UI Style Guide Implementation - Block C)
1. ✅ Implemented comprehensive UI style guide overhaul:
   - Added Google Fonts (Spectral SC for headlines, Source Serif 4 for body, JetBrains Mono for code)
   - Created CSS variable system for light/dark themes with color tokens (ink, parchment, brass, verdigris, navy, garnet, smoke)
   - Updated Tailwind config with custom color palette, spacing, typography, and shadows
   - Implemented component styles: cards, buttons, inputs, chat bubbles matching style guide
2. ✅ Updated all layout components:
   - Layout: Parchment background with brass accents
   - Header: Parchment background, brass borders, verdigris hover states
   - Sidebar: Parchment background, verdigris active states
   - StatusFooter: Updated status badges with new color scheme
3. ✅ Updated Chat page with new styling:
   - Reorganized layout: chat window in center (flex-1), sessions sidebar on right (192px fixed width)
   - AI chat bubbles: parchment background with brass left stripe
   - User chat bubbles: navy background with white text
   - Improved spacing and typography for readability
4. ✅ Updated GraphView component with style guide Cytoscape styling:
   - Topics: rounded rectangles, parchment fill (#F1EAD5), brass border (#B08D57)
   - Skills: circles, white fill, mastery rings (garnet <0.4, brass 0.4-0.7, verdigris ≥0.7)
   - Artifacts: hexagons, pale navy fill (#E6EAF4)
   - Edges: brass solid (contains), navy dashed (prereq), verdigris dotted (applies_in)
5. ✅ Updated HoverCard component with card styling matching style guide
6. ✅ Updated Console page with new styling (cards, buttons, inputs)
7. ✅ Updated KnowledgeTree page with new styling (controls, filters)
8. ✅ Updated placeholder pages (Review, Context) with new styling
9. ✅ All components now use "neo-Victorian minimalism" aesthetic with parchment + brass + ink theme

### Completed (PR #12 - Block C)
1. ✅ Installed Cytoscape.js and cytoscape-elk dependencies
2. ✅ Extended API client with graph and hover endpoints:
   - `getGraph()` method with filtering parameters (scope, depth, relation, include_events)
   - `getHover()` method for node hover payloads
   - TypeScript interfaces for GraphData, GraphNode, GraphEdge, HoverPayload
3. ✅ Created GraphView component with Cytoscape.js integration:
   - Node styling (topics: blue, skills: green with mastery intensity, events: gray)
   - Edge styling (parent-child: solid blue, belongs-to: dashed green, evidence: dotted gray)
   - ELK layout integration (fallback to breadthfirst if ELK unavailable)
   - Search filtering with node highlighting
   - Collapse/expand functionality for hierarchical nodes
   - Zoom controls (zoom in, zoom out, fit, reset) with zoom level display
   - Hover tooltips with 200ms debounce
   - Node click navigation to Context page
4. ✅ Created HoverCard component for hover tooltips:
   - Topic payloads (summary, event count, last event)
   - Skill payloads (mastery percentage, evidence count, last evidence)
   - Event payloads (content, type, actor, created date)
   - Smart positioning to avoid viewport edges
5. ✅ Updated KnowledgeTree page with full implementation:
   - Graph loading with filters (scope, depth, relation, include_events)
   - Search functionality with real-time filtering
   - Collapse/expand controls (expand all, collapse all)
   - Zoom controls with current zoom display
   - WebSocket real-time updates for graph refresh
   - Navigation to Context page on node click
   - Hover caching for performance
6. ✅ Added performance optimizations:
   - Debounced hover requests (200ms delay)
   - Hover payload caching
   - Viewport-based rendering (handled by Cytoscape.js)
7. ✅ Created comprehensive test suite:
   - Tests for GraphView component (4 tests)
   - Tests for HoverCard component (4 tests)
   - All 21 tests passing
8. ✅ Updated file index documentation

### Completed (PR #11 - Block C)
1. ✅ Implemented Chat interface with session management:
   - Message display with student/tutor distinction
   - Session list sidebar with resume functionality
   - Message input with Enter to send
   - Loading states with typing indicators
   - Context chunks display on hover for AI messages
   - Export/delete session functionality
   - Persistent logs per session (localStorage)
2. ✅ Implemented Command Console with form-based UI:
   - Tabbed interface (DB, Index, AI, Chat)
   - Form-based commands for all CLI actions:
     - Database: Check, Init
     - Index: Build, Status, Search
     - AI: Routes, Test
     - Chat: Start, Resume, List
   - Persistent logs panel with command history
   - Structured output display (JSON/tables)
3. ✅ Added toast notifications using react-hot-toast:
   - Success/error notifications
   - Integrated into App component
4. ✅ Created WebSocket hook for live updates:
   - Connection management with auto-reconnect
   - Message handling and subscription support
5. ✅ Created LocalStorage hook for persistent data:
   - Typed localStorage access with JSON serialization
   - Used for chat logs and console logs
6. ✅ Extended API client with chat and console methods:
   - Chat endpoints (start, resume, list, turn)
   - Database endpoints (check, init)
   - Index endpoints (build, status, search)
   - AI endpoints (routes, test)
7. ✅ Added error handling and retry logic:
   - Error toasts for failed requests
   - Manual retry for chat turns
   - Error display in console logs
8. ✅ Created comprehensive test suite:
   - Tests for Chat component (3 tests)
   - Tests for Console component (3 tests)
   - All 13 tests passing
9. ✅ Updated file index documentation

### Completed (PR #10 - Block C)
1. ✅ Initialized React + TypeScript + Vite project structure
2. ✅ Set up Tailwind CSS with PostCSS configuration
3. ✅ Created React Router setup with routes for Chat, Console, Review, Context, KnowledgeTree
4. ✅ Created Layout component with header, sidebar, and status footer:
   - `Header.tsx` - Top menu bar with navigation links
   - `Sidebar.tsx` - Collapsible navigation shortcuts
   - `StatusFooter.tsx` - API health, database path, and index state
   - `Layout.tsx` - Main layout wrapper
5. ✅ Created placeholder page components for all routes:
   - `Home.tsx` - Redirects to Chat
   - `Chat.tsx` - Placeholder for Tutor Chat (PR #11)
   - `Console.tsx` - Placeholder for Command Console (PR #11)
   - `Review.tsx` - Placeholder for Review Queue
   - `Context.tsx` - Placeholder for Context Inspector
   - `KnowledgeTree.tsx` - Placeholder for Knowledge Tree (PR #12)
6. ✅ Set up API client (`lib/api.ts`) with base URL configuration and environment variable support
7. ✅ Set up testing infrastructure:
   - Vitest + React Testing Library
   - Test setup file with jest-dom matchers
   - Tests for App, Layout, and API client (7 tests, all passing)
8. ✅ Updated file index documentation

### Completed (PR #9 - Block C)
1. ✅ Added FastAPI dependencies to `requirements.txt` (fastapi, uvicorn[standard], websockets, python-multipart)
2. ✅ Created `backend/api/main.py` with FastAPI application:
   - Lifespan management for facade initialization
   - CORS middleware configured for localhost-only policy
   - WebSocket support
   - Router registration for all endpoints
3. ✅ Created `backend/api/facade.py` for facade instance access (avoids circular imports)
4. ✅ Created route modules in `backend/api/routes/`:
   - `db.py` - Database endpoints (check, init)
   - `index.py` - Index endpoints (build, status, search)
   - `ai.py` - AI endpoints (routes, test)
   - `chat.py` - Chat endpoints (start, resume, list, turn)
   - `graph.py` - Graph endpoint (get graph JSON)
   - `hover.py` - Hover endpoint (get hover payload)
   - `review.py` - Review endpoint (next)
   - `import_route.py` - Import endpoints (transcript import, file upload)
   - `refresh.py` - Refresh endpoint (summaries refresh)
   - `progress.py` - Progress endpoint (summary)
   - `websocket.py` - WebSocket endpoint (live updates)
5. ✅ All endpoints return Pydantic models (CommandResult, HoverPayload, etc.)
6. ✅ Error handling with proper HTTP status codes (400 for validation, 500 for server errors)
7. ✅ WebSocket endpoint supports ping/pong, subscribe, and error handling
8. ✅ Created comprehensive test suite (`tests/test_api.py`) - 23 tests, all passing:
   - Root endpoints (root, health)
   - Database endpoints (check, init)
   - Index endpoints (status, build)
   - AI endpoints (routes, test)
   - Chat endpoints (start, list)
   - Graph endpoints (get, with filters)
   - Hover endpoints (topic, invalid node ID)
   - Review endpoints (next)
   - Import endpoints (invalid path)
   - Refresh endpoints (summaries)
   - Progress endpoints (summary)
   - WebSocket endpoints (connection, subscribe, invalid message)
   - Error handling (invalid endpoint, CORS)
9. ✅ Updated file index documentation

### Completed (PR #3 - Interface Block A)
1. ✅ Created `src/interface_common/models.py` with shared Pydantic models:
   - `GraphNode` - Graph node model for knowledge tree visualization (topic, skill, event)
   - `GraphEdge` - Graph edge model for relationships between nodes
   - `HoverPayload` - Discriminated union for hover payloads (TopicHoverPayload, SkillHoverPayload, EventHoverPayload)
   - `ChatMessage` - Chat message model for tutor chat interface
   - `CommandResult` - Command result model for facade operations
   - Supporting models: `EventSnippet`, `HoverStatistics`
2. ✅ Updated `src/interface_common/__init__.py` to export all new models
3. ✅ Created comprehensive unit tests (`tests/test_interface_models.py`) - 30 tests, all passing:
   - Model validation (creation, serialization, deserialization, round-trip)
   - Validation error handling (invalid types, invalid values)
   - Facade output validation (graph_provider, hover_provider, facade outputs match models)
4. ✅ Updated file index documentation

### Completed (PR #2 - Interface Block A)
1. ✅ Created `src/context/graph_provider.py` with DAG JSON generation from database
2. ✅ Implemented `get_graph_json()` function with:
   - Cytoscape.js format output (nodes/edges)
   - Networkx DAG traversal utilities
   - Filtering by scope (topic ID), depth (hierarchy level), and relation type
   - Support for topics, skills, and optional event nodes
   - Parent-child, belongs-to, and evidence edge types
3. ✅ Created `src/context/hover_provider.py` with:
   - `get_hover_payload()` function for per-node summaries and statistics
   - Support for topic, skill, and event node types
   - Hover payload includes: title, mastery (for skills), last evidence, summary, statistics, event snippets
   - LRU cache with TTL (5 minutes) for performance optimization
   - Cache invalidation support via `invalidate_hover_cache()`
4. ✅ Updated `src/context/__init__.py` to export graph and hover provider functions
5. ✅ Created comprehensive unit tests (`tests/test_graph_provider.py`) - 17 tests, all passing
6. ✅ Created comprehensive unit tests (`tests/test_hover_provider.py`) - 15 tests, all passing
7. ✅ Created integration tests (`tests/test_graph_hover_integration.py`) - 6 tests, all passing
   - Tests combined FAISS + SQLite queries
   - Validates <200ms hover latency requirement for 500 nodes
   - Tests graph JSON schema validation
8. ✅ Updated file index documentation

### Completed (PR #1 - Interface Block A)
1. ✅ Created `src/interface_common/` module with `__init__.py`, `exceptions.py`, and `app_facade.py`
2. ✅ Implemented custom exception classes (FacadeError, FacadeTimeoutError, FacadeDatabaseError, FacadeIndexError, FacadeAIError, FacadeChatError) with JSON serialization
3. ✅ Created AppFacade class with async wrappers for all CLI commands:
   - Database: `db_check()`, `db_init()`
   - Index: `index_build()`, `index_status()`, `index_search()`
   - AI: `ai_routes()`, `ai_test()`
   - Chat: `chat_start()`, `chat_resume()`, `chat_list()`, `chat_turn()`
   - Review: `review_next()`
   - Import: `import_transcript()`
   - Refresh: `refresh_summaries()`
   - Progress: `progress_summary()`
4. ✅ Implemented error handling with timeout guards (LLM: 60s, FAISS/DB: 30s)
5. ✅ Added logging hooks for all GUI-initiated operations with structured logging
6. ✅ Created `run_command(name, args)` dispatcher for GUI use
7. ✅ Added missing summarization configuration constants to `src/config.py`
8. ✅ Fixed missing `FAISS_INDEX_PATH` import in `src/retrieval/pipeline.py`
9. ✅ Created comprehensive unit and integration tests (`tests/test_facade.py`) - 36 tests, all passing
10. ✅ Updated file index documentation
11. ✅ Added pytest-asyncio to requirements.txt and pytest.ini configuration

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

### Block C (GUI Framework): PR #13 - Review Queue & Context Inspector (Web)
1. Implement Review Queue interface with spaced repetition
2. Implement Context Inspector with tree view
3. Add node focus and navigation from Knowledge Tree
4. Integrate with review scheduler backend

## Active Decisions

1. **Database Path**: Default to `$PROJECT_ROOT/data/`, configurable via `AI_TUTOR_DATA_DIR`
2. **Embedding Storage**: Embeddings stored as BLOB in SQLite (not just referenced)
3. **Topic Hierarchy**: Implemented as foreign key relationship (parent_topic_id)
4. **JSON Storage**: List and dictionary fields stored as JSON strings in TEXT columns
5. **Testing Framework**: Using pytest for all tests
6. **Python Version**: Using Python 3.14+ with no version pins in requirements.txt

## Current Blockers

None - Block C PR #12 complete; proceeding to PR #13

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

### Block A (Interface): Backend Integration Layer
- ✅ PR #1: Unified GUI–Backend Facade (COMPLETED)
- ✅ PR #2: Graph + Hover Providers (COMPLETED)
- ✅ PR #3: UI Model Definitions (COMPLETED)

### Block C (GUI Framework): GUI Framework
- ✅ PR #9: FastAPI Backend for Tauri (COMPLETED)
- ✅ PR #10: Frontend Scaffolding (COMPLETED)
- ✅ PR #11: Tutor Chat & Command Console (Web) (COMPLETED)
- ✅ PR #12: Knowledge Tree Visualization (Web) (COMPLETED)
- ✅ UI Style Guide Implementation (COMPLETED)

## Notes

- All tests passing
- No linter errors (only import warnings for installed dependencies)
- Database schema supports hierarchical topics
- Transcript import fully functional with AI classification, summarization, and state updates
- Write-time summarization fully functional with APScheduler background jobs and audit logging
- Review scheduler fully functional with decay-based mastery model and priority computation
- Frontend scaffolding complete with routing, layout, and testing infrastructure
- Chat and Console interfaces complete with full CLI parity
- Knowledge Tree visualization complete with Cytoscape.js, search, collapse, zoom, and navigation
- Ready to proceed with PR #13: Review Queue & Context Inspector (Web)

