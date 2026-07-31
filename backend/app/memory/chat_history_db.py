"""
SQLite Chat History Persistence Store (`chat_history.sqlite`).

Persists turn-by-turn chat messages per user_id and session_id.
Uses WAL mode for non-blocking concurrent operations.
"""

import sqlite3
import json
import time
import uuid
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


def _conn():
    conn = sqlite3.connect("./data/chat_history.sqlite")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Initialize chat_history SQLite table."""
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS chat_history (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            sender TEXT NOT NULL,
            text TEXT NOT NULL,
            sources TEXT,
            relevance_action TEXT,
            model_used TEXT,
            created_at REAL NOT NULL
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_chat_user_session ON chat_history (user_id, session_id)")
    logger.info("Chat history DB initialized")


def save_chat_message(
    user_id: str,
    session_id: str,
    sender: str,
    text: str,
    sources: list | None = None,
    relevance_action: str | None = None,
    model_used: str | None = None,
) -> dict:
    """Save a single chat message (user or assistant) to SQLite."""
    msg_id = f"{sender[:3]}_{uuid.uuid4().hex[:12]}"
    created_at = time.time()
    sources_json = json.dumps(sources) if sources else None

    with _conn() as c:
        c.execute(
            """INSERT INTO chat_history 
               (id, user_id, session_id, sender, text, sources, relevance_action, model_used, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (msg_id, user_id, session_id, sender, text, sources_json, relevance_action, model_used, created_at),
        )

    return {
        "id": msg_id,
        "sender": sender,
        "text": text,
        "sources": sources or [],
        "relevance_action": relevance_action,
        "model_used": model_used,
        "timestamp": time.strftime("%H:%M", time.localtime(created_at)),
    }


def get_chat_history(user_id: str, session_id: str) -> list[dict]:
    """Fetch all saved chat messages for a specific user and session, ordered chronologically."""
    with _conn() as c:
        rows = c.execute(
            """SELECT id, sender, text, sources, relevance_action, model_used, created_at
               FROM chat_history
               WHERE user_id=? AND session_id=?
               ORDER BY created_at ASC""",
            (user_id, session_id),
        ).fetchall()

    result = []
    for r in rows:
        sources_list = json.loads(r[3]) if r[3] else []
        result.append({
            "id": r[0],
            "sender": r[1],
            "text": r[2],
            "sources": sources_list,
            "relevance_action": r[4],
            "model_used": r[5],
            "timestamp": time.strftime("%H:%M", time.localtime(r[6])),
        })
    return result


def get_user_sessions(user_id: str) -> list[str]:
    """Fetch list of distinct session_ids for a user."""
    with _conn() as c:
        rows = c.execute(
            "SELECT DISTINCT session_id FROM chat_history WHERE user_id=? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
    return [r[0] for r in rows]
