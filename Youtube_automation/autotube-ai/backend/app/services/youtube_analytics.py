"""YouTube Analytics Service — pulls performance data for published videos."""

from datetime import date, timedelta
from dataclasses import dataclass

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential

from app.database import async_session_factory
from app.models.analytics import VideoAnalytics
from app.models.channel import Channel
from app.models.video import Video, VideoStatus
from app.utils.youtube_auth import build_youtube_client


class YouTubeAnalyticsService:
    """Pull analytics from YouTube and store in the database."""

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=5, min=10, max=60))
    def pull_video_analytics(
        self,
        encrypted_credentials: str,
        youtube_video_id: str,
    ) -> dict:
        """Pull analytics for a single video from YouTube API."""
        youtube, _ = build_youtube_client(encrypted_credentials)

        response = youtube.videos().list(
            part="statistics,snippet",
            id=youtube_video_id,
        ).execute()

        items = response.get("items", [])
        if not items:
            return {}

        stats = items[0].get("statistics", {})
        return {
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "dislikes": int(stats.get("dislikeCount", 0)),
            "comments": int(stats.get("commentCount", 0)),
        }

    async def pull_channel_analytics(self, channel_id: int) -> int:
        """Pull analytics for all published videos in a channel. Returns count updated."""
        async with async_session_factory() as db:
            channel = await db.get(Channel, channel_id)
            if not channel or not channel.oauth_credentials_encrypted:
                logger.warning(f"Channel {channel_id}: no OAuth credentials")
                return 0

            result = await db.execute(
                select(Video)
                .where(Video.channel_id == channel_id)
                .where(Video.status == VideoStatus.PUBLISHED)
                .where(Video.youtube_video_id.is_not(None))
            )
            videos = result.scalars().all()

            updated = 0
            today = date.today()

            for video in videos:
                try:
                    stats = self.pull_video_analytics(
                        channel.oauth_credentials_encrypted,
                        video.youtube_video_id,
                    )
                    if not stats:
                        continue

                    # Check if today's entry exists
                    existing = await db.execute(
                        select(VideoAnalytics)
                        .where(VideoAnalytics.video_id == video.id)
                        .where(VideoAnalytics.date == today)
                    )
                    analytics = existing.scalar_one_or_none()

                    if analytics:
                        analytics.views = stats["views"]
                        analytics.likes = stats["likes"]
                        analytics.dislikes = stats["dislikes"]
                        analytics.comments = stats["comments"]
                    else:
                        analytics = VideoAnalytics(
                            video_id=video.id,
                            date=today,
                            views=stats["views"],
                            likes=stats["likes"],
                            dislikes=stats["dislikes"],
                            comments=stats["comments"],
                        )
                        db.add(analytics)

                    updated += 1
                except Exception as e:
                    logger.error(f"Failed to pull analytics for video {video.id}: {e}")
                    continue

            await db.commit()
            logger.info(f"Updated analytics for {updated}/{len(videos)} videos in channel {channel_id}")
            return updated

    async def pull_all_channels_analytics(self) -> dict:
        """Pull analytics for all active channels."""
        async with async_session_factory() as db:
            result = await db.execute(
                select(Channel).where(Channel.is_active.is_(True))
            )
            channels = result.scalars().all()

        total_updated = 0
        for channel in channels:
            count = await self.pull_channel_analytics(channel.id)
            total_updated += count

        return {"channels_processed": len(channels), "videos_updated": total_updated}
