"""Celery tasks for analytics, trend research, content calendar, and cleanup."""

import asyncio

from loguru import logger

from app.workers.celery_app import celery_app


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def pull_channel_analytics_task(self, channel_id: int):
    """Pull analytics for all videos in a channel."""
    from app.services.youtube_analytics import YouTubeAnalyticsService

    try:
        service = YouTubeAnalyticsService()
        count = _run_async(service.pull_channel_analytics(channel_id))
        logger.info(f"Analytics task: updated {count} videos for channel {channel_id}")
        return {"channel_id": channel_id, "videos_updated": count}
    except Exception as exc:
        logger.error(f"Analytics task failed for channel {channel_id}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def pull_all_analytics_task(self):
    """Pull analytics for all active channels."""
    from app.services.youtube_analytics import YouTubeAnalyticsService

    try:
        service = YouTubeAnalyticsService()
        result = _run_async(service.pull_all_channels_analytics())
        logger.info(f"All analytics task: {result}")
        return result
    except Exception as exc:
        logger.error(f"All analytics task failed: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def daily_trend_research_task(self):
    """Research trending topics for all active channels."""
    from app.database import async_session_factory
    from app.models.channel import Channel
    from app.services.trend_researcher import TrendResearcher
    from sqlalchemy import select

    async def _research():
        researcher = TrendResearcher()
        async with async_session_factory() as db:
            result = await db.execute(
                select(Channel).where(Channel.is_active.is_(True))
            )
            channels = result.scalars().all()

        results = {}
        for channel in channels:
            topics = researcher.get_trending_topics(channel.niche, count=10)
            results[channel.id] = [t.title for t in topics]
            logger.info(f"Trend research for channel {channel.id} ({channel.niche}): "
                        f"{len(topics)} topics found")

        return results

    try:
        return _run_async(_research())
    except Exception as exc:
        logger.error(f"Daily trend research failed: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=1, default_retry_delay=600)
def weekly_content_calendar_task(self):
    """Generate weekly content calendars for all active channels."""
    from app.database import async_session_factory
    from app.models.channel import Channel
    from app.services.content_strategy import ContentStrategy
    from sqlalchemy import select

    async def _generate():
        strategy = ContentStrategy()
        async with async_session_factory() as db:
            result = await db.execute(
                select(Channel).where(Channel.is_active.is_(True))
            )
            channels = result.scalars().all()

        total_entries = 0
        for channel in channels:
            entries = await strategy.generate_content_calendar(channel.id, weeks=1)
            total_entries += len(entries)
            logger.info(f"Content calendar for channel {channel.id}: {len(entries)} entries")

        return {"channels": len(channels), "total_entries": total_entries}

    try:
        return _run_async(_generate())
    except Exception as exc:
        logger.error(f"Weekly content calendar failed: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=1, default_retry_delay=60)
def weekly_cleanup_task(self):
    """Clean up old temp files and expired media."""
    from app.utils.file_manager import cleanup_old_videos, cleanup_temp_files

    try:
        temp_deleted = cleanup_temp_files(max_age_hours=24)
        videos_deleted = cleanup_old_videos(max_age_days=30)
        result = {
            "temp_files_deleted": temp_deleted,
            "old_videos_deleted": videos_deleted,
        }
        logger.info(f"Weekly cleanup: {result}")
        return result
    except Exception as exc:
        logger.error(f"Weekly cleanup failed: {exc}")
        raise self.retry(exc=exc)
