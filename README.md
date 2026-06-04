# VentureMind AI

**AI-powered multi-agent startup idea analysis and company comparison platform**

VentureMind AI helps founders, students, and early-stage teams research startup ideas or compare companies using web research, citations, optional document evidence, and readable business reports.

## Project Title

**VentureMind AI: Multi-Agent Business Research and Competitive Intelligence Platform**

## Problem Statement

Startup founders often need market research, competitor analysis, pricing comparison, SWOT analysis, and strategy recommendations before validating an idea. Doing this manually takes time, requires checking many sources, and can lead to unsupported assumptions.

VentureMind AI solves this by allowing a user to enter a startup idea or company comparison, then automatically collecting public evidence, checking citations, and generating a structured business report.

## Key Features

- Startup idea analysis with market, product, pricing, SWOT, risk, and strategy sections
- Company comparison for inputs like `Canva vs Adobe Express` or `Zomato vs Swiggy`
- Multi-agent workflow with supervisor, research, competitor, SWOT, strategy, critic, and report agents
- Web research using trusted public sources and optional search API providers
- PostgreSQL for users, reports, comparisons, logs, metrics, security events, and feedback
- ChromaDB for RAG, uploaded document chunks, ingested URL chunks, embeddings, and semantic search
- Clean readable reports instead of raw JSON or backend dictionaries
- Citation-aware output with source links and confidence indicators
- Optional knowledge base upload and URL ingestion for supporting evidence
- Admin-only evaluation and security dashboards
- PDF and DOCX report export
- Responsive React interface with hover states, skeleton loading, and clean report cards

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | React, Vite, Tailwind CSS, React Router, Recharts, Lucide Icons |
| Backend | FastAPI, SQLAlchemy, Pydantic, Uvicorn |
| Database | PostgreSQL |
| Vector Store | ChromaDB |
| AI / LLM | Groq-compatible LLM configuration |
| Search | Tavily, SerpAPI, or Brave Search through `SEARCH_PROVIDER` and `SEARCH_API_KEY` |
| Auth / Security | JWT authentication, role-based access, prompt-injection checks, rate limiting |
| Reports | Backend report formatter, PDF export, DOCX export |

## Architecture Design

```mermaid
flowchart TD
    User["User enters startup idea or company comparison"] --> Frontend["React + Vite Frontend"]
    Frontend --> API["FastAPI Backend"]
    API --> Auth["JWT Auth + RBAC"]
    API --> Supervisor["Supervisor Agent"]
    Supervisor --> Research["Web Research Agent"]
    Supervisor --> Competitor["Competitor Agent"]
    Supervisor --> SWOT["SWOT Agent"]
    Supervisor --> Strategy["Strategy Agent"]
    Supervisor --> Critic["Critic Agent"]
    Research --> SearchAPI["Search Provider: Tavily / SerpAPI / Brave"]
    Research --> Chroma["ChromaDB Vector Store"]
    API --> Postgres["PostgreSQL Structured Data"]
    Chroma --> Formatter["Report Formatter"]
    Competitor --> Formatter
    SWOT --> Formatter
    Strategy --> Formatter
    Critic --> Formatter
    Formatter --> Report["Readable Business Report + Citations"]
    Report --> Exports["PDF / DOCX Exports"]
    Postgres --> Admin["Admin Dashboards: Evaluation + Security"]
```

## How It Works

1. The user enters a startup idea or company comparison.
2. The Supervisor Agent identifies what research is needed.
3. The Web Research Agent searches public sources such as official websites, product pages, pricing pages, and trusted business sources.
4. Optional uploaded documents or ingested URLs are stored in ChromaDB for semantic retrieval.
5. The Competitor, SWOT, and Strategy agents analyze only the collected evidence.
6. The Critic Agent checks whether important claims have sources.
7. The Report Agent formats everything into a readable business report.
8. Reports, logs, metrics, feedback, and security events are saved in PostgreSQL.

## Installation Steps

### Prerequisites

- Python 3.11 or later
- Node.js 18 or later
- PostgreSQL 15 or later
- Git

### 1. Clone the Repository

