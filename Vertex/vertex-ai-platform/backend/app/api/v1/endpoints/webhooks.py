"""Webhook endpoints for WhatsApp and other channels."""

from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.channels.whatsapp import whatsapp_client
from app.services.conversation_service import conversation_service

settings = get_settings()
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.get("/whatsapp")
async def verify_whatsapp_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """WhatsApp webhook verification (GET)."""
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        return PlainTextResponse(content=hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp")
async def handle_whatsapp_webhook(request: Request):
    """Handle incoming WhatsApp messages."""
    body = await request.json()

    # Parse the incoming message
    parsed = whatsapp_client.parse_webhook_message(body)
    if not parsed:
        return {"status": "ok"}  # Status update, not a message

    # Mark as read
    await whatsapp_client.mark_as_read(parsed["message_id"])

    # Process the message
    async with AsyncSessionLocal() as db:
        try:
            # Find or create conversation
            # In production, map phone_number_id to tenant_id via a lookup table
            conversation, contact = await conversation_service.get_or_create_conversation(
                db=db,
                tenant_id=settings.WHATSAPP_PHONE_NUMBER_ID,  # Would be mapped to tenant
                channel="whatsapp",
                contact_phone=parsed["from"],
                contact_name=parsed.get("contact_name"),
            )

            # Process message and get AI response
            ai_message = await conversation_service.process_message(
                db=db,
                conversation_id=str(conversation.id),
                content=parsed["content"],
                channel="whatsapp",
            )

            # Send AI response via WhatsApp
            await whatsapp_client.send_text_message(
                to=parsed["from"],
                text=ai_message.content,
            )

            await db.commit()
        except Exception as e:
            await db.rollback()
            raise

    return {"status": "ok"}
