# AI Tutor Proof of Concept — Task Breakdown

> **Purpose:** Implement a modular, local AI tutoring engine with persistent context storage, retrieval, and spaced repetition, using SQLite + FAISS + OpenAI API.

**Total Implementation Time:** ~140 hours  
**Parallelization:** Up to 3 blocks can run concurrently once Block A completes

---

## 🔴 BLOCK A: Core Data Infrastructure
**Dependencies:** None  
**Total Time:** ~30 hours  
**Critical Path:** Must complete before any other block (foundation for context management)

---

### PR #1: Define Data Models and Schemas
**Prerequisites:** None  
**Time:** 8 hours  
**Impact:** Establishes all tables and Pydantic models; baseline for database and state management.

#### Tasks:
- [ ] Create Pydantic schemas for `Event`, `SkillState`, `TopicSummary`, `Goal`, `Commitment`, `NudgeLog`
- [ ] Define SQLite tables and schema migrations
- [ ] Add indexes for timestamps, topics, and embeddings
- [ ] Implement JSON serialization/deserialization utilities
- [ ] Create stub data generation script for local testing

#### Files Created:
- `src/models/base.py`  
- `src/storage/schema.sql`  
- `src/utils/serialization.py`

#### Files Modified:
- `src/config.py` – Add database path and global constants  
- `README.md` – Document schema entities

#### Testing:
**Unit Tests - NO FAIL:**
- [ ] Schemas validate sample input  
- [ ] Database initializes successfully  
- [ ] JSON utilities serialize/deserialize consistently  

**Integration Tests - NO FAIL:**
- [ ] Database writes and reads event records  
- [ ] Topic hierarchy reconstructs correctly  
- [ ] Startup script creates tables automatically  

#### Validation:
- [ ] Local database initializes on fresh clone  
- [ ] Sample data populates without error  
- [ ] All models pass Pydantic validation  

---

### PR #2: Database I/O Layer
**Prerequisites:** PR #1 complete  
**Time:** 10 hours  
**Impact:** Enables CRUD access to events, states, and summaries.

#### Tasks:
- [ ] Implement insert/update methods for all entities  
- [ ] Add query wrappers for topic/time/skill-based filtering  
- [ ] Create persistence helpers for `SkillState` updates  
- [ ] Add SQLite FTS5 search table for transcript retrieval  
- [ ] Implement DB health check utilities  

#### Files Created:
- `src/storage/db.py`  
- `src/storage/queries.py`

#### Files Modified:
- `src/models/base.py` – Add table bindings  

#### Testing:
**Unit Tests - NO FAIL:**
- [ ] Insert + retrieve event round-trips cleanly  
- [ ] FTS5 search returns expected text chunks  
- [ ] Update/delete operations function safely  

**Integration Tests - NO FAIL:**
- [ ] Context loader builds from multiple sessions  
- [ ] State recomputation runs without corruption  

#### Validation:
- [ ] CLI tool `python cli.py db check` returns OK  
- [ ] 1,000+ inserts complete without error  

---

### PR #3: Vector Store & Embedding Pipeline
**Prerequisites:** PR #2 complete  
**Time:** 12 hours  
**Impact:** Enables semantic retrieval and context windowing for LLM interactions.

#### Tasks:
- [ ] Integrate FAISS index  
- [ ] Store chunk embeddings for sessions and transcripts  
- [ ] Add batch embed/update pipeline using OpenAI embeddings  
- [ ] Implement nearest-neighbor search API  
- [ ] Build hybrid retriever (FAISS + SQL filters)

#### Files Created:
- `src/retrieval/faiss_index.py`  
- `src/retrieval/pipeline.py`

#### Files Modified:
- `src/storage/db.py` – Add embedding metadata field  

#### Testing:
**Unit Tests - NO FAIL:**
- [ ] Embeddings saved/retrieved accurately  
- [ ] FAISS search returns top-N relevant chunks  
- [ ] Index rebuild completes successfully  

**Integration Tests - NO FAIL:**
- [ ] Retrieval merges SQL + vector results correctly  
- [ ] Retrieval latency under 200ms for 1k chunks  

