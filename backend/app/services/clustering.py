"""Stage 2 — AGGREGATE (F3): dedupe signals into demands.

Embedding-based: nearest demand centroid by cosine similarity, ward-scoped
first (0.75), then cross-ward (0.85). Falls back to the category+ward
heuristic for signals without embeddings. Titles come from one cheap Gemini
call; centroid is a running mean.
"""
import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..config import settings

WARD_SIM_THRESHOLD = 0.75
CROSS_WARD_SIM_THRESHOLD = 0.85


def _nearest_demand(db: Session, sig, ward_scoped: bool):
    where = "category = :cat AND centroid IS NOT NULL"
    if ward_scoped:
        where += " AND ward_code IS NOT DISTINCT FROM :ward"
    row = db.execute(
        text(
            f"SELECT id, signal_count, 1 - (centroid <=> (:emb)::vector) AS sim "
            f"FROM demands WHERE {where} "
            f"ORDER BY centroid <=> (:emb)::vector LIMIT 1"
        ),
        {"cat": sig["category"], "ward": sig["ward_code"], "emb": sig["embedding"]},
    ).mappings().first()
    return row


def _title_for(sig) -> str:
    fallback = f"{sig['category'].title()} — {sig['ward_code'] or 'unlocated'}"
    if not settings.gemini_api_key:
        return fallback
    try:
        from google import genai

        client = genai.Client(api_key=settings.gemini_api_key)
        resp = client.models.generate_content(
            model=settings.structuring_model,
            contents=(
                "Title this civic demand in 6 words or fewer, plain English, "
                f"no punctuation flourishes: {sig['summary_en']}"
            ),
        )
        title = (resp.text or "").strip().strip('"')
        return title[:80] if title else fallback
    except Exception:
        return fallback


def _attach(db: Session, demand_id: int, sig, prev_count: int):
    """Add signal to demand; update centroid to running mean."""
    if sig["embedding"] is not None:
        emb = json.loads(sig["embedding"]) if isinstance(sig["embedding"], str) else list(sig["embedding"])
        cur = db.execute(
            text("SELECT centroid::text FROM demands WHERE id = :id"), {"id": demand_id}
        ).scalar_one()
        if cur:
            centroid = json.loads(cur)
            n = prev_count
            centroid = [(c * n + e) / (n + 1) for c, e in zip(centroid, emb)]
        else:
            centroid = emb
        db.execute(
            text(
                "UPDATE demands SET signal_count = signal_count + 1, "
                "centroid = (:c)::vector, updated_at = now() WHERE id = :id"
            ),
            {"id": demand_id, "c": str(centroid)},
        )
    else:
        db.execute(
            text(
                "UPDATE demands SET signal_count = signal_count + 1, "
                "updated_at = now() WHERE id = :id"
            ),
            {"id": demand_id},
        )


def reassign(db: Session, signal_id: int) -> int:
    """Detach a signal from its demand (e.g. after a ward correction) and
    re-cluster it. Centroid means are not recomputed on detach — acceptable
    drift for single corrections."""
    old = db.execute(
        text("SELECT demand_id FROM demand_signals WHERE id = :id"), {"id": signal_id}
    ).scalar_one()
    if old:
        db.execute(
            text("UPDATE demands SET signal_count = signal_count - 1 WHERE id = :id"),
            {"id": old},
        )
        db.execute(
            text("UPDATE demand_signals SET demand_id = NULL WHERE id = :id"),
            {"id": signal_id},
        )
        db.execute(text("DELETE FROM demands WHERE id = :id AND signal_count <= 0"), {"id": old})
        db.commit()
    return assign_to_demand(db, signal_id)


def assign_to_demand(db: Session, signal_id: int) -> int:
    sig = db.execute(
        text("SELECT *, embedding::text AS embedding_txt FROM demand_signals WHERE id = :id"),
        {"id": signal_id},
    ).mappings().one()
    sig = dict(sig)
    sig["embedding"] = sig.pop("embedding_txt")

    demand_id = None
    if sig["embedding"] is not None:
        near = _nearest_demand(db, sig, ward_scoped=True)
        if near and near["sim"] >= WARD_SIM_THRESHOLD:
            demand_id = near["id"]
            _attach(db, demand_id, sig, near["signal_count"])
        else:
            near = _nearest_demand(db, sig, ward_scoped=False)
            if near and near["sim"] >= CROSS_WARD_SIM_THRESHOLD:
                demand_id = near["id"]
                _attach(db, demand_id, sig, near["signal_count"])
        if demand_id is None:
            # demands created without embeddings are invisible to the
            # similarity search — adopt them by category+ward (and _attach
            # seeds their centroid from this signal)
            row = db.execute(
                text(
                    "SELECT id, signal_count FROM demands WHERE category = :cat "
                    "AND ward_code IS NOT DISTINCT FROM :ward "
                    "AND centroid IS NULL LIMIT 1"
                ),
                {"cat": sig["category"], "ward": sig["ward_code"]},
            ).mappings().first()
            if row:
                demand_id = row["id"]
                _attach(db, demand_id, sig, row["signal_count"])
    else:
        row = db.execute(
            text(
                "SELECT id, signal_count FROM demands WHERE category = :cat "
                "AND ward_code IS NOT DISTINCT FROM :ward LIMIT 1"
            ),
            {"cat": sig["category"], "ward": sig["ward_code"]},
        ).mappings().first()
        if row:
            demand_id = row["id"]
            _attach(db, demand_id, sig, row["signal_count"])

    if demand_id is None:
        demand_id = db.execute(
            text(
                "INSERT INTO demands (title, category, ward_code, signal_count, centroid) "
                "VALUES (:title, :cat, :ward, 1, (:emb)::vector) RETURNING id"
            ),
            {
                "title": _title_for(sig), "cat": sig["category"],
                "ward": sig["ward_code"],
                "emb": sig["embedding"],
            },
        ).scalar_one()

    db.execute(
        text("UPDATE demand_signals SET demand_id = :d WHERE id = :s"),
        {"d": demand_id, "s": signal_id},
    )
    db.commit()
    return demand_id
