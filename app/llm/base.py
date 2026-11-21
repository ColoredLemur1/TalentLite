from typing import Protocol


class LLMClient(Protocol):
    """Any model provider: it receives a system and a user message and returns raw text."""

    provider: str
    model: str

    def complete(self, system: str, user: str) -> str: ...


class LLMError(Exception):
    """The provider failed. Subclasses say how; none carries the prompt or the response."""


class LLMTimeoutError(LLMError):
    pass


class LLMUnavailableError(LLMError):
    pass
