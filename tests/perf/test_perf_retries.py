"""Yellow test Y3: what retries cost in time and prompt size. It never asserts or blocks."""

import pytest

from app.analysis import run_analysis
from tests.helpers import OFFER_SKILLS, OFFER_TITLE, ScriptedLLM, read_cv, valid_output
from tests.perf.report import report

DELAY_S = 0.05
CV = read_cv("cv_backend_senior.txt")


@pytest.mark.performance
def test_perf_retry_cost():
    rows = []
    for success_on in (1, 2, 3):
        script = ["{bad"] * (success_on - 1) + [valid_output()]
        llm = ScriptedLLM(script, delay_s=DELAY_S)
        outcome = run_analysis(
            llm, cv_text=CV, job_title=OFFER_TITLE, required_skills=OFFER_SKILLS
        )
        sent = sum(len(system) + len(user) for system, user in llm.prompts)
        rows.append(
            (
                f"succeeds on attempt {success_on}: total time",
                float(outcome.duration_ms),
                "ms",
            )
        )
        rows.append(
            (f"succeeds on attempt {success_on}: prompt sent", sent, "characters")
        )

    report(f"Y3 · Cost of retries (fake model, {DELAY_S * 1000:.0f} ms per call)", rows)
