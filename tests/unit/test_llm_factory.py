import pytest

from app.config import ConfigError, load_settings
from app.llm.factory import make_llm
from app.llm.mock import MockLLM
from tests.helpers import TEST_API_KEY


def _llm_for(**env):
    return make_llm(load_settings({"API_KEY": TEST_API_KEY, **env}))


def test_provider_unset_defaults_to_mock():
    assert isinstance(_llm_for(), MockLLM)


def test_provider_mock_returns_mock():
    assert isinstance(_llm_for(LLM_PROVIDER="mock"), MockLLM)


def test_provider_uppercase_is_normalized():
    assert isinstance(_llm_for(LLM_PROVIDER="MOCK"), MockLLM)


def test_provider_gemini_without_key_raises():
    with pytest.raises(ConfigError):
        load_settings(
            {"API_KEY": TEST_API_KEY, "LLM_PROVIDER": "gemini", "GEMINI_MODEL": "m"}
        )


def test_provider_gemini_without_model_raises():
    with pytest.raises(ConfigError):
        load_settings(
            {"API_KEY": TEST_API_KEY, "LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "g"}
        )


def test_provider_unknown_raises():
    with pytest.raises(ConfigError):
        load_settings({"API_KEY": TEST_API_KEY, "LLM_PROVIDER": "openai"})
