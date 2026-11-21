import json
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Query

from app.db import count_analysis_runs, get_candidate, list_analysis_runs
from app.errors import error_response
from app.llm.output import AnalysisResult
from app.routers.candidates import CandidateId, DbConnection
from app.schemas import AuditItem, AuditPage

router = APIRouter()

Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0, le=1_000_000)]


def _to_item(row: sqlite3.Row) -> AuditItem:
    # The row holds exactly the 13 audit columns: error_detail is never selected.
    return AuditItem(
        id=row["id"],
        created_at=row["created_at"],
        job_title=row["job_title"],
        required_skills=json.loads(row["required_skills"]),
        status=row["status"],
        result=None
        if row["result"] is None
        else AnalysisResult.model_validate(json.loads(row["result"])),
        error_code=row["error_code"],
        provider=row["provider"],
        model=row["model"],
        prompt_version=row["prompt_version"],
        attempts=row["attempts"],
        duration_ms=row["duration_ms"],
        reference=row["reference"],
    )


@router.get("/candidates/{candidate_id}/audit", response_model=AuditPage)
def read_audit(
    candidate_id: CandidateId,
    conn: DbConnection,
    limit: Limit = 20,
    offset: Offset = 0,
) -> AuditPage:
    if get_candidate(conn, candidate_id) is None:
        # Checked before either audit query.
        return error_response(404, "not_found")
    rows = list_analysis_runs(conn, candidate_id, limit, offset)
    return AuditPage(
        candidate_id=candidate_id,
        items=[_to_item(row) for row in rows],
        total=count_analysis_runs(conn, candidate_id),
        limit=limit,
        offset=offset,
    )
