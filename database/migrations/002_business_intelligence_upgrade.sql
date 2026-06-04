ALTER TABLE agent_logs ADD COLUMN IF NOT EXISTS input_json JSONB NOT NULL DEFAULT '{}';
ALTER TABLE agent_logs ADD COLUMN IF NOT EXISTS evidence_json JSONB NOT NULL DEFAULT '{}';
ALTER TABLE agent_logs ADD COLUMN IF NOT EXISTS reasoning_summary TEXT NOT NULL DEFAULT '';
ALTER TABLE agent_logs ADD COLUMN IF NOT EXISTS output_json JSONB NOT NULL DEFAULT '{}';
ALTER TABLE evaluation_metrics ADD COLUMN IF NOT EXISTS citation_correctness DOUBLE PRECISION NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    website_url TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS research_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    query TEXT NOT NULL,
    mode VARCHAR(50) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'running',
    sources_collected INTEGER NOT NULL DEFAULT 0,
    rejected_sources INTEGER NOT NULL DEFAULT 0,
    confidence_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS comparisons (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    report_id INTEGER REFERENCES reports(id),
    query TEXT NOT NULL,
    entities JSONB NOT NULL DEFAULT '{}',
    summary TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS web_sources (
    id SERIAL PRIMARY KEY,
    research_session_id INTEGER REFERENCES research_sessions(id),
    report_id INTEGER REFERENCES reports(id),
    title VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    snippet TEXT NOT NULL,
    source_type VARCHAR(80) NOT NULL DEFAULT 'web',
    confidence_score DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    collected_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS source_evidence (
    id SERIAL PRIMARY KEY,
    report_id INTEGER NOT NULL REFERENCES reports(id),
    title VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    snippet TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    collected_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES uploaded_documents(id),
    chunk_id VARCHAR(120) NOT NULL,
    source TEXT NOT NULL,
    page_number INTEGER,
    text TEXT NOT NULL,
    metadata_json JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_web_sources_report ON web_sources(report_id);
CREATE INDEX IF NOT EXISTS idx_web_sources_session ON web_sources(research_session_id);
CREATE INDEX IF NOT EXISTS idx_research_sessions_user_created ON research_sessions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_document_chunks_chunk_id ON document_chunks(chunk_id);
CREATE INDEX IF NOT EXISTS idx_source_evidence_report ON source_evidence(report_id);
