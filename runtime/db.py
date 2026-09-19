"""
db.py — Concurrency-safe SQLite WAL state storage engine for NanoHat v3.0.0.
Manages persistent user memory and scheduled tasks at ~/.local/state/nanohat/state.db.
"""

import os
import sqlite3
from pathlib import Path
from typing import Optional

DEFAULT_DB_DIR = Path(os.environ.get("XDG_STATE_HOME", os.path.expanduser("~/.local/state"))) / "nanohat"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "state.db"


def get_db_path() -> str:
    """Returns the configured state database path, respecting NANOHAT_DB_PATH."""
    return os.environ.get("NANOHAT_DB_PATH", str(DEFAULT_DB_PATH))


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Creates a connection to the SQLite state database with WAL mode enabled."""
    path = db_path or get_db_path()
    if path != ":memory:":
        os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path, timeout=5.0)
    conn.row_factory = sqlite3.Row
    if path != ":memory:":
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initializes the database schema if tables do not exist."""
    conn = get_connection(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_memory (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                due_time TEXT NOT NULL,
                notify_minutes_before INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
    finally:
        conn.close()
