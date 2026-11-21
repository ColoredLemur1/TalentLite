"""MockLLM: a deterministic keyword rubric (skills 50, years 30, evidence 20)."""

from app.llm.mock import (
    MockLLM,
    evidence_points,
    extract_years,
    find_skills,
    skills_points,
    years_points,
)
from app.llm.output import parse_and_validate
from app.llm.prompt import build_prompt
from tests.helpers import OFFER_SKILLS, OFFER_TITLE, read_cv

SENIOR = read_cv("cv_backend_senior.txt")
JUNIOR = read_cv("cv_junior_no_years.txt")
MALICIOUS = read_cv("cv_malicious.txt")


def run_mock(cv, title=OFFER_TITLE, skills=OFFER_SKILLS):
    prompt = build_prompt(cv, title, skills)
    return parse_and_validate(MockLLM().complete(prompt.system, prompt.user))


def test_mock_is_deterministic():
    assert run_mock(SENIOR) == run_mock(SENIOR)


def test_mock_output_valid_for_all_fixture_cvs():
    for cv in (SENIOR, JUNIOR, MALICIOUS):
        run_mock(cv)


def test_mock_rubric_cases():
    assert run_mock(SENIOR).match_score == 90  # 40 + 30 + 20
    assert run_mock(JUNIOR).match_score == 30  # 20 + 0 + 10
    assert run_mock(MALICIOUS).match_score == 90


def test_years_band_edges():
    expected = {0: 0, 1: 10, 2: 10, 3: 20, 5: 20, 6: 20, 7: 20, 8: 30, 40: 30}
    assert {years: years_points(years) for years in expected} == expected


def test_evidence_full_partial_none():
    assert evidence_points("Backend Developer en Acme", "Backend Developer") == 20
    assert evidence_points("Developer en Acme", "Backend Developer") == 10
    assert evidence_points("Cocinero en Acme", "Backend Developer") == 0
    assert evidence_points("Trabajo de QA en Acme", "QA") == 20
    assert evidence_points("Trabajo de soporte en Acme", "QA") == 0


def test_skills_points_round_half_up():
    assert skills_points(1, 4) == 13
    assert skills_points(3, 4) == 38
    assert skills_points(2, 5) == 20


def test_skills_returned_lowercase_deduplicated_in_cv_order():
    text = "SQL y Python, luego python y FastAPI"
    assert find_skills(text, ["Python", "FastAPI", "SQL"]) == [
        "sql",
        "python",
        "fastapi",
    ]


def test_skill_match_whole_word():
    assert find_skills("JavaScript", ["Java"]) == []
    assert find_skills("C++, C# y Node.js", ["C++", "C#", "Node.js"]) == [
        "c++",
        "c#",
        "node.js",
    ]


def test_skill_and_title_with_regex_metacharacters():
    assert find_skills("abc", ["(.*)"]) == []
    run_mock(SENIOR, title="C++ Dev (.*)", skills=["(.*)", "C++"])


def test_years_extraction():
    cases = {
        "5 years": 5,
        "5+ years": 5,
        "5 años": 5,
        "1 year": 1,
        "1 año": 1,
        "10+ años": 10,
        "sin experiencia": 0,
        "2 years in Acme, then 7 years in Beta": 7,
        "99 years": 50,
    }
    assert {text: extract_years(text) for text in cases} == cases


def test_mock_zero_match_is_valid_output():
    result = run_mock("Chef con experiencia en cocina.")
    assert result.match_score == 0
    assert result.skills == []


def test_malicious_cv_scores_same_as_clean_cv():
    assert run_mock(MALICIOUS) == run_mock(SENIOR)


def test_summary_within_400_with_longest_job_title():
    assert len(run_mock(SENIOR, title="a" * 200).summary) <= 400
