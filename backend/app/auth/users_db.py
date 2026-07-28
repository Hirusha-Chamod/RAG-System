"""
SQLite User Store (`users.sqlite`).

Stores user accounts: user_id, username, email, hashed_password, created_at.
Uses WAL mode for non-blocking concurrent reads/writes.
"""

import sqlite3
import time
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


def _conn():
    conn = sqlite3.connect(settings.USERS_DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Initialize users table."""
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            hashed_password TEXT,
            created_at REAL
        )""")
    logger.info("Users DB initialized")


def create_user(user_id: str, username: str, email: str, hashed_password: str) -> dict:
    """Create a new user account."""
    created_at = time.time()
    with _conn() as c:
        c.execute(
            "INSERT INTO users VALUES (?,?,?,?,?)",
            (user_id, username.lower(), email.lower(), hashed_password, created_at),
        )
    logger.info(f"User created: {username} ({user_id})")
    return {
        "user_id": user_id,
        "username": username.lower(),
        "email": email.lower(),
        "created_at": created_at,
    }


def get_user_by_username_or_email(identifier: str) -> dict | None:
    """Find a user by username OR email."""
    ident = identifier.lower()
    with _conn() as c:
        row = c.execute(
            "SELECT user_id, username, email, hashed_password, created_at FROM users WHERE username=? OR email=?",
            (ident, ident),
        ).fetchone()
    if row:
        return {
            "user_id": row[0],
            "username": row[1],
            "email": row[2],
            "hashed_password": row[3],
            "created_at": row[4],
        }
    return None


def get_user_by_id(user_id: str) -> dict | None:
    """Find a user by user_id."""
    with _conn() as c:
        row = c.execute(
            "SELECT user_id, username, email, hashed_password, created_at FROM users WHERE user_id=?",
            (user_id,),
        ).fetchone()
    if row:
        return {
            "user_id": row[0],
            "username": row[1],
            "email": row[2],
            "hashed_password": row[3],
            "created_at": row[4],
        }
    return None
