import importlib
import importlib.util
import socket

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from tests.helpers import TEST_API_KEY, RealLLMCalledInTests, ScriptedLLM


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise RuntimeError("network blocked in tests")

    monkeypatch.setattr(socket.socket, "connect", refuse)


@pytest.fixture(autouse=True)
def block_real_llm(request, monkeypatch):
    """Every test: calling the real Gemini provider raises instead of reaching Google.

    It patches the class, so every instance is covered, including ones built inside the app.
    Only modules marked real_llm_adapter (fake client, network still blocked) are skipped.
    """
    if request.node.get_closest_marker("real_llm_adapter"):
        return
    if importlib.util.find_spec("app.llm.real") is None:
        return  # The optional provider (Task 5.5) does not exist: nothing to block.
    real = importlib.import_module("app.llm.real")

    def refuse(self, system, user):
        raise RealLLMCalledInTests("the real LLM must never be called in tests")

    monkeypatch.setattr(real.GeminiLLM, "complete", refuse)


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
def make_client(settings):
    """Builds a keyed client around a ScriptedLLM: make_client(outputs, delay_s=0.0)."""
    opened = []

    def _make(outputs, delay_s=0.0):
        llm = ScriptedLLM(outputs, delay_s)
        client = TestClient(
            create_app(settings, llm=llm), headers={"X-API-Key": TEST_API_KEY}
        )
        client.__enter__()
        opened.append(client)
        return client, llm

    yield _make
    for client in opened:
        client.__exit__(None, None, None)


@pytest.fixture
def client_500(app):
    with TestClient(
        app, headers={"X-API-Key": TEST_API_KEY}, raise_server_exceptions=False
    ) as c:
        yield c
