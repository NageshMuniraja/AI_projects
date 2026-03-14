"""Conversation service — handles message flow, AI responses, and context management."""

import uuid
from datetime import datetime, timezone
from typing import Optional

import structlog
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import (
    Conversation, Message, Contact, Tenant, Service,
    Appointment, Lead, AnalyticsEvent
)
from app.ai_engine.claude_client import claude_client
from app.ai_engine.rag import rag_pipeline

logger = structlog.get_logger()


class ConversationService:
    """Manages conversations, messages, and AI response generation."""

    async def get_or_create_conversation(
        self,
        db: AsyncSession,
        tenant_id: str,
        channel: str,
        contact_id: Optional[str] = None,
        contact_phone: Optional[str] = None,
        contact_name: Optional[str] = None,
    ) -> tuple:
        """Find active conversation or create a new one."""
        # Find or create contact
        contact = None
        if contact_phone:
            result = await db.execute(
                select(Contact).where(
                    Contact.tenant_id == tenant_id,
                    Contact.phone == contact_phone,
                )
            )
            contact = result.scalar_one_or_none()

        if not contact and (contact_phone or contact_name):
            contact = Contact(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                phone=contact_phone,
                name=contact_name,
                channel=channel,
            )
            db.add(contact)
            await db.flush()

        # Find active conversation
        query = select(Conversation).where(
            Conversation.tenant_id == tenant_id,
            Conversation.channel == channel,
            Conversation.status == "active",
        )
        if contact:
            query = query.where(Conversation.contact_id == contact.id)

        result = await db.execute(query.order_by(Conversation.last_message_at.desc()))
        conversation = result.scalar_one_or_none()

        if not conversation:
            conversation = Conversation(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                contact_id=contact.id if contact else None,
                channel=channel,
                status="active",
                ai_enabled=True,
            )
            db.add(conversation)
            await db.flush()

        return conversation, contact

    async def process_message(
        self,
        db: AsyncSession,
        conversation_id: str,
        content: str,
        channel: str = "web",
    ) -> Message:
        """Process an incoming message and generate AI response."""
        # Get conversation with tenant
        result = await db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise ValueError("Conversation not found")

        # Get tenant config
        result = await db.execute(
            select(Tenant).where(Tenant.id == conversation.tenant_id)
        )
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise ValueError("Tenant not found")

        # Save user message
        user_message = Message(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            role="user",
            content=content,
            channel=channel,
        )
        db.add(user_message)

        # Update conversation timestamp
        conversation.last_message_at = datetime.now(timezone.utc)

        # Check message limits
        if tenant.monthly_messages_used >= tenant.monthly_message_limit:
            limit_msg = Message(
                id=uuid.uuid4(),
                conversation_id=conversation_id,
                role="assistant",
                content=tenant.fallback_message or "Please contact us directly for further assistance.",
                channel=channel,
            )
            db.add(limit_msg)
            await db.flush()
            return limit_msg

        # Build tenant config dict
        services_result = await db.execute(
            select(Service).where(
                Service.tenant_id == tenant.id,
                Service.is_active == True,
            )
        )
        services = services_result.scalars().all()

        tenant_config = {
            "business_name": tenant.business_name or tenant.name,
            "business_phone": tenant.business_phone,
            "business_email": tenant.business_email,
            "business_address": tenant.business_address,
            "business_hours": tenant.business_hours or {},
            "industry": tenant.industry,
            "ai_persona_name": tenant.ai_persona_name,
            "ai_tone": tenant.ai_tone,
            "ai_instructions": tenant.ai_instructions,
            "greeting_message": tenant.greeting_message,
            "fallback_message": tenant.fallback_message,
            "services": [
                {
                    "name": s.name,
                    "description": s.description,
                    "price": s.price,
                    "duration_minutes": s.duration_minutes,
                    "category": s.category,
                }
                for s in services
            ],
        }

        # RAG retrieval
        rag_chunks = await rag_pipeline.retrieve(
            db=db,
            tenant_id=str(tenant.id),
            query=content,
        )
        rag_context = rag_pipeline.format_rag_context(rag_chunks) if rag_chunks else None

        # Build message history
        message_history = [
            {"role": msg.role, "content": msg.content}
            for msg in conversation.messages[-20:]  # Last 20 messages for context
        ]
        message_history.append({"role": "user", "content": content})

        # Get contact info
        contact_info = None
        if conversation.contact_id:
            result = await db.execute(
                select(Contact).where(Contact.id == conversation.contact_id)
            )
            contact = result.scalar_one_or_none()
            if contact:
                contact_info = {
                    "name": contact.name,
                    "phone": contact.phone,
                    "email": contact.email,
                }

        # Generate AI response
        ai_response = await claude_client.generate_response(
            tenant=tenant_config,
            messages=message_history,
            channel=channel,
            rag_context=rag_context,
            contact_info=contact_info,
        )

        # Save AI response
        ai_message = Message(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            role="assistant",
            content=ai_response["content"],
            channel=channel,
            ai_model=ai_response.get("model"),
            tokens_used=ai_response.get("tokens_used"),
            tool_calls=ai_response.get("tool_calls"),
        )
        db.add(ai_message)

        # Update usage counter
        tenant.monthly_messages_used += 1

        # Process tool call results (appointments, leads)
        if ai_response.get("tool_calls"):
            for tool_call in ai_response["tool_calls"]:
                await self._process_tool_result(
                    db, tenant, conversation, tool_call, contact_info
                )

        # Analyze intent asynchronously
        intent_data = await claude_client.analyze_intent(content, tenant.industry)
        conversation.intent = intent_data.get("intent")
        conversation.sentiment = intent_data.get("sentiment")

        # Track analytics
        event = AnalyticsEvent(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            event_type="message_sent",
            channel=channel,
            event_data={
                "conversation_id": str(conversation_id),
                "intent": intent_data.get("intent"),
                "tokens": ai_response.get("tokens_used", 0),
            },
        )
        db.add(event)

        await db.flush()
        return ai_message

    async def _process_tool_result(
        self, db, tenant, conversation, tool_call, contact_info
    ):
        """Process tool call results — create appointments, leads, etc."""
        tool_name = tool_call["tool"]
        tool_input = tool_call["input"]

        if tool_name == "book_appointment":
            from dateutil.parser import parse as parse_date
            try:
                scheduled_at = parse_date(
                    f"{tool_input['preferred_date']} {tool_input['preferred_time']}"
                )
            except (ValueError, KeyError):
                scheduled_at = datetime.now(timezone.utc)

            appointment = Appointment(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                conversation_id=conversation.id,
                customer_name=tool_input.get("customer_name", ""),
                customer_phone=tool_input.get("customer_phone") or (
                    contact_info.get("phone") if contact_info else None
                ),
                scheduled_at=scheduled_at,
                notes=tool_input.get("notes"),
                status="pending",
            )
            db.add(appointment)

            # Track event
            event = AnalyticsEvent(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                event_type="appointment_booked",
                channel=conversation.channel,
                event_data={"appointment": tool_input},
            )
            db.add(event)

        elif tool_name == "capture_lead":
            lead = Lead(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                conversation_id=conversation.id,
                name=tool_input.get("name"),
                phone=tool_input.get("phone") or (
                    contact_info.get("phone") if contact_info else None
                ),
                email=tool_input.get("email"),
                interest=tool_input.get("interest"),
                notes=tool_input.get("notes"),
                source=conversation.channel,
                status="new",
            )
            db.add(lead)

            event = AnalyticsEvent(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                event_type="lead_captured",
                channel=conversation.channel,
                event_data={"lead": tool_input},
            )
            db.add(event)

        elif tool_name == "escalate_to_human":
            conversation.status = "escalated"

    async def get_conversations(
        self,
        db: AsyncSession,
        tenant_id: str,
        status: Optional[str] = None,
        channel: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list:
        """Get conversations for a tenant."""
        query = (
            select(Conversation)
            .where(Conversation.tenant_id == tenant_id)
            .order_by(Conversation.last_message_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if status:
            query = query.where(Conversation.status == status)
        if channel:
            query = query.where(Conversation.channel == channel)

        result = await db.execute(query)
        return result.scalars().all()

    async def get_conversation_with_messages(
        self, db: AsyncSession, conversation_id: str, tenant_id: str
    ) -> Optional[Conversation]:
        """Get a single conversation with all messages."""
        result = await db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(
                Conversation.id == conversation_id,
                Conversation.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()


# Singleton
conversation_service = ConversationService()
