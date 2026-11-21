"""Tests and CI can never reach the real LLM or the network."""

import socket

import pytest

from tests.helpers import RealLLMCalledInTests


def test_gemini_complete_raises_in_tests():
    real = pytest.importorskip("app.llm.real")
    llm = real.GeminiLLM(api_key="fake", model="fake", timeout_s=1.0, client=object())
    with pytest.raises(RealLLMCalledInTests):
        llm.complete("system", "user")


def test_outbound_network_blocked_in_tests():
    # 192.0.2.1 is a documentation-only address, so no DNS lookup happens.
    with pytest.raises(RuntimeError, match="network blocked in tests"):
        socket.create_connection(("192.0.2.1", 443), timeout=1)
