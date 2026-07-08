"""Stage 1 — STRUCTURE (F2): raw submission -> DemandSignal via Gemini.

One Gemini multimodal call handles text, voice notes (transcription included)
and photos. Falls back to a keyword heuristic when GEMINI_API_KEY is unset so
the pipeline stays demoable end-to-end without credentials.
"""
import json
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..config import settings
from . import clustering

EXTRACTION_PROMPT = """You are structuring a citizen's development request for an
Indian MP's office. Input may be in any Indian language, as text,
a voice note, or a photo of a civic issue.

- If audio: transcribe it in the original language into `transcript`.
- If a photo: describe the civic issue it shows in `summary_en`.
- `location_text`: the place as stated/visible (colony, ward, landmark), else null.
- `urgency`: 1 (suggestion) to 5 (safety risk / essential service down).
- `summary_en`: one factual English sentence.
- `is_civic_request`: false for greetings, confirmations, tests, spam,
  unintelligible input, or anything that is not a civic complaint or a
  development request/suggestion. When false, still fill summary_en with
  what the input appears to be.

Citizen input follows.
"""

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
        "transcript": {"type": "STRING", "nullable": True},
        "is_civic_request": {"type": "BOOLEAN"},
    },
    "required": ["category", "urgency", "summary_en", "language", "is_civic_request"],
}

_MIME_BY_EXT = {
    ".ogg": "audio/ogg", ".oga": "audio/ogg", ".mp3": "audio/mp3",
    ".wav": "audio/wav", ".m4a": "audio/aac", ".aac": "audio/aac",
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}

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


def _load_media(media_url: str) -> tuple[bytes, str]:
    mime = _MIME_BY_EXT.get(Path(media_url.split("?")[0]).suffix.lower(), "application/octet-stream")
    if media_url.startswith(("http://", "https://")):
        import httpx

        # Twilio enforces basic auth on media URLs for new accounts
        auth = None
        if "api.twilio.com" in media_url and settings.twilio_auth_token:
            auth = (settings.twilio_account_sid, settings.twilio_auth_token)
        resp = httpx.get(media_url, timeout=30, follow_redirects=True, auth=auth)
        resp.raise_for_status()
        # Twilio media URLs carry no file extension — trust the header
        header_mime = (resp.headers.get("content-type") or "").split(";")[0].strip()
        return resp.content, header_mime or mime
    return Path(media_url).read_bytes(), mime


def _extract_with_gemini(raw_text: str, media_url: str | None = None) -> dict:
    from google import genai
    from google.genai import types

    contents: list = [EXTRACTION_PROMPT]
    if raw_text:
        contents.append(raw_text)
    if media_url:
        data, mime = _load_media(media_url)
        contents.append(types.Part.from_bytes(data=data, mime_type=mime))

    client = genai.Client(api_key=settings.gemini_api_key)
    resp = client.models.generate_content(
        model=settings.structuring_model,
        contents=contents,
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


def transcribe_short(media_url: str) -> str:
    """One cheap Gemini call to transcribe a short clarification voice note."""
    from google import genai
    from google.genai import types

    data, mime = _load_media(media_url)
    client = genai.Client(api_key=settings.gemini_api_key)
    resp = client.models.generate_content(
        model=settings.structuring_model,
        contents=[
            "Transcribe this short audio exactly as spoken (it is likely an "
            "Indian place/colony name). Return ONLY the transcription.",
            types.Part.from_bytes(data=data, mime_type=mime),
        ],
    )
    return (resp.text or "").strip()


def _embed(summary_en: str) -> list[float] | None:
    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)
    resp = client.models.embed_content(
        model=settings.embedding_model,
        contents=summary_en,
        config={"output_dimensionality": 768},
    )
    return list(resp.embeddings[0].values)


def _resolve_ward(db: Session, location_text: str | None) -> str | None:
    if not location_text:
        return None
    row = db.execute(
        text(
            "SELECT ward_code FROM wards "
            "WHERE :loc ILIKE '%' || name || '%' OR name ILIKE '%' || :loc || '%' "
            "   OR EXISTS (SELECT 1 FROM unnest(coalesce(aliases, '{}')) a "
            "              WHERE :loc ILIKE '%' || a || '%') "
            "LIMIT 1"
        ),
        {"loc": location_text},
    ).first()
    return row[0] if row else None


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

    raw = sub["raw_text"] or ""
    if settings.gemini_api_key:
        data = _extract_with_gemini(raw, sub["media_url"])
    else:
        data = _extract_fallback(raw)

    if not data.get("is_civic_request", True):
        # noise (greeting/confirmation/spam): record the audit trail,
        # create no signal, spend no embedding call
        db.execute(
            text(
                "UPDATE submissions SET processed_at = now(), language = :lang, "
                "raw_text = COALESCE(raw_text, :transcript) WHERE id = :id"
            ),
            {"id": submission_id, "lang": data.get("language"),
             "transcript": data.get("transcript")},
        )
        db.commit()
        return {"rejected": True, **data}

    ward_code = _resolve_ward(db, data.get("location_text"))
    embedding = _embed(data["summary_en"]) if settings.gemini_api_key else None

    row = db.execute(
        text(
            "INSERT INTO demand_signals "
            "(submission_id, category, sub_type, location_text, ward_code, urgency, "
            " summary_en, embedding) "
            "VALUES (:sid, :category, :sub_type, :location_text, :ward, :urgency, "
            "        :summary_en, :emb) "
            "RETURNING id"
        ),
        {
            "sid": submission_id, "ward": ward_code,
            "emb": str(embedding) if embedding else None,
            **{k: data.get(k) for k in
               ("category", "sub_type", "location_text", "urgency", "summary_en")},
        },
    )
    signal_id = row.scalar_one()

    # voice/photo: persist the transcript so reprocessing never needs the media
    db.execute(
        text(
            "UPDATE submissions SET processed_at = now(), language = :lang, "
            "raw_text = COALESCE(raw_text, :transcript) WHERE id = :id"
        ),
        {"id": submission_id, "lang": data.get("language"),
         "transcript": data.get("transcript")},
    )
    db.commit()

    clustering.assign_to_demand(db, signal_id)
    return {"signal_id": signal_id, "ward_code": ward_code, **data}
