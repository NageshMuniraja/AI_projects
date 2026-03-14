"""Analytics service for dashboard metrics and reporting."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    Conversation, Message, Appointment, Lead, AnalyticsEvent
)


class AnalyticsService:
    """Generate analytics and metrics for tenant dashboards."""

    async def get_dashboard_summary(
        self,
        db: AsyncSession,
        tenant_id: str,
        days: int = 30,
    ) -> dict:
        """Get comprehensive dashboard analytics."""
        since = datetime.now(timezone.utc) - timedelta(days=days)

        # Total conversations
        total_convos = await db.execute(
            select(func.count(Conversation.id)).where(
                Conversation.tenant_id == tenant_id,
                Conversation.started_at >= since,
            )
        )
        total_conversations = total_convos.scalar() or 0

        # Active conversations
        active_convos = await db.execute(
            select(func.count(Conversation.id)).where(
                Conversation.tenant_id == tenant_id,
                Conversation.status == "active",
            )
        )
        active_conversations = active_convos.scalar() or 0

        # Total messages
        total_msgs = await db.execute(
            select(func.count(Message.id))
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(
                Conversation.tenant_id == tenant_id,
                Message.created_at >= since,
            )
        )
        total_messages = total_msgs.scalar() or 0

        # AI messages
        ai_msgs = await db.execute(
            select(func.count(Message.id))
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(
                Conversation.tenant_id == tenant_id,
                Message.role == "assistant",
                Message.created_at >= since,
            )
        )
        ai_messages = ai_msgs.scalar() or 0

        # Appointments
        appts = await db.execute(
            select(func.count(Appointment.id)).where(
                Appointment.tenant_id == tenant_id,
                Appointment.created_at >= since,
            )
        )
        appointments_booked = appts.scalar() or 0

        # Leads
        leads_count = await db.execute(
            select(func.count(Lead.id)).where(
                Lead.tenant_id == tenant_id,
                Lead.created_at >= since,
            )
        )
        leads_captured = leads_count.scalar() or 0

        # Top intents
        intent_query = await db.execute(
            select(
                Conversation.intent,
                func.count(Conversation.id).label("count")
            ).where(
                Conversation.tenant_id == tenant_id,
                Conversation.intent.isnot(None),
                Conversation.started_at >= since,
            ).group_by(Conversation.intent)
            .order_by(func.count(Conversation.id).desc())
            .limit(5)
        )
        top_intents = [
            {"intent": row.intent, "count": row.count}
            for row in intent_query.fetchall()
        ]

        # Messages by channel
        channel_query = await db.execute(
            select(
                Conversation.channel,
                func.count(Message.id).label("count")
            )
            .join(Message, Message.conversation_id == Conversation.id)
            .where(
                Conversation.tenant_id == tenant_id,
                Message.created_at >= since,
            )
            .group_by(Conversation.channel)
        )
        messages_by_channel = {
            row.channel: row.count for row in channel_query.fetchall()
        }

        # Messages by day (last 30 days)
        daily_query = await db.execute(
            text("""
                SELECT DATE(m.created_at) as day, COUNT(m.id) as count
                FROM messages m
                JOIN conversations c ON c.id = m.conversation_id
                WHERE c.tenant_id = :tenant_id
                AND m.created_at >= :since
                GROUP BY DATE(m.created_at)
                ORDER BY day
            """),
            {"tenant_id": tenant_id, "since": since}
        )
        messages_by_day = [
            {"date": str(row.day), "count": row.count}
            for row in daily_query.fetchall()
        ]

        return {
            "total_conversations": total_conversations,
            "active_conversations": active_conversations,
            "total_messages": total_messages,
            "ai_messages": ai_messages,
            "appointments_booked": appointments_booked,
            "leads_captured": leads_captured,
            "avg_response_time_seconds": None,
            "satisfaction_score": None,
            "top_intents": top_intents,
            "messages_by_channel": messages_by_channel,
            "messages_by_day": messages_by_day,
        }


analytics_service = AnalyticsService()
