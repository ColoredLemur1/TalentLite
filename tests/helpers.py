import re

from fastapi import FastAPI

TEST_API_KEY = "test-key-" + "k" * 34


def candidate_payload(**overrides) -> dict:
    """A valid, invented candidate; any field can be overridden."""
    return {
        "name": "Ana Torres",
        "email": "ana.torres@example.com",
        "cv_text": "Backend Developer con 3 años de Python.",
        **overrides,
    }


def api_routes(app: FastAPI) -> list[tuple[str, str]]:
    """Every (path, method) in the app's OpenAPI document, with each {param} replaced by "1".

    It reads the public OpenAPI document because FastAPI 0.165 wraps included routers
    instead of copying their routes onto app.routes.
    """
    routes = []
    for path, operations in app.openapi()["paths"].items():
        concrete = re.sub(r"\{[^}]+\}", "1", path)
        for method in sorted(operations):
            routes.append((concrete, method.upper()))
    return routes
