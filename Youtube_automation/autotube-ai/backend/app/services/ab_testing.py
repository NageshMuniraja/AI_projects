"""A/B Testing Service — tests thumbnail variants for optimal CTR."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.analytics import VideoAnalytics
from app.models.channel import Channel
from app.models.video import Video, VideoStatus


class TestStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    NO_DATA = "no_data"


@dataclass
class ABTestResult:
    video_id: int
    status: TestStatus
    variant_a_ctr: float = 0.0
    variant_b_ctr: float = 0.0
    winner: str = ""  # "A" or "B"
    improvement_pct: float = 0.0
    current_thumbnail: str = ""


class ABTestingService:
    """Manages A/B testing of thumbnails for uploaded videos."""

    # Test parameters
    TEST_DURATION_HOURS = 48
    MIN_IMPRESSIONS = 100  # minimum impressions before declaring a winner

    async def should_swap_thumbnail(self, video_id: int) -> ABTestResult:
        """Check if a video's thumbnail should be swapped based on CTR performance."""
        async with async_session_factory() as db:
            video = await db.get(Video, video_id)
            if not video or not video.youtube_video_id:
                return ABTestResult(video_id=video_id, status=TestStatus.NO_DATA)

            # Get analytics over the test period
            result = await db.execute(
                select(VideoAnalytics)
                .where(VideoAnalytics.video_id == video_id)
                .order_by(VideoAnalytics.date.desc())
                .limit(7)
            )
            analytics_entries = result.scalars().all()

            if not analytics_entries:
                return ABTestResult(video_id=video_id, status=TestStatus.NO_DATA)

            # Calculate average CTR
            total_impressions = sum(a.impressions for a in analytics_entries)
            total_views = sum(a.views for a in analytics_entries)

            if total_impressions < self.MIN_IMPRESSIONS:
                return ABTestResult(
                    video_id=video_id,
                    status=TestStatus.RUNNING,
                    variant_a_ctr=float(analytics_entries[0].ctr) if analytics_entries else 0,
                )

            current_ctr = (total_views / total_impressions * 100) if total_impressions > 0 else 0

            # Get niche benchmark
            channel = await db.get(Channel, video.channel_id)
            niche = channel.niche.lower() if channel else "general"
            benchmark = self._get_niche_ctr_benchmark(niche)

            test_result = ABTestResult(
                video_id=video_id,
                status=TestStatus.COMPLETED,
                variant_a_ctr=current_ctr,
                current_thumbnail=video.thumbnail_path or "",
            )

            # If CTR is below benchmark, recommend swapping
            if current_ctr < benchmark * 0.85:
                test_result.winner = "B"
                test_result.improvement_pct = ((benchmark - current_ctr) / current_ctr * 100) if current_ctr > 0 else 0
                logger.info(
                    f"Video {video_id}: CTR {current_ctr:.1f}% below benchmark {benchmark:.1f}% — "
                    f"recommending thumbnail swap"
                )
            else:
                test_result.winner = "A"
                logger.info(f"Video {video_id}: CTR {current_ctr:.1f}% at/above benchmark — keeping current thumbnail")

            return test_result

    async def get_swap_candidates(self, channel_id: int) -> list[ABTestResult]:
        """Find all videos in a channel that should have their thumbnails swapped."""
        candidates = []

        async with async_session_factory() as db:
            result = await db.execute(
                select(Video)
                .where(Video.channel_id == channel_id)
                .where(Video.status == VideoStatus.PUBLISHED)
                .where(Video.youtube_video_id.is_not(None))
            )
            videos = result.scalars().all()

        for video in videos:
            test_result = await self.should_swap_thumbnail(video.id)
            if test_result.status == TestStatus.COMPLETED and test_result.winner == "B":
                candidates.append(test_result)

        logger.info(f"Found {len(candidates)} thumbnail swap candidates for channel {channel_id}")
        return candidates

    async def swap_thumbnail(self, video_id: int, new_thumbnail_path: str) -> bool:
        """Swap a video's thumbnail on YouTube."""
        async with async_session_factory() as db:
            video = await db.get(Video, video_id)
            if not video or not video.youtube_video_id:
                return False

            channel = await db.get(Channel, video.channel_id)
            if not channel or not channel.oauth_credentials_encrypted:
                return False

            try:
                from app.utils.youtube_auth import build_youtube_client
                from googleapiclient.http import MediaFileUpload

                youtube, _ = build_youtube_client(channel.oauth_credentials_encrypted)

                youtube.thumbnails().set(
                    videoId=video.youtube_video_id,
                    media_body=MediaFileUpload(new_thumbnail_path, mimetype="image/jpeg"),
                ).execute()

                # Update in DB
                video.thumbnail_path = new_thumbnail_path
                await db.commit()

                logger.info(f"Swapped thumbnail for video {video_id}")
                return True

            except Exception as e:
                logger.error(f"Failed to swap thumbnail for video {video_id}: {e}")
                return False

    async def run_ab_test_cycle(self, channel_id: int) -> dict:
        """Run a full A/B test cycle: check all videos, swap underperformers."""
        candidates = await self.get_swap_candidates(channel_id)

        swapped = 0
        for candidate in candidates:
            # Find alternative thumbnail variant
            async with async_session_factory() as db:
                video = await db.get(Video, candidate.video_id)
                if not video:
                    continue

                # Get all thumbnail variants from assets
                from app.models.asset import Asset, AssetType
                result = await db.execute(
                    select(Asset)
                    .where(Asset.video_id == video.id)
                    .where(Asset.type == AssetType.THUMBNAIL)
                )
                thumb_assets = result.scalars().all()

                # Find a variant that isn't the current one
                current = video.thumbnail_path
                for asset in thumb_assets:
                    if asset.local_path and asset.local_path != current:
                        success = await self.swap_thumbnail(video.id, asset.local_path)
                        if success:
                            swapped += 1
                        break

        return {
            "candidates_found": len(candidates),
            "thumbnails_swapped": swapped,
        }

    @staticmethod
    def _get_niche_ctr_benchmark(niche: str) -> float:
        """Get CTR benchmark for a niche."""
        benchmarks = {
            "tech": 5.0, "ai": 5.5, "finance": 4.5,
            "motivation": 6.5, "history": 5.0, "health": 4.5,
            "science": 5.0, "gaming": 6.0, "psychology": 5.5,
            "luxury": 6.0, "scary": 7.0, "horror": 7.0, "space": 5.5,
        }
        for keyword, benchmark in benchmarks.items():
            if keyword in niche:
                return benchmark
        return 5.0
