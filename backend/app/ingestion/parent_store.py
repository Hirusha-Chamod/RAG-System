"""
SQLite storage for parent document text.

Keyed by `parent_id`. Used by retrieve_node during the parent-fetch hop.
"""

import sqlite3
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


def _conn():
    conn = sqlite3.connect(settings.PARENT_STORE_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Initialize parent_store SQLite table."""
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS parents (
            parent_id TEXT PRIMARY KEY,
            content TEXT,
            source TEXT,
            user_id TEXT
        )""")
    logger.info("Parent store DB initialized")


def save_parent(parent_id: str, content: str, source: str, user_id: str):
    """Store or update a parent document entry."""
    with _conn() as c:
        c.execute(
            "REPLACE INTO parents VALUES (?,?,?,?)",
            (parent_id, content, source, user_id),
        )


def get_parents(parent_ids: list[str]) -> dict[str, str]:
    """Fetch parent content for a list of parent_ids. Returns {parent_id: content}."""
    if not parent_ids:
        return {}
    with _conn() as c:
        placeholders = ",".join("?" for _ in parent_ids)
        rows = c.execute(
            f"SELECT parent_id, content FROM parents WHERE parent_id IN ({placeholders})",
            parent_ids,
        ).fetchall()
    return dict(rows)
