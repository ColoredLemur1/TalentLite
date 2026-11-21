"""Request bodies over 262,144 bytes are refused with 413, without the app reading them."""

import json

from app.middleware import SECURITY_HEADERS
from tests.helpers import candidate_payload as p

LIMIT = 262_144
JSON = {"Content-Type": "application/json"}


def test_body_over_256kib_returns_413(client):
    r = client.post("/candidates", content=b"x" * (LIMIT + 1), headers=JSON)
    assert r.status_code == 413
    assert r.json()["error"]["code"] == "payload_too_large"
    for name, value in SECURITY_HEADERS.items():
        assert r.headers.get(name) == value, name


def test_body_exactly_256kib_is_not_413(client):
    r = client.post("/candidates", content=b"x" * LIMIT, headers=JSON)
    assert r.status_code == 422


def test_worst_case_valid_cv_fits_under_limit(client):
    body = json.dumps(p(cv_text="😀" * 20000)).encode()
    assert len(body) < LIMIT
    r = client.post("/candidates", content=body, headers=JSON)
    assert r.status_code == 201


def test_chunked_body_over_limit_returns_413(client):
    r = client.post("/candidates", content=iter([b"x" * 100_000] * 3), headers=JSON)
    assert r.status_code == 413


def test_oversized_body_without_key_returns_401(anon_client):
    r = anon_client.post("/candidates", content=b"x" * 300_000, headers=JSON)
    assert r.status_code == 401
