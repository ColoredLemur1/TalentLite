import logging
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.db import DuplicateEmailError, get_candidate, get_db, insert_candidate
from app.errors import error_response
from app.schemas import CandidateCreate, CandidateOut

logger = logging.getLogger("talentlite")
router = APIRouter()

DbConnection = Annotated[sqlite3.Connection, Depends(get_db)]
# SQLite stores integer IDs in 64 bits; a larger value could never match a row.
CandidateId = Annotated[int, Path(gt=0, le=2**63 - 1)]


def _to_out(row: sqlite3.Row) -> CandidateOut:
    return CandidateOut(
        id=row["id"],
        name=row["name"],
        email=row["email"],
        cv_text=row["cv_text"],
        created_at=row["created_at"],
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
    return _to_out(row)
