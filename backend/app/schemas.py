from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisRequest(BaseModel):
    mode: Literal["startup", "company_comparison"]
    query: str = Field(min_length=3, max_length=2000)
    project_name: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default="General", max_length=120)


class ReportResponse(BaseModel):
    id: int
    title: str
    mode: str
    input_text: str
    content: dict[str, Any]
    viability_score: float
    confidence_score: float
    created_at: datetime

    model_config = {"from_attributes": True}


class FeedbackRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=2000)


class DocumentUploadResponse(BaseModel):
    id: int
    filename: str
    collection: str
    chunk_count: int


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    collection: str | None = None
    limit: int = Field(default=5, ge=1, le=20)


class UrlIngestRequest(BaseModel):
    url: str = Field(min_length=8, max_length=2000)
    collection: str = Field(default="Web Research", max_length=120)
