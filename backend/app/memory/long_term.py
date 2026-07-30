"""
SQLite Long-Term User Memory Store (`memory.sqlite`).

Stores user-specific facts, background, and preferences across sessions keyed by user_id.
Uses WAL mode for non-blocking concurrent operations.
"""

import sqlite3
import json
import time
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


def _conn():
    conn = sqlite3.connect(settings.LONG_TERM_DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Initialize long-term user_memory SQLite table."""
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS user_memory (
            user_id TEXT,
            key TEXT,
            value TEXT,
            updated_at REAL,
            PRIMARY KEY (user_id, key)
        )""")
    logger.info("Long-term memory DB initialized")


def set_memory(user_id: str, key: str, value: str):
    """Store or update a long-term memory entry for a user."""
    with _conn() as c:
        c.execute(
            "REPLACE INTO user_memory VALUES (?,?,?,?)",
            (user_id, key, value, time.time()),
        )
    logger.info(f"Memory saved for user={user_id}, key={key}")


def get_all_memory(user_id: str) -> dict[str, str]:
    """Retrieve all memory entries for a user as {key: value} dict."""
    with _conn() as c:
        rows = c.execute(
            "SELECT key, value FROM user_memory WHERE user_id=? ORDER BY updated_at DESC",
            (user_id,),
        ).fetchall()
    return dict(rows)


def delete_memory_key(user_id: str, key: str):
    """Delete a specific memory key for a user."""
    with _conn() as c:
        c.execute("DELETE FROM user_memory WHERE user_id=? AND key=?", (user_id, key))
    logger.info(f"Memory key '{key}' deleted for user={user_id}")


def delete_all_memory(user_id: str):
    """Clear all long-term memory entries for a user."""
    with _conn() as c:
        c.execute("DELETE FROM user_memory WHERE user_id=?", (user_id,))
    logger.info(f"All long-term memory cleared for user={user_id}")
