"""
Pydantic request/response models for all API endpoints.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, Literal


# ──────────────────────────────────────────────
# Authentication
# ──────────────────────────────────────────────

class UserSignupRequest(BaseModel):
    """Request body for POST /auth/signup."""
    username: str
    email: EmailStr
    password: str


class UserLoginRequest(BaseModel):
    """Request body for POST /auth/login."""
    username_or_email: str
    password: str


class TokenResponse(BaseModel):
    """JWT response from POST /auth/login or POST /auth/signup."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    email: str


class UserResponse(BaseModel):
    """Authenticated user info response."""
    user_id: str
    username: str
    email: str
    created_at: float


# ──────────────────────────────────────────────
# Ingest
# ──────────────────────────────────────────────

class IngestFileResult(BaseModel):
    """Result of processing a single uploaded file."""
    filename: str
    status: Literal["success", "error"]
    chunks_created: int = 0
    images_processed: int = 0
    error_message: Optional[str] = None


class IngestResponse(BaseModel):
    """Response from POST /ingest — per-file results + totals."""
    results: list[IngestFileResult]
    total_chunks: int
    total_images: int


# ──────────────────────────────────────────────
# Chat
# ──────────────────────────────────────────────

class ChatRequest(BaseModel):
    """Request body for POST /chat."""
    message: str
    session_id: str
    model: Optional[str] = None


class SourceDoc(BaseModel):
    """A single retrieved document with its relevance score."""
    content: str
    score: float
    source: str


class ChatResponse(BaseModel):
    """Response from POST /chat — answer + sources + metadata."""
    answer: str
    sources: list[SourceDoc]
    session_id: str
    relevance_ok: bool
    relevance_action: Literal["synthesize", "clarify", "fallback"] = "fallback"
    model_used: str


# ──────────────────────────────────────────────
# Retrieve
# ──────────────────────────────────────────────

class RetrieveRequest(BaseModel):
    """Request body for POST /retrieve — raw retrieval, no LLM."""
    query: str
    k: int = 5


class RetrieveResponse(BaseModel):
    """Response from POST /retrieve — matching chunks with scores."""
    results: list[SourceDoc]
    query: str


# ──────────────────────────────────────────────
# Memory
# ──────────────────────────────────────────────

class MemoryEntry(BaseModel):
    """A single long-term memory entry."""
    key: str
    value: dict
    updated_at: float


class MemoryResponse(BaseModel):
    """Response from GET /memory — all entries for a user."""
    user_id: str
    memories: list[MemoryEntry]
