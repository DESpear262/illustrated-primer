# AI Tutor Proof of Concept

> **Purpose:** Build a self-contained prototype demonstrating persistent, context-aware AI tutoring and spaced repetition, powered by local storage and modular context management.

## Project Overview

This proof of concept builds a **local AI tutoring engine** capable of:
- Persisting study sessions as structured events (chats, transcripts, assessments)
- Dynamically retrieving relevant context for continued discussion
- Generating summaries, progress tracking, and spaced repetition schedules
- Integrating external "session recordings" from human tutors into the same context model

The system operates entirely **offline except for OpenAI API calls**, with a **CLI/TUI interface** providing two primary modes:
1. **Tutor Chat** — conversational study sessions
2. **Command Chat** — administrative queries and context operations

## Data Schema

### Core Entities

#### Event
Represents a single interaction event (chat turn, transcript, quiz, etc.). Events are the atomic units of learning history.

**Fields:**
- `event_id`: Unique event identifier (UUID)
- `content`: Raw content text (chat, transcript, etc.)
- `event_type`: Type: 'chat', 'transcript', 'quiz', 'assessment'
- `actor`: Actor: 'student', 'tutor', 'system'
- `topics`: List of topic identifiers (JSON array)
- `skills`: List of skill identifiers (JSON array)
- `created_at`: Event creation timestamp
- `recorded_at`: Original recording timestamp (for imports)
- `embedding`: Serialized embedding vector (FAISS format, BLOB)
- `embedding_id`: FAISS index ID for this embedding
- `metadata`: Additional JSON metadata
- `source`: Source identifier (e.g., 'imported_transcript_v1')

#### SkillState
Represents the mastery state of a specific skill. Tracks probability of mastery (p_mastery) and evidence history for spaced repetition.

**Fields:**
- `skill_id`: Unique skill identifier
- `p_mastery`: Probability of mastery (0.0 to 1.0)
- `last_evidence_at`: Most recent evidence timestamp
- `evidence_count`: Total number of evidence events
- `topic_id`: Parent topic identifier
- `created_at`: State creation timestamp
- `updated_at`: Last update timestamp
- `metadata`: Additional JSON metadata

#### TopicSummary
Represents a high-level summary of a topic across multiple sessions. Topics form a hierarchical DAG (Directed Acyclic Graph) where topics can have parent-child relationships.

**Fields:**
- `topic_id`: Unique topic identifier
- `parent_topic_id`: Parent topic in DAG hierarchy (NULL for root topics)
- `summary`: AI-generated summary text
- `open_questions`: List of open questions or gaps (JSON array)
- `event_count`: Number of events associated with this topic
- `last_event_at`: Most recent event timestamp
- `created_at`: Summary creation timestamp
- `updated_at`: Last update timestamp
- `metadata`: Additional JSON metadata

#### Goal
Represents a learning goal or objective. Tracks student intentions and can be linked to topics/skills for progress tracking.

**Fields:**
- `goal_id`: Unique goal identifier
- `title`: Goal title
- `description`: Detailed goal description
- `topic_ids`: Related topic identifiers (JSON array)
- `skill_ids`: Related skill identifiers (JSON array)
- `status`: Status: 'active', 'completed', 'archived'
- `created_at`: Goal creation timestamp
- `target_date`: Target completion date
- `completed_at`: Completion timestamp
- `metadata`: Additional JSON metadata

#### Commitment
Represents a student commitment or study plan. Tracks intended study schedules for accountability and reminder generation.

**Fields:**
- `commitment_id`: Unique commitment identifier
- `description`: Commitment description
- `frequency`: Frequency: 'daily', 'weekly', 'custom'
- `duration_minutes`: Intended duration in minutes
- `topic_ids`: Related topic identifiers (JSON array)
- `status`: Status: 'active', 'completed', 'paused'
- `created_at`: Commitment creation timestamp
- `start_date`: Start date
- `end_date`: End date
- `metadata`: Additional JSON metadata

#### NudgeLog
Represents a log entry for system nudges or reminders. Tracks when the system sends reminders, prompts, or motivational messages.

**Fields:**
- `nudge_id`: Unique nudge identifier
- `nudge_type`: Type: 'reminder', 'motivation', 'review_prompt'
- `message`: Nudge message text
- `topic_ids`: Related topic identifiers (JSON array)
- `commitment_id`: Related commitment identifier
- `status`: Status: 'sent', 'acknowledged', 'dismissed'
- `created_at`: Nudge creation timestamp
- `acknowledged_at`: Acknowledgment timestamp
- `metadata`: Additional JSON metadata

### Database Schema

The database uses SQLite with the following key features:

- **FTS5 Full-Text Search**: `events_fts` virtual table for fast text search on event content
- **Hierarchical Topics**: Foreign key relationships support topic DAG structure
- **Indexes**: Optimized indexes on timestamps, topics, skills, and common query fields
- **Triggers**: Automatic FTS updates and timestamp management
- **JSON Storage**: List and dictionary fields stored as JSON strings in TEXT columns
- **Embedding Storage**: Embeddings stored as BLOB in `events` table

### Key Indexes

