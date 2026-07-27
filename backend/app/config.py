"""
Environment-driven configuration using Pydantic BaseSettings.

All settings are read from environment variables or a .env file.
Import the singleton: `from app.config import settings`

To understand what each setting does, see .env.example.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings — loaded from environment variables / .env file."""

    # ── OpenRouter (LLM) ──
    OPENROUTER_API_KEY: str = ""
    LLM_MODEL: str = "openai/gpt-4o-mini"
    VISION_LLM_MODEL: str = "openai/gpt-4o-mini"
    APP_URL: str = "http://localhost:8000"

    # ── Embeddings ──
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_MODE: str = "local"  # "local" or "remote"
    HF_API_TOKEN: str = ""

    # ── Storage Paths ──
    CHROMA_DB_PATH: str = "./data/chroma_db"
    PARENT_STORE_PATH: str = "./data/parent_store.sqlite"
    LONG_TERM_DB_PATH: str = "./data/memory.sqlite"
    UPLOAD_DIR: str = "./data/uploads"
    IMAGE_DIR: str = "./data/images"

    # ── Retrieval ──
    RELEVANCE_THRESHOLD: float = 0.40
    RETRIEVAL_K: int = 5

    # ── Memory ──
    SUMMARY_TRIGGER: int = 20
    KEEP_RECENT: int = 6

    # ── LangSmith ──
    LANGSMITH_TRACING: str = "true"
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "ai-nexus-rag-engine"
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"

    # ── Server ──
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",  # don't fail on unknown env vars
    }

    def ensure_data_dirs(self) -> None:
        """Create all data directories at startup. Idempotent."""
        for dir_path in [self.CHROMA_DB_PATH, self.UPLOAD_DIR, self.IMAGE_DIR]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        # SQLite files are created on first connect,
        # but their parent directories need to exist
        for file_path in [self.PARENT_STORE_PATH, self.LONG_TERM_DB_PATH]:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    def setup_langsmith_env(self) -> None:
        """Push LangSmith settings into os.environ.
        
        LangChain/LangGraph read tracing config from env vars automatically.
        We set them here so they're available before the graph compiles.
        """
        if self.LANGSMITH_API_KEY:
            os.environ.setdefault("LANGSMITH_TRACING", self.LANGSMITH_TRACING)
            os.environ.setdefault("LANGSMITH_API_KEY", self.LANGSMITH_API_KEY)
            os.environ.setdefault("LANGSMITH_PROJECT", self.LANGSMITH_PROJECT)
            os.environ.setdefault("LANGSMITH_ENDPOINT", self.LANGSMITH_ENDPOINT)


# Singleton — imported by every other module
settings = Settings()
