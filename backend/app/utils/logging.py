"""
Structured logging setup for the AI Nexus RAG Engine.

Usage:
    from app.utils.logging import get_logger
    logger = get_logger(__name__)
    logger.info("Something happened")
"""

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger with a clean, readable format.
    
    Called once at app startup from main.py's lifespan.
    """
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,  # override any existing config
    )

    # Quiet down noisy libraries
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger. Use __name__ as the name for module-level loggers."""
    return logging.getLogger(name)
