import json
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import verify_meta_signature
from app.db.models import Message
from app.db.session import get_db
from app.services.conversation import ConversationService
from app.services.whatsapp import iter_status_updates, iter_webhook_messages, normalize_incoming_message
from app.tasks import dispatch_incoming_message

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/webhooks/whatsapp", tags=["whatsapp"])
async def verify_whatsapp_webhook(request: Request, settings: Settings = Depends(get_settings)) -> Response:
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    expected = settings.webhook_verify_token.get_secret_value() if settings.webhook_verify_token else None
    if mode == "subscribe" and expected and token == expected and challenge:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Webhook verification failed")


@router.post("/webhooks/whatsapp", status_code=status.HTTP_200_OK, tags=["whatsapp"])
async def receive_whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    app_secret = settings.meta_app_secret.get_secret_value() if settings.meta_app_secret else None
    if not verify_meta_signature(raw_body, signature, app_secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON") from exc

    service = ConversationService(settings)
    queued = 0
    for raw_message in iter_webhook_messages(payload):
        try:
            incoming = normalize_incoming_message(raw_message)
            message_id = service.receive(db, incoming)
            if message_id:
                background_tasks.add_task(dispatch_incoming_message, message_id)
                queued += 1
        except (KeyError, ValueError):
            logger.warning("Ignored malformed incoming WhatsApp message")
    for status_update in iter_status_updates(payload):
        provider_id = status_update.get("id")
        delivery_status = status_update.get("status")
        if provider_id and delivery_status:
            outgoing = db.scalar(select(Message).where(
                Message.provider == "whatsapp", Message.provider_message_id == provider_id,
                Message.direction == "outgoing",
            ))
            if outgoing:
                outgoing.metadata_json = {**(outgoing.metadata_json or {}), "delivery_status": delivery_status}
                db.commit()
    return {"status": "accepted", "queued": str(queued)}
