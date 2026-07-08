from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db

router = APIRouter(tags=["demands"])

STATUSES = ("open", "in_progress", "resolved")


@router.get("/constituencies")
def constituencies(db: Session = Depends(get_db)):
    rows = db.execute(
        text("SELECT code, name, state, lat, lon FROM constituencies ORDER BY name")
    ).mappings().all()
    return {"constituencies": [dict(r) for r in rows]}


@router.get("/demands")
def list_demands(c: str = "south-delhi", db: Session = Depends(get_db)):
    """Clustered demands with counts — feeds the hotspot map (F3)."""
    rows = db.execute(
        text(
            "SELECT d.id, d.title, d.category, d.ward_code, d.signal_count, "
            "       d.trend_7d, d.status, w.lat, w.lon "
            "FROM demands d LEFT JOIN wards w USING (ward_code) "
            "WHERE d.constituency = :c "
            "ORDER BY d.signal_count DESC"
        ),
        {"c": c},
    ).mappings().all()
    return {"demands": [dict(r) for r in rows]}


class StatusBody(BaseModel):
    status: str


@router.post("/demands/{demand_id}/status")
def set_status(demand_id: int, body: StatusBody, db: Session = Depends(get_db)):
    """MP-office action: move a demand through open → in_progress → resolved.
    (Auth is a production concern — the pilot dashboard is office-internal.)"""
    if body.status not in STATUSES:
        raise HTTPException(status_code=422, detail=f"status must be one of {STATUSES}")
    updated = db.execute(
        text(
            "UPDATE demands SET status = :s, "
            "resolved_at = CASE WHEN :s = 'resolved' THEN now() ELSE NULL END "
            "WHERE id = :id RETURNING id"
        ),
        {"s": body.status, "id": demand_id},
    ).first()
    db.commit()
    if not updated:
        raise HTTPException(status_code=404, detail="demand not found")
    return {"id": demand_id, "status": body.status}


@router.get("/public/board")
def public_board(c: str = "south-delhi", db: Session = Depends(get_db)):
    """Citizen-facing transparency board: what's raised, what's resolved."""
    rows = db.execute(
        text(
            "SELECT d.id, d.title, d.category, d.status, d.signal_count, "
            "       d.resolved_at::date::text AS resolved_on, w.name AS ward_name "
            "FROM demands d LEFT JOIN wards w USING (ward_code) "
            "WHERE d.constituency = :c "
            "ORDER BY (d.status = 'resolved'), d.signal_count DESC"
        ),
        {"c": c},
    ).mappings().all()
    items = [dict(r) for r in rows]
    return {
        "open": [i for i in items if i["status"] != "resolved"],
        "resolved": [i for i in items if i["status"] == "resolved"],
    }


@router.get("/demands/{demand_id}")
def get_demand(demand_id: int, db: Session = Depends(get_db)):
    demand = db.execute(
        text("SELECT * FROM demands WHERE id = :id"), {"id": demand_id}
    ).mappings().first()
    signals = db.execute(
        text(
            "SELECT s.summary_en, s.urgency, s.created_at, sub.kind, sub.language, "
            "       sub.raw_text AS original "
            "FROM demand_signals s JOIN submissions sub ON sub.id = s.submission_id "
            "WHERE s.demand_id = :id ORDER BY s.created_at DESC LIMIT 20"
        ),
        {"id": demand_id},
    ).mappings().all()
    return {"demand": dict(demand) if demand else None, "sample_signals": [dict(s) for s in signals]}
