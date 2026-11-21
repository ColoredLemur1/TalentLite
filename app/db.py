import json
import sqlite3
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from fastapi import Request

if TYPE_CHECKING:
    from app.analysis import AnalysisOutcome

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    cv_text TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- One row per analysis attempt cycle. There is deliberately no copy of the CV here.
CREATE TABLE IF NOT EXISTS analysis_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL REFERENCES candidates(id),
    created_at TEXT NOT NULL,
    job_title TEXT NOT NULL,
    required_skills TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    attempts INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('succeeded', 'failed')),
    result TEXT,
    error_code TEXT,
    error_detail TEXT,
    reference TEXT NOT NULL UNIQUE,
    duration_ms INTEGER NOT NULL
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


def insert_analysis_run(
    conn: sqlite3.Connection,
    *,
    candidate_id: int,
    job_title: str,
    required_skills: list[str],
    outcome: "AnalysisOutcome",
) -> int:
    """Stores one analysis outcome and commits. A failed outcome stores a null result."""
    result_json = (
        None
        if outcome.result is None
        else json.dumps(outcome.result.model_dump(), ensure_ascii=False)
    )
    try:
        cursor = conn.execute(
            "INSERT INTO analysis_runs (candidate_id, created_at, job_title, "
            "required_skills, provider, model, prompt_version, attempts, status, "
            "result, error_code, error_detail, reference, duration_ms) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                candidate_id,
                utc_now_iso(),
                job_title,
                json.dumps(required_skills, ensure_ascii=False),
                outcome.provider,
                outcome.model,
                outcome.prompt_version,
                outcome.attempts,
                outcome.status,
                result_json,
                outcome.error_code,
                outcome.error_detail,
                outcome.reference,
                outcome.duration_ms,
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise
    return cursor.lastrowid


LATEST_SUCCEEDED_SQL = (
    "SELECT result FROM analysis_runs "
    "WHERE candidate_id = ? AND status = ? "
    "ORDER BY created_at DESC, id DESC LIMIT 1"
)


def get_latest_succeeded_result(
    conn: sqlite3.Connection, candidate_id: int
) -> dict | None:
    """The newest succeeded result (4 fields, as stored), or None if there is none."""
    row = conn.execute(LATEST_SUCCEEDED_SQL, (candidate_id, "succeeded")).fetchone()
    return None if row is None else json.loads(row["result"])
