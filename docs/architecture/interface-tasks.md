# AI Tutor – Interface Development Tasks Breakdown

> **Purpose:** Implement full GUI feature parity with the CLI and add a knowledge tree visualization:  
> - Tauri + FastAPI WebView  

**Total Implementation Time:** ~160 hours  
**Parallelization:** Up to 3 blocks (Core Backend, Qt GUI, Tauri GUI) can be developed concurrently once the backend bridge is complete.  

---

## 🔴 BLOCK A: Backend Integration Layer
**Dependencies:** Core CLI and backend complete  
**Total Time:** ~30 hours  
**Critical Path:** Must complete before GUI front-end implementation.  

---

### PR #1: Unified GUI–Backend Facade  
**Prerequisites:** Existing backend modules stable  
**Time:** 10 hours  
**Impact:** Provides a single async API layer between the GUI and all backend services.

#### Tasks:
- [ ] Implement `app_facade.py` with async wrappers for CLI-equivalent commands  
- [ ] Wrap DB, Index, AI, and Chat functions from CLI  
- [ ] Add error handling and timeout guards for LLM and FAISS operations  
- [ ] Expose async `run_command(name, args)` dispatcher for GUI use  
- [ ] Add logging hooks for all GUI-initiated operations  

#### Files Created:
- `src/interface_common/app_facade.py`  
- `src/interface_common/exceptions.py`  

#### Testing:
**Unit Tests - NO FAIL:**
- [ ] All facade methods execute CLI-equivalent functions  
- [ ] Exceptions correctly caught and serialized for UI display  
- [ ] Mock OpenAI + SQLite backends pass smoke tests  

**Integration Tests - NO FAIL:**
- [ ] GUI prototype can call `app_facade.chat_turn()` successfully  
- [ ] LLM calls run asynchronously without blocking  

#### Validation:
- [ ] CLI and GUI commands produce identical results for `db check`, `index build`, `ai test`, and `chat start`.  

---

### PR #2: Graph + Hover Providers  
**Prerequisites:** PR #1 complete  
**Time:** 12 hours  
**Impact:** Backend data for knowledge tree visualization and hover summaries.  

#### Tasks:
- [ ] Implement `graph_provider.py` to return DAG JSON from database  
- [ ] Implement `hover_provider.py` for per-node summaries and statistics  
- [ ] Integrate `networkx` DAG traversal utilities  
- [ ] Add query filters for `scope`, `depth`, and `relation`  
- [ ] Cache hover payloads to minimize repeated lookups  

#### Files Created:
- `src/context/graph_provider.py`  
- `src/context/hover_provider.py`  

#### Testing:
**Unit Tests - NO FAIL:**
- [ ] Graph JSON format matches schema (nodes/edges)  
- [ ] Hover payload includes title, mastery, and last evidence  
- [ ] Depth filtering correctly truncates output  

**Integration Tests - NO FAIL:**
- [ ] FAISS + SQLite combined queries populate node info  
- [ ] Hover latency <200ms for 500 nodes  

#### Validation:
- [ ] Sample graph renders in prototype viewer with accurate hover text  

---

### PR #3: UI Model Definitions  
**Prerequisites:** PR #1 and PR #2 complete  
**Time:** 8 hours  
**Impact:** Ensures consistent data model.  

#### Tasks:
- [ ] Create shared Pydantic models for `GraphNode`, `GraphEdge`, `HoverPayload`, `ChatMessage`, and `CommandResult`  
- [ ] Define schema contracts used by both GUI front-ends  
- [ ] Add JSON serialization helpers  

#### Files Created:
- `src/interface_common/models.py`  

#### Testing:
**Unit Tests - NO FAIL:**
- [ ] Models validate CLI outputs and GUI responses  
- [ ] Serialization is round-trip safe  

#### Validation:
- [ ] All facade methods return valid Pydantic models  

---

