"""Submission intake: demo-inject endpoint (F2) and shared pipeline entry.

The WhatsApp webhook (F1) and this demo endpoint both funnel into
`process_submission`, so the engine is channel-agnostic.
"""
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..services import structuring

router = APIRouter(tags=["ingest"])


class DemoSubmission(BaseModel):
    kind: str = "text"          # text | voice | image
    raw_text: str | None = None
    media_url: str | None = None
    language: str | None = None


@router.post("/ingest/demo")
def ingest_demo(
    body: DemoSubmission,
    x_demo_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    if not settings.demo_inject_token or x_demo_token != settings.demo_inject_token:
        raise HTTPException(status_code=401, detail="bad demo token")

    row = db.execute(
        text(
            "INSERT INTO submissions (channel, kind, raw_text, media_url, language) "
            "VALUES ('demo', :kind, :raw_text, :media_url, :language) RETURNING id"
        ),
        body.model_dump(),
    )
    submission_id = row.scalar_one()
    db.commit()

    signal = structuring.process_submission(db, submission_id)
    return {"submission_id": submission_id, "signal": signal}


@router.post("/ingest/reprocess")
def reprocess(
    x_demo_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Re-run the pipeline for submissions that never produced a signal."""
    if not settings.demo_inject_token or x_demo_token != settings.demo_inject_token:
        raise HTTPException(status_code=401, detail="bad demo token")

    stuck = db.execute(
        text(
            "SELECT s.id FROM submissions s "
            "LEFT JOIN demand_signals d ON d.submission_id = s.id "
            "WHERE d.id IS NULL AND s.processed_at IS NULL ORDER BY s.id"
        )
    ).scalars().all()
    done, failed = [], []
    for sid in stuck:
        try:
            structuring.process_submission(db, sid)
            done.append(sid)
        except Exception as exc:
            db.rollback()
            failed.append({"id": sid, "error": f"{exc.__class__.__name__}: {exc}"[:160]})
    return {"reprocessed": done, "failed": failed}
