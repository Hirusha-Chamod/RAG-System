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

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle for the FastAPI app.
    
    Startup:
        - Configure logging
        - Create data directories
        - Set LangSmith environment variables
        - (Phase 2) Initialize SQLite databases
        - (Phase 3) Compile LangGraph workflow
    
    Shutdown:
        - Cleanup resources if needed
    """
    # ── Startup ──
    setup_logging()
    logger.info("Starting AI Nexus RAG Engine...")

    # Create data directories (uploads, chroma_db, images)
    settings.ensure_data_dirs()
    logger.info("Data directories verified")

    # Configure LangSmith tracing (env vars read by LangChain automatically)
    settings.setup_langsmith_env()
    if settings.LANGSMITH_API_KEY:
        logger.info(f"LangSmith tracing enabled → project: {settings.LANGSMITH_PROJECT}")
    else:
        logger.info("LangSmith tracing disabled (no API key)")

    # Phase 2: Initialize parent store + long-term memory databases
    # from app.ingestion.parent_store import init_db as init_parent_store
    # from app.memory.long_term import init_db as init_long_term_memory
    # init_parent_store()
    # init_long_term_memory()

    # Phase 3: Compile the LangGraph workflow and store on app.state
    # from app.core.graph import build_graph
    # app.state.graph = build_graph()
    # logger.info("LangGraph workflow compiled")

    logger.info(f"Server ready — docs at {settings.APP_URL}/docs")

    yield

    # ── Shutdown ──
    logger.info("Shutting down AI Nexus RAG Engine...")


# ── Create the FastAPI application ──
app = FastAPI(
    title="AI Nexus RAG Engine",
    description="RAG-powered chatbot backend with multi-session memory, "
                "document ingestion, and image understanding.",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS middleware — allows the React frontend to call the API ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount routers (uncommented as phases are completed) ──
# Phase 2:
# from app.api.routes_ingest import router as ingest_router
# app.include_router(ingest_router, tags=["Ingestion"])

# Phase 3:
# from app.api.routes_chat import router as chat_router
# from app.api.routes_retrieve import router as retrieve_router
# app.include_router(chat_router, tags=["Chat"])
# app.include_router(retrieve_router, tags=["Retrieval"])

# Phase 4:
# from app.api.routes_memory import router as memory_router
# app.include_router(memory_router, tags=["Memory"])


# ── Health check ──
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint. Returns 200 if the server is running."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "embedding_mode": settings.EMBEDDING_MODE,
        "llm_model": settings.LLM_MODEL,
    }
