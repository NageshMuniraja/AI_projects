from celery import Celery

from app.config import settings

celery_app = Celery(
    "autotube",
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
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=86400,  # 24 hours
    broker_connection_retry_on_startup=True,
)

from app.services.scheduler_service import BEAT_SCHEDULE
celery_app.conf.beat_schedule = BEAT_SCHEDULE

celery_app.autodiscover_tasks(["app.workers"])
