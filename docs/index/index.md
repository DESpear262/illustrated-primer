# Project File Index

This document indexes all files in the AI Tutor Proof of Concept project, organized by directory and purpose.

## Root Directory Files

### Configuration and Setup
- **README.md** - Project overview, setup instructions, and documentation
- **requirements.txt** - Python package dependencies
- **pytest.ini** - Pytest configuration for test execution

## Source Code (`src/`)

### Root Module
- **src/__init__.py** - Package initialization for src module
- **src/config.py** - Configuration module handling environment variables, database paths, OpenAI API settings, and global constants

### CLI Module (`src/cli/`)
- **src/cli/__init__.py** - Package initialization for CLI module
- **src/cli/main.py** - Main CLI entry point providing top-level commands (version, db, index, ai, chat, review, import subcommands)
- **src/cli/db.py** - Database CLI commands for health checks and database initialization
- **src/cli/index.py** - FAISS index CLI commands for building, checking status, and searching
- **src/cli/ai.py** - AI service CLI commands for testing AI functionality and viewing routing configuration
- **src/cli/chat.py** - Tutor chat CLI commands (start, resume, list)
- **src/cli/review.py** - Review scheduler CLI commands (next: get prioritized review list)
- **src/cli/import_cmd.py** - Transcript import CLI commands (transcript: import single file, batch: import multiple files)
- **src/cli/refresh.py** - Summarization refresh CLI commands (summaries: refresh topic summaries, status: show topics needing refresh)

### Models Module (`src/models/`)
- **src/models/__init__.py** - Package initialization for models module
- **src/models/base.py** - Pydantic models for all entities: Event, SkillState, TopicSummary, Goal, Commitment, NudgeLog

### Storage Module (`src/storage/`)
- **src/storage/__init__.py** - Package initialization for storage module
- **src/storage/schema.sql** - SQLite database schema with tables, indexes, FTS5 virtual table, and triggers
- **src/storage/db.py** - Database I/O layer with context manager, initialization, and CRUD operations for all entities
- **src/storage/queries.py** - High-level query wrappers for filtering events, skills, and topics by various criteria

### Utils Module (`src/utils/`)
- **src/utils/__init__.py** - Package initialization for utils module
- **src/utils/serialization.py** - JSON serialization/deserialization utilities for Pydantic models, datetime objects, and binary data

### Services Module (`src/services/`)
- **src/services/__init__.py** - Package initialization for services module

### AI Services Module (`src/services/ai/`)
- **src/services/ai/__init__.py** - Package initialization for AI services module
- **src/services/ai/router.py** - Model routing registry with task-based routing (SUMMARIZE_EVENT, CLASSIFY_TOPICS, UPDATE_SKILL, CHAT_REPLY)
- **src/services/ai/prompts.py** - Prompt templates and structured output schemas for all AI tasks
- **src/services/ai/utils.py** - Utility functions for retry, rate limiting, token counting, and error handling
- **src/services/ai/client.py** - AI client for OpenAI API integration with retry, rate limiting, and structured output parsing

### Interface Module (`src/interface/`)
- **src/interface/utils.py** - Chat utilities for history building and token budgeting
- **src/interface/tutor_chat.py** - TUI engine for chat sessions, upload handling, and summarization

### Interface Common Module (`src/interface_common/`)
- **src/interface_common/__init__.py** - Package initialization for interface_common module
- **src/interface_common/exceptions.py** - Custom exception classes for GUI–backend facade operations (FacadeError, FacadeTimeoutError, FacadeDatabaseError, FacadeIndexError, FacadeAIError, FacadeChatError)
- **src/interface_common/app_facade.py** - Unified GUI–backend facade with async wrappers for all CLI commands, error handling, timeout guards, logging hooks, and run_command dispatcher
- **src/interface_common/models.py** - Shared Pydantic models for consistent data structures between CLI outputs and GUI responses (GraphNode, GraphEdge, HoverPayload, ChatMessage, CommandResult)

### Backend API Module (`backend/api/`)
- **backend/__init__.py** - Package initialization for backend module
- **backend/api/__init__.py** - Package initialization for API module
- **backend/api/main.py** - FastAPI application with CORS middleware, WebSocket support, and lifespan management
- **backend/api/facade.py** - Facade instance access module to avoid circular imports
- **backend/api/routes/__init__.py** - Package initialization for routes module
- **backend/api/routes/db.py** - Database API routes (check, init)
- **backend/api/routes/index.py** - Index API routes (build, status, search)
- **backend/api/routes/ai.py** - AI API routes (routes, test)
- **backend/api/routes/chat.py** - Chat API routes (start, resume, list, turn)
- **backend/api/routes/graph.py** - Graph API routes (get graph JSON)
- **backend/api/routes/hover.py** - Hover API routes (get hover payload)
- **backend/api/routes/review.py** - Review API routes (next)
- **backend/api/routes/import_route.py** - Import API routes (transcript import, file upload)
- **backend/api/routes/refresh.py** - Refresh API routes (summaries refresh)
- **backend/api/routes/progress.py** - Progress API routes (summary)
- **backend/api/routes/websocket.py** - WebSocket API routes (live updates)

