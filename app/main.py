from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from app.auth import ApiKeyMiddleware, api_key_header
from app.config import Settings, load_settings
from app.db import init_db
from app.errors import CatchAllErrorMiddleware, register_exception_handlers
from app.llm.base import LLMClient
from app.llm.factory import make_llm
from app.middleware import BodySizeLimitMiddleware, SecurityHeadersMiddleware
from app.routers import audit, candidates, health


def create_app(settings: Settings, llm: LLMClient | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        init_db(settings.database_path)
        yield

    app = FastAPI(
        title="TalentLite",
        dependencies=[Depends(api_key_header)],
        lifespan=lifespan,
    )
    app.state.settings = settings
    # Tests inject a scripted model; otherwise the provider comes from the settings.
    app.state.llm = llm if llm is not None else make_llm(settings)
    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(candidates.router)
    app.include_router(audit.router)
    # The last middleware added is the outermost:
    # security headers, then catch-all, then auth, then body limit, then the app.
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.max_body_bytes)
    app.add_middleware(ApiKeyMiddleware, api_key=settings.api_key)
    app.add_middleware(CatchAllErrorMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    return app


def build_app() -> FastAPI:
    """Entry point for `uvicorn app.main:build_app --factory`; the only place that reads the environment."""
    return create_app(load_settings())
