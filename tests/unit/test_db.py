import re
import sqlite3

import pytest

import app.db
from app.analysis import AnalysisOutcome
from app.db import (
    DuplicateEmailError,
    connect,
    get_candidate,
    get_latest_succeeded_result,
    init_db,
    insert_analysis_run,
    insert_candidate,
)
from app.llm.output import AnalysisResult

ISO_UTC = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")


def _outcome(match_score: int | None, reference: str) -> AnalysisOutcome:
    """A succeeded outcome with that score, or a failed one when the score is None."""
    result = (
        None
        if match_score is None
        else AnalysisResult(
            skills=["python"],
            years_experience=3,
            summary="Resumen.",
            match_score=match_score,
        )
    )
    return AnalysisOutcome(
        status="failed" if result is None else "succeeded",
        result=result,
        error_code="llm_invalid_output" if result is None else None,
        error_detail="json_decode_error" if result is None else None,
        attempts=3 if result is None else 1,
        duration_ms=10,
        reference=reference,
        provider="scripted",
        model="scripted-v0",
        prompt_version="v1",
    )


def _insert_run(conn, candidate_id, match_score, reference):
    return insert_analysis_run(
        conn,
        candidate_id=candidate_id,
        job_title="Backend Developer",
        required_skills=["Python", "SQL"],
        outcome=_outcome(match_score, reference),
    )


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "test.db")
    init_db(path)
    return path


@pytest.fixture
def conn(db_path):
    conn = connect(db_path)
    yield conn
    conn.close()


def test_insert_and_get_candidate_roundtrip(conn):
    candidate_id = insert_candidate(
        conn,
        name="Ana Torres",
        email="ana.torres@example.com",
        cv_text="Backend Developer con 3 años de Python.",
    )
    row = get_candidate(conn, candidate_id)
    assert row["id"] == candidate_id
    assert row["name"] == "Ana Torres"
    assert row["email"] == "ana.torres@example.com"
    assert row["cv_text"] == "Backend Developer con 3 años de Python."
    assert ISO_UTC.match(row["created_at"])


def test_insert_duplicate_email_raises_duplicate_error(conn):
    insert_candidate(conn, name="Ana Torres", email="ana@example.com", cv_text="CV 1")
    with pytest.raises(DuplicateEmailError):
        insert_candidate(conn, name="Otra", email="ana@example.com", cv_text="CV 2")


def test_get_missing_candidate_returns_none(conn):
    assert get_candidate(conn, 999) is None


def test_init_db_twice_is_idempotent(db_path):
    init_db(db_path)


def test_insert_is_committed(db_path, conn):
    candidate_id = insert_candidate(
        conn, name="Ana Torres", email="ana@example.com", cv_text="CV"
    )
    other = connect(db_path)
    try:
        assert get_candidate(other, candidate_id) is not None
    finally:
        other.close()


def test_init_db_twice_keeps_existing_data(db_path, conn):
    candidate_id = insert_candidate(
        conn, name="Ana Torres", email="ana@example.com", cv_text="CV"
    )
    init_db(db_path)
    assert get_candidate(conn, candidate_id) is not None


def test_connect_enables_foreign_keys(db_path):
    conn = connect(db_path)
    try:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        conn.close()


# --- analysis_runs -----------------------------------------------------------


def _candidate(conn):
    return insert_candidate(
        conn, name="Ana Torres", email="ana@example.com", cv_text="CV"
    )


def test_insert_run_and_read_latest_result(conn):
    candidate_id = _candidate(conn)
    _insert_run(conn, candidate_id, 50, "a" * 16)
    assert get_latest_succeeded_result(conn, candidate_id) == {
        "skills": ["python"],
        "years_experience": 3.0,
        "summary": "Resumen.",
        "match_score": 50,
    }


def test_latest_is_newest_by_created_at_then_id(conn, monkeypatch):
    candidate_id = _candidate(conn)
    monkeypatch.setattr(app.db, "utc_now_iso", lambda: "2026-11-21T10:00:00Z")
    _insert_run(conn, candidate_id, 50, "a" * 16)
    _insert_run(conn, candidate_id, 70, "b" * 16)
    assert get_latest_succeeded_result(conn, candidate_id)["match_score"] == 70


def test_latest_ignores_failed_runs(conn):
    candidate_id = _candidate(conn)
    _insert_run(conn, candidate_id, 50, "a" * 16)
    _insert_run(conn, candidate_id, None, "b" * 16)
    assert get_latest_succeeded_result(conn, candidate_id)["match_score"] == 50


def test_latest_prefers_newer_created_at_over_higher_id(conn, monkeypatch):
    candidate_id = _candidate(conn)
    monkeypatch.setattr(app.db, "utc_now_iso", lambda: "2026-11-21T12:00:00Z")
    _insert_run(conn, candidate_id, 70, "a" * 16)
    monkeypatch.setattr(app.db, "utc_now_iso", lambda: "2026-11-21T10:00:00Z")
    _insert_run(conn, candidate_id, 50, "b" * 16)
    assert get_latest_succeeded_result(conn, candidate_id)["match_score"] == 70


def test_latest_is_isolated_per_candidate(conn):
    first = _candidate(conn)
    second = insert_candidate(
        conn, name="Ana Torres", email="otra@example.com", cv_text="CV"
    )
    _insert_run(conn, first, 50, "a" * 16)
    assert get_latest_succeeded_result(conn, second) is None


def test_duplicate_reference_rejected(conn):
    candidate_id = _candidate(conn)
    _insert_run(conn, candidate_id, 50, "a" * 16)
    with pytest.raises(sqlite3.IntegrityError):
        _insert_run(conn, candidate_id, 70, "a" * 16)