### Ingestion Module (`src/ingestion/`)
- **src/ingestion/__init__.py** - Package initialization for ingestion module
- **src/ingestion/transcripts.py** - Transcript importer for .txt, .md, and .json formats with AI classification, summarization, embedding, and topic/skill state updates

### Summarizers Module (`src/summarizers/`)
- **src/summarizers/__init__.py** - Package initialization for summarizers module
- **src/summarizers/update.py** - Summarization update functions with batch processing, aggregation, audit logging, and versioning
- **src/summarizers/scheduler.py** - APScheduler background job for write-time summarization
- **src/summarizers/hooks.py** - Hooks to trigger summarization after event creation

### Context Module (`src/context/`)
- **src/context/__init__.py** - Package initialization for context module
- **src/context/filters.py** - Hybrid scoring, recency decay, and filtering utilities
- **src/context/assembler.py** - Context assembler with dynamic token allocation, hybrid retrieval, and MMR diversity
- **src/context/graph_provider.py** - Graph provider for DAG JSON generation from database for knowledge tree visualization with filtering by scope, depth, and relation type
- **src/context/hover_provider.py** - Hover provider for per-node summaries and statistics with caching to minimize repeated lookups and ensure <200ms latency

### Scheduler Module (`src/scheduler/`)
- **src/scheduler/__init__.py** - Package initialization for scheduler module
- **src/scheduler/review.py** - Review scheduler with decay-based mastery model, priority computation, and outcome recording

## Scripts (`scripts/`)

### Data Generation
- **scripts/generate_stub_data.py** - Stub data generation script for local testing; creates sample events, topics, skills, goals, and commitments

## Tests (`tests/`)

### Test Suite
- **tests/__init__.py** - Package initialization for tests module
- **tests/test_models.py** - Unit tests for Pydantic models (Event, SkillState, TopicSummary, etc.)
- **tests/test_serialization.py** - Unit tests for serialization utilities
- **tests/test_database.py** - Unit tests for database initialization and schema
- **tests/test_db_io.py** - Unit tests for database I/O operations (CRUD)
- **tests/test_queries.py** - Unit tests for query wrapper functions
- **tests/test_ai_router.py** - Unit tests for AI router and routing logic
- **tests/test_ai_prompts.py** - Unit tests for prompt templates and JSON parsing
- **tests/test_ai_utils.py** - Unit tests for AI utilities (retry, rate limiting, token counting)
- **tests/test_ai_client.py** - Integration tests for AI client with mocked API responses
- **tests/test_chat_utils.py** - Unit tests for chat utilities (history building, transcript)
- **tests/test_chat_interface.py** - Integration tests for chat interface with mocked API responses
- **tests/test_context_filters.py** - Unit tests for context filters (hybrid scoring, recency decay, filtering)
- **tests/test_context_assembler.py** - Unit tests for context assembler (token allocation, composition)
- **tests/test_scheduler.py** - Unit and integration tests for review scheduler (decay model, priority computation, outcome recording)
- **tests/test_transcript_import.py** - Unit and integration tests for transcript import (parsing, actor inference, timestamp parsing, AI classification, event creation, summarization, embedding, topic/skill updates)
- **tests/test_summarizers.py** - Unit and integration tests for summarization (audit logging, versioning, batch processing, scheduler, refresh functions)
- **tests/test_integration.py** - Integration tests for database operations, topic hierarchy, and FTS search
- **tests/test_facade.py** - Unit and integration tests for GUI–backend facade (async wrappers, error handling, timeout guards, command dispatcher)
- **tests/test_interface_models.py** - Unit tests for interface common models (validation, serialization, round-trip safety, facade output validation)
- **tests/test_api.py** - Unit and integration tests for FastAPI endpoints (all routes, WebSocket, error handling, CORS)
- **tests/test_graph_provider.py** - Unit tests for graph provider (JSON format validation, depth filtering, scope filtering, relation filtering)
- **tests/test_hover_provider.py** - Unit tests for hover provider (payload structure validation, caching, performance, error handling)
- **tests/test_graph_hover_integration.py** - Integration tests for graph and hover providers (combined FAISS + SQLite queries, performance requirements, large dataset testing)

## Documentation (`docs/`)

