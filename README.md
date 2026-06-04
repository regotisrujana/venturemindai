# VentureMind AI

Multi-Agent Business Research & Competitive Strategy Platform.

VentureMind AI is a production-oriented GenAI capstone project with a FastAPI backend, React SaaS frontend, PostgreSQL schema, ChromaDB-ready RAG pipeline, LangGraph-style multi-agent workflow, evaluation metrics, RBAC security, and report exports.

## Features

- JWT authentication with `user` and `admin` roles
- User dashboard for projects, analyses, reports, scorecards, and history
- Admin dashboard for users, reports, agent usage, analytics, logs, evaluation, and security events
- Three analysis modes:
  - Startup idea analysis
  - Company comparison
  - Startup vs competitors
- RAG pipeline: document upload, chunking, embeddings, retrieval, citations, confidence scoring
- Multi-agent workflow: supervisor, research, competitor, SWOT, financial, strategy, critic, report
- Business scorecard and final viability score
- Evaluation metrics for accuracy, relevance, faithfulness, hallucination rate, latency, cost, feedback
- Prompt-injection checks, rate limiting, input validation, audit logs, security events
- PDF and DOCX report generation endpoints

## Repository

```text
backend/        FastAPI API, services, models, agents, RAG, reporting
frontend/       React + Tailwind + React Router + Recharts UI
docs/           Architecture, API, deployment, implementation guide
database/       PostgreSQL schema and seed data
render.yaml     Render backend deployment config
vercel.json     Vercel frontend deployment config
```

## Quick Start

Start PostgreSQL first:

```powershell
docker compose up -d postgres
```

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

Demo users are created by the seed script:

- User: `founder@venturemind.ai` / `Founder123!`
- Admin: `admin@venturemind.ai` / `Admin123!`

## Environment

Backend variables live in `backend/.env`.

```env
DATABASE_URL=postgresql+psycopg://user:password@host:5432/venturemind
JWT_SECRET=replace-with-a-long-random-secret
GROQ_API_KEY=your-groq-key
GROQ_MODEL=llama3-70b-8192
SEARCH_PROVIDER=tavily
SEARCH_API_KEY=your-tavily-serpapi-or-brave-key
CHROMA_PATH=./chroma
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-key
ALLOWED_ORIGINS=http://localhost:5173
```

Frontend variables live in `frontend/.env`.

```env
VITE_API_URL=http://localhost:8000
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [API Documentation](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Implementation Plan](docs/IMPLEMENTATION_PLAN.md)

## Production Notes

- Deploy frontend to Vercel with `frontend` as the root directory.
- Deploy backend to Render with `render.yaml`.
- Use Neon PostgreSQL for `DATABASE_URL`.
- Persist ChromaDB on a Render disk or use a managed vector database adapter.
- Set all secrets in platform environment variables. Do not commit `.env`.
