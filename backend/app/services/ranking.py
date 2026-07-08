"""Stage 4 — SCORE (F5): rank demands, write Gemini justifications.

score = signal_count * (1 + trend) * evidence_gap_weight
Weights are deliberately simple and visible — the MP must be able to defend
"why #1 over #7" publicly.
"""
import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..config import settings
from . import evidence


def rerank_all(db: Session) -> int:
    demands = db.execute(text("SELECT id, signal_count, trend_7d FROM demands")).mappings().all()
    scored = []
    for d in demands:
        ev = evidence.evidence_for(db, d["id"])
        gap_weight = 1.5 if ev.get("available") else 1.0  # TODO(F5): real gap scoring
        score = d["signal_count"] * (1 + (d["trend_7d"] or 0)) * gap_weight
        scored.append((d["id"], score, ev))

    scored.sort(key=lambda t: t[1], reverse=True)
    for rank, (demand_id, score, ev) in enumerate(scored, start=1):
        db.execute(
            text(
                "UPDATE demands SET score = :score, rank = :rank, evidence = :ev, "
                "justification = COALESCE(justification, :just) WHERE id = :id"
            ),
            {
                "id": demand_id, "score": score, "rank": rank,
                "ev": json.dumps(ev),
                "just": None if settings.gemini_api_key else "(justification pending Gemini key)",
            },
        )
    db.commit()
    # TODO(F5): batch Gemini call to write plain-language justifications
    return len(scored)