## 🔵 BLOCK C: GUI Framework
**Dependencies:** BLOCK A complete  
**Total Time:** ~65 hours  

---

### PR #9: FastAPI Backend for Tauri  
**Prerequisites:** Facade complete  
**Time:** 10 hours  
**Impact:** Provides API layer between GUI and shared Python backend.  

#### Tasks:
- [ ] Create FastAPI app with endpoints for all facade methods  
- [ ] Add WebSocket endpoint for live updates  
- [ ] Implement CORS + localhost-only policy  
- [ ] Unit test all endpoints  

#### Files Created:
- `backend/api/main.py`  
- `backend/api/routes/*.py`  

#### Testing:
**Integration Tests - NO FAIL:**
- [ ] API returns valid JSON responses for all commands  

#### Validation:
- [ ] Tauri frontend receives and displays data correctly  

---

### PR #10: Frontend Scaffolding  
**Prerequisites:** PR #9 complete  
**Time:** 12 hours  
**Impact:** Basic routing and layout for SPA frontend.  

#### Tasks:
- [ ] Implement React (or Svelte) base project  
- [ ] Create routes for Chat, Console, Review, Context, KnowledgeTree  
- [ ] Add header, sidebar, and status footer  
- [ ] Configure API client with base URL  

#### Files Created:
- `frontend/src/pages/*`  
- `frontend/src/components/Layout.tsx`  

#### Testing:
**Integration Tests - NO FAIL:**
- [ ] Routing works; navigation preserves app state  

#### Validation:
- [ ] All tabs load and show initial placeholder data  

---

### PR #11: Tutor Chat & Command Console (Web)  
**Prerequisites:** PR #10 complete  
**Time:** 12 hours  
**Impact:** Parity with CLI functionality in webview GUI.  

#### Tasks:
- [ ] Chat interface with streaming AI responses  
- [ ] Command Console replicating all CLI actions  
- [ ] Persistent logs per session  
- [ ] Toast notifications for success/error  

#### Files Created:
- `frontend/src/pages/Chat.tsx`  
- `frontend/src/pages/Console.tsx`  

#### Testing:
**Integration Tests - NO FAIL:**
- [ ] Commands trigger correct API endpoints  
- [ ] Chat and console coexist without websocket conflicts  

#### Validation:
- [ ] AI response latency <4s  

---

### PR #12: Knowledge Tree Visualization (Web)  
**Prerequisites:** PR #11 complete  
**Time:** 21 hours  
**Impact:** Implements full graph visualization in web context.  

#### Tasks:
- [ ] Integrate Cytoscape.js with ELK layout  
- [ ] Fetch `/graph` and `/hover/{node_id}` from backend  
- [ ] Implement hover tooltips, zoom, pan, and focus transitions  
- [ ] Add search and collapse features  

#### Files Created:
- `frontend/src/components/GraphView.tsx`  
- `frontend/src/components/HoverCard.tsx`  

#### Testing:
**Integration Tests - NO FAIL:**
- [ ] Graph loads <1s for 1000 nodes  
- [ ] Hover card latency <200ms  

#### Validation:
- [ ] Node click → Context page focuses on that node  

---

## 📊 Dependency Graph

```
CRITICAL PATH:
BLOCK A → (BLOCK B ∥ BLOCK C)

INDEPENDENT BLOCKS (parallel after A):
├─ BLOCK B: Qt GUI (65h)
└─ BLOCK C: Tauri GUI (65h)

Total Sequential Time: ~30h  
Total Parallel Time: ~130h  
Total Project Effort: ~160h
```

---

## Critical Success Factors

1. **Block A first** — shared API and models must exist before UI.  
2. **Blocks B and C in parallel** — both GUIs reference the same backend logic.  
3. **Feature parity validation** — both implementations produce identical outputs.  
4. **No backend divergence** — CLI, Qt, and Tauri share one app_facade.  
5. **Graph performance target** — <1s render, <200ms hover response.  
