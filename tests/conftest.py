import socket

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from tests.helpers import TEST_API_KEY


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise RuntimeError("network blocked in tests")

    monkeypatch.setattr(socket.socket, "connect", refuse)


@pytest.fixture
def settings(tmp_path):
    return Settings(api_key=TEST_API_KEY, database_path=str(tmp_path / "test.db"))


@pytest.fixture
def app(settings):
    return create_app(settings)


@pytest.fixture
def client(app):
    with TestClient(app, headers={"X-API-Key": TEST_API_KEY}) as c:
        yield c


@pytest.fixture
def anon_client(app):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def client_500(app):
    with TestClient(
        app, headers={"X-API-Key": TEST_API_KEY}, raise_server_exceptions=False
    ) as c:
        yield c