#### Validation:
- [ ] Verify cosine similarity accuracy on known pairs  
- [ ] Index persists across restarts  

---

## 🟢 BLOCK B: AI Tutor Chat System
**Dependencies:** BLOCK A complete  
**Total Time:** ~40 hours  
**Critical Path:** Foundation for context persistence and testing future blocks  

---

### PR #4: AI Orchestration Layer
**Prerequisites:** PR #3 complete  
**Time:** 12 hours  
**Impact:** Creates modular LLM routing and orchestration layer.

#### Tasks:
- [ ] Implement model routing registry (nano/classifier/4o)  
- [ ] Create standardized prompt interface  
- [ ] Add retry, rate limiting, and error handling  
- [ ] Implement summarization and classification tool functions  
- [ ] Add config for per-model usage  

#### Files Created:
- `src/services/ai/router.py`  
- `src/services/ai/utils.py`  
- `src/services/ai/prompts.py`

#### Files Modified:
- `src/config.py` – Add OpenAI keys and model defaults  

#### Testing:
**Unit Tests - NO FAIL:**
- [ ] All model routes return responses  
- [ ] Summarization prompt outputs JSON consistently  
- [ ] Error retries capped at 3 attempts  

**Integration Tests - NO FAIL:**
- [ ] LLM calls respect timeout and token budget  
- [ ] Prompt history logged correctly  

#### Validation:
- [ ] AI calls operational offline except API  
- [ ] Fallback routing works if model unavailable  

---

### PR #5: Tutor Chat Interface (TUI)
**Prerequisites:** PR #4 complete  
**Time:** 14 hours  
**Impact:** Creates interactive session layer for student dialogue and logging.

#### Tasks:
- [ ] Implement text-based TUI using `typer` + `rich`  
- [ ] Add conversational history buffer  
- [ ] Log each turn as `Event`  
- [ ] Display loading indicators and summaries  
- [ ] Implement session save/resume  

#### Files Created:
- `src/interface/tutor_chat.py`  
- `src/interface/utils.py`

#### Files Modified:
- `src/storage/db.py` – Add `insert_event()` call  
- `src/config.py` – Add chat config options  

#### Testing:
**Unit Tests - NO FAIL:**
- [ ] Chat sessions record correctly  
- [ ] Summaries triggered on session end  
- [ ] CLI commands display correctly  

**Integration Tests - NO FAIL:**
- [ ] End-to-end session persists events  
- [ ] Reopen session restores last context  

#### Validation:
- [ ] Test 3-topic chat continuity between runs  

---

### PR #6: Context Composition Engine
**Prerequisites:** PR #5 complete  
**Time:** 14 hours  
**Impact:** Builds task-specific prompt from retrieved and summarized memory.

#### Tasks:
- [ ] Implement retrieval pipeline using SQL + FAISS  
- [ ] Add relevance scoring and recency decay  
- [ ] Compose context slice and system prompt dynamically  
- [ ] Cap token usage per model constraints  
- [ ] Log retrieval decisions for audit  

#### Files Created:
- `src/context/assembler.py`  
- `src/context/filters.py`

#### Testing:
**Unit Tests - NO FAIL:**
- [ ] Retrieval merges multiple sources accurately  
- [ ] Token budgets respected  
- [ ] Recency weighting decays properly  

**Integration Tests - NO FAIL:**
- [ ] Multi-topic retrieval builds coherent prompt  
- [ ] Same query yields consistent result  

#### Validation:
- [ ] Session replay reproduces context within 5% token variance  

---

## 🔵 BLOCK C: Transcript Ingestion Pipeline
**Dependencies:** BLOCK B complete  
**Total Time:** ~25 hours  
**Can run in parallel with:** BLOCK D

---

### PR #7: Transcript Importer
**Prerequisites:** Context engine complete  
**Time:** 10 hours  
**Impact:** Enables importing of human tutor sessions and external transcripts.

#### Tasks:
- [ ] Parse .txt/.md/.json transcripts into structured `Event`s  
- [ ] Tag with topics, skills, and timestamps  
- [ ] Auto-summarize and embed new events  
- [ ] Update skill and topic summaries automatically  
- [ ] Log provenance and model version  

