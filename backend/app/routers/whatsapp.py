"""WhatsApp Cloud API webhook (F1). Wired last — see docs/F1-whatsapp-intake.md."""
from fastapi import APIRouter, Query, Request, Response

from ..config import settings

router = APIRouter(tags=["whatsapp"])


@router.get("/whatsapp/webhook")
def verify(
    mode: str = Query(default="", alias="hub.mode"),
    token: str = Query(default="", alias="hub.verify_token"),
    challenge: str = Query(default="", alias="hub.challenge"),
):
    """Meta webhook verification handshake."""
    if mode == "subscribe" and token == settings.whatsapp_verify_token and token:
        return Response(content=challenge, media_type="text/plain")
    return Response(status_code=403)


@router.post("/whatsapp/webhook")
async def receive(request: Request):
    """Receive message events. TODO(F1): download media, insert submission,
    call structuring.process_submission, reply via Cloud API in sender language."""
    _payload = await request.json()
    return {"status": "received"}
