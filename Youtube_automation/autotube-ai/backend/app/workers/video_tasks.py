"""Celery tasks for video pipeline execution."""

import asyncio

from loguru import logger

from app.workers.celery_app import celery_app


def _run_async(coro):
    """Run an async coroutine from sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_pipeline_task(self, video_id: int, topic: str | None = None):
    """Run the full video pipeline for a single video."""
    from app.pipeline.video_pipeline import VideoPipeline

    logger.info(f"Celery task: run_pipeline for video {video_id}")

    try:
        pipeline = VideoPipeline()
        result = _run_async(pipeline.run_full_pipeline(video_id, topic))

        if not result.success:
            logger.error(f"Pipeline failed for video {video_id}: {result.error}")
            raise RuntimeError(result.error)

        logger.info(f"Pipeline completed for video {video_id}: {result.video_path}")
        return {
            "video_id": video_id,
            "success": True,
            "video_path": result.video_path,
            "thumbnail_path": result.thumbnail_path,
        }
    except Exception as exc:
        logger.error(f"Pipeline task error for video {video_id}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def resume_pipeline_task(self, video_id: int):
    """Resume a failed pipeline from the last successful step."""
    from app.pipeline.video_pipeline import VideoPipeline

    logger.info(f"Celery task: resume_pipeline for video {video_id}")

    try:
        pipeline = VideoPipeline()
        result = _run_async(pipeline.run_full_pipeline(video_id))

        if not result.success:
            raise RuntimeError(result.error)

        return {
            "video_id": video_id,
            "success": True,
            "video_path": result.video_path,
        }
    except Exception as exc:
        logger.error(f"Resume task error for video {video_id}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=1, default_retry_delay=60)
def run_kids_short_task(self, topic: str, channel_id: int | None = None):
    """Generate a standalone kids-focused YouTube Short."""
    from app.services.shorts_generator import ShortsGenerator

    logger.info(f"Celery task: kids_short for topic '{topic}'")

    try:
        generator = ShortsGenerator()
        result = generator.generate_kids_short(topic=topic, voice_id="nova")

        if not result:
            raise RuntimeError("Kids Short generation returned None")

        logger.info(
            f"Kids Short completed: {result.video_path} "
            f"({result.duration_seconds:.1f}s), cost=${result.cost_usd:.4f}"
        )

        # Upload if channel credentials available
        if channel_id:
            _run_async(_upload_kids_short(channel_id, result))

        return {
            "success": True,
            "video_path": result.video_path,
            "duration": result.duration_seconds,
            "cost": result.cost_usd,
        }
    except Exception as exc:
        logger.error(f"Kids Short task error: {exc}")
        raise self.retry(exc=exc)


async def _upload_kids_short(channel_id: int, result):
    """Upload kids Short to YouTube if channel has OAuth credentials."""
    from app.database import async_session_factory
    from app.models.channel import Channel

    async with async_session_factory() as db:
        channel = await db.get(Channel, channel_id)
        if channel and channel.oauth_credentials_encrypted:
            try:
                from app.services.youtube_uploader import YouTubeUploader
                uploader = YouTubeUploader(channel.oauth_credentials_encrypted)
                upload_result = uploader.upload_video(
                    video_path=result.video_path,
                    title=f"{result.hook_text} #shorts #kids #fun",
                    description="Amazing fun facts for kids! Like and subscribe for more!\n#shorts #kids #funfacts #amazing",
                    tags=["shorts", "kids", "fun facts", "amazing", "education", "children"],
                    category_id="22",
                    privacy_status="public",
                )
                logger.info(f"Kids Short uploaded: youtube.com/shorts/{upload_result.video_id}")
            except Exception as e:
                logger.warning(f"Kids Short upload failed: {e}")


@celery_app.task(bind=True, max_retries=1, default_retry_delay=120)
def run_batch_pipeline_task(self, channel_id: int, count: int = 5):
    """Run pipeline for multiple videos by dispatching individual tasks."""
    from app.database import async_session_factory
    from app.models.video import Video, VideoStatus

    async def _create_and_dispatch():
        async with async_session_factory() as db:
            video_ids = []
            for _ in range(count):
                video = Video(
                    channel_id=channel_id,
                    status=VideoStatus.QUEUED,
                    pipeline_step=0,
                )
                db.add(video)
                await db.flush()
                video_ids.append(video.id)
            await db.commit()
            return video_ids

    video_ids = _run_async(_create_and_dispatch())

    # Dispatch individual pipeline tasks
    for vid in video_ids:
        run_pipeline_task.delay(vid)

    logger.info(f"Batch pipeline: dispatched {len(video_ids)} tasks for channel {channel_id}")
    return {"channel_id": channel_id, "video_ids": video_ids}