#### Files Created:
- `src/ingestion/transcripts.py`

#### Testing:
**Unit Tests - NO FAIL:**
- [ ] Transcripts parsed into clean events  
- [ ] Summaries saved to database  
- [ ] Errors caught for malformed input  

**Integration Tests - NO FAIL:**
- [ ] Full transcript import updates TopicSummary  
- [ ] Index rebuild includes new embeddings  

#### Validation:
- [ ] Import two tutor sessions; verify summary accuracy  

---

### PR #8: Update Propagation & Summarization
**Prerequisites:** PR #7 complete  
**Time:** 15 hours  
**Impact:** Maintains up-to-date summaries when new content added.

#### Tasks:
- [ ] Create write-time summarization job  
- [ ] Update TopicSummary and SkillState deltas  
- [ ] Implement background job via APScheduler  
- [ ] Add summarization audit logs  
- [ ] CLI command: `cli refresh summaries`  

#### Files Created:
- `src/summarizers/update.py`  
- `src/cli/refresh.py`

#### Testing:
**Unit Tests - NO FAIL:**
- [ ] Scheduler runs job as expected  
- [ ] Summaries versioned correctly  
- [ ] State recomputed without duplication  

**Integration Tests - NO FAIL:**
- [ ] 100-event import triggers one summarization per topic  

#### Validation:
- [ ] Refresh command updates summaries visibly  

---

## 🟡 BLOCK D: Spaced Repetition & Mastery Tracking
**Dependencies:** BLOCK B complete  
**Total Time:** ~25 hours  
**Can run in parallel with:** BLOCK C  

---

### PR #9: Review Scheduler
**Prerequisites:** Context manager functional  
**Time:** 12 hours  
**Impact:** Generates spaced repetition review list from learning state.

#### Tasks:
- [ ] Implement decay-based mastery model  
- [ ] Compute review priority by recency and p_mastery  
- [ ] CLI: `cli review next`  
- [ ] Record outcomes to new Event objects  
- [ ] Update mastery deltas  

#### Files Created:
- `src/scheduler/review.py`

#### Testing:
**Unit Tests - NO FAIL:**
- [ ] Decay function produces expected results  
- [ ] Top-N review topics reflect weak skills  
- [ ] CLI command outputs formatted list  

**Integration Tests - NO FAIL:**
- [ ] Review outcomes update SkillState  
- [ ] Multiple runs persist updated mastery  

#### Validation:
- [ ] Verify review cycle reproduces expected intervals  

---

### PR #10: Performance Tracking
**Prerequisites:** PR #9 complete  
**Time:** 13 hours  
**Impact:** Quantifies improvement between timestamps.

#### Tasks:
- [ ] Add delta calculator comparing p_mastery between A/B times  
- [ ] CLI: `cli progress summary`  
- [ ] Generate JSON and markdown report  
- [ ] Add plotting option using `rich` charts  
- [ ] Link reports to student profile  

#### Files Created:
- `src/analysis/performance.py`

#### Testing:
**Unit Tests - NO FAIL:**
- [ ] Delta calculations accurate  
- [ ] Report JSON schema valid  
- [ ] CLI renders without crash  

**Integration Tests - NO FAIL:**
- [ ] Two review sessions yield measurable delta  

#### Validation:
- [ ] Output matches manual spreadsheet verification  

---

## 📊 Dependency Graph

```
CRITICAL PATH:
BLOCK A → BLOCK B → BLOCK C/D (parallel)

INDEPENDENT BLOCKS (start after B):
├─ BLOCK C: Transcript Integration (25h)
└─ BLOCK D: Spaced Repetition (25h)

Total Sequential Time (A+B): ~70h  
Total Parallel Time (C+D): ~50h  
Total Project Effort: ~140h
```

---

## Critical Success Factors

1. **Block A first** — database + FAISS are prerequisites for all others.  
2. **Block B next** — chat + context orchestration enable user interaction.  
3. **Blocks C and D in parallel** — ingestion and spaced repetition can be tested concurrently.  
4. **Write-time summarization must be robust** — errors here will break persistence tests.  
5. **End-to-end test** before moving to metrics layer.
