import json
import re
from typing import Annotated, NoReturn

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError

ERROR_SUMMARY_MAX_LENGTH = 500

# One optional ```json fence around the whole answer. The body is not searched for
# further fences, so a second fence is left in place and fails to parse.
_FENCE = re.compile(r"\A```(?:json)?[ \t]*\n(?P<body>.*)\n```\Z", re.DOTALL)

Skill = Annotated[str, StringConstraints(min_length=1, max_length=100)]


class AnalysisResult(BaseModel):
    """The only shape a model answer may have. Anything else is rejected, never repaired."""

    model_config = ConfigDict(strict=True, extra="forbid")

    skills: Annotated[list[Skill], Field(max_length=50)]
    # Strict float still accepts a JSON integer, but never a bool or a string.
    years_experience: Annotated[float, Field(ge=0, le=80, allow_inf_nan=False)]
    summary: Annotated[str, StringConstraints(min_length=1, max_length=400)]
    match_score: Annotated[int, Field(ge=0, le=100)]


class InvalidLLMOutput(Exception):
    """The model's answer was rejected.

    `summary` names only field paths and error types, or one of `empty`,
    `json_decode_error` and `not_an_object`. It never contains a value from the answer.
    """

    def __init__(self, summary: str) -> None:
        self.summary = summary[:ERROR_SUMMARY_MAX_LENGTH]
        super().__init__(self.summary)


def _refuse_non_finite(constant: str) -> NoReturn:
    # json.loads calls this for NaN, Infinity and -Infinity, which plain JSON does not allow.
    raise ValueError("non-finite number")


def _location(loc: tuple[int | str, ...]) -> str:
    # A key the model invented could carry any text, so only known field names are kept.
    parts = [
        str(part)
        if isinstance(part, int) or part in AnalysisResult.model_fields
        else "<extra>"
        for part in loc
    ]
    return ".".join(parts)


def _summarize(exc: ValidationError) -> str:
    return "; ".join(f"{_location(err['loc'])}: {err['type']}" for err in exc.errors())


def parse_and_validate(raw: str) -> AnalysisResult:
    text = raw.strip()
    if not text:
        raise InvalidLLMOutput("empty")
    fenced = _FENCE.match(text)
    if fenced:
        text = fenced.group("body").strip()
    try:
        data = json.loads(text, parse_constant=_refuse_non_finite)
    except ValueError:
        raise InvalidLLMOutput("json_decode_error") from None
    if not isinstance(data, dict):
        raise InvalidLLMOutput("not_an_object")
    try:
        return AnalysisResult.model_validate(data)
    except ValidationError as exc:
        raise InvalidLLMOutput(_summarize(exc)) from None
