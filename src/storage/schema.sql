-- SQLite schema for AI Tutor Proof of Concept
-- Supports hierarchical topics, event storage, and state management

-- Enable FTS5 for full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS events_fts USING fts5(
    event_id UNINDEXED,
    content,
    topics,
    skills,
    content='events',
    content_rowid='id'
);

-- Events table: stores all interactions (chats, transcripts, quizzes)
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    content TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK(event_type IN ('chat', 'transcript', 'quiz', 'assessment')),
    actor TEXT NOT NULL CHECK(actor IN ('student', 'tutor', 'system')),
    topics TEXT NOT NULL DEFAULT '[]',  -- JSON array of topic identifiers
    skills TEXT NOT NULL DEFAULT '[]',  -- JSON array of skill identifiers
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    recorded_at TIMESTAMP,
    embedding BLOB,  -- Serialized embedding vector
    embedding_id INTEGER,
    metadata TEXT NOT NULL DEFAULT '{}',  -- JSON metadata
    source TEXT
);

-- Indexes for events
CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_events_recorded_at ON events(recorded_at);
CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_actor ON events(actor);
CREATE INDEX IF NOT EXISTS idx_events_embedding_id ON events(embedding_id);
-- Index for topic queries (using JSON extraction)
CREATE INDEX IF NOT EXISTS idx_events_topics ON events(topics);

-- Skills table: stores mastery state for individual skills
CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_id TEXT UNIQUE NOT NULL,
    p_mastery REAL NOT NULL CHECK(p_mastery >= 0.0 AND p_mastery <= 1.0) DEFAULT 0.5,
    last_evidence_at TIMESTAMP,
    evidence_count INTEGER NOT NULL DEFAULT 0,
    topic_id TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT NOT NULL DEFAULT '{}'  -- JSON metadata
);

-- Indexes for skills
CREATE INDEX IF NOT EXISTS idx_skills_skill_id ON skills(skill_id);
CREATE INDEX IF NOT EXISTS idx_skills_topic_id ON skills(topic_id);
CREATE INDEX IF NOT EXISTS idx_skills_p_mastery ON skills(p_mastery);
CREATE INDEX IF NOT EXISTS idx_skills_last_evidence_at ON skills(last_evidence_at);

-- Topics table: stores hierarchical topic summaries
CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id TEXT UNIQUE NOT NULL,
    parent_topic_id TEXT,  -- NULL for root topics
    summary TEXT NOT NULL,
    open_questions TEXT NOT NULL DEFAULT '[]',  -- JSON array of questions
    event_count INTEGER NOT NULL DEFAULT 0,
    last_event_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT NOT NULL DEFAULT '{}',  -- JSON metadata
    FOREIGN KEY (parent_topic_id) REFERENCES topics(topic_id) ON DELETE SET NULL
);

-- Indexes for topics
CREATE INDEX IF NOT EXISTS idx_topics_topic_id ON topics(topic_id);
CREATE INDEX IF NOT EXISTS idx_topics_parent_topic_id ON topics(parent_topic_id);
CREATE INDEX IF NOT EXISTS idx_topics_last_event_at ON topics(last_event_at);

-- Goals table: stores learning goals and objectives
CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    topic_ids TEXT NOT NULL DEFAULT '[]',  -- JSON array of topic identifiers
    skill_ids TEXT NOT NULL DEFAULT '[]',  -- JSON array of skill identifiers
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'completed', 'archived')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    target_date TIMESTAMP,
    completed_at TIMESTAMP,
    metadata TEXT NOT NULL DEFAULT '{}'  -- JSON metadata
);

-- Indexes for goals
CREATE INDEX IF NOT EXISTS idx_goals_goal_id ON goals(goal_id);
CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);
CREATE INDEX IF NOT EXISTS idx_goals_target_date ON goals(target_date);

-- Commitments table: stores study commitments and plans
CREATE TABLE IF NOT EXISTS commitments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    commitment_id TEXT UNIQUE NOT NULL,
    description TEXT NOT NULL,
    frequency TEXT NOT NULL CHECK(frequency IN ('daily', 'weekly', 'custom')),
    duration_minutes INTEGER,
    topic_ids TEXT NOT NULL DEFAULT '[]',  -- JSON array of topic identifiers
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'completed', 'paused')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    metadata TEXT NOT NULL DEFAULT '{}'  -- JSON metadata
);

-- Indexes for commitments
CREATE INDEX IF NOT EXISTS idx_commitments_commitment_id ON commitments(commitment_id);
CREATE INDEX IF NOT EXISTS idx_commitments_status ON commitments(status);
CREATE INDEX IF NOT EXISTS idx_commitments_start_date ON commitments(start_date);

-- Nudge logs table: stores system nudges and reminders
CREATE TABLE IF NOT EXISTS nudge_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nudge_id TEXT UNIQUE NOT NULL,
    nudge_type TEXT NOT NULL CHECK(nudge_type IN ('reminder', 'motivation', 'review_prompt')),
    message TEXT NOT NULL,
    topic_ids TEXT NOT NULL DEFAULT '[]',  -- JSON array of topic identifiers
    commitment_id TEXT,
    status TEXT NOT NULL DEFAULT 'sent' CHECK(status IN ('sent', 'acknowledged', 'dismissed')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP,
    metadata TEXT NOT NULL DEFAULT '{}'  -- JSON metadata
);

-- Indexes for nudge logs
CREATE INDEX IF NOT EXISTS idx_nudge_logs_nudge_id ON nudge_logs(nudge_id);
CREATE INDEX IF NOT EXISTS idx_nudge_logs_nudge_type ON nudge_logs(nudge_type);
CREATE INDEX IF NOT EXISTS idx_nudge_logs_status ON nudge_logs(status);
CREATE INDEX IF NOT EXISTS idx_nudge_logs_created_at ON nudge_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_nudge_logs_commitment_id ON nudge_logs(commitment_id);

-- Trigger to update events_fts when events are inserted/updated/deleted
CREATE TRIGGER IF NOT EXISTS events_fts_insert AFTER INSERT ON events BEGIN
    INSERT INTO events_fts(rowid, event_id, content, topics, skills)
    VALUES (new.id, new.event_id, new.content, new.topics, new.skills);
END;

CREATE TRIGGER IF NOT EXISTS events_fts_update AFTER UPDATE ON events BEGIN
    UPDATE events_fts SET
        content = new.content,
        topics = new.topics,
        skills = new.skills
    WHERE rowid = new.id;
END;

CREATE TRIGGER IF NOT EXISTS events_fts_delete AFTER DELETE ON events BEGIN
    DELETE FROM events_fts WHERE rowid = old.id;
END;

-- Trigger to update updated_at timestamp for skills
CREATE TRIGGER IF NOT EXISTS skills_update_timestamp AFTER UPDATE ON skills BEGIN
    UPDATE skills SET updated_at = CURRENT_TIMESTAMP WHERE id = new.id;
END;

-- Trigger to update updated_at timestamp for topics
CREATE TRIGGER IF NOT EXISTS topics_update_timestamp AFTER UPDATE ON topics BEGIN
    UPDATE topics SET updated_at = CURRENT_TIMESTAMP WHERE id = new.id;
END;

