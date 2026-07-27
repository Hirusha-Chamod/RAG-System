"""
Pydantic request/response models for all API endpoints.

These define the contract between the backend and any client (React UI, AI Nexus, etc.).
FastAPI uses these to auto-generate OpenAPI docs at /docs.
"""

from pydantic import BaseModel
from typing import Optional, Literal


# ──────────────────────────────────────────────
# Ingest (Phase 2)
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
# Chat (Phase 3)
# ──────────────────────────────────────────────

class ChatRequest(BaseModel):
    """Request body for POST /chat."""
    message: str
    user_id: str
    session_id: str


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


# ──────────────────────────────────────────────
# Retrieve (Phase 3)
# ──────────────────────────────────────────────

class RetrieveRequest(BaseModel):
    """Request body for POST /retrieve — raw retrieval, no LLM."""
    query: str
    user_id: str
    k: int = 5


class RetrieveResponse(BaseModel):
    """Response from POST /retrieve — matching chunks with scores."""
    results: list[SourceDoc]
    query: str


# ──────────────────────────────────────────────
# Memory (Phase 4)
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
