import logging
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request

from app.analysis import run_analysis
from app.db import (
    DuplicateEmailError,
    get_candidate,
    get_db,
    get_latest_succeeded_result,
    insert_analysis_run,
    insert_candidate,
)
from app.errors import error_response
from app.llm.output import AnalysisResult
from app.schemas import AnalyzeRequest, CandidateCreate, CandidateOut

logger = logging.getLogger("talentlite")
router = APIRouter()

DbConnection = Annotated[sqlite3.Connection, Depends(get_db)]
# How a failed analysis is answered. The reference lets support find the logged attempt.
ANALYSIS_ERROR_STATUS = {
    "llm_invalid_output": 502,
    "llm_unavailable": 502,
    "llm_timeout": 504,
}
# SQLite stores integer IDs in 64 bits; a larger value could never match a row.
CandidateId = Annotated[int, Path(gt=0, le=2**63 - 1)]


def _to_out(row: sqlite3.Row, latest: dict | None = None) -> CandidateOut:
    return CandidateOut(
        id=row["id"],
        name=row["name"],
        email=row["email"],
        cv_text=row["cv_text"],
        created_at=row["created_at"],
        latest_analysis=None
        if latest is None
        else AnalysisResult.model_validate(latest),
    )


@router.post("/candidates", status_code=201, response_model=CandidateOut)
def create_candidate(body: CandidateCreate, conn: DbConnection) -> CandidateOut:
    try:
        candidate_id = insert_candidate(
            conn, name=body.name, email=body.email, cv_text=body.cv_text
        )
    except DuplicateEmailError:
        return error_response(409, "conflict")
    logger.info("candidate_created id=%s", candidate_id)
    return _to_out(get_candidate(conn, candidate_id))


@router.get("/candidates/{candidate_id}", response_model=CandidateOut)
def read_candidate(candidate_id: CandidateId, conn: DbConnection) -> CandidateOut:
    row = get_candidate(conn, candidate_id)
    if row is None:
        return error_response(404, "not_found")
    return _to_out(row, get_latest_succeeded_result(conn, candidate_id))


@router.post("/candidates/{candidate_id}/analyze", response_model=AnalysisResult)
def analyze_candidate(
    candidate_id: CandidateId,
    body: AnalyzeRequest,
    request: Request,
    conn: DbConnection,
) -> AnalysisResult:
    # A plain def: FastAPI runs it in a worker thread, so a slow model call does not
    # block other requests.
    row = get_candidate(conn, candidate_id)
    if row is None:
        # Checked before any model call: a missing candidate never costs one.
        return error_response(404, "not_found")
    outcome = run_analysis(
        request.app.state.llm,
        cv_text=row["cv_text"],
        job_title=body.job_title,
        required_skills=body.required_skills,
    )
    if outcome.result is None:
        logger.warning(
            "analysis_failed candidate_id=%s error_code=%s attempts=%s reference=%s",
            candidate_id,
            outcome.error_code,
            outcome.attempts,
            outcome.reference,
        )
        return error_response(
            ANALYSIS_ERROR_STATUS[outcome.error_code],
            outcome.error_code,
            reference=outcome.reference,
        )
    insert_analysis_run(
        conn,
        candidate_id=candidate_id,
        job_title=body.job_title,
        required_skills=body.required_skills,
        outcome=outcome,
    )
    return outcome.result
