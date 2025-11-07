# AI Tutor – Interface Development PRD

> **Purpose:** Create a graphical interface that provides full feature parity with the CLI while offering an intuitive, visual environment for tutoring sessions, context management, and spaced repetition. This project uses Tauri + FastAPI WebView

**Deadline:** TBD  
**Success Criteria:**  
- GUI reproduces all CLI functionality from the MVP (database, index, AI, and chat commands).  
- Knowledge Tree visualization operates smoothly and displays contextual hover summaries.  
- LLM operations remain responsive (<4 s average for common actions).  
- Code architecture remains modular and shares backend logic with the CLI.

---

## Project Overview

The GUI introduces a **multi-pane desktop interface** where users can:
- Conduct chat sessions with the AI Tutor.
- Manage databases, indexes, and models visually.
- View summaries, review queues, and performance progress.
- Explore a **knowledge tree graph** representing the topic–skill–artifact DAG.
- Hover over nodes to view summaries and statistics.
- Import transcripts and monitor summarization updates.

The GUI will call directly into the existing Python modules (storage, retrieval, summarization, orchestration), maintaining a single codebase.

---

## Current State

### Existing Components
- ✅ CLI commands for DB, index, AI, and chat (see *Illustrated Primer*).
- ✅ Modular backend (`src/storage`, `src/retrieval`, `src/services/ai`, `src/context`).
- ✅ Event/state schema and summarization pipeline.
- ✅ Proof-of-concept Tutor Chat (text-based).
- ✅ FAISS retrieval and SQLite persistence.

### What We’re Adding
- 🎯 Multi-tab GUI replicating CLI commands.
- 🎯 Knowledge Tree visualization of the database graph.
- 🎯 Hover popups with per-node summaries and mastery data.
- 🎯 Modular backend interface shared across both GUIs.

---

## User Stories

### Primary User: Student
- As a student, I want to launch the app and chat naturally with my tutor.  
- As a student, I want to visualize what I’ve learned using a knowledge tree.  
- As a student, I want to hover on a node and see how well I understand it.  
- As a student, I want to review weak topics without using the command line.

### Secondary User: Human Tutor
- As a tutor, I want to import transcripts through a file selector and see them integrated.  
- As a tutor, I want to inspect a student’s knowledge graph and summaries interactively.

### System
- As the system, I must map GUI events to existing command-line functionality.  
- As the system, I must render graphs efficiently, handle long-running API calls asynchronously, and avoid blocking the main thread.

---

## Feature Requirements

### 1. Core Layout (Critical)
- **Tabs:**  
  1. Tutor Chat  
  2. Command Console  
  3. Review Queue  
  4. Knowledge Tree  
  5. Context Inspector  

- **Shared Elements:**  
  - Top Menu Bar: File → Import, Database → Check / Init, Index → Build / Status  
  - Status Bar: API health, database path, FAISS index state  
  - Sidebar: Collapsible navigation shortcuts  
  - Loading overlay for LLM requests  

Implements as a single-page React (or Svelte) app rendered in a Tauri webview. Tabs handled via a router (e.g. `react-router-dom`). Backend calls routed through FastAPI endpoints.

---

### 2. Tutor Chat (Critical)
- Full chat window with AI assistant, session list, and context awareness.  
- Auto-saves every exchange to the database.  
- Hovering over AI messages reveals which context chunks were used.  
- Option to summarize, export, or delete sessions.

---

### 3. Command Console (High)
- Visual equivalents for all CLI commands listed in *Illustrated Primer*:  
  - **Database:** Check, Init  
  - **Index:** Build, Status, Search  
  - **AI:** Route config, test summarize/classify/chat  
  - **Chat:** Start, Resume, List sessions  
- Each command runs asynchronously and displays structured output (tables or JSON).

Implements as React components using `fetch('/api/command')` endpoints; results displayed in a collapsible log panel.

---

### 4. Review Queue (High)
- Displays topics scheduled for review.  
- Clicking an item opens a mini-quiz dialog; results update mastery state.  
- Integrates with `src/scheduler/review.py`.

---

### 5. Context Inspector (Medium)
- Tree view of topics/skills with summaries and recent events.  
- “Expand” button retrieves related nodes and artifacts.  
- “Summarize” and “Recompute” actions available per node.

