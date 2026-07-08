"""Stage 3 — ENRICH (F4): join demands with ward-level public data.

Ward data source: SEC Delhi Delimitation 2022 Annexure-1 (Census 2011
population + SC population), loaded by backend/initdb/03_ward_indicators.sql.
gap_score is deliberately simple and explainable:
  0.5 baseline when ward data exists
+ up to 0.5 for SC population share (equity weight, MPLADS 15% SC mandate)
+ 0.5 if the ward's colony profile indicates unauthorized/resettlement
  areas (infrastructure-deficit proxy)
Range 0.5–1.5 → gap_weight (1+gap) 1.5–2.5.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session

DEFICIT_MARKERS = ("unauthorized", "resettlement", "jj")


def evidence_for(db: Session, demand_id: int) -> dict:
    row = db.execute(
        text(
            "SELECT d.category, w.name, w.population, w.sc_st_share, w.indicators "
            "FROM demands d LEFT JOIN wards w USING (ward_code) WHERE d.id = :id"
        ),
        {"id": demand_id},
    ).mappings().first()
    if not row or row["indicators"] is None:
        return {"available": False, "facts": [], "gap_score": 0.0}

    ind = row["indicators"]
    sc = row["sc_st_share"] or 0.0
    profile = (ind.get("colony_profile") or "").lower()
    deficit = any(m in profile for m in DEFICIT_MARKERS)

    gap_score = 0.5 + min(sc, 0.5) + (0.5 if deficit else 0.0)

    facts = [
        f"Ward population {row['population']:,} (Census 2011; SEC Delimitation 2022, ward {ind.get('ward_no')})",
        f"SC population share {sc:.1%} ({ind.get('sc_population'):,} residents)",
        f"Colony profile: {ind.get('colony_profile')}",
    ]
    return {
        "available": True,
        "population": row["population"],
        "sc_st_share": sc,
        "gap_score": round(gap_score, 3),
        "facts": facts,
        "source": ind.get("source"),
    }