```powershell
git clone https://github.com/regotisrujana/venturemindai.git
cd VentureMindAI
```

### 2. Create PostgreSQL Database

If PostgreSQL is installed locally on Windows, use PowerShell with the call operator:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\createdb.exe" -U postgres venturemind
```

If your PostgreSQL path or version is different, update the path accordingly.

### 3. Backend Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Update `backend/.env` with your PostgreSQL password and API keys.

Start the backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Backend URL:

```text
http://127.0.0.1:8000
```

Database health check:

```text
http://127.0.0.1:8000/health/db
```

### 4. Frontend Setup

Open a new terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend URL:

```text
http://127.0.0.1:5173
```

## Environmental Variables

Backend variables are stored in `backend/.env`.

```env
APP_NAME=VentureMind AI
ENVIRONMENT=development
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/venturemind
JWT_SECRET=change-me-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120
GROQ_API_KEY=
GROQ_MODEL=llama3-70b-8192
SEARCH_PROVIDER=tavily
SEARCH_API_KEY=
CHROMA_PATH=./chroma
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
RATE_LIMIT=120/minute
```

Frontend variables can be stored in `frontend/.env`.

```env
VITE_API_URL=http://127.0.0.1:8000
```

## Demo Link

- Local frontend demo: [http://127.0.0.1:5173](http://127.0.0.1:5173)
- Local backend API: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- GitHub repository: [https://github.com/regotisrujana/venturemindai](https://github.com/regotisrujana/venturemindai)
- Hosted demo: Add deployment URL after hosting

## Screenshots

### User Dashboard

![User Dashboard](docs/screenshots/user-dashboard.png)

### Dashboard Report History

![Dashboard Report History](docs/screenshots/dashboard-report-list.png)

### Startup Idea Analysis

![Startup Idea Analysis](docs/screenshots/startup-analysis.png)

### Knowledge Base

![Knowledge Base](docs/screenshots/knowledge-base.png)

### Admin Dashboard

![Admin Dashboard](docs/screenshots/admin-dashboard.png)

### Evaluation Dashboard

![Evaluation Dashboard](docs/screenshots/evaluation-dashboard.png)

## Evaluation

The project tracks report quality and system performance through evaluation metrics stored in PostgreSQL.

- Accuracy
- Relevance
- Faithfulness
- Citation correctness
- Hallucination rate
- Latency
- Cost per query
- User feedback

These metrics are shown in the admin evaluation dashboard to help understand whether generated reports are useful, cited, and reliable.

## Challenges Overcome

- Replaced SQLite usage with PostgreSQL for structured application data
- Kept ChromaDB only for RAG, embeddings, document chunks, and semantic search
- Converted raw JSON-like report output into readable business report sections
- Improved web research so users do not need to upload documents for every company
- Added source cleaning to remove boilerplate, login text, menus, and irrelevant snippets
- Prevented unsupported financial numbers from appearing unless directly verified
- Simplified company comparison so it focuses on useful comparison data instead of unnecessary scorecards
- Moved analytics, security, and evaluation views into admin-only areas
- Improved frontend responsiveness, hover states, loading skeletons, and visual theme

## Future Improvements

- Add background job processing for long-running research tasks
- Improve source ranking with domain authority and freshness signals
- Add deployment-ready cloud PostgreSQL and managed vector database support
- Add richer charts for comparison and evaluation dashboards
- Add more export templates for investor summaries and academic reports
- Add per-agent LLM routing for better cost and quality control
- Add automated screenshot capture for README and presentation updates
- Add stronger company entity detection for complex user inputs

## Repository Structure

```text
backend/        FastAPI API, database models, services, agents, RAG, reports
frontend/       React + Vite user interface
database/       PostgreSQL schema and seed data
docs/           Architecture, API, deployment, and project documentation
tools/          Utility scripts
outputs/        Generated local outputs, ignored from Git
```

## Author Info

**Name:** Regoti Srujana  
**PIN:** 24EG505H01  
**Branch:** CSE  
**GitHub:** [regotisrujana](https://github.com/regotisrujana)
