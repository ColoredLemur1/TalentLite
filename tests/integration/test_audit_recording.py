"""Every analysis attempt, failed or succeeded, is recorded in analysis_runs."""

import json

from app.db import connect
from app.llm.base import LLMTimeoutError, LLMUnavailableError
from tests.helpers import candidate_payload, offer_payload, valid_output

CV_SENTENCE = "Backend Developer con 3 años de Python."


def _create(client, **overrides) -> int:
    r = client.post("/candidates", json=candidate_payload(**overrides))
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _analyze(client, candidate_id):
    return client.post(f"/candidates/{candidate_id}/analyze", json=offer_payload())


def _rows(settings):
    conn = connect(settings.database_path)
    try:
        return conn.execute("SELECT * FROM analysis_runs ORDER BY id").fetchall()
    finally:
        conn.close()


def test_failed_invalid_output_recorded_with_3_attempts(make_client, settings):
    client, _ = make_client(["{bad"])
    assert _analyze(client, _create(client)).status_code == 502
    [row] = _rows(settings)
    assert row["status"] == "failed"
    assert row["attempts"] == 3
    assert row["error_code"] == "llm_invalid_output"


def test_failed_timeout_recorded_with_1_attempt(make_client, settings):
    client, _ = make_client([LLMTimeoutError()])
    assert _analyze(client, _create(client)).status_code == 504
    [row] = _rows(settings)
    assert row["attempts"] == 1
    assert row["error_code"] == "llm_timeout"


def test_success_recorded_with_provider_model_prompt_version_attempts(client, settings):
    assert _analyze(client, _create(client)).status_code == 200
    [row] = _rows(settings)
    assert row["provider"] == "mock"
    assert row["model"] == "mock-keyword-v1"
    assert row["prompt_version"] == "v1"
    assert row["attempts"] == 1


def test_duration_ms_recorded(make_client, settings):
    fast, _ = make_client([valid_output()])
    slow, _ = make_client([valid_output()], delay_s=0.05)
    candidate_id = _create(fast)
    assert _analyze(fast, candidate_id).status_code == 200
    assert _analyze(slow, candidate_id).status_code == 200
    fast_row, slow_row = _rows(settings)
    assert fast_row["duration_ms"] >= 0
    assert slow_row["duration_ms"] >= 50


def test_error_detail_has_no_raw_output_or_cv_text(make_client, settings):
    client, _ = make_client([valid_output(summary=CV_SENTENCE * 20)])
    assert _analyze(client, _create(client, cv_text=CV_SENTENCE)).status_code == 502
    [row] = _rows(settings)
    assert CV_SENTENCE not in row["error_detail"]
    assert "summary" in row["error_detail"]


def test_analysis_runs_has_no_cv_column(client, settings):
    conn = connect(settings.database_path)
    try:
        columns = {c["name"] for c in conn.execute("PRAGMA table_info(analysis_runs)")}
    finally:
        conn.close()
    assert "cv_text" not in columns


def test_latest_analysis_is_last_succeeded_even_after_failure(make_client):
    # Call 1 succeeds; every later call repeats "{bad", so the second analysis fails.
    client, _ = make_client([valid_output(), "{bad"])
    candidate_id = _create(client)
    success = _analyze(client, candidate_id).json()
    assert _analyze(client, candidate_id).status_code == 502
    latest = client.get(f"/candidates/{candidate_id}").json()["latest_analysis"]
    assert latest == success


def test_latest_analysis_null_when_only_failures(make_client):
    client, _ = make_client(["{bad"])
    candidate_id = _create(client)
    assert _analyze(client, candidate_id).status_code == 502
    assert client.get(f"/candidates/{candidate_id}").json()["latest_analysis"] is None


def test_failed_row_reference_matches_response(make_client, settings):
    client, _ = make_client(["{bad"])
    r = _analyze(client, _create(client))
    assert r.status_code == 502
    [row] = _rows(settings)
    assert row["reference"] == r.json()["error"]["reference"]


def test_failed_row_stores_null_result_and_offer(make_client, settings):
    client, _ = make_client(["{bad"])
    assert _analyze(client, _create(client)).status_code == 502
    [row] = _rows(settings)
    assert row["result"] is None
    assert row["job_title"] == "Backend Developer"
    assert json.loads(row["required_skills"]) == offer_payload()["required_skills"]


def test_failed_provider_error_recorded(make_client, settings):
    client, _ = make_client([LLMUnavailableError()])
    assert _analyze(client, _create(client)).status_code == 502
    [row] = _rows(settings)
    assert row["status"] == "failed"
    assert row["attempts"] == 1
    assert row["error_code"] == "llm_unavailable"
    assert row["error_detail"] == "provider_error:LLMUnavailableError"
