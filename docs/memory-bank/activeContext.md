# Active Context: AI Tutor Proof of Concept

## Current Work Focus

**Block A: Core Data Infrastructure - PR #2: Database I/O Layer** ✅ **COMPLETED**

## Recent Changes

### Completed (PR #2)
1. ✅ Created Database context manager with connection management
2. ✅ Implemented CRUD operations for all entities (Event, SkillState, TopicSummary, Goal, Commitment, NudgeLog)
3. ✅ Created query wrappers for filtering by topic, time, skill, and event type
4. ✅ Implemented FTS5 full-text search API
5. ✅ Created persistence helpers for SkillState updates with evidence
6. ✅ Implemented database health check utilities
7. ✅ Created minimal CLI structure with `db check` command
8. ✅ Created comprehensive unit and integration tests

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

### Immediate Next Task: Block A, PR #3 - Vector Store & Embedding Pipeline
**Prerequisites**: PR #2 complete ✅  
**Time**: 12 hours  
**Impact**: Enables semantic retrieval and context windowing for LLM interactions

#### Tasks:
- [ ] Integrate FAISS index
- [ ] Store chunk embeddings for sessions and transcripts
- [ ] Add batch embed/update pipeline using OpenAI embeddings
- [ ] Implement nearest-neighbor search API
- [ ] Build hybrid retriever (FAISS + SQL filters)

#### Files to Create:
- `src/retrieval/faiss_index.py` - FAISS index operations
- `src/retrieval/pipeline.py` - Embedding pipeline

#### Files to Modify:
- `src/storage/db.py` - Add embedding metadata field (if needed)

## Active Decisions

1. **Database Path**: Default to `$PROJECT_ROOT/data/`, configurable via `AI_TUTOR_DATA_DIR`
2. **Embedding Storage**: Embeddings stored as BLOB in SQLite (not just referenced)
3. **Topic Hierarchy**: Implemented as foreign key relationship (parent_topic_id)
4. **JSON Storage**: List and dictionary fields stored as JSON strings in TEXT columns
5. **Testing Framework**: Using pytest for all tests
6. **Python Version**: Using Python 3.14+ with no version pins in requirements.txt

## Current Blockers

None - PR #1 is complete and ready for PR #2

## Implementation Status

### Block A: Core Data Infrastructure
- ✅ PR #1: Define Data Models and Schemas (COMPLETED)
- ⏳ PR #2: Database I/O Layer (NEXT)
- ⏳ PR #3: Vector Store & Embedding Pipeline

### Block B: AI Tutor Chat System
- ⏳ PR #4: AI Orchestration Layer
- ⏳ PR #5: Tutor Chat Interface (TUI)
- ⏳ PR #6: Context Composition Engine

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

