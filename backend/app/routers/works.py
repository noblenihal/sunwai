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


POP_FLOOR = 30000  # tiny areas distort per-capita normalization


@router.get("/silent-needs")
def silent_needs(db: Session = Depends(get_db)):
    """F6: silence_score = need × (1 − voice).

    need  = SC share (equity, capped) + colony-deficit proxy, capped at 1
    voice = submissions per 1000 residents, normalized to the loudest ward
    High need + low voice = likely unheard, not unneeding.
    """
    from ..services.evidence import DEFICIT_MARKERS

    rows = db.execute(
        text(
            "SELECT w.ward_code, w.name, w.population, w.sc_st_share, w.indicators, "
            "       COALESCE(s.cnt, 0) AS signals "
            "FROM wards w LEFT JOIN ("
            "    SELECT ward_code, count(*) AS cnt FROM demand_signals "
            "    WHERE ward_code IS NOT NULL GROUP BY ward_code) s USING (ward_code) "
            "WHERE w.population IS NOT NULL AND w.population >= :floor"
        ),
        {"floor": POP_FLOOR},
    ).mappings().all()
    if not rows:
        return {"wards": [], "population_floor": POP_FLOOR}

    per_1000 = {r["ward_code"]: r["signals"] * 1000.0 / r["population"] for r in rows}
    v_max = max(per_1000.values()) or 1.0

    out = []
    for r in rows:
        ind = r["indicators"] or {}
        profile = (ind.get("colony_profile") or "").lower()
        deficit = any(m in profile for m in DEFICIT_MARKERS)
        sc = r["sc_st_share"] or 0.0
        need = min(1.0, sc * 1.2 + (0.5 if deficit else 0.0))
        voice = per_1000[r["ward_code"]] / v_max if v_max else 0.0
        silence = need * (1.0 - voice)
        facts = [
            f"SC population share {sc:.1%}",
            f"Colony profile: {ind.get('colony_profile', 'n/a')}",
            f"{r['signals']} submissions for {r['population']:,} residents "
            f"({per_1000[r['ward_code']]:.2f}/1000)",
        ]
        out.append({
            "ward_code": r["ward_code"], "name": r["name"],
            "population": r["population"], "signals": r["signals"],
            "silence_score": round(silence, 3), "need_score": round(need, 3),
            "facts": facts,
            "suggest_visit": False,
        })

    out.sort(key=lambda w: w["silence_score"], reverse=True)
    for w in out[:3]:
        w["suggest_visit"] = True
    return {"wards": out, "population_floor": POP_FLOOR}
