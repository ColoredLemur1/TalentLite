from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
)

from app.llm.output import AnalysisResult

NAME_MAX_LENGTH = 100
CV_MAX_LENGTH = 20_000
JOB_TITLE_MAX_LENGTH = 200
SKILL_MAX_LENGTH = 50
MAX_REQUIRED_SKILLS = 30


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


def _no_repeated_skills(skills: list[str]) -> list[str]:
    # Runs after each item has been stripped, so " python " repeats "Python".
    seen: set[str] = set()
    for skill in skills:
        key = skill.casefold()
        if key in seen:
            raise ValueError("required_skills must not repeat a skill (ignoring case)")
        seen.add(key)
    return skills


JobTitle = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, min_length=1, max_length=JOB_TITLE_MAX_LENGTH
    ),
]
RequiredSkill = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=SKILL_MAX_LENGTH),
]
RequiredSkills = Annotated[
    list[RequiredSkill],
    Field(min_length=1, max_length=MAX_REQUIRED_SKILLS),
    AfterValidator(_no_repeated_skills),
]


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    job_title: JobTitle
    required_skills: RequiredSkills


class CandidateOut(BaseModel):
    """Exactly the fields the brief lists.

    latest_analysis is the newest succeeded result, with only its 4 fields, or null.
    """

    id: int
    name: str
    email: str
    cv_text: str
    created_at: str
    latest_analysis: AnalysisResult | None = None
