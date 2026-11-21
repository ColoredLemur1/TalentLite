import time
from dataclasses import dataclass
from typing import Literal

from app.errors import new_reference
from app.llm.base import LLMClient, LLMError, LLMTimeoutError
from app.llm.output import AnalysisResult, InvalidLLMOutput, parse_and_validate
from app.llm.prompt import PROMPT_VERSION, build_prompt

MAX_ATTEMPTS = 3


@dataclass(frozen=True)
class AnalysisOutcome:
    status: Literal["succeeded", "failed"]
    result: AnalysisResult | None
    error_code: str | None  # llm_invalid_output | llm_timeout | llm_unavailable
    error_detail: str | None  # field paths and error types only, never values
    attempts: int
    duration_ms: int
    reference: str
    provider: str
    model: str
    prompt_version: str


def run_analysis(
    llm: LLMClient, *, cv_text: str, job_title: str, required_skills: list[str]
) -> AnalysisOutcome:
    """Asks the model up to MAX_ATTEMPTS times and never raises for LLM errors.

    Only an invalid answer is retried, with the same prompt. A timeout or a provider
    error ends the analysis after that single call.
    """
    prompt = build_prompt(cv_text, job_title, required_skills)
    started = time.perf_counter()
    attempts = 0
    result: AnalysisResult | None = None
    error_code: str | None = None
    error_detail: str | None = None

    while attempts < MAX_ATTEMPTS:
        attempts += 1
        try:
            result = parse_and_validate(llm.complete(prompt.system, prompt.user))
            error_code = error_detail = None
            break
        except InvalidLLMOutput as exc:
            error_code, error_detail = "llm_invalid_output", exc.summary
        except LLMTimeoutError:
            error_code, error_detail = "llm_timeout", "timeout"
            break
        except LLMError as exc:
            error_code = "llm_unavailable"
            error_detail = f"provider_error:{type(exc).__name__}"
            break

    return AnalysisOutcome(
        status="succeeded" if result is not None else "failed",
        result=result,
        error_code=error_code,
        error_detail=error_detail,
        attempts=attempts,
        duration_ms=int((time.perf_counter() - started) * 1000),
        reference=new_reference(),
        provider=llm.provider,
        model=llm.model,
        prompt_version=PROMPT_VERSION,
    )
