"""WhatsApp Business Cloud API integration."""

import structlog
import httpx
from typing import Optional

from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

WHATSAPP_API_BASE = f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}"


class WhatsAppClient:
    """Client for WhatsApp Business Cloud API."""

    def __init__(self):
        self.api_base = WHATSAPP_API_BASE
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID

    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def send_text_message(self, to: str, text: str) -> dict:
        """Send a text message via WhatsApp."""
        url = f"{self.api_base}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            logger.info("WhatsApp message sent", to=to, message_id=data.get("messages", [{}])[0].get("id"))
            return data

    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str = "en",
        components: Optional[list] = None,
    ) -> dict:
        """Send a template message (for initiating conversations)."""
        url = f"{self.api_base}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
            },
        }
        if components:
            payload["template"]["components"] = components

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def send_interactive_message(
        self,
        to: str,
        body_text: str,
        buttons: list[dict],
    ) -> dict:
        """Send an interactive button message."""
        url = f"{self.api_base}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body_text},
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {"id": btn["id"], "title": btn["title"][:20]}
                        }
                        for btn in buttons[:3]  # WhatsApp allows max 3 buttons
                    ]
                },
            },
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def mark_as_read(self, message_id: str) -> dict:
        """Mark a message as read."""
        url = f"{self.api_base}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self.headers)
            return response.json()

    def parse_webhook_message(self, body: dict) -> Optional[dict]:
        """Parse incoming WhatsApp webhook payload."""
        try:
            entry = body.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})

            if "messages" not in value:
                return None  # Status update, not a message

            message = value["messages"][0]
            contact = value.get("contacts", [{}])[0]

            parsed = {
                "message_id": message["id"],
                "from": message["from"],
                "timestamp": message["timestamp"],
                "type": message["type"],
                "contact_name": contact.get("profile", {}).get("name"),
                "phone_number_id": value.get("metadata", {}).get("phone_number_id"),
            }

            if message["type"] == "text":
                parsed["content"] = message["text"]["body"]
            elif message["type"] == "interactive":
                interactive = message.get("interactive", {})
                if interactive.get("type") == "button_reply":
                    parsed["content"] = interactive["button_reply"]["title"]
                    parsed["button_id"] = interactive["button_reply"]["id"]
                elif interactive.get("type") == "list_reply":
                    parsed["content"] = interactive["list_reply"]["title"]
            elif message["type"] in ("image", "document", "audio", "video"):
                media = message.get(message["type"], {})
                parsed["media_id"] = media.get("id")
                parsed["media_mime"] = media.get("mime_type")
                parsed["content"] = media.get("caption", f"[{message['type']}]")
            else:
                parsed["content"] = f"[Unsupported message type: {message['type']}]"

            return parsed

        except (IndexError, KeyError) as e:
            logger.error("Failed to parse WhatsApp webhook", error=str(e))
            return None


whatsapp_client = WhatsAppClient()
