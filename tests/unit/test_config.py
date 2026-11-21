import pytest

from app.config import ConfigError, load_settings
from tests.helpers import TEST_API_KEY


def test_load_settings_missing_api_key_raises():
    with pytest.raises(ConfigError):
        load_settings({})


def test_load_settings_placeholder_api_key_raises():
    with pytest.raises(ConfigError):
        load_settings({"API_KEY": "cambia-esto"})


def test_load_settings_short_api_key_raises():
    with pytest.raises(ConfigError):
        load_settings({"API_KEY": "k" * 31})


def test_load_settings_32_char_api_key_ok():
    key = "k" * 32
    assert load_settings({"API_KEY": key}).api_key == key


def test_config_error_message_does_not_contain_key():
    key = "rejected-secret-marker"
    with pytest.raises(ConfigError) as exc_info:
        load_settings({"API_KEY": key})
    assert key not in str(exc_info.value)


def test_load_settings_valid_api_key_ok():
    settings = load_settings({"API_KEY": TEST_API_KEY})
    assert settings.api_key == TEST_API_KEY
