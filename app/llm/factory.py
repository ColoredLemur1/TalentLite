from app.config import ConfigError, Settings
from app.llm.base import LLMClient
from app.llm.mock import MockLLM


def make_llm(settings: Settings) -> LLMClient:
    if settings.llm_provider == "mock":
        return MockLLM()
    if settings.llm_provider == "gemini":
        if not settings.gemini_api_key or not settings.gemini_model:
            # load_settings already refuses this; Settings built by hand must not reach
            # the SDK without a key, or it would look for one in the environment.
            raise ConfigError("Gemini needs GEMINI_API_KEY and GEMINI_MODEL.")
        # Imported here so the default mock path never loads the optional SDK.
        from app.llm.real import GeminiLLM

        return GeminiLLM(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            timeout_s=settings.gemini_timeout_seconds,
        )
    raise ConfigError("LLM_PROVIDER must be one of: mock, gemini.")
