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

### Interface GUI Module (`src/interface_gui/`)
- **src/interface_gui/__init__.py** - Package initialization for interface_gui module
- **src/interface_gui/app.py** - Application entry point with qasync event loop setup and main() function
- **src/interface_gui/views/__init__.py** - Package initialization for views module
- **src/interface_gui/views/main_window.py** - Main window with multi-tab layout, menu bar, status bar, and all CLI command equivalents
- **src/interface_gui/views/tutor_chat_view.py** - Tutor chat view with message display, input, context sidebar, and session management
- **src/interface_gui/views/command_view.py** - Command console view with visual interface for all CLI operations, form inputs, results display, and command history
- **src/interface_gui/views/review_queue_view.py** - Review queue view with table of topics sorted by review priority, filtering, mark complete dialog, and refresh functionality
- **src/interface_gui/views/context_inspector_view.py** - Context inspector view with tree view of topics/skills, expand/collapse, node details, and actions (summarize, recompute)
- **src/interface_gui/widgets/__init__.py** - Package initialization for widgets module
- **src/interface_gui/widgets/message_list.py** - Message list widget with styled message bubbles and context indicators

### Interface Common Module (`src/interface_common/`)
- **src/interface_common/__init__.py** - Package initialization for interface_common module
- **src/interface_common/app_facade.py** - Unified GUI-backend facade with async wrappers for all backend operations (database, index, AI, chat, review, context), error handling, timeout guards, and logging hooks
- **src/interface_common/exceptions.py** - Custom exceptions for facade operations (FacadeError, FacadeTimeoutError, FacadeValidationError)
- **src/interface_common/models.py** - Shared Pydantic models for GUI interfaces (GraphNode, GraphEdge, HoverPayload, ChatMessage, CommandResult) with JSON serialization helpers

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
- **src/context/graph_provider.py** - DAG JSON generation from database for knowledge tree visualization using networkx
- **src/context/hover_provider.py** - Per-node summaries and statistics for knowledge tree visualization with caching

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
- **tests/test_app_facade.py** - Unit tests for GUI-backend facade (async wrappers, error handling, timeout guards, logging hooks)
- **tests/test_app_facade_integration.py** - Integration tests for facade with real backend components (async operations, session persistence, error serialization)
- **tests/test_graph_provider.py** - Unit tests for graph provider (DAG JSON generation, networkx traversal, filtering)
- **tests/test_hover_provider.py** - Unit tests for hover provider (per-node summaries, statistics, caching)
- **tests/test_graph_hover_integration.py** - Integration tests for graph and hover providers (FAISS + SQLite queries, hover latency, performance)
- **tests/test_interface_models.py** - Unit tests for interface common models (GraphNode, GraphEdge, HoverPayload, ChatMessage, CommandResult) with serialization round-trip tests
- **tests/test_gui_app.py** - Integration tests for GUI application (app launch, menu actions, basic functionality)
- **tests/test_tutor_chat_view.py** - Unit and integration tests for tutor chat view (chat session logging, context retrieval, session persistence)
- **tests/test_command_view.py** - Integration tests for command console view (command execution, results display, history)
- **tests/test_review_queue_view.py** - Integration tests for review queue view (review list display, filtering, mark complete functionality)
- **tests/test_context_inspector_view.py** - Integration tests for context inspector view (tree view, node details, expand/summarize/recompute actions)

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

