"""
SQLite hash cache for image descriptions.

Avoids duplicate vision LLM calls when the same image (e.g. company logo, header graphic)
appears repeatedly across pages or files.
Uses thread-local connection manager with WAL mode & busy_timeout.
"""

import time
from app.db import get_db_connection
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


def init_db():
    """Initialize image cache table."""
    with get_db_connection(settings.IMAGE_CACHE_DB_PATH) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS image_cache (
            image_hash TEXT PRIMARY KEY,
            description TEXT,
            created_at REAL
        )""")
    logger.info("Image cache DB initialized")


def get_cached_description(image_hash: str) -> str | None:
    """Retrieve cached description by SHA256 image hash if it exists."""
    with get_db_connection(settings.IMAGE_CACHE_DB_PATH) as c:
        row = c.execute(
            "SELECT description FROM image_cache WHERE image_hash=?",
            (image_hash,),
        ).fetchone()
    if row:
        logger.debug(f"Image cache HIT for hash: {image_hash[:10]}...")
        return row[0]
    return None


def cache_description(image_hash: str, description: str):
    """Store image description indexed by SHA256 hash."""
    with get_db_connection(settings.IMAGE_CACHE_DB_PATH) as c:
        c.execute(
            "REPLACE INTO image_cache VALUES (?,?,?)",
            (image_hash, description, time.time()),
        )
    logger.debug(f"Image cache STORED for hash: {image_hash[:10]}...")
