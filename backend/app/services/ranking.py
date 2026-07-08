"""Stage 4 — SCORE (F5): rank demands, write Gemini justifications.

score = signal_count * (1 + trend) * gap_weight
Weights are deliberately simple and visible — the MP must be able to defend
"why #1 over #7" publicly.

Justifications: Gemini Flash, top-10 only, cached by an input hash
(justification_key) so a rerank with unchanged data makes zero LLM calls.
"""
import hashlib
import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..config import settings
from . import evidence

JUSTIFY_TOP_N = 10

JUSTIFY_PROMPT = """You write one-paragraph briefs for an MP's office in South Delhi.

Development demand: "{title}" (ward: {ward}).
Citizen submissions: {count} (week-over-week trend: {trend}).
Evidence facts: {facts}
Sample citizen voices: {quotes}

Write exactly 3 sentences explaining why this work deserves its priority.
Cite ONLY the figures given above — do not invent numbers, places, or schemes.
Factual tone. No flattery, no hedging."""


def _refresh_trends(db: Session) -> None:
    """trend_7d = (signals last 7d − prior 7d) / max(prior 7d, 1), per demand."""
    db.execute(
        text(
            "UPDATE demands d SET trend_7d = t.trend FROM ("
            "  SELECT demand_id,"
            "         (count(*) FILTER (WHERE created_at >= now() - interval '7 days')"
            "          - count(*) FILTER (WHERE created_at >= now() - interval '14 days'"
            "                              AND created_at < now() - interval '7 days'))::real"
            "         / GREATEST(count(*) FILTER (WHERE created_at >= now() - interval '14 days'"
            "                              AND created_at < now() - interval '7 days'), 1) AS trend"
            "  FROM demand_signals WHERE demand_id IS NOT NULL GROUP BY demand_id"
            ") t WHERE d.id = t.demand_id"
        )
    )
    db.commit()


def _sample_quotes(db: Session, demand_id: int, limit: int = 3) -> list[str]:
    rows = db.execute(
        text(
            "SELECT summary_en FROM demand_signals WHERE demand_id = :id "
            "ORDER BY created_at DESC LIMIT :n"
        ),
        {"id": demand_id, "n": limit},
    ).all()
    return [r[0] for r in rows]


def _justification_inputs(demand, ev: dict, quotes: list[str]) -> tuple[str, str]:
    """Returns (prompt, cache_key)."""
    facts = "; ".join(ev.get("facts", [])) or "no public-data evidence loaded yet"
    prompt = JUSTIFY_PROMPT.format(
        title=demand["title"], ward=demand["ward_code"] or "unlocated",
        count=demand["signal_count"],
        trend=f"{demand['trend_7d']:+.0%}" if demand["trend_7d"] is not None else "n/a",
        facts=facts, quotes=" | ".join(quotes) or "none",
    )
    key = hashlib.md5(prompt.encode()).hexdigest()
    return prompt, key


def _generate_justification(prompt: str) -> str | None:
    try:
        from google import genai

        client = genai.Client(api_key=settings.gemini_api_key)
        resp = client.models.generate_content(
            model=settings.structuring_model,  # Flash: cost over polish; swap to
            contents=prompt,                   # ranking_model for demo day
        )
        out = (resp.text or "").strip()
        return out or None
    except Exception as exc:
        print(f"[ranking] justification failed: {exc.__class__.__name__}: {exc}")
        return None


def rerank_all(db: Session) -> int:
    _refresh_trends(db)
    demands = db.execute(
        text("SELECT id, signal_count, trend_7d, constituency FROM demands")
    ).mappings().all()
    by_constituency: dict[str, list] = {}
    for d in demands:
        ev = evidence.evidence_for(db, d["id"])
        gap_weight = 1 + ev.get("gap_score", 0.5 if ev.get("available") else 0.0)
        score = d["signal_count"] * (1 + (d["trend_7d"] or 0)) * gap_weight
        by_constituency.setdefault(d["constituency"] or "south-delhi", []).append(
            (d["id"], score, gap_weight, ev)
        )

    total = 0
    for scored in by_constituency.values():  # rank is per-constituency
        scored.sort(key=lambda t: t[1], reverse=True)
        for rank, (demand_id, score, gap_weight, ev) in enumerate(scored, start=1):
            ev["gap_weight"] = gap_weight
            db.execute(
                text(
                    "UPDATE demands SET score = :score, rank = :rank, evidence = :ev "
                    "WHERE id = :id"
                ),
                {"id": demand_id, "score": score, "rank": rank, "ev": json.dumps(ev)},
            )
            total += 1
    db.commit()

    # justifications for the top N — skipped when the cache key is unchanged
    generated = 0
    if settings.gemini_api_key:
        top = db.execute(
            text(
                "SELECT id, title, ward_code, signal_count, trend_7d, evidence, "
                "       justification_key "
                "FROM demands WHERE rank <= :n ORDER BY rank"
            ),
            {"n": JUSTIFY_TOP_N},
        ).mappings().all()
        for d in top:
            ev = d["evidence"] if isinstance(d["evidence"], dict) else json.loads(d["evidence"] or "{}")
            quotes = _sample_quotes(db, d["id"])
            prompt, key = _justification_inputs(d, ev, quotes)
            if key == d["justification_key"]:
                continue
            justification = _generate_justification(prompt)
            if justification:
                db.execute(
                    text(
                        "UPDATE demands SET justification = :j, justification_key = :k "
                        "WHERE id = :id"
                    ),
                    {"id": d["id"], "j": justification, "k": key},
                )
                generated += 1
        db.commit()
        if generated:
            print(f"[ranking] generated {generated} justifications")

    return total
