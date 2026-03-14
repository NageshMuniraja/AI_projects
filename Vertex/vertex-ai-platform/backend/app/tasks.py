"""Celery tasks for background processing."""

from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "vertex",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    beat_schedule={
        "reset-monthly-usage": {
            "task": "app.tasks.reset_monthly_usage",
            "schedule": 86400.0,  # Daily check
        },
        "send-appointment-reminders": {
            "task": "app.tasks.send_appointment_reminders",
            "schedule": 3600.0,  # Hourly
        },
    },
)


@celery_app.task
def reset_monthly_usage():
    """Reset monthly message counters on the 1st of each month."""
    import asyncio
    from datetime import datetime, timezone
    from sqlalchemy import update
    from app.core.database import AsyncSessionLocal
    from app.models.models import Tenant

    now = datetime.now(timezone.utc)
    if now.day != 1:
        return "Not the first of the month"

    async def _reset():
        async with AsyncSessionLocal() as db:
            await db.execute(
                update(Tenant).values(monthly_messages_used=0)
            )
            await db.commit()

    asyncio.run(_reset())
    return "Monthly usage reset"


@celery_app.task
def send_appointment_reminders():
    """Send reminders for upcoming appointments."""
    import asyncio
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.models import Appointment, Tenant
    from app.channels.whatsapp import whatsapp_client

    async def _send_reminders():
        now = datetime.now(timezone.utc)
        reminder_window = now + timedelta(hours=24)

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Appointment).where(
                    Appointment.scheduled_at.between(now, reminder_window),
                    Appointment.reminder_sent == False,
                    Appointment.status.in_(["pending", "confirmed"]),
                )
            )
            appointments = result.scalars().all()

            for appt in appointments:
                if appt.customer_phone:
                    try:
                        await whatsapp_client.send_text_message(
                            to=appt.customer_phone,
                            text=f"Reminder: You have an appointment tomorrow at {appt.scheduled_at.strftime('%I:%M %p')}. "
                                 f"Please confirm or let us know if you need to reschedule.",
                        )
                        appt.reminder_sent = True
                    except Exception:
                        pass

            await db.commit()

    asyncio.run(_send_reminders())
    return "Reminders sent"
