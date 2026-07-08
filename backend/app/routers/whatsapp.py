"""F1 — WhatsApp intake via Twilio Sandbox webhook.

Twilio POSTs application/x-www-form-urlencoded on each inbound message:
From (whatsapp:+91...), Body, NumMedia, MediaUrl0, MediaContentType0,
MessageSid. We store a submission, run the pipeline synchronously (Gemini
~2-4s, well inside Twilio's 15s timeout) and reply with TwiML — no REST
client or outbound auth needed. Legacy Meta-handshake route kept for
compatibility.
"""
import hashlib

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import text as sql
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..services import clustering, structuring

router = APIRouter(tags=["whatsapp"])

CATEGORY_HI = {
    "road": "सड़क", "water": "पानी", "school": "स्कूल", "health": "स्वास्थ्य",
    "drainage": "नाली", "electricity": "बिजली", "other": "अन्य",
}


def _twiml(message: str) -> Response:
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<Response><Message>{message}</Message></Response>"
    )
    return Response(content=xml, media_type="application/xml")


ASK_LOCATION = (
    "यह किस इलाके/कॉलोनी की बात है? कृपया इलाके का नाम भेजें। "
    "(Which area/colony is this about? Please send the area name.)"
)
NOT_A_REQUEST = (
    "यह किसी समस्या या सुझाव जैसा नहीं लगा। कृपया अपनी समस्या बताएं — "
    "आवाज़, फोटो या लिखकर। (This didn't look like a civic complaint or "
    "suggestion — please describe your issue by voice, photo or text.)"
)


def _ward_name(db: Session, ward_code: str) -> str:
    row = db.execute(
        sql("SELECT name FROM wards WHERE ward_code = :w"), {"w": ward_code}
    ).first()
    return row[0] if row else ward_code


def _handle_clarification(db: Session, sender_hash: str, body: str) -> str | None:
    """If this sender owes us a location and sent a short text, treat it as
    the answer. Returns a reply, or None to fall through to normal intake."""
    if not body or len(body) > 60:
        return None
    pending = db.execute(
        sql(
            "SELECT s.id AS submission_id, ds.id AS signal_id "
            "FROM submissions s JOIN demand_signals ds ON ds.submission_id = s.id "
            "WHERE s.sender_hash = :sh AND s.pending_clarification = 'location' "
            "AND s.received_at > now() - interval '24 hours' "
            "ORDER BY s.id DESC LIMIT 1"
        ),
        {"sh": sender_hash},
    ).mappings().first()
    if not pending:
        return None

    # one shot: clear the flag either way so we never loop
    db.execute(
        sql("UPDATE submissions SET pending_clarification = NULL WHERE id = :id"),
        {"id": pending["submission_id"]},
    )
    ward = structuring._resolve_ward(db, body)
    if not ward:
        db.commit()
        return None  # not a recognizable area — treat message as new intake

    db.execute(
        sql(
            "UPDATE demand_signals SET ward_code = :w, location_text = :loc "
            "WHERE id = :id"
        ),
        {"w": ward, "loc": body, "id": pending["signal_id"]},
    )
    db.commit()
    clustering.reassign(db, pending["signal_id"])
    return (
        f"✓ स्थान दर्ज / Location noted: {_ward_name(db, ward)}. "
        f"संदर्भ / Ref #S{pending['submission_id']}."
    )


@router.post("/whatsapp/webhook")
async def receive(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    sid = form.get("MessageSid", "")
    sender = form.get("From", "")
    body = (form.get("Body") or "").strip()
    num_media = int(form.get("NumMedia") or 0)
    media_url = form.get("MediaUrl0") if num_media else None
    media_type = (form.get("MediaContentType0") or "") if num_media else ""

    if not sid:
        return _twiml("sunwai: unrecognized request")

    # Twilio retries on non-200 — dedupe by MessageSid
    dup = db.execute(
        sql("SELECT id FROM submissions WHERE wa_sid = :sid"), {"sid": sid}
    ).first()
    if dup:
        return _twiml("✓ पहले से दर्ज / already recorded")

    sender_hash = hashlib.sha256(sender.encode()).hexdigest()[:16]

    if not media_url:
        clarified = _handle_clarification(db, sender_hash, body)
        if clarified:
            return _twiml(clarified)

    kind = "text"
    if media_type.startswith("audio"):
        kind = "voice"
    elif media_type.startswith("image"):
        kind = "image"

    submission_id = db.execute(
        sql(
            "INSERT INTO submissions (channel, sender_hash, kind, raw_text, "
            "media_url, wa_sid) VALUES ('whatsapp', :sh, :kind, :body, :murl, :sid) "
            "RETURNING id"
        ),
        {"sh": sender_hash, "kind": kind, "body": body or None,
         "murl": media_url, "sid": sid},
    ).scalar_one()
    db.commit()

    try:
        signal = structuring.process_submission(db, submission_id)
        if signal.get("rejected"):
            return _twiml(NOT_A_REQUEST)
        cat = signal.get("category", "other")
        confirmation = (
            f"✓ दर्ज हुआ / Recorded — {CATEGORY_HI.get(cat, cat)} ({cat}). "
            f"संदर्भ / Ref #S{submission_id}."
        )
        if signal.get("ward_code"):
            reply = (
                f"{confirmation} स्थान: {_ward_name(db, signal['ward_code'])}. "
                "आपकी बात सांसद कार्यालय तक पहुंचेगी।"
            )
        else:
            db.execute(
                sql("UPDATE submissions SET pending_clarification = 'location' WHERE id = :id"),
                {"id": submission_id},
            )
            db.commit()
            reply = f"{confirmation} {ASK_LOCATION}"
    except Exception as exc:
        print(f"[whatsapp] pipeline failed for {submission_id}: {exc.__class__.__name__}: {exc}")
        reply = (
            f"✓ दर्ज हुआ / Recorded. संदर्भ / Ref #S{submission_id}. "
            "(processing queued)"
        )
    return _twiml(reply)


@router.get("/whatsapp/webhook")
def verify(
    mode: str = Query(default="", alias="hub.mode"),
    token: str = Query(default="", alias="hub.verify_token"),
    challenge: str = Query(default="", alias="hub.challenge"),
):
    """Legacy Meta webhook verification handshake (unused on Twilio)."""
    if mode == "subscribe" and token == settings.whatsapp_verify_token and token:
        return Response(content=challenge, media_type="text/plain")
    return Response(status_code=403)
