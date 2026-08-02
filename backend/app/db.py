"""
Thread-local SQLite connection manager with WAL mode and 5s busy_timeout.

Prevents connection leaks and handles concurrent SQLite access cleanly.
"""

import sqlite3
import threading
from contextlib import contextmanager
from app.utils.logging import get_logger

logger = get_logger(__name__)

_local = threading.local()


@contextmanager
def get_db_connection(db_path: str):
    """Thread-local SQLite connection context manager with WAL mode & busy timeout."""
    if not hasattr(_local, "connections"):
        _local.connections = {}

    if db_path not in _local.connections:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        _local.connections[db_path] = conn

    conn = _local.connections[db_path]
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
