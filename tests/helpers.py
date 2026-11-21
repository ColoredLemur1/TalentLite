import re

from fastapi import FastAPI
from fastapi.routing import APIRoute

TEST_API_KEY = "test-key-" + "k" * 34


def api_routes(app: FastAPI) -> list[tuple[str, str]]:
    """Every (path, method) the app serves, with each {param} replaced by "1"."""
    routes = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            path = re.sub(r"\{[^}]+\}", "1", route.path)
            for method in sorted(route.methods):
                routes.append((path, method))
    return routes
