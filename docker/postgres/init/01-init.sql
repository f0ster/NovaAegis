-- Initialize database for NovaAegis's knowledge store

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS knowledge;
CREATE SCHEMA IF NOT EXISTS research;

-- Knowledge tables
CREATE TABLE knowledge.papers (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    abstract TEXT,
    authors TEXT[],
    published_date TIMESTAMP,
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    tags TEXT[],
    metadata JSONB
);

CREATE TABLE knowledge.concepts (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    confidence FLOAT NOT NULL DEFAULT 0.0,
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE TABLE knowledge.relationships (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id uuid REFERENCES knowledge.concepts(id),
    target_id uuid REFERENCES knowledge.concepts(id),
    type TEXT NOT NULL,
    confidence FLOAT NOT NULL DEFAULT 0.0,
    evidence JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Create a join table for patterns and concepts
CREATE TABLE knowledge.pattern_concepts (
    pattern_id uuid,
    concept_id uuid REFERENCES knowledge.concepts(id),
    PRIMARY KEY (pattern_id, concept_id)
);

CREATE TABLE knowledge.patterns (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    support_count INTEGER NOT NULL DEFAULT 0,
    confidence FLOAT NOT NULL DEFAULT 0.0,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Research tables
CREATE TABLE research.tasks (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    priority INTEGER NOT NULL DEFAULT 0,
    params JSONB,
    result JSONB,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE TABLE research.visual_states (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id uuid REFERENCES research.tasks(id),
    type TEXT NOT NULL,
    screenshot BYTEA,
    html_snapshot TEXT,
    context JSONB,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Indexes
CREATE INDEX papers_tags_idx ON knowledge.papers USING gin (tags);
CREATE INDEX relationships_type_idx ON knowledge.relationships(type);
CREATE INDEX tasks_status_idx ON research.tasks(status);
CREATE INDEX tasks_type_idx ON research.tasks(type);

-- Functions
CREATE OR REPLACE FUNCTION update_last_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers
CREATE TRIGGER concepts_updated
    BEFORE UPDATE ON knowledge.concepts
    FOR EACH ROW
    EXECUTE FUNCTION update_last_updated_at();

CREATE TRIGGER patterns_updated
    BEFORE UPDATE ON knowledge.patterns
    FOR EACH ROW
    EXECUTE FUNCTION update_last_updated_at();