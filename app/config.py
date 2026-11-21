import math
import os
from collections.abc import Mapping
from dataclasses import dataclass, field

PLACEHOLDER_API_KEY = "cambia-esto"
MIN_API_KEY_LENGTH = 32
DEFAULT_DATABASE_PATH = "talentlite.db"
# 256 KiB. The largest valid body is about 240 KB: 20,000 emojis, each written by
# json.dumps as a 12-byte surrogate pair ("😀").
DEFAULT_MAX_BODY_BYTES = 262_144
SUPPORTED_LLM_PROVIDERS = ("mock", "gemini")
DEFAULT_LLM_PROVIDER = "mock"
DEFAULT_GEMINI_TIMEOUT_SECONDS = 60.0


class ConfigError(Exception):
    """The environment cannot produce valid settings. The message never contains secret values."""


@dataclass(frozen=True)
class Settings:
    # repr=False keeps both keys out of any printed or logged Settings.
    api_key: str = field(repr=False)
    database_path: str = DEFAULT_DATABASE_PATH
    max_body_bytes: int = DEFAULT_MAX_BODY_BYTES
    llm_provider: str = DEFAULT_LLM_PROVIDER
    gemini_api_key: str | None = field(default=None, repr=False)
    gemini_model: str | None = None
    gemini_timeout_seconds: float = DEFAULT_GEMINI_TIMEOUT_SECONDS


def _gemini_timeout(raw: str | None) -> float:
    if not raw:
        return DEFAULT_GEMINI_TIMEOUT_SECONDS
    try:
        value = float(raw)
    except ValueError:
        value = math.nan
    if not math.isfinite(value) or value <= 0:
        raise ConfigError("GEMINI_TIMEOUT_SECONDS must be a positive number.")
    return value


def load_settings(env: Mapping[str, str] = os.environ) -> Settings:
    api_key = env.get("API_KEY", "")
    if not api_key:
        raise ConfigError("API_KEY is not set.")
    if api_key == PLACEHOLDER_API_KEY:
        raise ConfigError("API_KEY is still the placeholder from .env.example.")
    if len(api_key) < MIN_API_KEY_LENGTH:
        raise ConfigError(
            f"API_KEY must be at least {MIN_API_KEY_LENGTH} characters long."
        )
    database_path = env.get("DATABASE_PATH") or DEFAULT_DATABASE_PATH

    llm_provider = (env.get("LLM_PROVIDER") or DEFAULT_LLM_PROVIDER).strip().lower()
    if llm_provider not in SUPPORTED_LLM_PROVIDERS:
        raise ConfigError("LLM_PROVIDER must be one of: mock, gemini.")
    gemini_api_key = env.get("GEMINI_API_KEY") or None
    gemini_model = env.get("GEMINI_MODEL") or None
    gemini_timeout_seconds = _gemini_timeout(env.get("GEMINI_TIMEOUT_SECONDS"))
    if llm_provider == "gemini":
        if not gemini_api_key:
            raise ConfigError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini.")
        if not gemini_model:
            raise ConfigError("GEMINI_MODEL is required when LLM_PROVIDER=gemini.")

    return Settings(
        api_key=api_key,
        database_path=database_path,
        llm_provider=llm_provider,
        gemini_api_key=gemini_api_key,
        gemini_model=gemini_model,
        gemini_timeout_seconds=gemini_timeout_seconds,
    )
