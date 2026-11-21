import secrets

from fastapi.security import APIKeyHeader
from starlette.types import ASGIApp, Receive, Scope, Send

from app.errors import error_response

DOCS_PATHS = frozenset({"/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"})

# Documentation only: it adds the Authorize button to /docs. It never rejects a request;
# ApiKeyMiddleware does that before any route runs.
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def key_matches(provided: bytes | None, expected: bytes) -> bool:
    """Constant-time comparison of the raw header bytes against the configured key."""
    if provided is None:
        return False
    return secrets.compare_digest(provided, expected)


def _raw_header(scope: Scope, name: bytes) -> bytes | None:
    for key, value in scope["headers"]:
        if key == name:
            return value
    return None


class ApiKeyMiddleware:
    """Rejects every request without the right X-API-Key before the app reads the body."""

    def __init__(
        self, app: ASGIApp, api_key: str, exempt_paths: frozenset[str] = DOCS_PATHS
    ) -> None:
        self.app = app
        self.expected = api_key.encode()
        self.exempt_paths = exempt_paths

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":
            await self.app(scope, receive, send)
            return
        if scope["type"] != "http":
            await send({"type": "websocket.close", "code": 1008})
            return
        if scope["path"] in self.exempt_paths:
            await self.app(scope, receive, send)
            return
        if not key_matches(_raw_header(scope, b"x-api-key"), self.expected):
            await error_response(401, "unauthorized")(scope, receive, send)
            return
        await self.app(scope, receive, send)
