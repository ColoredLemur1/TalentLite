from app.config import ConfigError, Settings
from app.llm.base import LLMClient
from app.llm.mock import MockLLM


def make_llm(settings: Settings) -> LLMClient:
    if settings.llm_provider == "mock":
        return MockLLM()
    # load_settings only accepts "mock" and "gemini"; Task 5.5 adds the Gemini provider.
    raise ConfigError("LLM_PROVIDER=gemini is not available in this build.")
