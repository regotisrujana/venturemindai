from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

from app.api import admin, analysis, auth, dashboard, rag, reports
from app.core.config import get_settings
from app.core.database import Base, engine
from sqlalchemy import text

settings = get_settings()
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])

app = FastAPI(title=settings.app_name, version="1.0.0", docs_url="/api/docs", openapi_url="/api/openapi.json")
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(_, exc):
    return JSONResponse(status_code=429, content={"detail": f"Rate limit exceeded: {exc.detail}"})


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": settings.app_name, "environment": settings.environment}


@app.get("/api/health/db")
def database_health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok", "database": "postgresql"}


app.include_router(auth.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")
app.include_router(rag.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
