"""POST /candidates/{id}/analyze and latest_analysis in GET /candidates/{id}."""

import json
import logging

from app.db import connect
from app.llm.base import LLMTimeoutError, LLMUnavailableError
from tests.helpers import candidate_payload, offer_payload, read_cv, valid_output

RESULT_FIELDS = {"skills", "years_experience", "summary", "match_score"}
AI_INTERNALS = (
    "provider",
    "model",
    "prompt_version",
    "attempts",
    "reference",
    "error_detail",
)


def _create(client, **overrides) -> int:
    r = client.post("/candidates", json=candidate_payload(**overrides))
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _analyze(client, candidate_id, **overrides):
    return client.post(
        f"/candidates/{candidate_id}/analyze", json=offer_payload(**overrides)
    )


def _assert_422(r):
    assert r.status_code == 422, r.text
    assert r.json()["error"]["code"] == "validation_error"


# --- Success -----------------------------------------------------------------


def test_analyze_returns_200_with_four_fields(client):
    r = _analyze(client, _create(client))
    assert r.status_code == 200, r.text
    assert set(r.json()) == RESULT_FIELDS


def test_analyze_missing_candidate_returns_404_without_calling_llm(make_client):
    client, llm = make_client([valid_output()])
    r = _analyze(client, 999)
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"
    assert llm.calls == 0


# --- Request limits ----------------------------------------------------------


def test_analyze_job_title_limits(client):
    candidate_id = _create(client)
    _assert_422(_analyze(client, candidate_id, job_title=""))
    assert _analyze(client, candidate_id, job_title="a" * 200).status_code == 200
    _assert_422(_analyze(client, candidate_id, job_title="a" * 201))


def test_analyze_required_skills_limits(client):
    candidate_id = _create(client)
    for skills in ([], [f"s{i}" for i in range(31)], ["a" * 51], [" "]):
        _assert_422(_analyze(client, candidate_id, required_skills=skills))


def test_analyze_duplicate_skills_case_insensitive_returns_422(client):
    candidate_id = _create(client)
    _assert_422(_analyze(client, candidate_id, required_skills=["Python", "python"]))


def test_analyze_extra_field_returns_422(client):
    candidate_id = _create(client)
    r = client.post(
        f"/candidates/{candidate_id}/analyze", json={**offer_payload(), "cv_text": "x"}
    )
    _assert_422(r)


# --- latest_analysis in GET --------------------------------------------------


def test_get_after_analyze_includes_latest_analysis(client):
    candidate_id = _create(client)
    analysis = _analyze(client, candidate_id).json()
    assert (
        client.get(f"/candidates/{candidate_id}").json()["latest_analysis"] == analysis
    )


def test_get_before_any_analysis_has_latest_analysis_null(client):
    candidate_id = _create(client)
    assert client.get(f"/candidates/{candidate_id}").json()["latest_analysis"] is None


def test_get_has_exactly_the_brief_fields(client):
    candidate_id = _create(client)
    _analyze(client, candidate_id)
    body = client.get(f"/candidates/{candidate_id}").json()
    assert set(body) == {
        "id",
        "name",
        "email",
        "cv_text",
        "created_at",
        "latest_analysis",
    }
    assert set(body["latest_analysis"]) == RESULT_FIELDS


def test_get_never_exposes_ai_internals(client):
    candidate_id = _create(client)
    _analyze(client, candidate_id)
    r = client.get(f"/candidates/{candidate_id}")
    body = r.json()
    for key in AI_INTERNALS:
        assert key not in body, key
        assert key not in body["latest_analysis"], key
    assert "mock-keyword-v1" not in r.text


def test_latest_analysis_is_the_newest_of_two(client):
    candidate_id = _create(client)
    _analyze(client, candidate_id)
    second = _analyze(client, candidate_id, required_skills=["Python"]).json()
    assert client.get(f"/candidates/{candidate_id}").json()["latest_analysis"] == second


# --- Storage -----------------------------------------------------------------


def test_two_analyses_create_two_rows(client, settings):
    candidate_id = _create(client)
    _analyze(client, candidate_id)
    _analyze(client, candidate_id)
    conn = connect(settings.database_path)
    try:
        assert conn.execute("SELECT COUNT(*) FROM analysis_runs").fetchone()[0] == 2
    finally:
        conn.close()


