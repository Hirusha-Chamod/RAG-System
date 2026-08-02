"""
SQLite storage for parent document text.

Keyed by `parent_id`. Used by retrieve_node during the parent-fetch hop.
Supports listing user documents and deleting documents.
Uses thread-local connection manager with WAL mode & busy_timeout.
"""

from app.db import get_db_connection
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


def init_db():
    """Initialize parent_store SQLite table."""
    with get_db_connection(settings.PARENT_STORE_PATH) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS parents (
            parent_id TEXT PRIMARY KEY,
            content TEXT,
            source TEXT,
            user_id TEXT
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_parents_user ON parents (user_id)")
    logger.info("Parent store DB initialized")


def save_parent(parent_id: str, content: str, source: str, user_id: str):
    """Store or update a parent document entry."""
    with get_db_connection(settings.PARENT_STORE_PATH) as c:
        c.execute(
            "REPLACE INTO parents VALUES (?,?,?,?)",
            (parent_id, content, source, user_id),
        )


def get_parents(parent_ids: list[str]) -> dict[str, str]:
    """Fetch parent content for a list of parent_ids. Returns {parent_id: content}."""
    if not parent_ids:
        return {}
    with get_db_connection(settings.PARENT_STORE_PATH) as c:
        placeholders = ",".join("?" for _ in parent_ids)
        rows = c.execute(
            f"SELECT parent_id, content FROM parents WHERE parent_id IN ({placeholders})",
            parent_ids,
        ).fetchall()
    return dict(rows)


def get_user_documents(user_id: str) -> list[dict]:
    """List distinct document sources and chunk counts for a specific user."""
    with get_db_connection(settings.PARENT_STORE_PATH) as c:
        rows = c.execute(
            """SELECT source, COUNT(parent_id) as count 
               FROM parents 
               WHERE user_id=? 
               GROUP BY source""",
            (user_id,),
        ).fetchall()
    return [{"source": r[0], "parent_chunks": r[1]} for r in rows]


def delete_user_document(user_id: str, source: str) -> int:
    """Delete all parent entries for a given user and document source."""
    with get_db_connection(settings.PARENT_STORE_PATH) as c:
        cur = c.execute(
            "DELETE FROM parents WHERE user_id=? AND source=?",
            (user_id, source),
        )
        return cur.rowcount
