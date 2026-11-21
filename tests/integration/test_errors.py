"""Every error uses the {"error": {...}} format and never echoes input values or exception text."""

import logging

import pytest
from pydantic import BaseModel, EmailStr

from app.main import create_app


class EchoBody(BaseModel):
    email: EmailStr


@pytest.fixture
def app(settings):
    app = create_app(settings)

    @app.post("/_test/echo")
    def echo(body: EchoBody):
        return {"email": body.email}

    @app.get("/_test/boom")
    def boom():
        raise RuntimeError("ana.torres@example.com")

    return app


def test_unknown_route_returns_404_in_error_format(client):
    r = client.get("/nope")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


def test_wrong_method_returns_405_in_error_format(client):
    r = client.delete("/_test/echo")
    assert r.status_code == 405
    assert r.json()["error"]["code"] == "method_not_allowed"


def test_422_response_omits_input_values(client):
    r = client.post("/_test/echo", json={"email": "pii-marker@@x"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"
    assert "pii-marker" not in r.text
    for item in r.json()["error"]["details"]:
        assert "input" not in item
        assert "ctx" not in item


def test_unhandled_exception_returns_generic_500_with_reference(client_500):
    r = client_500.get("/_test/boom")
    assert r.status_code == 500
    error = r.json()["error"]
    assert error["code"] == "internal_error"
    assert len(error["reference"]) == 16
    assert "ana.torres" not in r.text


def test_unhandled_exception_does_not_propagate_to_server(client):
    r = client.get("/_test/boom")
    assert r.status_code == 500
    assert r.json()["error"]["code"] == "internal_error"


def test_unhandled_exception_log_has_reference_but_not_message(client_500, caplog):
    with caplog.at_level(logging.ERROR, logger="talentlite"):
        r = client_500.get("/_test/boom")
    reference = r.json()["error"]["reference"]
    assert reference in caplog.text
    assert "RuntimeError" in caplog.text
    assert "ana.torres@example.com" not in caplog.text
