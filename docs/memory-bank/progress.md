# Progress: AI Tutor Proof of Concept

## What Works

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

### 🔴 Block A: Core Data Infrastructure (IN PROGRESS)

#### PR #2: Database I/O Layer (NEXT)
- [ ] Database connection management
- [ ] Insert/update methods for all entities
- [ ] Query wrappers for filtering (topic/time/skill)
- [ ] FTS5 search API
- [ ] DB health check utilities
- [ ] Unit and integration tests

#### PR #3: Vector Store & Embedding Pipeline
- [ ] FAISS index integration
- [ ] Embedding generation pipeline
- [ ] Batch embed/update operations
- [ ] Nearest-neighbor search API
- [ ] Hybrid retriever (FAISS + SQL filters)
- [ ] Unit and integration tests

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

#### PR #7: Transcript Importer
- [ ] Parse .txt/.md/.json transcripts
- [ ] Tag with topics, skills, timestamps
- [ ] Auto-summarize and embed events
- [ ] Update skill and topic summaries
- [ ] Log provenance and model version
- [ ] Unit and integration tests

#### PR #8: Update Propagation & Summarization
- [ ] Write-time summarization job
- [ ] TopicSummary and SkillState delta updates
- [ ] Background job via APScheduler
- [ ] Summarization audit logs
- [ ] CLI command: `cli refresh summaries`
- [ ] Unit and integration tests

### 🟡 Block D: Spaced Repetition & Mastery Tracking

#### PR #9: Review Scheduler
- [ ] Decay-based mastery model
- [ ] Review priority computation (recency + p_mastery)
- [ ] CLI: `cli review next`
- [ ] Outcome recording to Event objects
- [ ] Mastery delta updates
- [ ] Unit and integration tests

#### PR #10: Performance Tracking
- [ ] Delta calculator (p_mastery between timestamps)
- [ ] CLI: `cli progress summary`
- [ ] JSON and markdown report generation
- [ ] Plotting option using rich charts
- [ ] Link reports to student profile
- [ ] Unit and integration tests

## Current Status

### Overall Progress
- **Block A**: 1/3 PRs complete (33%)
- **Block B**: 0/3 PRs complete (0%)
- **Block C**: 0/2 PRs complete (0%)
- **Block D**: 0/2 PRs complete (0%)
- **Total**: 1/10 PRs complete (10%)

### Timeline
- **Block A**: ~8/30 hours complete (27%)
- **Total**: ~8/140 hours complete (6%)

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
- [ ] Spaced repetition algorithm generates review lists accurately
- [ ] Transcripts integrate into topic summaries automatically
- [ ] User can query performance deltas between timestamps

### Secondary Goals
- [ ] Mastery tracking via lightweight Bayesian update or Elo model
- [ ] Context visualizer (CLI heatmap of reviewed topics)
- [ ] Plugin-style API for external data ingestion

