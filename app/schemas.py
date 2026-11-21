from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    StringConstraints,
)

NAME_MAX_LENGTH = 100
CV_MAX_LENGTH = 20_000


def _normalize_email(value: str) -> str:
    # EmailStr has already validated it, stripped spaces and capped it at 254 characters.
    return value.strip().lower()


def _not_blank(value: str) -> str:
    if not value.strip():
        raise ValueError("cv_text must not be blank")
    return value


Name = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=NAME_MAX_LENGTH),
]
Email = Annotated[EmailStr, AfterValidator(_normalize_email)]
# The CV is stored exactly as sent: no stripping, only the length and not-blank rules.
CvText = Annotated[
    str,
    StringConstraints(min_length=1, max_length=CV_MAX_LENGTH),
    AfterValidator(_not_blank),
]


class CandidateCreate(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    name: Name
    email: Email
    cv_text: CvText


class CandidateOut(BaseModel):
    """Exactly the fields the brief lists. latest_analysis becomes a real type in branch 6."""

    id: int
    name: str
    email: str
    cv_text: str
    created_at: str
    latest_analysis: None = None
