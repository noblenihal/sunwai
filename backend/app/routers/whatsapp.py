"""F1 — WhatsApp intake via Twilio Sandbox webhook.

Twilio POSTs form-encoded fields per inbound message (From, Body, NumMedia,
MediaUrl0, MediaContentType0, MessageSid). We store a submission, run the
pipeline synchronously and reply with TwiML — formatted for WhatsApp
(*bold*, line breaks) in the citizen's own language.

Clarification loop: while a "which area?" question is pending, a short text
OR a short voice note from the same sender is treated as the answer.
"""
import hashlib
from xml.sax.saxutils import escape

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

L10N = {
    "en": {
        "recorded": "✅ *Recorded* — {cat}\n📌 Ref: #S{id}",
        "reach": "Your voice will reach the MP's office.",
        "ask_loc": "📍 Which area/colony is this about?\nPlease send the area name (text or voice).",
        "loc_noted": "✅ *Location noted:* {ward}\n📌 Ref: #S{id}",
        "not_req": "This didn't look like a civic complaint or suggestion.\nPlease describe your issue — by voice, photo or text.",
    },
    "hi": {
        "recorded": "✅ *दर्ज हुआ* — {cat}\n📌 संदर्भ: #S{id}",
        "reach": "आपकी बात सांसद कार्यालय तक पहुंचेगी।",
        "ask_loc": "📍 यह किस इलाके/कॉलोनी की बात है?\nइलाके का नाम भेजें (लिखकर या बोलकर)।",
        "loc_noted": "✅ *स्थान दर्ज:* {ward}\n📌 संदर्भ: #S{id}",
        "not_req": "यह किसी समस्या या सुझाव जैसा नहीं लगा।\nकृपया अपनी समस्या बताएं — आवाज़, फोटो या लिखकर।",
    },
    "bn": {
        "recorded": "✅ *নথিভুক্ত হয়েছে* — {cat}\n📌 রেফারেন্স: #S{id}",
        "reach": "আপনার কথা সাংসদের অফিসে পৌঁছাবে।",
        "ask_loc": "📍 এটি কোন এলাকার সমস্যা?\nএলাকার নাম পাঠান (লিখে বা বলে)।",
        "loc_noted": "✅ *এলাকা নথিভুক্ত:* {ward}\n📌 রেফারেন্স: #S{id}",
        "not_req": "এটি কোনো সমস্যা বা পরামর্শ বলে মনে হয়নি।\nদয়া করে আপনার সমস্যা জানান — ভয়েস, ছবি বা লিখে।",
    },
    "gu": {
        "recorded": "✅ *નોંધાયું* — {cat}\n📌 સંદર્ભ: #S{id}",
        "reach": "તમારી વાત સાંસદની ઑફિસ સુધી પહોંચશે.",
        "ask_loc": "📍 આ કયા વિસ્તાર/કૉલોનીની વાત છે?\nવિસ્તારનું નામ મોકલો (લખીને કે બોલીને).",
        "loc_noted": "✅ *સ્થળ નોંધાયું:* {ward}\n📌 સંદર્ભ: #S{id}",
        "not_req": "આ કોઈ સમસ્યા કે સૂચન જેવું લાગ્યું નહીં.\nકૃપા કરીને તમારી સમસ્યા જણાવો — અવાજ, ફોટો કે લખીને.",
    },
    "mr": {
        "recorded": "✅ *नोंदवले* — {cat}\n📌 संदर्भ: #S{id}",
        "reach": "तुमचे म्हणणे खासदार कार्यालयापर्यंत पोहोचेल.",
        "ask_loc": "📍 हे कोणत्या भागाबद्दल आहे?\nभागाचे/कॉलनीचे नाव पाठवा (लिहून किंवा बोलून).",
        "loc_noted": "✅ *ठिकाण नोंदवले:* {ward}\n📌 संदर्भ: #S{id}",
        "not_req": "हे समस्येसारखे किंवा सूचनेसारखे वाटले नाही.\nकृपया तुमची समस्या सांगा — आवाज, फोटो किंवा लिहून.",
    },
    "ta": {
        "recorded": "✅ *பதிவு செய்யப்பட்டது* — {cat}\n📌 குறிப்பு: #S{id}",
        "reach": "உங்கள் குரல் எம்.பி. அலுவலகத்தை சென்றடையும்.",
        "ask_loc": "📍 இது எந்த பகுதி/காலனி பற்றியது?\nபகுதியின் பெயரை அனுப்பவும் (எழுத்து அல்லது குரல்).",
        "loc_noted": "✅ *இடம் பதிவானது:* {ward}\n📌 குறிப்பு: #S{id}",
        "not_req": "இது புகார் அல்லது பரிந்துரையாகத் தெரியவில்லை.\nஉங்கள் பிரச்சனையை கூறவும் — குரல், புகைப்படம் அல்லது எழுத்தில்.",
    },
}

_LANG_KEYS = {"hindi": "hi", "bengali": "bn", "bangla": "bn", "gujarati": "gu",
              "marathi": "mr", "tamil": "ta"}