def test_stored_result_equals_returned_result(client, settings):
    candidate_id = _create(client)
    r = _analyze(client, candidate_id)
    conn = connect(settings.database_path)
    try:
        row = conn.execute("SELECT result FROM analysis_runs").fetchone()
    finally:
        conn.close()
    assert json.loads(row["result"]) == r.json()


# --- Failures ----------------------------------------------------------------


def test_invalid_output_returns_502_generic_with_reference(make_client):
    client, _ = make_client(["{bad"])
    r = _analyze(client, _create(client))
    assert r.status_code == 502
    error = r.json()["error"]
    assert error["code"] == "llm_invalid_output"
    assert len(error["reference"]) == 16


def test_502_body_leaks_no_model_prompt_or_raw_output(make_client):
    client, _ = make_client(["{bad"])
    r = _analyze(client, _create(client))
    assert r.status_code == 502
    for leak in ("scripted", "{bad", "BEGIN-CV", "match_score"):
        assert leak not in r.text, leak


def test_timeout_returns_504_with_reference(make_client):
    client, _ = make_client([LLMTimeoutError()])
    r = _analyze(client, _create(client))
    assert r.status_code == 504
    assert r.json()["error"]["code"] == "llm_timeout"
    assert len(r.json()["error"]["reference"]) == 16


def test_provider_error_returns_502_llm_unavailable(make_client):
    client, _ = make_client([LLMUnavailableError()])
    r = _analyze(client, _create(client))
    assert r.status_code == 502
    assert r.json()["error"]["code"] == "llm_unavailable"


def test_references_are_unique_across_calls(make_client):
    client, _ = make_client(["{bad"])
    candidate_id = _create(client)
    first = _analyze(client, candidate_id).json()["error"]["reference"]
    second = _analyze(client, candidate_id).json()["error"]["reference"]
    assert first != second


# --- Manipulated CV ----------------------------------------------------------


def test_malicious_cv_end_to_end_same_score_as_clean(client):
    senior = _create(
        client, email="senior@example.com", cv_text=read_cv("cv_backend_senior.txt")
    )
    malicious = _create(
        client, email="malicious@example.com", cv_text=read_cv("cv_malicious.txt")
    )
    senior_score = _analyze(client, senior).json()["match_score"]
    malicious_score = _analyze(client, malicious).json()["match_score"]
    assert malicious_score == senior_score


def test_valid_but_wrong_score_is_accepted_known_limit(make_client):
    """Known limit, not a fixed bug.

    If a real model is persuaded by the malicious CV and answers with a score that is
    still valid (here 100 instead of 90), validation cannot tell it is wrong: the answer
    has the right shape and range. A deterministic cross-check of the skills against the
    CV would catch it; that improvement is tracked in Issue 2.
    """
    client, _ = make_client([valid_output(match_score=100)])
    candidate_id = _create(client, cv_text=read_cv("cv_malicious.txt"))
    r = _analyze(client, candidate_id)
    assert r.status_code == 200
    assert r.json()["match_score"] == 100


# --- Logs --------------------------------------------------------------------


def test_analyze_logs_no_personal_data(make_client, caplog):
    client, _ = make_client(["{bad"])
    payload = candidate_payload()
    with caplog.at_level(logging.DEBUG):
        candidate_id = _create(client)
        _analyze(client, candidate_id)
    assert payload["name"] not in caplog.text
    assert payload["email"] not in caplog.text
    assert payload["cv_text"][:40] not in caplog.text


def test_analyze_bad_candidate_id_returns_422_without_calling_llm(make_client):
    client, llm = make_client([valid_output()])
    for candidate_id in (0, 2**63):
        r = _analyze(client, candidate_id)
        assert r.status_code == 422, r.text
        assert r.json()["error"]["code"] == "validation_error"
    assert llm.calls == 0


def test_analyze_duplicate_skills_after_strip_returns_422(client):
    candidate_id = _create(client)
    _assert_422(_analyze(client, candidate_id, required_skills=["Python", " python "]))


def test_analyze_stores_stripped_offer(client, settings):
    candidate_id = _create(client)
    r = _analyze(
        client,
        candidate_id,
        job_title=" Backend Developer ",
        required_skills=[" Python "],
    )
    assert r.status_code == 200, r.text
    conn = connect(settings.database_path)
    try:
        row = conn.execute(
            "SELECT job_title, required_skills FROM analysis_runs"
        ).fetchone()
    finally:
        conn.close()
    assert row["job_title"] == "Backend Developer"
    assert json.loads(row["required_skills"]) == ["Python"]
