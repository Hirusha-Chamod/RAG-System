"""
Environment-driven configuration using Pydantic BaseSettings.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings — loaded from environment variables / .env file."""

    # ── JWT Authentication ──
    JWT_SECRET_KEY: str = "ai-nexus-rag-engine-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # ── OpenRouter (LLM) ──
    OPENROUTER_API_KEY: str = ""
    LLM_MODEL: str = "tencent/hy3:free"
    VISION_LLM_MODEL: str = "nvidia/nemotron-nano-12b-v2-vl:free"
    SUMMARY_MODEL: str = "nvidia/nemotron-nano-9b-v2:free"
    DEFAULT_MODEL: str = "tencent/hy3:free"
    APP_URL: str = "http://localhost:8000"

    # Server-side whitelisted models for client selection (/models endpoint)
    ALLOWED_MODELS: dict[str, str] = {
        "tencent/hy3:free": "Tencent Hy3 (Balanced, built for grounded/anti-hallucination answers)",
        "google/gemma-4-31b-it:free": "Gemma 4 31B (Strong document understanding)",
        "nvidia/nemotron-3-super-120b-a12b:free": "Nemotron 3 Super (Best for very large documents, 1M context)",
        "openai/gpt-oss-20b:free": "GPT-OSS 20B (Fastest responses)",
    }

    # ── Embeddings & Reranking ──
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_MODE: str = "local"  # "local" or "remote"
    HF_API_TOKEN: str = ""
    RERANK_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # ── Storage Paths ──
    CHROMA_DB_PATH: str = "./data/chroma_db"
    PARENT_STORE_PATH: str = "./data/parent_store.sqlite"
    LONG_TERM_DB_PATH: str = "./data/memory.sqlite"
    IMAGE_CACHE_DB_PATH: str = "./data/image_cache.sqlite"
    USERS_DB_PATH: str = "./data/users.sqlite"
    UPLOAD_DIR: str = "./data/uploads"
    IMAGE_DIR: str = "./data/images"

    # ── Retrieval & 3-Way Decision Thresholds ──
    # Reranker Logits: Pass (>= 0.0), Clarify (-2.0 to 0.0), Fallback (< -2.0)
    RERANK_PASS_THRESHOLD: float = 0.0
    RERANK_CLARIFY_THRESHOLD: float = -2.0
    RETRIEVAL_K: int = 15          # Widened Stage 1 vector search candidates
    TOP_N_SYNTHESIS: int = 5       # Final re-ranked top parents sent to LLM

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
        "extra": "ignore",
    }

    def ensure_data_dirs(self) -> None:
        """Create all data directories at startup. Idempotent."""
        for dir_path in [self.CHROMA_DB_PATH, self.UPLOAD_DIR, self.IMAGE_DIR]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        for file_path in [
            self.PARENT_STORE_PATH,
            self.LONG_TERM_DB_PATH,
            self.IMAGE_CACHE_DB_PATH,
            self.USERS_DB_PATH,
        ]:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    def setup_langsmith_env(self) -> None:
        """Push LangSmith settings into os.environ."""
        if self.LANGSMITH_API_KEY:
            os.environ.setdefault("LANGSMITH_TRACING", self.LANGSMITH_TRACING)
            os.environ.setdefault("LANGSMITH_API_KEY", self.LANGSMITH_API_KEY)
            os.environ.setdefault("LANGSMITH_PROJECT", self.LANGSMITH_PROJECT)
            os.environ.setdefault("LANGSMITH_ENDPOINT", self.LANGSMITH_ENDPOINT)


# Singleton
settings = Settings()
