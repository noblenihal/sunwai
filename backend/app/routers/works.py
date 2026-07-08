from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from ..services import ranking

router = APIRouter(tags=["works"])


@router.get("/works")
def ranked_works(db: Session = Depends(get_db)):
    """The ranked works list with evidence cards (F5)."""
    rows = db.execute(
        text(
            "SELECT id, rank, title, category, ward_code, signal_count, "
            "       trend_7d, score, evidence, justification "
            "FROM demands WHERE rank IS NOT NULL ORDER BY rank"
        )
    ).mappings().all()
    return {"works": [dict(r) for r in rows]}


@router.post("/works/rerank")
def rerank(db: Session = Depends(get_db)):
    """Recompute scores + justifications for all demands (stage 4)."""
    updated = ranking.rerank_all(db)
    return {"updated": updated}


@router.get("/silent-needs")
def silent_needs(db: Session = Depends(get_db)):
    """Wards with poor indicators but few submissions (F6)."""
    rows = db.execute(
        text(
            "SELECT w.ward_code, w.name, w.population, w.indicators, "
            "       COALESCE(SUM(d.signal_count), 0) AS signals "
            "FROM wards w LEFT JOIN demands d USING (ward_code) "
            "GROUP BY w.ward_code ORDER BY signals ASC"
        )
    ).mappings().all()
    return {"wards": [dict(r) for r in rows]}
