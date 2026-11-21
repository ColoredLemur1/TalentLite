import json
import re
from collections.abc import Iterable

from app.llm.base import LLMUnavailableError

SKILL_VOCABULARY: tuple[str, ...] = (
    "python",
    "fastapi",
    "django",
    "flask",
    "sql",
    "postgresql",
    "mysql",
    "sqlite",
    "mongodb",
    "redis",
    "docker",
    "kubernetes",
    "terraform",
    "aws",
    "azure",
    "gcp",
    "linux",
    "git",
    "graphql",
    "javascript",
    "typescript",
    "node.js",
    "react",
    "java",
    "kotlin",
    "c#",
    "c++",
    "rust",
    "pandas",
    "pytest",
)

YEARS_CAP = 50
TITLE_WORD_MIN_LETTERS = 4

# (?<!\d) stops "150 years" from matching as "50 years".
_YEARS = re.compile(r"(?<!\d)(\d{1,2})\s*\+?\s*(?:years?|años?)", re.IGNORECASE)
_NONCE = re.compile(r"BEGIN-CV-([0-9a-f]{32})")
_LETTER_WORDS = re.compile(r"[^\W\d_]+")
_TITLE_PREFIX = "Job title: "
_SKILLS_PREFIX = "\nRequired skills: "


def _whole_word(term: str) -> re.Pattern[str]:
    # re.escape makes "C++", ".NET" or "(.*)" match as plain text, never as a pattern.
    return re.compile(rf"(?<!\w){re.escape(term)}(?!\w)", re.IGNORECASE)


def find_skills(text: str, candidates: Iterable[str]) -> list[str]:
    """Skills found as whole words: lowercased, without duplicates, in CV order."""
    found = []
    for skill in candidates:
        match = _whole_word(skill).search(text)
        if match:
            found.append((match.start(), skill.lower()))
    result: list[str] = []
    for _, skill in sorted(found):
        if skill not in result:
            result.append(skill)
    return result


def extract_years(text: str) -> int:
    """The largest "N years" / "N años" in the text, capped at YEARS_CAP; 0 if none."""
    years = [int(match.group(1)) for match in _YEARS.finditer(text)]
    return min(max(years), YEARS_CAP) if years else 0


def years_points(years: int) -> int:
    if years >= 8:
        return 30
    if years >= 3:
        return 20
    if years >= 1:
        return 10
    return 0


def evidence_points(cv_text: str, job_title: str) -> int:
    """20 for the full title; 10 if at least half of its 4+ letter words appear; else 0."""
    if _whole_word(job_title.strip()).search(cv_text):
        return 20
    words = [
        w for w in _LETTER_WORDS.findall(job_title) if len(w) >= TITLE_WORD_MIN_LETTERS
    ]
    if not words:
        return 0
    found = sum(1 for word in words if _whole_word(word).search(cv_text))
    return 10 if found * 2 >= len(words) else 0


def skills_points(found: int, total: int) -> int:
    """50 x found / total, rounded half up. Integer arithmetic avoids float rounding."""
    return (100 * found + total) // (2 * total)


def _block(user: str, name: str, nonce: str) -> str:
    begin = f"BEGIN-{name}-{nonce}\n"
    start = user.index(begin) + len(begin)
    return user[start : user.index(f"\nEND-{name}-{nonce}", start)]


class MockLLM:
    """Default provider: deterministic, offline and free.

    It reads the offer and the CV back out of the marked blocks and applies the same
    rubric the system prompt describes. Nothing written inside the CV can change it.
    """

    provider = "mock"
    model = "mock-keyword-v1"

    def complete(self, system: str, user: str) -> str:
        nonce_match = _NONCE.search(system)
        if nonce_match is None:
            raise LLMUnavailableError("prompt format not recognised")
        nonce = nonce_match.group(1)
        offer = _block(user, "OFFER", nonce)
        cv_text = _block(user, "CV", nonce)

        skills_at = offer.rindex(_SKILLS_PREFIX)
        job_title = offer[len(_TITLE_PREFIX) : skills_at]
        required_skills = json.loads(offer[skills_at + len(_SKILLS_PREFIX) :])

        matched = find_skills(cv_text, required_skills)
        years = extract_years(cv_text)
        score = (
            skills_points(len(matched), len(required_skills))
            + years_points(years)
            + evidence_points(cv_text, job_title)
        )
        skills = find_skills(cv_text, [*required_skills, *SKILL_VOCABULARY])[:50]
        summary = (
            f"{years} años de experiencia; cumple {len(matched)} de "
            f"{len(required_skills)} skills requeridas para {job_title}."
        )
        return json.dumps(
            {
                "skills": skills,
                "years_experience": years,
                "summary": summary,
                "match_score": score,
            },
            ensure_ascii=False,
        )
