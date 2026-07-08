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
from ..services import structuring

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

    kind = "text"
    if media_type.startswith("audio"):
        kind = "voice"
    elif media_type.startswith("image"):
        kind = "image"

    sender_hash = hashlib.sha256(sender.encode()).hexdigest()[:16]
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
        cat = signal.get("category", "other")
        reply = (
            f"✓ दर्ज हुआ / Recorded — {CATEGORY_HI.get(cat, cat)} ({cat}). "
            f"संदर्भ / Ref #S{submission_id}. "
            "आपकी बात सांसद कार्यालय तक पहुंचेगी।"
        )
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
