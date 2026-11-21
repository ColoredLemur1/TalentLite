import re

import pytest

from app.db import (
    DuplicateEmailError,
    connect,
    get_candidate,
    init_db,
    insert_candidate,
)

ISO_UTC = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")


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
