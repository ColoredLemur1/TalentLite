from fastapi import Depends, FastAPI

from app.auth import ApiKeyMiddleware, api_key_header
from app.config import Settings, load_settings
from app.errors import CatchAllErrorMiddleware, register_exception_handlers
from app.middleware import SecurityHeadersMiddleware
from app.routers import health


def create_app(settings: Settings) -> FastAPI:
    app = FastAPI(title="TalentLite", dependencies=[Depends(api_key_header)])
    app.state.settings = settings
    register_exception_handlers(app)
    app.include_router(health.router)
    # The last middleware added is the outermost:
    # security headers, then catch-all, then auth, then the app.
    app.add_middleware(ApiKeyMiddleware, api_key=settings.api_key)
    app.add_middleware(CatchAllErrorMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    return app


def build_app() -> FastAPI:
    """Entry point for `uvicorn app.main:build_app --factory`; the only place that reads the environment."""
    return create_app(load_settings())
