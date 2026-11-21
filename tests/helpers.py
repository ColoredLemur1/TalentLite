import json
import re
import time
from pathlib import Path

from fastapi import FastAPI

TEST_API_KEY = "test-key-" + "k" * 34

CV_FIXTURES = Path(__file__).parent / "fixtures" / "cvs"
OFFER_TITLE = "Backend Developer"
OFFER_SKILLS = ["Python", "FastAPI", "SQL", "Docker", "Kubernetes"]


def read_cv(name: str) -> str:
    """One of the invented fixture CVs in tests/fixtures/cvs."""
    return (CV_FIXTURES / name).read_text(encoding="utf-8")


class RealLLMCalledInTests(RuntimeError):
    """Raised by the test guard if anything tries to call the real Gemini provider."""


class ScriptedLLM:
    """A fake model that returns, or raises, the next scripted output on each call.

    Once the script runs out, it repeats the last output.
    """

    provider = "scripted"
    model = "scripted-v0"

    def __init__(self, outputs: list[str | Exception], delay_s: float = 0.0) -> None:
        if not outputs:
            raise ValueError("ScriptedLLM needs at least one output")
        self._outputs = list(outputs)
        self.delay_s = delay_s
        self.calls = 0
        self.prompts: list[tuple[str, str]] = []

    def complete(self, system: str, user: str) -> str:
        self.prompts.append((system, user))
        output = self._outputs[min(self.calls, len(self._outputs) - 1)]
        self.calls += 1
        if self.delay_s:
            time.sleep(self.delay_s)
        if isinstance(output, Exception):
            raise output
        return output


def valid_output(**overrides) -> str:
    """A valid model answer as JSON text; any field can be overridden."""
    return json.dumps(
        {
            "skills": ["python"],
            "years_experience": 3,
            "summary": "Resumen.",
            "match_score": 50,
            **overrides,
        }
    )


def candidate_payload(**overrides) -> dict:
    """A valid, invented candidate; any field can be overridden."""
    return {
        "name": "Ana Torres",
        "email": "ana.torres@example.com",
        "cv_text": "Backend Developer con 3 años de Python.",
        **overrides,
    }


def offer_payload(**overrides) -> dict:
    """A valid job offer for POST /candidates/{id}/analyze; any field can be overridden."""
    return {"job_title": OFFER_TITLE, "required_skills": OFFER_SKILLS, **overrides}


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
