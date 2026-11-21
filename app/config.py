import os
from collections.abc import Mapping
from dataclasses import dataclass

PLACEHOLDER_API_KEY = "cambia-esto"
MIN_API_KEY_LENGTH = 32
DEFAULT_DATABASE_PATH = "talentlite.db"


class ConfigError(Exception):
    """The environment cannot produce valid settings. The message never contains secret values."""


@dataclass(frozen=True)
class Settings:
    api_key: str
    database_path: str = DEFAULT_DATABASE_PATH


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
    return Settings(api_key=api_key, database_path=database_path)
