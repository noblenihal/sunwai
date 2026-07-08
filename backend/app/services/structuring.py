"""Stage 1 — STRUCTURE (F2): raw submission -> DemandSignal via Gemini.

Falls back to a keyword heuristic when GEMINI_API_KEY is unset so the
pipeline stays demoable end-to-end without credentials.
"""
import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..config import settings
from . import clustering

EXTRACTION_PROMPT = """You are structuring a citizen's development request for an MP's office.
Input may be in any Indian language. Return STRICT JSON:
{"category": "road|water|school|health|drainage|electricity|other",
 "sub_type": "<short>", "location_text": "<place as stated, or null>",
 "urgency": 1-5, "summary_en": "<one English sentence>", "language": "<ISO code>"}

Citizen message:
"""

_KEYWORDS = {
    "road": "road", "pothole": "road", "water": "water", "borewell": "water",
    "school": "school", "hospital": "health", "phc": "health",
    "drain": "drainage", "electric": "electricity", "light": "electricity",
}


def _parse_first_json(s: str) -> dict:
    """Gemini sometimes appends extra content after the JSON object —
    take the first valid object instead of trusting the whole body."""
    s = s.strip()
    if s.startswith("```"):
        s = s.strip("`").removeprefix("json").strip()
    obj, _ = json.JSONDecoder().raw_decode(s)
    return obj


_SIGNAL_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "category": {
            "type": "STRING",
            "enum": ["road", "water", "school", "health", "drainage", "electricity", "other"],
        },
        "sub_type": {"type": "STRING", "nullable": True},
        "location_text": {"type": "STRING", "nullable": True},
        "urgency": {"type": "INTEGER"},
        "summary_en": {"type": "STRING"},
        "language": {"type": "STRING"},
    },
    "required": ["category", "urgency", "summary_en", "language"],
}


def _extract_with_gemini(raw_text: str) -> dict:
    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)
    resp = client.models.generate_content(
        model=settings.structuring_model,
        contents=EXTRACTION_PROMPT + raw_text,
        config={
            "response_mime_type": "application/json",
            "response_schema": _SIGNAL_SCHEMA,
        },
    )
    try:
        return _parse_first_json(resp.text)
    except json.JSONDecodeError:
        print(f"[structuring] unparseable model output: {resp.text[:300]!r}")
        raise


def _extract_fallback(raw_text: str) -> dict:
    lowered = (raw_text or "").lower()
    category = next((v for k, v in _KEYWORDS.items() if k in lowered), "other")
    return {
        "category": category, "sub_type": None, "location_text": None,
        "urgency": 3, "summary_en": (raw_text or "")[:200], "language": "en",
    }


def process_submission(db: Session, submission_id: int) -> dict:
    sub = db.execute(
        text("SELECT * FROM submissions WHERE id = :id"), {"id": submission_id}
    ).mappings().one()

    # TODO(F2): voice -> Cloud Speech-to-Text, image -> Gemini multimodal
    raw = sub["raw_text"] or ""
    if settings.gemini_api_key:
        data = _extract_with_gemini(raw)
    else:
        data = _extract_fallback(raw)

    row = db.execute(
        text(
            "INSERT INTO demand_signals "
            "(submission_id, category, sub_type, location_text, urgency, summary_en) "
            "VALUES (:sid, :category, :sub_type, :location_text, :urgency, :summary_en) "
            "RETURNING id"
        ),
        {"sid": submission_id, **{k: data.get(k) for k in
         ("category", "sub_type", "location_text", "urgency", "summary_en")}},
    )
    signal_id = row.scalar_one()
    db.execute(
        text("UPDATE submissions SET processed_at = now(), language = :lang WHERE id = :id"),
        {"id": submission_id, "lang": data.get("language")},
    )
    db.commit()

    clustering.assign_to_demand(db, signal_id)
    return {"signal_id": signal_id, **data}
