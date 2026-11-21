import sqlite3
from collections.abc import Iterator
from datetime import UTC, datetime

from fastapi import Request

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    cv_text TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def connect(path: str) -> sqlite3.Connection:
    # check_same_thread=False: FastAPI may open the connection in one worker thread and
    # use it in another. Each connection still serves a single request, one step at a time.
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path: str) -> None:
    conn = connect(path)
    try:
        conn.executescript(SCHEMA_SQL)
    finally:
        conn.close()


def get_db(request: Request) -> Iterator[sqlite3.Connection]:
    """FastAPI dependency: one connection per request, always closed afterwards."""
    conn = connect(request.app.state.settings.database_path)
    try:
        yield conn
    finally:
        conn.close()


def utc_now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class DuplicateEmailError(Exception):
    """A candidate with this email already exists. It carries no values."""


def insert_candidate(
    conn: sqlite3.Connection, *, name: str, email: str, cv_text: str
) -> int:
    """Inserts and commits. The UNIQUE constraint detects duplicates; there is no pre-check."""
    try:
        cursor = conn.execute(
            "INSERT INTO candidates (name, email, cv_text, created_at) "
            "VALUES (?, ?, ?, ?)",
            (name, email, cv_text, utc_now_iso()),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        if exc.sqlite_errorname == "SQLITE_CONSTRAINT_UNIQUE":
            raise DuplicateEmailError() from None
        raise
    return cursor.lastrowid


def get_candidate(conn: sqlite3.Connection, candidate_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT id, name, email, cv_text, created_at FROM candidates WHERE id = ?",
        (candidate_id,),
    ).fetchone()
