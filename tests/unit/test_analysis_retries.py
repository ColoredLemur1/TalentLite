"""run_analysis: at most 3 attempts, and only an invalid answer is retried."""

from app.analysis import run_analysis
from app.llm.base import LLMTimeoutError, LLMUnavailableError
from tests.helpers import OFFER_SKILLS, OFFER_TITLE, ScriptedLLM, read_cv, valid_output

CV = read_cv("cv_backend_senior.txt")


def _run(llm):
    return run_analysis(
        llm, cv_text=CV, job_title=OFFER_TITLE, required_skills=OFFER_SKILLS
    )


def test_invalid_then_valid_returns_result_with_2_attempts():
    llm = ScriptedLLM(["{bad", valid_output()])
    outcome = _run(llm)
    assert outcome.status == "succeeded"
    assert outcome.result.match_score == 50
    assert outcome.attempts == 2
    assert llm.calls == 2


def test_invalid_three_times_fails_after_exactly_3_calls():
    llm = ScriptedLLM(["{bad"])
    outcome = _run(llm)
    assert outcome.status == "failed"
    assert outcome.error_code == "llm_invalid_output"
    assert outcome.attempts == 3
    assert llm.calls == 3


def test_manipulated_score_every_time_is_rejected():
    outcome = _run(ScriptedLLM([valid_output(match_score=250)]))
    assert outcome.status == "failed"
    assert outcome.error_code == "llm_invalid_output"
    assert outcome.result is None


def test_broken_json_every_time_is_rejected():
    outcome = _run(ScriptedLLM(['{"skills": [']))
    assert outcome.status == "failed"
    assert outcome.error_code == "llm_invalid_output"


def test_timeout_not_retried():
    llm = ScriptedLLM([LLMTimeoutError()])
    outcome = _run(llm)
    assert outcome.status == "failed"
    assert outcome.error_code == "llm_timeout"
    assert llm.calls == 1


def test_provider_error_not_retried():
    llm = ScriptedLLM([LLMUnavailableError()])
    outcome = _run(llm)
    assert outcome.status == "failed"
    assert outcome.error_code == "llm_unavailable"
    assert llm.calls == 1


def test_outcome_records_provider_model_prompt_version():
    outcome = _run(ScriptedLLM([valid_output()]))
    assert outcome.provider == "scripted"
    assert outcome.model == "scripted-v0"
    assert outcome.prompt_version == "v1"
    assert len(outcome.reference) == 16


def test_prompt_built_once_for_all_attempts():
    llm = ScriptedLLM(["{bad"])
    _run(llm)
    assert len(llm.prompts) == 3
    assert len(set(llm.prompts)) == 1


def test_duration_covers_every_attempt():
    outcome = _run(ScriptedLLM(["{bad"], delay_s=0.05))
    assert outcome.attempts == 3
    assert outcome.duration_ms >= 100


def test_error_detail_values():
    manipulated = _run(ScriptedLLM([valid_output(match_score=250)]))
    assert manipulated.error_detail == "match_score: less_than_equal"
    assert _run(ScriptedLLM([LLMTimeoutError()])).error_detail == "timeout"
    unavailable = _run(ScriptedLLM([LLMUnavailableError()]))
    assert unavailable.error_detail == "provider_error:LLMUnavailableError"
