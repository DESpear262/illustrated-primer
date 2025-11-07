# Technical Context: AI Tutor Proof of Concept

## Technology Stack

| Component | Choice | Purpose |
|-----------|--------|---------|
| **Core Language** | Python 3.14+ | Rapid prototyping |
| **Database** | SQLite (FTS5) | Events, states, metadata |
| **Vector Search** | FAISS | Semantic retrieval |
| **Graph Handling** | networkx | Topic/skill DAG |
| **Model Integration** | OpenAI API | LLM + embeddings |
| **Validation** | Pydantic | Schema enforcement |
| **Interface** | typer + rich | CLI / TUI command pages |
| **Web Frontend** | React + TypeScript + Vite | Tauri web interface |
| **Styling** | Tailwind CSS | Utility-first CSS framework |
| **Graph Visualization** | Cytoscape.js + ELK | Knowledge tree visualization |
| **State Management** | React Hooks | Component state and localStorage |
| **API Client** | Fetch API | HTTP client for backend communication |
| **Scheduling** | APScheduler | Spaced repetition + maintenance tasks |
| **Testing** | pytest | Unit and integration testing |

## Dependencies

### Backend (Python)
All dependencies are specified in `requirements.txt` without version pins:
- `pydantic` - Data validation and models
- `openai` - OpenAI API integration
- `faiss-cpu` - Vector similarity search
- `networkx` - Graph/topic DAG handling
- `typer` - CLI framework
- `rich` - Rich text and UI components
- `apscheduler` - Task scheduling
- `pytest` - Testing framework
- `fastapi` - Web framework for API
- `uvicorn` - ASGI server
- `websockets` - WebSocket support

### Frontend (Node.js)
Dependencies specified in `frontend/package.json`:
- `react` + `react-dom` - UI framework
- `react-router-dom` - Client-side routing
- `typescript` - Type safety
- `vite` - Build tool and dev server
- `tailwindcss` - Utility-first CSS framework
- `cytoscape` - Graph visualization
- `cytoscape-elk` - ELK layout algorithm
- `react-hot-toast` - Toast notifications
- `vitest` + `@testing-library/react` - Testing framework

## Configuration

### Environment Variables
- `AI_TUTOR_DATA_DIR` - Override default data directory (default: `$PROJECT_ROOT/data`)
- `OPENAI_API_KEY` - Required for OpenAI API calls

### Default Paths
- Database: `$PROJECT_ROOT/data/ai_tutor.db`
- FAISS Index: `$PROJECT_ROOT/data/faiss_index.bin`
- Data Directory: `$PROJECT_ROOT/data/`

## Technical Constraints

1. **Local-First**: All state remains local; no cloud dependencies (except OpenAI API)
2. **Python 3.14+**: Using latest Python features
3. **SQLite**: Single-file database for portability
4. **FAISS CPU**: Using CPU version for compatibility (can upgrade to GPU later)
5. **OpenAI API**: Required for embeddings and LLM calls

## Development Setup

1. Python 3.14+ environment
2. Install dependencies: `pip install -r requirements.txt`
3. Set `OPENAI_API_KEY` environment variable
4. Database auto-initializes on first use
5. Run stub data generator: `python scripts/generate_stub_data.py`

## Testing

- Framework: pytest
- Test structure:
  - Unit tests: `tests/test_models.py`, `tests/test_serialization.py`, `tests/test_database.py`
  - Integration tests: `tests/test_integration.py`
- Run tests: `pytest tests/`

