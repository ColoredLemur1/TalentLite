from fastapi import FastAPI

from app.config import Settings, load_settings
from app.errors import CatchAllErrorMiddleware, register_exception_handlers


def create_app(settings: Settings) -> FastAPI:
    app = FastAPI(title="TalentLite")
    app.state.settings = settings
    register_exception_handlers(app)
    app.add_middleware(CatchAllErrorMiddleware)
    return app


def build_app() -> FastAPI:
    """Entry point for `uvicorn app.main:build_app --factory`; the only place that reads the environment."""
    return create_app(load_settings())
