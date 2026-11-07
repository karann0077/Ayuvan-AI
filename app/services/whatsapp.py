import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.db.models import Message
from app.schemas import NormalizedIncomingMessage

logger = logging.getLogger(__name__)


class WhatsAppSendError(RuntimeError):
    """Provider failure with diagnostic codes, without tokens or message content."""

    def __init__(self, status: int, code: int | None, subcode: int | None) -> None:
        self.details = {
            "provider": "whatsapp", "http_status": status,
            "code": code, "subcode": subcode,
            "reason": "access_token_expired" if code == 190 and subcode == 463 else "send_rejected",
        }
        super().__init__(f"WhatsApp send rejected: HTTP {status}, code {code}, subcode {subcode}")


def parse_meta_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return None


def normalize_incoming_message(message: dict[str, Any]) -> NormalizedIncomingMessage:
    message_type = message.get("type", "unsupported")
    base: dict[str, Any] = {
        "provider_message_id": message["id"],
        "sender": message["from"],
        "timestamp": parse_meta_timestamp(message.get("timestamp")),
        "message_type": message_type if message_type in {
            "text", "interactive", "image", "audio", "document", "video", "location"
        } else "unsupported",
    }
    if message_type == "text":
        base["content"] = message.get("text", {}).get("body")
    elif message_type == "interactive":
        interactive = message.get("interactive", {})
        kind = interactive.get("type")
        if kind == "nfm_reply":
            reply = interactive.get("nfm_reply", {})
            base["content"] = reply.get("body") or "WhatsApp Flow submission"
            base["metadata"] = {
                "reply_type": "flow",
                "response_json": reply.get("response_json"),
                "flow_token": reply.get("flow_token"),
            }
        else:
            reply = interactive.get("button_reply" if kind == "button_reply" else "list_reply", {})
            base["content"] = reply.get("title")
            base["metadata"] = {
                "reply_type": "button" if kind == "button_reply" else "list",
                "reply_id": reply.get("id"),
                "description": reply.get("description"),
            }
    elif message_type in {"image", "audio", "document", "video"}:
        media = message.get(message_type, {})
        base["media_id"] = media.get("id")
        base["metadata"] = {
            "mime_type": media.get("mime_type"),
            "filename": media.get("filename"),
            "caption": media.get("caption"),
        }
    elif message_type == "location":
        location = message.get("location", {})
        base["metadata"] = {
            "latitude": location.get("latitude"),
            "longitude": location.get("longitude"),
            "name": location.get("name"),
            "address": location.get("address"),
        }
    return NormalizedIncomingMessage(**base)


def iter_webhook_messages(payload: dict[str, Any]):
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                yield message


def iter_status_updates(payload: dict[str, Any]):
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for status in change.get("value", {}).get("statuses", []):
                yield status


class WhatsAppClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def configured(self) -> bool:
        return bool(self.settings.whatsapp_phone_number_id and self.settings.whatsapp_access_token)

    @property
    def endpoint(self) -> str:
        return (
            f"https://graph.facebook.com/{self.settings.graph_api_version}/"
            f"{self.settings.whatsapp_phone_number_id}/messages"
        )

    async def _send(self, to: str, payload: dict[str, Any]) -> str | None:
        if not self.configured:
            logger.warning("WhatsApp client not configured; outgoing message not sent")
            return None
        headers = {
            "Authorization": f"Bearer {self.settings.whatsapp_access_token.get_secret_value()}",
            "Content-Type": "application/json",
        }
        body = {"messaging_product": "whatsapp", "to": to, **payload}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(self.endpoint, headers=headers, json=body)
            if response.is_error:
                try:
                    error = response.json().get("error", {})
                except ValueError:
                    error = {}
                raise WhatsAppSendError(response.status_code, error.get("code"), error.get("error_subcode"))
            response.raise_for_status()
            response_body = response.json()
        messages = response_body.get("messages", [])
        return messages[0].get("id") if messages else None

    async def send_text(self, to: str, text: str) -> str | None:
        return await self._send(to, {"type": "text", "text": {"body": text}})

    async def send_buttons(self, to: str, text: str, options: list[tuple[str, str]]) -> str | None:
        if not 1 <= len(options) <= 3:
            raise ValueError("WhatsApp reply buttons require one to three options")
        buttons = [
            {"type": "reply", "reply": {"id": option_id, "title": title[:20]}}
            for option_id, title in options
        ]
        return await self._send(to, {
            "type": "interactive",
            "interactive": {"type": "button", "body": {"text": text}, "action": {"buttons": buttons}},
        })

    async def send_list(self, to: str, text: str, button_label: str, rows: list[tuple[str, str, str]]) -> str | None:
        if not 1 <= len(rows) <= 10:
            raise ValueError("WhatsApp list messages require one to ten rows")
        return await self._send(to, {
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {"text": text},
                "action": {"button": button_label[:20], "sections": [{"title": "Options", "rows": [
                    {"id": row_id, "title": title[:24], "description": description[:72]}
                    for row_id, title, description in rows
                ]}]},
            },
        })

    async def send_flow(self, to: str, text: str, flow_id: str, screen: str) -> str | None:
        """Open a pre-published Meta Flow; its UI and fields remain Meta-managed content."""
        return await self._send(to, {
            "type": "interactive",
            "interactive": {
                "type": "flow",
                "body": {"text": text},
                "action": {
                    "name": "flow",
                    "parameters": {
                        "flow_message_version": "3",
                        "flow_token": f"ayuvan-intake:{flow_id}",
                        "flow_id": flow_id,
                        "flow_cta": "Open intake",
                        "flow_action": "navigate",
                        "flow_action_payload": {"screen": screen, "data": {}},
                    },
                },
            },
        })


def save_outgoing_message(
    db: Any, patient_id: str, conversation_id: str, provider_message_id: str | None,
    content: str, message_type: str, metadata: dict[str, Any] | None = None,
) -> Message:
    message = Message(
        patient_id=patient_id,
        conversation_id=conversation_id,
        provider="whatsapp",
        provider_message_id=provider_message_id or f"unsent:{datetime.now(tz=timezone.utc).timestamp()}",
        direction="outgoing",
        message_type=message_type,
        content=content,
        processing_status="sent" if provider_message_id else "failed",
        metadata_json=metadata or {},
    )
    db.add(message)
    return message
