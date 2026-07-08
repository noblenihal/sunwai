"""Stage 2 — AGGREGATE (F3): dedupe signals into demands.

MVP heuristic: same (category, ward_code) -> same demand. Embedding-based
clustering (pgvector cosine) replaces this in F3 — see docs/F3-clustering-map.md.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session


def assign_to_demand(db: Session, signal_id: int) -> int:
    sig = db.execute(
        text("SELECT * FROM demand_signals WHERE id = :id"), {"id": signal_id}
    ).mappings().one()

    demand = db.execute(
        text(
            "SELECT id FROM demands WHERE category = :cat "
            "AND ward_code IS NOT DISTINCT FROM :ward LIMIT 1"
        ),
        {"cat": sig["category"], "ward": sig["ward_code"]},
    ).first()

    if demand:
        demand_id = demand[0]
        db.execute(
            text(
                "UPDATE demands SET signal_count = signal_count + 1, "
                "updated_at = now() WHERE id = :id"
            ),
            {"id": demand_id},
        )
    else:
        title = f"{sig['category'].title()} — {sig['ward_code'] or 'unlocated'}"
        demand_id = db.execute(
            text(
                "INSERT INTO demands (title, category, ward_code, signal_count) "
                "VALUES (:title, :cat, :ward, 1) RETURNING id"
            ),
            {"title": title, "cat": sig["category"], "ward": sig["ward_code"]},
        ).scalar_one()

    db.execute(
        text("UPDATE demand_signals SET demand_id = :d WHERE id = :s"),
        {"d": demand_id, "s": signal_id},
    )
    db.commit()
    return demand_id
