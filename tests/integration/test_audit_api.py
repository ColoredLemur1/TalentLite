"""GET /candidates/{id}/audit: every analysis attempt of one candidate, newest first, paged.

It never shows error_detail or any CV text, and never another candidate's runs.
"""

import app.db
from app.db import connect
from tests.helpers import candidate_payload, offer_payload, read_cv, valid_output

AUDIT_FIELDS = {
    "id",
    "created_at",
    "job_title",
    "required_skills",
    "status",
    "result",
    "error_code",
    "provider",
    "model",
    "prompt_version",
    "attempts",
    "duration_ms",
    "reference",
}


def _create(client, **overrides) -> int:
    r = client.post("/candidates", json=candidate_payload(**overrides))
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _analyze(client, candidate_id):
    return client.post(f"/candidates/{candidate_id}/analyze", json=offer_payload())


def _audit(client, candidate_id, **params):
    return client.get(f"/candidates/{candidate_id}/audit", params=params)


def _with_runs(client, count: int) -> int:
    candidate_id = _create(client)
    for _ in range(count):
        assert _analyze(client, candidate_id).status_code == 200
    return candidate_id


# --- Basics ------------------------------------------------------------------


def test_audit_missing_candidate_returns_404(client):
    r = _audit(client, 999)
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


def test_audit_candidate_without_analyses_returns_empty_items_total_0(client):
    body = _audit(client, _create(client)).json()
    assert body["items"] == []
    assert body["total"] == 0


def test_audit_item_has_exactly_the_audit_fields(client):
    [item] = _audit(client, _with_runs(client, 1)).json()["items"]
    assert set(item) == AUDIT_FIELDS


# --- What it never shows -----------------------------------------------------


def test_audit_never_exposes_error_detail(make_client, settings):
    client, _ = make_client(["{bad"])
    candidate_id = _create(client)
    assert _analyze(client, candidate_id).status_code == 502
    conn = connect(settings.database_path)
    try:
        stored = conn.execute("SELECT error_detail FROM analysis_runs").fetchone()[0]
    finally:
        conn.close()
    r = _audit(client, candidate_id)
    [item] = r.json()["items"]
    assert "error_detail" not in item
    assert stored not in r.text


def test_audit_does_not_contain_cv_text(client):
    cv = read_cv("cv_backend_senior.txt")
    candidate_id = _create(client, cv_text=cv)
    assert _analyze(client, candidate_id).status_code == 200
    assert cv[:40] not in _audit(client, candidate_id).text


# --- Failed and succeeded attempts -------------------------------------------


def test_reference_from_502_is_found_in_audit(make_client):
    client, _ = make_client(["{bad"])
    candidate_id = _create(client)
    reference = _analyze(client, candidate_id).json()["error"]["reference"]
    assert _audit(client, candidate_id).json()["items"][0]["reference"] == reference


def test_audit_shows_failed_and_succeeded_attempts(make_client):
    # Call 1 succeeds; every later call repeats "{bad", so the second analysis fails.
    client, _ = make_client([valid_output(), "{bad"])
    candidate_id = _create(client)
    _analyze(client, candidate_id)
    _analyze(client, candidate_id)
    statuses = {item["status"] for item in _audit(client, candidate_id).json()["items"]}
    assert statuses == {"failed", "succeeded"}


# --- Paging ------------------------------------------------------------------


def test_audit_paging_default_limit_20_of_25(client):
    body = _audit(client, _with_runs(client, 25)).json()
    assert len(body["items"]) == 20
    assert body["total"] == 25
    assert body["limit"] == 20
    assert body["offset"] == 0


def test_audit_paging_offset_20_returns_5(client):
    body = _audit(client, _with_runs(client, 25), offset=20).json()
    assert len(body["items"]) == 5


def test_audit_paging_limit_bounds(client):
    candidate_id = _create(client)
    assert _audit(client, candidate_id, limit=0).status_code == 422
    assert _audit(client, candidate_id, limit=101).status_code == 422
    assert _audit(client, candidate_id, limit=100).status_code == 200


def test_audit_paging_offset_negative_returns_422(client):
    assert _audit(client, _create(client), offset=-1).status_code == 422


def test_audit_paging_offset_beyond_total_returns_empty_with_total(client):
    body = _audit(client, _with_runs(client, 25), offset=100).json()
    assert body["items"] == []
    assert body["total"] == 25


# --- Order and isolation -----------------------------------------------------


def test_audit_newest_first_with_id_tiebreak(client, monkeypatch):
    monkeypatch.setattr(app.db, "utc_now_iso", lambda: "2026-11-21T10:00:00Z")
    candidate_id = _with_runs(client, 3)
    ids = [item["id"] for item in _audit(client, candidate_id).json()["items"]]
    assert ids == sorted(ids, reverse=True)
    assert len(ids) == 3


def test_audit_isolated_per_candidate(client):
    first = _with_runs(client, 2)
    second = _create(client, email="otra@example.com")
    assert _analyze(client, second).status_code == 200
    first_refs = {i["reference"] for i in _audit(client, first).json()["items"]}
    body = _audit(client, second).json()
    assert body["total"] == 1
    assert not first_refs & {i["reference"] for i in body["items"]}
