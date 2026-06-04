CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(30) NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    industry VARCHAR(120) NOT NULL DEFAULT 'General',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    website_url TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE research_sessions (
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

CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    mode VARCHAR(50) NOT NULL CHECK (mode IN ('startup', 'company_comparison', 'startup_vs_competitors')),
    input_text TEXT NOT NULL,
    content JSONB NOT NULL,
    viability_score DOUBLE PRECISION NOT NULL,
    confidence_score DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE comparisons (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    report_id INTEGER REFERENCES reports(id),
    query TEXT NOT NULL,
    entities JSONB NOT NULL DEFAULT '{}',
    summary TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE agent_logs (
    id SERIAL PRIMARY KEY,
    report_id INTEGER REFERENCES reports(id),
    agent_name VARCHAR(80) NOT NULL,
    status VARCHAR(40) NOT NULL,
    latency_ms INTEGER NOT NULL DEFAULT 0,
    token_estimate INTEGER NOT NULL DEFAULT 0,
    message TEXT NOT NULL DEFAULT '',
    input_json JSONB NOT NULL DEFAULT '{}',
    evidence_json JSONB NOT NULL DEFAULT '{}',
    reasoning_summary TEXT NOT NULL DEFAULT '',
    output_json JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(120) NOT NULL,
    resource VARCHAR(120) NOT NULL,
    metadata_json JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE feedback (
    id SERIAL PRIMARY KEY,
    report_id INTEGER NOT NULL REFERENCES reports(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE uploaded_documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    filename VARCHAR(255) NOT NULL,
    collection VARCHAR(120) NOT NULL,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    metadata_json JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES uploaded_documents(id),
    chunk_id VARCHAR(120) NOT NULL,
    source TEXT NOT NULL,
    page_number INTEGER,
    text TEXT NOT NULL,
    metadata_json JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE evaluation_metrics (
    id SERIAL PRIMARY KEY,
    report_id INTEGER REFERENCES reports(id),
    accuracy DOUBLE PRECISION NOT NULL,
    relevance DOUBLE PRECISION NOT NULL,
    faithfulness DOUBLE PRECISION NOT NULL,
    citation_correctness DOUBLE PRECISION NOT NULL DEFAULT 0,
    hallucination_rate DOUBLE PRECISION NOT NULL,
    latency_ms INTEGER NOT NULL,
    cost_usd DOUBLE PRECISION NOT NULL,
    feedback_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE source_evidence (
    id SERIAL PRIMARY KEY,
    report_id INTEGER REFERENCES reports(id),
    title VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    snippet TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    collected_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE web_sources (
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

CREATE TABLE security_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    severity VARCHAR(30) NOT NULL,
    event_type VARCHAR(120) NOT NULL,
    description TEXT NOT NULL,
    metadata_json JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE analysis_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    mode VARCHAR(50) NOT NULL,
    query TEXT NOT NULL,
    report_id INTEGER REFERENCES reports(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reports_user_created ON reports(user_id, created_at DESC);
CREATE INDEX idx_projects_owner ON projects(owner_id);
CREATE INDEX idx_agent_logs_agent ON agent_logs(agent_name);
CREATE INDEX idx_document_chunks_chunk_id ON document_chunks(chunk_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at DESC);
CREATE INDEX idx_security_events_created ON security_events(created_at DESC);
CREATE INDEX idx_source_evidence_report ON source_evidence(report_id);
CREATE INDEX idx_web_sources_report ON web_sources(report_id);
CREATE INDEX idx_web_sources_session ON web_sources(research_session_id);
CREATE INDEX idx_research_sessions_user_created ON research_sessions(user_id, created_at DESC);