def _lang(code_or_name: str | None) -> str:
    s = (code_or_name or "").lower()
    if s[:2] in L10N:
        return s[:2]
    for name, code in _LANG_KEYS.items():
        if name in s:
            return code
    return "en"


def _t(lang: str, key: str, **kw) -> str:
    return L10N.get(lang, L10N["en"])[key].format(**kw)


def _compose(lang: str, local_parts: list[str], en_parts: list[str]) -> str:
    """Local language leads; English follows as one italic line (skipped when
    the local language IS English)."""
    local = "\n\n".join(p for p in local_parts if p)
    if lang == "en":
        return local
    en = " ".join(p.replace("\n", " ").replace("*", "") for p in en_parts if p)
    return f"{local}\n\n_{en}_"


def _cat_label(lang: str, cat: str) -> str:
    if lang == "hi":
        return f"{CATEGORY_HI.get(cat, cat)} ({cat})"
    return cat


def _twiml(message: str) -> Response:
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<Response><Message>{escape(message)}</Message></Response>"
    )
    return Response(content=xml, media_type="application/xml")


def _ward_name(db: Session, ward_code: str) -> str:
    row = db.execute(
        sql("SELECT name FROM wards WHERE ward_code = :w"), {"w": ward_code}
    ).first()
    return row[0] if row else ward_code


def _handle_clarification(db: Session, sender_hash: str, body: str,
                          media_url: str | None, media_type: str) -> str | None:
    """If this sender owes us a location: short text OR a short voice note is
    treated as the answer. Returns a reply, or None to fall through."""
    pending = db.execute(
        sql(
            "SELECT s.id AS submission_id, s.language, ds.id AS signal_id "
            "FROM submissions s JOIN demand_signals ds ON ds.submission_id = s.id "
            "WHERE s.sender_hash = :sh AND s.pending_clarification = 'location' "
            "AND s.received_at > now() - interval '24 hours' "
            "ORDER BY s.id DESC LIMIT 1"
        ),
        {"sh": sender_hash},
    ).mappings().first()
    if not pending:
        return None

    answer = None
    if body and len(body) <= 60:
        answer = body
    elif media_url and media_type.startswith("audio") and settings.gemini_api_key:
        try:
            transcript = structuring.transcribe_short(media_url)
            if transcript and len(transcript) <= 80:
                answer = transcript
        except Exception as exc:
            print(f"[whatsapp] clarification transcribe failed: {exc.__class__.__name__}")
    if not answer:
        return None

    # one shot: clear the flag either way so we never loop
    db.execute(
        sql("UPDATE submissions SET pending_clarification = NULL WHERE id = :id"),
        {"id": pending["submission_id"]},
    )
    ward = structuring._resolve_ward(db, answer)
    if not ward:
        db.commit()
        return None  # not a recognizable area — treat message as new intake

    db.execute(
        sql(
            "UPDATE demand_signals SET ward_code = :w, location_text = :loc "
            "WHERE id = :id"
        ),
        {"w": ward, "loc": answer, "id": pending["signal_id"]},
    )
    db.commit()
    clustering.reassign(db, pending["signal_id"])
    lang = _lang(pending["language"])
    kw = {"ward": _ward_name(db, ward), "id": pending["submission_id"]}
    return _compose(lang, [_t(lang, "loc_noted", **kw)], [_t("en", "loc_noted", **kw)])


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
        return _twiml("✅")

    sender_hash = hashlib.sha256(sender.encode()).hexdigest()[:16]

    clarified = _handle_clarification(db, sender_hash, body, media_url, media_type)
    if clarified:
        db.execute(
            sql("INSERT INTO submissions (channel, sender_hash, kind, raw_text, wa_sid, processed_at) "
                "VALUES ('whatsapp', :sh, 'clarification', :body, :sid, now())"),
            {"sh": sender_hash, "body": body or "(voice answer)", "sid": sid},
        )
        db.commit()
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
        lang = _lang(signal.get("language"))
        if signal.get("rejected"):
            return _twiml(_compose(lang, [_t(lang, "not_req")], [_t("en", "not_req")]))
        kw = {"cat": _cat_label(lang, signal.get("category", "other")), "id": submission_id}
        en_kw = {"cat": signal.get("category", "other"), "id": submission_id}
        recorded = _t(lang, "recorded", **kw)
        if signal.get("ward_code"):
            ward_line = f"📍 {_ward_name(db, signal['ward_code'])}"
            reply = _compose(
                lang,
                [recorded, ward_line, _t(lang, "reach")],
                [_t("en", "recorded", **en_kw), ward_line, _t("en", "reach")],
            )
        else:
            db.execute(
                sql("UPDATE submissions SET pending_clarification = 'location' WHERE id = :id"),
                {"id": submission_id},
            )
            db.commit()
            reply = _compose(
                lang,
                [recorded, _t(lang, "ask_loc")],
                [_t("en", "recorded", **en_kw), _t("en", "ask_loc")],
            )
    except Exception as exc:
        print(f"[whatsapp] pipeline failed for {submission_id}: {exc.__class__.__name__}: {exc}")
        reply = f"✅ Recorded — Ref #S{submission_id} (processing queued)"
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
