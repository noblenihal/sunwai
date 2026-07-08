"""Stage 3 — ENRICH (F4): join demands with ward-level public data.

Ward indicators (Census / UDISE / facility registry) are loaded into the
`wards` table by scripts/load_public_data.py (F4). This service reads them.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session


def evidence_for(db: Session, demand_id: int) -> dict:
    row = db.execute(
        text(
            "SELECT d.category, w.population, w.sc_st_share, w.indicators "
            "FROM demands d LEFT JOIN wards w USING (ward_code) WHERE d.id = :id"
        ),
        {"id": demand_id},
    ).mappings().first()
    if not row or row["indicators"] is None:
        return {"available": False}
    # TODO(F4): category-specific gap analysis (school distance vs enrollment, etc.)
    return {"available": True, "population": row["population"],
            "sc_st_share": row["sc_st_share"], "indicators": row["indicators"]}