- `idx_events_created_at`: Fast time-based event queries
- `idx_events_event_type`: Filter by event type
- `idx_events_topics`: Topic-based queries
- `idx_skills_p_mastery`: Mastery-based skill queries
- `idx_skills_last_evidence_at`: Evidence recency queries
- `idx_topics_parent_topic_id`: Hierarchical topic traversal
- `idx_topics_last_event_at`: Recent topic activity

## Setup

### Prerequisites

- Python 3.14+
- pip

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set environment variables (optional):
   ```bash
   export AI_TUTOR_DATA_DIR=/path/to/data  # Default: $PROJECT_ROOT/data
   export OPENAI_API_KEY=your_api_key_here
   ```

### Database Initialization

The database is automatically created when first accessed. To initialize explicitly:

```bash
python -m src.cli.main db init
```

To check database health:

```bash
python -m src.cli.main db check
```

To initialize with stub data:

```bash
python scripts/generate_stub_data.py
```

## Usage

### CLI Commands

All commands use the main CLI entry point:

```bash
python -m src.cli.main <command> [options]
```

Or if you have a virtual environment activated:

```bash
# Windows
venv\Scripts\python.exe -m src.cli.main <command> [options]

# Linux/Mac
venv/bin/python -m src.cli.main <command> [options]
```

#### Database Commands (`db`)

- **Check database health:**
  ```bash
  python -m src.cli.main db check [--db-path PATH]
  ```

- **Initialize database:**
  ```bash
  python -m src.cli.main db init [--db-path PATH]
  ```

#### Index Commands (`index`)

- **Build FAISS index from all chunks:**
  ```bash
  python -m src.cli.main index build [--db-path PATH] [--faiss-path PATH] [--batch-size SIZE]
  ```

- **Check index status:**
  ```bash
  python -m src.cli.main index status [--faiss-path PATH]
  ```

- **Search index semantically:**
  ```bash
  python -m src.cli.main index search "query text" [--top-k K] [--faiss-path PATH] [--db-path PATH]
  ```

#### AI Service Commands (`ai`)

- **View model routing configuration:**
  ```bash
  python -m src.cli.main ai routes
  ```

- **Test AI functionality:**
  ```bash
  # Summarize text
  python -m src.cli.main ai test summarize --text "Your text here"
  
  # Summarize an event by ID
  python -m src.cli.main ai test summarize --event-id EVENT_ID [--db PATH]
  
  # Classify topics
  python -m src.cli.main ai test classify --text "Learning about derivatives"
  
  # Chat reply
  python -m src.cli.main ai test chat --text "What is a derivative?"
  
  # Override model
  python -m src.cli.main ai test chat --text "Hello" --model gpt-4o-mini
  ```

#### Chat Commands (`chat`)

- **Start a new chat session:**
  ```bash
  python -m src.cli.main chat start [--title "Session Title"] [--db PATH]
  ```

- **Resume an existing session:**
  ```bash
  python -m src.cli.main chat resume <session-id> [--db PATH]
  ```

- **List recent sessions:**
  ```bash
  python -m src.cli.main chat list [--limit N] [--db PATH]
  ```

#### Chat Session Commands

While in a chat session, you can use these commands:

- `/help` - Show available commands
- `/end` - End the session (triggers summarization)
- `/upload <path>` - Upload and summarize a document file

**Features:**
- First user message automatically generates a session title via LLM
- Session is automatically summarized when you exit
- Uploaded documents are immediately summarized
- All turns are logged as `Event` objects with `metadata.session_id`

## Testing

Run tests with pytest:

```bash
pytest tests/
```

### Test Structure

- **Unit Tests** (`tests/test_models.py`, `tests/test_serialization.py`, `tests/test_database.py`):
  - Schema validation
  - Serialization utilities
  - Database initialization

- **Integration Tests** (`tests/test_integration.py`):
  - End-to-end database operations
  - Topic hierarchy reconstruction
  - Context loading from multiple sessions
  - FTS search functionality

## Project Structure

```
.
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   └── base.py          # Pydantic models
│   ├── storage/
│   │   ├── __init__.py
│   │   └── schema.sql        # SQLite schema
│   ├── utils/
│   │   ├── __init__.py
│   │   └── serialization.py  # JSON utilities
│   └── config.py             # Configuration
├── scripts/
│   └── generate_stub_data.py # Stub data generator
├── tests/
│   ├── __init__.py
│   ├── test_models.py        # Model tests
│   ├── test_serialization.py # Serialization tests
│   ├── test_database.py      # Database tests
│   └── test_integration.py   # Integration tests
├── requirements.txt          # Dependencies
└── README.md                 # This file
```

## Development Status

### Block A: Core Data Infrastructure ✅

- [x] **PR #1**: Define Data Models and Schemas
- [x] **PR #2**: Database I/O Layer
- [x] **PR #3**: Vector Store & Embedding Pipeline

### Block B: AI Tutor Chat System

- [x] **PR #4**: AI Orchestration Layer
- [x] **PR #5**: Tutor Chat Interface (TUI)
- [ ] **PR #6**: Context Composition Engine

### Next Steps

- **Block C**: Transcript Ingestion Pipeline
- **Block D**: Spaced Repetition & Mastery Tracking

## License

[To be determined]

