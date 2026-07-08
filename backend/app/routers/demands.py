from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db

router = APIRouter(tags=["demands"])


@router.get("/demands")
def list_demands(db: Session = Depends(get_db)):
    """Clustered demands with counts — feeds the hotspot map (F3)."""
    rows = db.execute(
        text(
            "SELECT d.id, d.title, d.category, d.ward_code, d.signal_count, "
            "       d.trend_7d, w.lat, w.lon "
            "FROM demands d LEFT JOIN wards w USING (ward_code) "
            "ORDER BY d.signal_count DESC"
        )
    ).mappings().all()
    return {"demands": [dict(r) for r in rows]}


@router.get("/demands/{demand_id}")
def get_demand(demand_id: int, db: Session = Depends(get_db)):
    demand = db.execute(
        text("SELECT * FROM demands WHERE id = :id"), {"id": demand_id}
    ).mappings().first()
    signals = db.execute(
        text(
            "SELECT s.summary_en, s.urgency, s.created_at, sub.kind, sub.language "
            "FROM demand_signals s JOIN submissions sub ON sub.id = s.submission_id "
            "WHERE s.demand_id = :id ORDER BY s.created_at DESC LIMIT 20"
        ),
        {"id": demand_id},
    ).mappings().all()
    return {"demand": dict(demand) if demand else None, "sample_signals": [dict(s) for s in signals]}
