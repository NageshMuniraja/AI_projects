"""YouTube Analytics Service — pulls full performance data for published videos."""

from datetime import date, timedelta
from dataclasses import dataclass
from decimal import Decimal

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
    """Pull comprehensive analytics from YouTube and store in the database."""

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=5, min=10, max=60))
    def pull_video_analytics(
        self,
        encrypted_credentials: str,
        youtube_video_id: str,
    ) -> dict:
        """Pull full analytics for a single video from YouTube API."""
        youtube, credentials = build_youtube_client(encrypted_credentials)

        # Basic statistics from YouTube Data API
        response = youtube.videos().list(
            part="statistics,snippet",
            id=youtube_video_id,
        ).execute()

        items = response.get("items", [])
        if not items:
            return {}

        stats = items[0].get("statistics", {})
        result = {
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "dislikes": int(stats.get("dislikeCount", 0)),
            "comments": int(stats.get("commentCount", 0)),
        }

        # Try to get extended analytics from YouTube Analytics API
        try:
            extended = self._pull_extended_analytics(
                credentials, youtube_video_id
            )
            result.update(extended)
        except Exception as e:
            logger.debug(f"Extended analytics unavailable for {youtube_video_id}: {e}")

        return result

    def _pull_extended_analytics(
        self, credentials, youtube_video_id: str
    ) -> dict:
        """Pull extended metrics from YouTube Analytics API."""
        from googleapiclient.discovery import build

        analytics = build("youtubeAnalytics", "v2", credentials=credentials)

        today = date.today()
        start_date = (today - timedelta(days=7)).isoformat()
        end_date = today.isoformat()

        response = analytics.reports().query(
            ids="channel==MINE",
            startDate=start_date,
            endDate=end_date,
            metrics=(
                "estimatedMinutesWatched,averageViewDuration,"
                "averageViewPercentage,annotationClickThroughRate,"
                "subscribersGained,shares,estimatedRevenue,"
                "impressions,impressionClickThroughRate"
            ),
            filters=f"video=={youtube_video_id}",
        ).execute()

        rows = response.get("rows", [])
        if not rows:
            return {}

        row = rows[0]
        return {
            "watch_time_hours": round(float(row[0]) / 60, 2),  # minutes → hours
            "avg_view_duration": float(row[1]),
            "avg_view_percentage": float(row[2]),
            "ctr": float(row[4]) if len(row) > 4 else 0,
            "subscribers_gained": int(row[5]) if len(row) > 5 else 0,
            "shares": int(row[6]) if len(row) > 6 else 0,
            "estimated_revenue": float(row[7]) if len(row) > 7 else 0,
            "impressions": int(row[8]) if len(row) > 8 else 0,
        }

    def _pull_traffic_sources(
        self, credentials, youtube_video_id: str
    ) -> dict:
        """Pull traffic source breakdown from YouTube Analytics API."""
        from googleapiclient.discovery import build

        analytics = build("youtubeAnalytics", "v2", credentials=credentials)

        today = date.today()
        start_date = (today - timedelta(days=28)).isoformat()
        end_date = today.isoformat()

        try:
            response = analytics.reports().query(
                ids="channel==MINE",
                startDate=start_date,
                endDate=end_date,
                metrics="views",
                dimensions="insightTrafficSourceType",
                filters=f"video=={youtube_video_id}",
                sort="-views",
            ).execute()

            sources = {}
            for row in response.get("rows", []):
                sources[row[0]] = int(row[1])
            return sources
        except Exception as e:
            logger.debug(f"Traffic sources unavailable: {e}")
            return {}

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
                        analytics.shares = stats.get("shares", 0)
                        analytics.watch_time_hours = Decimal(str(stats.get("watch_time_hours", 0)))
                        analytics.avg_view_duration = Decimal(str(stats.get("avg_view_duration", 0)))
                        analytics.avg_view_percentage = Decimal(str(stats.get("avg_view_percentage", 0)))
                        analytics.ctr = Decimal(str(stats.get("ctr", 0)))
                        analytics.impressions = stats.get("impressions", 0)
                        analytics.subscribers_gained = stats.get("subscribers_gained", 0)
                        analytics.estimated_revenue = Decimal(str(stats.get("estimated_revenue", 0)))
                    else:
                        analytics = VideoAnalytics(
                            video_id=video.id,
                            date=today,
                            views=stats["views"],
                            likes=stats["likes"],
                            dislikes=stats["dislikes"],
                            comments=stats["comments"],
                            shares=stats.get("shares", 0),
                            watch_time_hours=Decimal(str(stats.get("watch_time_hours", 0))),
                            avg_view_duration=Decimal(str(stats.get("avg_view_duration", 0))),
                            avg_view_percentage=Decimal(str(stats.get("avg_view_percentage", 0))),
                            ctr=Decimal(str(stats.get("ctr", 0))),
                            impressions=stats.get("impressions", 0),
                            subscribers_gained=stats.get("subscribers_gained", 0),
                            estimated_revenue=Decimal(str(stats.get("estimated_revenue", 0))),
                        )
                        db.add(analytics)

                    # Try to pull traffic sources
                    try:
                        from app.utils.youtube_auth import build_youtube_client
                        _, credentials = build_youtube_client(channel.oauth_credentials_encrypted)
                        traffic = self._pull_traffic_sources(credentials, video.youtube_video_id)
                        if traffic:
                            analytics.traffic_sources = traffic
                    except Exception:
                        pass

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
