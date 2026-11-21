"""Yellow tests Y1 and Y2: they measure and report, never assert, never block."""

import statistics
import time

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db import connect, init_db, utc_now_iso
from app.main import create_app
from tests.helpers import TEST_API_KEY, candidate_payload
from tests.perf.report import report

Y1_POSTS = 50
Y2_SIZES = (10, 1_000, 10_000)
CV_19999 = "a" * 19_999


def _ms_since(start: float) -> float:
    return (time.perf_counter() - start) * 1000


@pytest.mark.performance
def test_perf_post_cv_20000_chars(client):
    durations = []
    for i in range(Y1_POSTS):
        payload = candidate_payload(email=f"y1-{i}@example.com", cv_text=CV_19999)
        start = time.perf_counter()
        client.post("/candidates", json=payload)
        durations.append(_ms_since(start))

    report(
        f"Y1 · POST /candidates with a 19,999-character CV ({Y1_POSTS} requests)",
        [
            ("median", statistics.median(durations), "ms"),
            ("p95", statistics.quantiles(durations, n=100)[94], "ms"),
        ],
    )


def _seed(path: str, size: int) -> None:
    init_db(path)
    now = utc_now_iso()
    conn = connect(path)
    try:
        conn.executemany(
            "INSERT INTO candidates (name, email, cv_text, created_at) "
            "VALUES (?, ?, ?, ?)",
            [(f"Seed {i}", f"seed-{i}@example.com", "CV", now) for i in range(size)],
        )
        conn.commit()
    finally:
        conn.close()


@pytest.mark.performance
def test_perf_email_lookup_among_many(tmp_path):
    rows = []
    plan = ""
    for size in Y2_SIZES:
        path = str(tmp_path / f"y2_{size}.db")
        _seed(path, size)
        app = create_app(Settings(api_key=TEST_API_KEY, database_path=path))
        with TestClient(app, headers={"X-API-Key": TEST_API_KEY}) as client:
            start = time.perf_counter()
            client.post("/candidates", json=candidate_payload(email="new@example.com"))
            rows.append((f"new POST, {size} candidates", _ms_since(start), "ms"))

            start = time.perf_counter()
            client.post(
                "/candidates", json=candidate_payload(email="seed-0@example.com")
            )
            rows.append((f"duplicate POST, {size} candidates", _ms_since(start), "ms"))

        conn = connect(path)
        try:
            plan = " / ".join(
                row["detail"]
                for row in conn.execute(
                    "EXPLAIN QUERY PLAN SELECT id FROM candidates WHERE email = ?",
                    ("seed-0@example.com",),
                )
            )
        finally:
            conn.close()

    rows.append(("query plan for email lookup", plan, "text"))
    report("Y2 · Email lookup among many candidates", rows)
