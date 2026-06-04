# Deployment Guide

## Frontend: Vercel

1. Create a Vercel project with `frontend` as the root directory.
2. Set build command: `npm run build`.
3. Set output directory: `dist`.
4. Add environment variable:

```env
VITE_API_URL=https://your-render-api.onrender.com
```

## Backend: Render

1. Create a Render Web Service connected to this repository.
2. Use `render.yaml` or configure manually:
   - Root directory: `backend`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Add a persistent disk if using local ChromaDB.
4. Add environment variables:

```env
DATABASE_URL=postgresql+psycopg://user:password@host:5432/venturemind
JWT_SECRET=long-random-production-secret
GROQ_API_KEY=your-groq-key
GROQ_MODEL=llama3-70b-8192
SEARCH_PROVIDER=tavily
SEARCH_API_KEY=your-search-provider-key
CHROMA_PATH=/var/data/chroma
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-key
ALLOWED_ORIGINS=https://your-frontend.vercel.app
```

## PostgreSQL: Neon

1. Create a Neon project.
2. Run `database/schema.sql` in the Neon SQL editor.
3. Use the pooled connection string as `DATABASE_URL`.

## ChromaDB

For this capstone, the local backend service exposes a Chroma-ready RAG abstraction. In production:

- Use Render persistent disk at `/var/data/chroma`, or
- Swap `RAGService` internals to a managed Chroma server or compatible vector store.

## LangSmith and RAGAS

Set `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_API_KEY` in Render. The evaluation service persists quality metrics and is designed to be extended with live RAGAS dataset evaluation jobs.

## Production Checklist

- Rotate `JWT_SECRET`.
- Restrict `ALLOWED_ORIGINS`.
- Use HTTPS-only frontend/backend URLs.
- Configure Render health checks at `/api/health`.
- Keep `.env` files out of git.
- Seed demo users only in non-production.
