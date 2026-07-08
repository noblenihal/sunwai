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


DEFAULT_CONFIG = {"trend_weight": 1.0, "evidence_weight": 1.0,
                  "category_boosts": {}, "directives": ""}

DIRECTIVE_PROMPT = """The MP's office has stated these priorities for ranking
development works: "{directives}"

Demand: "{title}" · category: {category} · ward: {ward} · {count} citizen submissions.

How strongly do the stated priorities apply to this demand? Return STRICT JSON:
{{"modifier": <number between 0.8 and 1.25, 1.0 = priorities don't apply>,
  "note": "<one short sentence explaining the adjustment, or empty if 1.0>"}}"""


def load_config(db: Session, constituency: str) -> dict:
    row = db.execute(
        text("SELECT trend_weight, evidence_weight, category_boosts, directives "
             "FROM ranking_config WHERE constituency = :c"),
        {"c": constituency},
    ).mappings().first()
    return dict(row) if row else dict(DEFAULT_CONFIG)


def _directive_modifier(db: Session, demand, directives: str) -> tuple[float, str]:
    key = hashlib.md5(
        f"{directives}|{demand['id']}|{demand['signal_count']}|{demand['category']}".encode()
    ).hexdigest()
    if demand["directive_key"] == key and demand["directive_modifier"]:
        return demand["directive_modifier"], demand["directive_note"] or ""
    modifier, note = 1.0, ""
    try:
        from google import genai

        client = genai.Client(api_key=settings.gemini_api_key)
        resp = client.models.generate_content(
            model=settings.structuring_model,
            contents=DIRECTIVE_PROMPT.format(
                directives=directives[:500], title=demand["title"],
                category=demand["category"], ward=demand["ward_code"] or "unlocated",
                count=demand["signal_count"],
            ),
            config={"response_mime_type": "application/json"},
        )
        data = json.loads(resp.text.strip().strip("`").removeprefix("json"))
        modifier = min(1.25, max(0.8, float(data.get("modifier", 1.0))))
        note = (data.get("note") or "")[:200]
    except Exception as exc:
        print(f"[ranking] directive modifier failed: {exc.__class__.__name__}")
    db.execute(
        text("UPDATE demands SET directive_modifier = :m, directive_note = :n, "
             "directive_key = :k WHERE id = :id"),
        {"m": modifier, "n": note, "k": key, "id": demand["id"]},
    )
    db.commit()
    return modifier, note


def rerank_all(db: Session) -> int:
    _refresh_trends(db)
    demands = db.execute(
        text("SELECT id, title, category, ward_code, signal_count, trend_7d, "
             "constituency, directive_modifier, directive_note, directive_key "
             "FROM demands")
    ).mappings().all()
    by_constituency: dict[str, list] = {}
    for d in demands:
        by_constituency.setdefault(d["constituency"] or "south-delhi", []).append(d)

    total = 0
    for constituency, group in by_constituency.items():
        cfg = load_config(db, constituency)
        boosts = cfg.get("category_boosts") or {}
        directives = (cfg.get("directives") or "").strip()

        scored = []
        for d in group:
            ev = evidence.evidence_for(db, d["id"])
            gap_weight = 1 + ev.get("gap_score", 0.5 if ev.get("available") else 0.0)
            trend_term = 1 + cfg["trend_weight"] * (d["trend_7d"] or 0)
            evidence_term = 1 + cfg["evidence_weight"] * (gap_weight - 1)
            boost = float(boosts.get(d["category"], 1.0))
            base = max(0.0, d["signal_count"] * trend_term * evidence_term * boost)
            ev.update({"gap_weight": gap_weight, "trend_weight": cfg["trend_weight"],
                       "evidence_weight": cfg["evidence_weight"], "category_boost": boost})
            scored.append([d, base, ev])

        # plain-language office priorities: Gemini modifier for the top 15
        if directives and settings.gemini_api_key:
            scored.sort(key=lambda t: t[1], reverse=True)
            for entry in scored[:15]:
                modifier, note = _directive_modifier(db, entry[0], directives)
                entry[1] *= modifier
                entry[2]["directive_modifier"] = modifier
                entry[2]["directive_note"] = note

        scored.sort(key=lambda t: t[1], reverse=True)
        for rank, (d, score, ev) in enumerate(scored, start=1):
            db.execute(
                text("UPDATE demands SET score = :score, rank = :rank, evidence = :ev "
                     "WHERE id = :id"),
                {"id": d["id"], "score": score, "rank": rank, "ev": json.dumps(ev)},
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
