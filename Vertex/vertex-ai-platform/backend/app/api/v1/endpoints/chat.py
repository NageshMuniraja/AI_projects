"""Public chat endpoints for the embeddable widget — no auth required."""

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.models import Tenant, Conversation
from app.services.conversation_service import conversation_service
from app.schemas.schemas import MessageRequest, MessageResponse

router = APIRouter(prefix="/chat", tags=["Public Chat"])


@router.post("/widget/{tenant_slug}/start")
async def start_chat(tenant_slug: str, visitor_name: Optional[str] = None):
    """Start a new chat session from the website widget."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Tenant).where(Tenant.slug == tenant_slug, Tenant.status == "active")
        )
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(status_code=404, detail="Business not found")

        conversation, contact = await conversation_service.get_or_create_conversation(
            db=db,
            tenant_id=str(tenant.id),
            channel="web",
            contact_name=visitor_name,
        )

        await db.commit()

        return {
            "conversation_id": str(conversation.id),
            "greeting": tenant.greeting_message or f"Hi! I'm {tenant.ai_persona_name}. How can I help you today?",
            "business_name": tenant.business_name,
            "ai_name": tenant.ai_persona_name,
            "primary_color": tenant.primary_color,
        }


@router.post("/widget/{tenant_slug}/message", response_model=MessageResponse)
async def send_widget_message(
    tenant_slug: str,
    request: MessageRequest,
    conversation_id: str = Query(...),
):
    """Send a message from the website widget."""
    async with AsyncSessionLocal() as db:
        # Verify tenant
        result = await db.execute(
            select(Tenant).where(Tenant.slug == tenant_slug, Tenant.status == "active")
        )
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(status_code=404, detail="Business not found")

        # Verify conversation belongs to tenant
        conv_result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.tenant_id == tenant.id,
            )
        )
        if not conv_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Process message
        ai_message = await conversation_service.process_message(
            db=db,
            conversation_id=conversation_id,
            content=request.content,
            channel="web",
        )

        await db.commit()
        return ai_message
