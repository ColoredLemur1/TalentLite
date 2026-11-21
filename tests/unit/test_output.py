"""Model output validation, which the brief requires.

The model's answer is untrusted input: a manipulated answer (match_score 250) and broken
JSON must both be rejected. The output is rejected, never repaired.
"""

import json

import pytest

from app.llm.output import InvalidLLMOutput, parse_and_validate
from tests.helpers import valid_output


def _rejected(raw: str) -> None:
    with pytest.raises(InvalidLLMOutput):
        parse_and_validate(raw)


def test_match_score_250_rejected():
    with pytest.raises(InvalidLLMOutput):
        parse_and_validate(valid_output(match_score=250))


def test_broken_json_rejected():
    with pytest.raises(InvalidLLMOutput):
        parse_and_validate('{"skills": ["python"], "match_score": ')


def test_valid_output_parses():
    assert parse_and_validate(valid_output()).match_score == 50


def test_match_score_bounds():
    _rejected(valid_output(match_score=-1))
    _rejected(valid_output(match_score=101))
    assert parse_and_validate(valid_output(match_score=0)).match_score == 0
    assert parse_and_validate(valid_output(match_score=100)).match_score == 100


def test_match_score_float_string_or_bool_rejected():
    for value in (85.5, "85", True):
        _rejected(valid_output(match_score=value))


def test_years_negative_nan_or_string_rejected():
    _rejected(valid_output(years_experience=-1))
    _rejected(
        '{"skills": ["python"], "years_experience": NaN, '
        '"summary": "Resumen.", "match_score": 50}'
    )
    _rejected(valid_output(years_experience="5"))
    assert (
        parse_and_validate(valid_output(years_experience=5.5)).years_experience == 5.5
    )
    assert parse_and_validate(valid_output(years_experience=0)).years_experience == 0


def test_years_bounds_and_bool_rejected():
    assert parse_and_validate(valid_output(years_experience=80)).years_experience == 80
    assert (
        parse_and_validate(valid_output(years_experience=5.5)).years_experience == 5.5
    )
    _rejected(valid_output(years_experience=81))
    _rejected(valid_output(years_experience=True))


def test_summary_400_ok_401_rejected():
    assert len(parse_and_validate(valid_output(summary="a" * 400)).summary) == 400
    _rejected(valid_output(summary="a" * 401))


def test_summary_empty_rejected():
    _rejected(valid_output(summary=""))


def test_skills_wrong_shape_rejected():
    for skills in ("python", [1], [""], ["a"] * 51):
        _rejected(valid_output(skills=skills))


def test_missing_or_extra_field_rejected():
    without_summary = json.loads(valid_output())
    del without_summary["summary"]
    _rejected(json.dumps(without_summary))
    _rejected(valid_output(admin=True))


def test_top_level_array_string_or_null_rejected():
    for raw in ("[]", '"x"', "null"):
        _rejected(raw)


def test_empty_output_rejected():
    for raw in ("", "   "):
        _rejected(raw)


def test_json_fence_tolerated():
    raw = "```json\n" + valid_output() + "\n```"
    assert parse_and_validate(raw).match_score == 50


def test_double_json_fence_rejected():
    _rejected("```json\n```json\n" + valid_output() + "\n```\n```")


def test_prose_around_json_rejected():
    _rejected("Sure! " + valid_output())


def test_extra_key_name_not_in_error_summary():
    raw = json.dumps({**json.loads(valid_output()), "SECRET-CV-LINE": 1})
    with pytest.raises(InvalidLLMOutput) as exc_info:
        parse_and_validate(raw)
    assert "<extra>: extra_forbidden" in exc_info.value.summary
    assert "SECRET-CV-LINE" not in exc_info.value.summary


def test_validation_error_summary_contains_no_values():
    with pytest.raises(InvalidLLMOutput) as exc_info:
        parse_and_validate(valid_output(summary="SECRET-CV-LINE" * 40))
    assert "SECRET" not in exc_info.value.summary
    assert "summary" in exc_info.value.summary
