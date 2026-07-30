"""
AI Nexus RAG Engine — FastAPI application entry point.

Start the server:
    uvicorn app.main:app --reload

API docs:
    http://localhost:8000/docs
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.utils.logging import setup_logging, get_logger
from app.auth.users_db import init_db as init_users_db
from app.ingestion.parent_store import init_db as init_parent_store
from app.ingestion.image_cache import init_db as init_image_cache
from app.memory.long_term import init_db as init_long_term_memory
from app.core.graph import build_graph
from app.api.routes_auth import router as auth_router
from app.api.routes_ingest import router as ingest_router
from app.api.routes_chat import router as chat_router
from app.api.routes_retrieve import router as retrieve_router
from app.api.routes_memory import router as memory_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle for the FastAPI app."""
    # ── Startup ──
    setup_logging()
    logger.info("Starting AI Nexus RAG Engine...")

    # Create data directories
    settings.ensure_data_dirs()
    logger.info("Data directories verified")

    # Configure LangSmith tracing
    settings.setup_langsmith_env()
    if settings.LANGSMITH_API_KEY:
        logger.info(f"LangSmith tracing enabled → project: {settings.LANGSMITH_PROJECT}")
    else:
        logger.info("LangSmith tracing disabled (no API key)")

    # Initialize SQLite databases
    init_users_db()
    init_parent_store()
    init_image_cache()
    init_long_term_memory()

    # Compile the LangGraph workflow once at startup and store on app.state
    app.state.graph = build_graph()
    logger.info("LangGraph workflow compiled and stored on app.state")

    logger.info(f"Server ready — docs at {settings.APP_URL}/docs")

    yield

    # ── Shutdown ──
    logger.info("Shutting down AI Nexus RAG Engine...")


# ── Create FastAPI application ──
app = FastAPI(
    title="AI Nexus RAG Engine",
    description="RAG-powered chatbot backend with JWT authentication, multi-session memory, "
                "long-term user memory, document ingestion, and image understanding.",
    version="0.4.0",
    lifespan=lifespan,
)

# ── CORS middleware ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount routers ──
app.include_router(auth_router)
app.include_router(ingest_router, tags=["Ingestion"])
app.include_router(chat_router, tags=["Chat"])
app.include_router(retrieve_router, tags=["Retrieval"])
app.include_router(memory_router)


# ── Health check ──
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.4.0",
        "embedding_mode": settings.EMBEDDING_MODE,
        "llm_model": settings.LLM_MODEL,
    }


@app.get("/models", tags=["System"])
async def list_models():
    """Returns the dictionary of whitelisted free models available for client selection."""
    return {
        "default_model": settings.DEFAULT_MODEL,
        "models": settings.ALLOWED_MODELS,
    }
