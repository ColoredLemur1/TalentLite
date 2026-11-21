"""Yellow test Y4: a candidate with many analyses, before the candidate_id index (branch 8).

It measures and reports; it never asserts or blocks.
"""

import json
import statistics
import time
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db import AUDIT_PAGE_SQL, LATEST_SUCCEEDED_SQL, connect, init_db
from app.main import create_app
from tests.helpers import TEST_API_KEY
from tests.perf.report import report

Y4_SIZES = (1_000, 10_000)
OTHER_CANDIDATES = 5
REPEATS = 5
RESULT_JSON = json.dumps(
    {
        "skills": ["python"],
        "years_experience": 3,
        "summary": "Resumen.",
        "match_score": 50,
    }
)


def _seed(path: str, runs_per_candidate: int) -> int:
    """One target candidate plus 5 others, each with that many runs; every 5th failed."""
    init_db(path)
    start = datetime(2026, 1, 1, tzinfo=UTC)
    conn = connect(path)
    try:
        candidate_ids = []
        for i in range(1 + OTHER_CANDIDATES):
            cursor = conn.execute(
                "INSERT INTO candidates (name, email, cv_text, created_at) "
                "VALUES (?, ?, ?, ?)",
                (f"Seed {i}", f"seed-{i}@example.com", "CV", "2026-01-01T00:00:00Z"),
            )
            candidate_ids.append(cursor.lastrowid)
        rows = []
        for candidate_id in candidate_ids:
            for n in range(runs_per_candidate):
                failed = n % 5 == 4
                created = (start + timedelta(seconds=n)).strftime("%Y-%m-%dT%H:%M:%SZ")
                rows.append(
                    (
                        candidate_id,
                        created,
                        "Backend Developer",
                        '["Python"]',
                        "mock",
                        "mock-keyword-v1",
                        "v1",
                        3 if failed else 1,
                        "failed" if failed else "succeeded",
                        None if failed else RESULT_JSON,
                        "llm_invalid_output" if failed else None,
                        "json_decode_error" if failed else None,
                        f"{candidate_id:04d}{n:012d}",
                        10,
                    )
                )
        conn.executemany(
            "INSERT INTO analysis_runs (candidate_id, created_at, job_title, "
            "required_skills, provider, model, prompt_version, attempts, status, "
            "result, error_code, error_detail, reference, duration_ms) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        conn.commit()
        return candidate_ids[0]
    finally:
        conn.close()


def _median_ms(client: TestClient, url: str) -> float:
    durations = []
    for _ in range(REPEATS):
        start = time.perf_counter()
        client.get(url)
        durations.append((time.perf_counter() - start) * 1000)
    return statistics.median(durations)


def _plan(path: str, sql: str, params: tuple) -> str:
    conn = connect(path)
    try:
        rows = conn.execute(f"EXPLAIN QUERY PLAN {sql}", params).fetchall()
        return " / ".join(row["detail"] for row in rows)
    finally:
        conn.close()


@pytest.mark.performance
def test_perf_candidate_with_many_analyses(tmp_path):
    rows = []
    path = ""
    for size in Y4_SIZES:
        path = str(tmp_path / f"y4_{size}.db")
        candidate_id = _seed(path, size)
        app = create_app(Settings(api_key=TEST_API_KEY, database_path=path))
        with TestClient(app, headers={"X-API-Key": TEST_API_KEY}) as client:
            base = f"/candidates/{candidate_id}"
            rows.append((f"GET candidate, {size} runs", _median_ms(client, base), "ms"))
            rows.append(
                (
                    f"audit first page, {size} runs",
                    _median_ms(client, f"{base}/audit?offset=0"),
                    "ms",
                )
            )
            rows.append(
                (
                    f"audit last page, {size} runs",
                    _median_ms(client, f"{base}/audit?offset={size - 20}"),
                    "ms",
                )
            )

    rows.append(
        (
            "plan: latest succeeded",
            _plan(path, LATEST_SUCCEEDED_SQL, (1, "succeeded")),
            "text",
        )
    )
    rows.append(("plan: audit page", _plan(path, AUDIT_PAGE_SQL, (1, 20, 0)), "text"))
    report(
        f"Y4 · Candidate with many analyses, among {OTHER_CANDIDATES} others "
        f"(median of {REPEATS} requests)",
        rows,
    )
