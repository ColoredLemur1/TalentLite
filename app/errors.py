import logging
import secrets

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger("talentlite")

ERROR_MESSAGES: dict[str, str] = {
    "unauthorized": "Missing or invalid API key.",
    "not_found": "Resource not found.",
    "method_not_allowed": "Method not allowed for this resource.",
    "conflict": "Resource already exists.",
    "payload_too_large": "Request body is too large.",
    "validation_error": "Request validation failed.",
    "internal_error": "Internal server error.",
    "llm_invalid_output": "The analysis model returned an invalid response.",
    "llm_unavailable": "The analysis model is unavailable.",
    "llm_timeout": "The analysis model timed out.",
}

HTTP_ERROR_CODES: dict[int, str] = {
    404: "not_found",
    405: "method_not_allowed",
    413: "payload_too_large",
}


def new_reference() -> str:
    return secrets.token_hex(8)


def error_response(
    status_code: int,
    code: str,
    *,
    reference: str | None = None,
    details: list[dict] | None = None,
) -> JSONResponse:
    error: dict = {"code": code, "message": ERROR_MESSAGES[code]}
    if reference is not None:
        error["reference"] = reference
    if details is not None:
        error["details"] = details
    return JSONResponse(status_code=status_code, content={"error": error})


def _internal_error(exc: Exception) -> JSONResponse:
    reference = new_reference()
    logger.error("unhandled_error type=%s reference=%s", type(exc).__name__, reference)
    return error_response(500, "internal_error", reference=reference)


async def _http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    code = HTTP_ERROR_CODES.get(exc.status_code)
    if code is None:
        return _internal_error(exc)
    response = error_response(exc.status_code, code)
    if exc.headers:
        response.headers.update(exc.headers)
    return response


async def _validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    details = [
        {"loc": list(err["loc"]), "msg": err["msg"], "type": err["type"]}
        for err in exc.errors()
    ]
    return error_response(422, "validation_error", details=details)


async def _unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    return _internal_error(exc)


class CatchAllErrorMiddleware:
    """Turns any unhandled exception into the generic 500 and does not re-raise it.

    Starlette re-raises after its own 500 so the server can log the traceback, and
    that traceback would carry the exception message. This stops it here instead.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def send_tracking_start(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, send_tracking_start)
        except Exception as exc:  # noqa: BLE001 - catching everything is this class's job
            response = _internal_error(exc)
            if not response_started:
                await response(scope, receive, send)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    app.add_exception_handler(Exception, _unhandled_exception_handler)
