import httpx2
from google import genai
from google.genai import types

from app.llm.base import LLMTimeoutError, LLMUnavailableError


class GeminiLLM:
    """Optional real provider. It is never called in tests (see block_real_llm).

    Nothing from the key, the request or the response is logged or kept in errors.
    """

    provider = "gemini"

    def __init__(self, api_key: str, model: str, timeout_s: float, client=None) -> None:
        self.model = model
        self._timeout_ms = int(timeout_s * 1000)
        # The key goes straight into the SDK client and is not stored on this object.
        self._client = client if client is not None else genai.Client(api_key=api_key)

    def complete(self, system: str, user: str) -> str:
        config = types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            http_options=types.HttpOptions(timeout=self._timeout_ms),
        )
        try:
            response = self._client.models.generate_content(
                model=self.model, contents=user, config=config
            )
        # The SDK's default HTTP client is httpx2; its timeouts are not TimeoutError.
        except (TimeoutError, httpx2.TimeoutException):
            raise LLMTimeoutError() from None
        except Exception:  # noqa: BLE001 - any SDK failure means the provider is unavailable
            raise LLMUnavailableError() from None
        # A blocked answer has no text; "" is then rejected as empty output, not a crash.
        return response.text or ""
