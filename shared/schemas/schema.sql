-- Learned Context SDK Database Schema
-- SQLite schema for storing messages and file metadata for subconscious agents

-- Table for registered messages
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    message_hash TEXT NOT NULL,
    content TEXT NOT NULL,
    role TEXT NOT NULL,
    name TEXT,
    metadata TEXT,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP NULL,
    UNIQUE(agent_id, message_hash)
);

-- Table for registered files
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    size INTEGER,
    last_modified TIMESTAMP,
    label TEXT NOT NULL,
    description TEXT NOT NULL,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP NULL,
    UNIQUE(agent_id, file_path, file_hash)
);

-- Indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_messages_agent_hash ON messages(agent_id, message_hash);
CREATE INDEX IF NOT EXISTS idx_messages_agent_processed ON messages(agent_id, processed);
CREATE INDEX IF NOT EXISTS idx_files_agent_path ON files(agent_id, file_path);
CREATE INDEX IF NOT EXISTS idx_files_agent_processed ON files(agent_id, processed);