"""The analysis_runs queries use the candidate_id index instead of scanning the table.

SQLite differs across the Mac, the Docker image and the CI runner, and each words query
plans a little differently. So these tests assert only the index name and the absence of
"SCAN analysis_runs", never the whole plan text.
"""

import pytest

from app.db import (
    AUDIT_COUNT_SQL,
    AUDIT_PAGE_SQL,
    LATEST_SUCCEEDED_SQL,
    connect,
    init_db,
)

INDEX = "idx_analysis_runs_candidate"


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "plans.db")
    init_db(path)
    return path


def _plan(path: str, sql: str, params: tuple) -> str:
    conn = connect(path)
    try:
        rows = conn.execute(f"EXPLAIN QUERY PLAN {sql}", params).fetchall()
        return " / ".join(row["detail"] for row in rows)
    finally:
        conn.close()


def _assert_uses_index(plan: str) -> None:
    assert INDEX in plan, plan
    assert "SCAN analysis_runs" not in plan, plan


def test_get_latest_analysis_query_uses_candidate_index(db_path):
    _assert_uses_index(_plan(db_path, LATEST_SUCCEEDED_SQL, (1, "succeeded")))


def test_audit_query_uses_candidate_index(db_path):
    _assert_uses_index(_plan(db_path, AUDIT_PAGE_SQL, (1, 20, 0)))
    _assert_uses_index(_plan(db_path, AUDIT_COUNT_SQL, (1,)))


def test_startup_twice_is_idempotent(db_path):
    init_db(db_path)
    conn = connect(db_path)
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type = 'index' AND name = ?",
            (INDEX,),
        ).fetchone()[0]
    finally:
        conn.close()
    assert count == 1
