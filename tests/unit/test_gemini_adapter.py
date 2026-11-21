"""GeminiLLM with a fake client: no key, no network, no real call.

This module opts out of the block_real_llm guard (the real_llm_adapter marker) so it can
call the real `complete` method. block_network still applies, and the client is fake.
"""

import httpx2
import pytest

from app.config import load_settings
from app.llm.base import LLMTimeoutError, LLMUnavailableError
from app.llm.factory import make_llm
from app.llm.real import GeminiLLM
from tests.helpers import TEST_API_KEY

pytestmark = pytest.mark.real_llm_adapter


class _FakeResponse:
    def __init__(self, text: str | None) -> None:
        self.text = text


class _FakeModels:
    def __init__(self, error: Exception | None = None, text: str | None = "") -> None:
        self.error = error
        self.text = text
        self.calls: list[dict] = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return _FakeResponse(self.text)


class _FakeClient:
    def __init__(self, error: Exception | None = None, text: str | None = "") -> None:
        self.models = _FakeModels(error, text)


def _llm(client: _FakeClient, timeout_s: float = 1.0) -> GeminiLLM:
    return GeminiLLM(
        api_key="fake", model="fake-model", timeout_s=timeout_s, client=client
    )


def test_gemini_maps_sdk_timeout_to_llm_timeout():
    with pytest.raises(LLMTimeoutError):
        _llm(_FakeClient(error=TimeoutError())).complete("system", "user")


def test_gemini_maps_httpx2_timeout_to_llm_timeout():
    with pytest.raises(LLMTimeoutError):
        _llm(_FakeClient(error=httpx2.ReadTimeout("timed out"))).complete(
            "system", "user"
        )


def test_gemini_maps_sdk_error_to_unavailable():
    with pytest.raises(LLMUnavailableError):
        _llm(_FakeClient(error=RuntimeError("provider down"))).complete(
            "system", "user"
        )


def test_gemini_passes_timeout_system_and_json_type():
    client = _FakeClient(text="{}")
    _llm(client, timeout_s=1.0).complete("the system text", "the user text")
    call = client.models.calls[0]
    assert call["model"] == "fake-model"
    assert call["contents"] == "the user text"
    config = call["config"]
    assert config.system_instruction == "the system text"
    assert config.response_mime_type == "application/json"
    assert config.http_options.timeout == 1000  # the SDK takes milliseconds


def test_gemini_returns_response_text():
    raw = '{"a": 1}'
    assert _llm(_FakeClient(text=raw)).complete("system", "user") == raw


def test_gemini_returns_empty_text_when_response_has_none():
    assert _llm(_FakeClient(text=None)).complete("system", "user") == ""


def test_factory_builds_gemini_for_gemini_settings():
    settings = load_settings(
        {
            "API_KEY": TEST_API_KEY,
            "LLM_PROVIDER": "gemini",
            "GEMINI_API_KEY": "fake-gemini-key",
            "GEMINI_MODEL": "fake-model",
        }
    )
    assert isinstance(make_llm(settings), GeminiLLM)
