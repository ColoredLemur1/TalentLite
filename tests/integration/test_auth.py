"""Every route requires X-API-Key, except the four documentation paths."""

import logging
import secrets

import pytest
from pydantic import BaseModel

from app.auth import DOCS_PATHS
from app.main import create_app
from tests.helpers import TEST_API_KEY, api_routes

WRONG_KEY = "wrong-" + "k" * 40


class EchoBody(BaseModel):
    value: str


@pytest.fixture
def app(settings):
    app = create_app(settings)

    @app.get("/_test/ping")
    def ping():
        return {"ok": True}

    @app.post("/_test/echo")
    def echo(body: EchoBody):
        return body

    return app


def _failures(client, app, expected_status, headers=None):
    routes = api_routes(app)
    assert routes, "no routes to check"
    failures = []
    for path, method in routes:
        r = client.request(method, path, headers=headers)
        if r.status_code != expected_status:
            failures.append(f"{method} {path} -> {r.status_code}")
    return failures


def test_every_route_without_key_returns_401(app, anon_client):
    routes = api_routes(app)
    assert routes, "no routes to check"
    failures = []
    for path, method in routes:
        r = anon_client.request(method, path)
        if r.status_code != 401 or r.json()["error"]["code"] != "unauthorized":
            failures.append(f"{method} {path} -> {r.status_code}")
    assert not failures, failures


def test_every_route_with_wrong_key_returns_401(app, anon_client):
    failures = _failures(anon_client, app, 401, headers={"X-API-Key": WRONG_KEY})
    assert not failures, failures


def test_every_route_with_right_key_is_not_401(app, client):
    routes = api_routes(app)
    assert routes, "no routes to check"
    failures = [
        f"{method} {path}"
        for path, method in routes
        if client.request(method, path).status_code == 401
    ]
    assert not failures, failures


def test_key_with_different_case_returns_401(anon_client):
    r = anon_client.get("/_test/ping", headers={"X-API-Key": TEST_API_KEY.upper()})
    assert r.status_code == 401


def test_key_prefix_of_real_key_returns_401(anon_client):
    r = anon_client.get("/_test/ping", headers={"X-API-Key": TEST_API_KEY[:42]})
    assert r.status_code == 401


def test_empty_key_header_returns_401(anon_client):
    r = anon_client.get("/_test/ping", headers={"X-API-Key": ""})
    assert r.status_code == 401


def test_non_ascii_key_returns_401_not_500(anon_client):
    r = anon_client.get("/_test/ping", headers={"X-API-Key": "clave-ñ".encode()})
    assert r.status_code == 401


def test_401_body_identical_for_missing_and_wrong_key(anon_client):
    missing = anon_client.get("/_test/ping")
    wrong = anon_client.get("/_test/ping", headers={"X-API-Key": WRONG_KEY})
    assert missing.json() == wrong.json()


def test_401_body_does_not_echo_sent_key(anon_client):
    r = anon_client.get("/_test/ping", headers={"X-API-Key": WRONG_KEY})
    assert "wrong-" not in r.text


def test_no_key_and_broken_json_returns_401(app, anon_client):
    post_paths = [path for path, method in api_routes(app) if method == "POST"]
    assert post_paths, "no POST routes to check"
    for path in post_paths:
        r = anon_client.post(
            path, content=b"{bad", headers={"Content-Type": "application/json"}
        )
        assert r.status_code == 401, path


def test_docs_exemptions_are_exactly_the_documented_list(anon_client):
    assert DOCS_PATHS == {"/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"}
    assert anon_client.get("/openapi.json").status_code == 200


def test_path_starting_like_docs_still_requires_key(anon_client):
    r = anon_client.get("/docsx")
    assert r.status_code == 401


def test_api_key_never_appears_in_logs(client, anon_client, caplog):
    with caplog.at_level(logging.DEBUG):
        client.get("/_test/ping")
        anon_client.get("/_test/ping", headers={"X-API-Key": WRONG_KEY})
    assert TEST_API_KEY not in caplog.text
    assert WRONG_KEY not in caplog.text


def test_auth_uses_compare_digest(client, monkeypatch):
    calls = []
    real_compare_digest = secrets.compare_digest

    def spy(a, b):
        calls.append((a, b))
        return real_compare_digest(a, b)

    monkeypatch.setattr(secrets, "compare_digest", spy)
    client.get("/_test/ping")
    assert len(calls) == 1
    provided, expected = calls[0]
    assert isinstance(provided, bytes)
    assert isinstance(expected, bytes)