### Memory Bank (`docs/memory-bank/`)
- **docs/memory-bank/projectbrief.md** - Foundation document defining core requirements, goals, success criteria, and timeline
- **docs/memory-bank/productContext.md** - Product context: why the project exists, problems it solves, and user experience goals
- **docs/memory-bank/activeContext.md** - Current work focus, recent changes, and next steps
- **docs/memory-bank/systemPatterns.md** - System architecture, key technical decisions, design patterns, and component relationships
- **docs/memory-bank/techContext.md** - Technologies used, development setup, technical constraints, and dependencies
- **docs/memory-bank/progress.md** - What works, what's left to build, current status, and known issues

### Architecture (`docs/architecture/`)
- **docs/architecture/ai-tutor-prd.md** - Product Requirements Document for the AI Tutor system
- **docs/architecture/ai-tutor-tasks.md** - Task breakdown with implementation blocks, PRs, time estimates, and file lists
- **docs/architecture/architecture.mermaid** - Architecture diagram in Mermaid format

### Index (`docs/index/`)
- **docs/index/index.md** - This file: comprehensive index of all project files

### Frontend Module (`frontend/`)
- **frontend/package.json** - Frontend package configuration with dependencies and scripts
- **frontend/vite.config.ts** - Vite build configuration with React plugin and Vitest test setup
- **frontend/tailwind.config.js** - Tailwind CSS configuration
- **frontend/postcss.config.js** - PostCSS configuration for Tailwind CSS
- **frontend/tsconfig.json** - TypeScript configuration for the frontend
- **frontend/tsconfig.app.json** - TypeScript configuration for application code
- **frontend/tsconfig.node.json** - TypeScript configuration for Node.js tooling
- **frontend/index.html** - HTML entry point for the React application
- **frontend/src/main.tsx** - React application entry point
- **frontend/src/App.tsx** - Main App component with React Router setup
- **frontend/src/index.css** - Global CSS with Tailwind directives
- **frontend/src/lib/api.ts** - API client for backend communication with base URL configuration
- **frontend/src/components/Layout.tsx** - Main layout component with header, sidebar, content area, and footer
- **frontend/src/components/Header.tsx** - Header component with top menu bar and navigation
- **frontend/src/components/Sidebar.tsx** - Sidebar component with collapsible navigation shortcuts
- **frontend/src/components/StatusFooter.tsx** - Status footer component displaying API health, database path, and index state
- **frontend/src/components/GraphView.tsx** - Graph view component using Cytoscape.js with ELK layout for knowledge tree visualization
- **frontend/src/components/HoverCard.tsx** - Hover card component displaying node summary information in tooltips
- **frontend/src/pages/Home.tsx** - Home page component that redirects to Chat
- **frontend/src/pages/Chat.tsx** - Chat page with session management, message display, and context awareness
- **frontend/src/pages/Console.tsx** - Console page with form-based UI for all CLI commands
- **frontend/src/pages/Review.tsx** - Review page placeholder
- **frontend/src/pages/Context.tsx** - Context page placeholder
- **frontend/src/pages/KnowledgeTree.tsx** - Knowledge Tree page with graph visualization, search, collapse, zoom, and navigation
- **frontend/src/hooks/useWebSocket.ts** - WebSocket hook for live updates
- **frontend/src/hooks/useLocalStorage.ts** - LocalStorage hook for persistent data storage
- **frontend/src/test/setup.ts** - Vitest test setup file with React Testing Library configuration
- **frontend/src/test/App.test.tsx** - Tests for App component
- **frontend/src/test/api.test.ts** - Tests for API client
- **frontend/src/test/Layout.test.tsx** - Tests for Layout component
- **frontend/src/test/Chat.test.tsx** - Tests for Chat component
- **frontend/src/test/Console.test.tsx** - Tests for Console component
- **frontend/src/test/GraphView.test.tsx** - Tests for GraphView component
- **frontend/src/test/HoverCard.test.tsx** - Tests for HoverCard component

## Data Directory (`data/`)

Currently empty. Used for storing:
- SQLite database files (`ai_tutor.db`)
- FAISS index files (`faiss_index.bin`)
- Other runtime data files

## Commits Directory (`commits/`)

### Commit Metadata (`commits/A/`)
- **commits/A/add.txt** - List of files staged for commit
- **commits/A/commit.txt** - Commit message

## Generated/Virtual Directories (Not Indexed)

These directories are generated at runtime and should not be indexed:
- `__pycache__/` - Python bytecode cache
- `venv/` - Python virtual environment
- `.pytest_cache/` - Pytest cache directory

## Notes

- All Python files follow the project's documentation standards with module-level docstrings, function descriptions, and inline comments
- Test files mirror the structure of source files with corresponding test modules
- Documentation is organized hierarchically: memory-bank for project context, architecture for technical design, and index for file reference

