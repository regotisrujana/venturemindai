from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "VentureMind AI"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/venturemind"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    search_provider: str = "tavily"
    search_api_key: str = ""
    chroma_path: str = "./chroma"
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173,https://venturemindai-taupe.vercel.app"
    rate_limit: str = "120/minute"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def is_postgresql(self) -> bool:
        return self.database_url.startswith(("postgresql://", "postgresql+psycopg://"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