---

### 6. Knowledge Tree Visualization (Critical, UI-Intensive)
- Displays the topic–skill–artifact DAG from the database.  
- Nodes colored by type; edges labeled by relationship.  
- Hover: shows summary popup (title, mastery, recency, event snippet).  
- Click: opens Context Inspector focused on that node.  
- Zoom, pan, and search.

**Tauri + FastAPI WebView**  
- Same front-end JS (Cytoscape.js) loaded from Tauri asset bundle.  
- Graph/hover APIs exposed by FastAPI:  
  - `GET /graph?scope=math&depth=2`  
  - `GET /hover/{node_id}`  
- Layout handled client-side with dagre or elkjs.  
- WebSocket channel for real-time updates (when summaries refresh).  

---

### 7. Import & Summarization (High)
- File selector imports `.txt`, `.md`, or `.json` transcripts.  
- Progress bar for ingestion and summarization pipeline.  
- Errors displayed in a modal dialog.

---

## Success Metrics

**Must Achieve**
- GUI executes all CLI functions without breaking backend modules.  
- Knowledge Tree renders ≤ 1 s for ≤ 1000 nodes; hover latency ≤ 200 ms.  
- Context summaries accurate and updated after import.  
- No blocking of LLM or DB threads in the UI.  
- Both implementations produce identical graph outputs.

**Stretch Goals**
- Live update of tree after new sessions.  
- Theme switch (light/dark).  
- Streaming chat responses.  
- Export graph snapshot as image or JSON.

---

## Technical Architecture

### Backend Layer
| Component | Purpose |
|------------|----------|
| **app_facade.py** | Unified async interface between GUI and backend modules |
| **graph_provider.py** | Builds graph JSON from SQLite/networkx |
| **hover_provider.py** | Returns hover summary payloads |
| **scheduler/review.py** | Generates spaced-repetition queue |
| **services/ai/** | Handles OpenAI API calls (shared with CLI) |

---

### Tauri + FastAPI

```
frontend/
  src/
    pages/
      Chat.tsx
      Console.tsx
      Review.tsx
      Context.tsx
      KnowledgeTree.tsx
  components/
    GraphView.tsx
    HoverCard.tsx
backend/
  api/
    graph.py
    hover.py
    facade.py
```

**Key Technologies**
- Tauri (Rust shell)
- React + Cytoscape.js
- FastAPI backend (shared logic)
- WebSocket for updates
- Vite build + Tauri bundler

---

## Risks & Mitigation

| Risk | Description | Mitigation |
|------|--------------|-------------|
| **Rendering performance** | Graph too large for real-time updates | Lazy loading + node culling |
| **Thread blocking** | Long AI calls freeze UI | Async tasks via qasync (A) / async FastAPI (B) |
| **API drift** | CLI and GUI diverge | Central `app_facade.py` API layer |
| **Layout instability** | Different frameworks produce inconsistent graph geometry | Lock layout algorithm (ELK/Dagre)|
| **Security** | Local webview → backend access | Restrict to `localhost`, disable external origins |

---

## Implementation Timeline (Estimated 4 Weeks)

| Week | Milestone | Deliverables |
|------|------------|--------------|
| 1 | GUI skeleton & backend bridge | Tabs, routing, app facade, build scripts |
| 2 | Chat & Command views | Tutor chat, command console parity |
| 3 | Knowledge Tree core | Graph provider, Cytoscape integration, hover popups |
| 4 | Review queue, import, polish | Spaced repetition UI, transcript loader, theming |

---

## Success Criteria (Definition of Done)
- [ ] GUI replicates all CLI commands visually  
- [ ] Knowledge Tree graph operational with hover summaries  
- [ ] Async operations stable (no freezes)  
- [ ] Backend unchanged across CLI / GUI  
- [ ] Graph layouts and hover data functional  

---

## Key Principles

1. **Single Source of Truth:** Backend logic remains in shared Python modules.  
2. **Lightweight Footprint:** No external servers or databases introduced.  
3. **Visual Transparency:** Users can see and interact with the data they produce.  
4. **Parallel Parity:** Both GUI versions must maintain feature equivalence.  
5. **Fail Gracefully:** If AI calls fail, cached summaries display automatically.  
