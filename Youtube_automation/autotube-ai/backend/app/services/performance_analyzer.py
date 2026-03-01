"""Performance Analyzer — scores videos and identifies optimization opportunities."""

from dataclasses import dataclass, field
from decimal import Decimal

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.analytics import VideoAnalytics
from app.models.channel import Channel
from app.models.video import Video, VideoStatus


# Niche-specific CTR benchmarks (industry averages)
NICHE_CTR_BENCHMARKS = {
    "tech": 5.0,
    "ai": 5.5,
    "finance": 4.5,
    "motivation": 6.5,
    "history": 5.0,
    "health": 4.5,
    "science": 5.0,
    "gaming": 6.0,
    "psychology": 5.5,
    "luxury": 6.0,
    "scary": 7.0,
    "horror": 7.0,
    "space": 5.5,
}


@dataclass
class VideoScore:
    video_id: int
    title: str
    retention_score: float = 0.0    # avg_view_percentage vs channel avg
    ctr_score: float = 0.0          # CTR vs niche benchmark
    engagement_score: float = 0.0   # (likes + comments*3 + shares*5) / views
    growth_score: float = 0.0       # subscribers_gained / views
    overall_score: float = 0.0      # weighted average
    flags: list[str] = field(default_factory=list)  # optimization suggestions


@dataclass
class ChannelPerformance:
    channel_id: int
    avg_retention: float = 0.0
    avg_ctr: float = 0.0
    avg_engagement: float = 0.0
    total_views: int = 0
    total_subscribers_gained: int = 0
    total_revenue: float = 0.0
    top_videos: list[VideoScore] = field(default_factory=list)
    underperformers: list[VideoScore] = field(default_factory=list)
    optimization_flags: list[str] = field(default_factory=list)


class PerformanceAnalyzer:
    """Analyzes video performance and generates optimization recommendations."""

    # Score weights
    RETENTION_WEIGHT = 0.40
    CTR_WEIGHT = 0.30
    ENGAGEMENT_WEIGHT = 0.20
    GROWTH_WEIGHT = 0.10

    async def score_video(self, video_id: int) -> VideoScore | None:
        """Calculate performance score for a single video."""
        async with async_session_factory() as db:
            video = await db.get(Video, video_id)
            if not video:
                return None

            # Get latest analytics
            result = await db.execute(
                select(VideoAnalytics)
                .where(VideoAnalytics.video_id == video_id)
                .order_by(VideoAnalytics.date.desc())
                .limit(1)
            )
            analytics = result.scalar_one_or_none()
            if not analytics:
                return VideoScore(video_id=video_id, title=video.title or video.topic or "")

            # Get channel averages for comparison
            channel_avgs = await self._get_channel_averages(db, video.channel_id)

            # Get niche benchmark
            channel = await db.get(Channel, video.channel_id)
            niche = channel.niche.lower() if channel else "general"
            niche_ctr = self._get_niche_ctr(niche)

            score = VideoScore(
                video_id=video_id,
                title=video.title or video.topic or "",
            )

            # Retention score: avg_view_percentage vs channel average
            if channel_avgs["avg_retention"] > 0:
                score.retention_score = float(analytics.avg_view_percentage) / channel_avgs["avg_retention"]
            elif float(analytics.avg_view_percentage) > 0:
                score.retention_score = float(analytics.avg_view_percentage) / 50.0  # assume 50% baseline

            # CTR score: video CTR vs niche benchmark
            if niche_ctr > 0:
                score.ctr_score = float(analytics.ctr) / niche_ctr

            # Engagement score: weighted engagement / views
            if analytics.views > 0:
                weighted_engagement = (
                    analytics.likes
                    + analytics.comments * 3
                    + analytics.shares * 5
                )
                score.engagement_score = (weighted_engagement / analytics.views) * 100

            # Growth score: subscribers per view (×1000 for readability)
            if analytics.views > 0:
                score.growth_score = (analytics.subscribers_gained / analytics.views) * 1000

            # Overall weighted score (normalized to 0-100)
            score.overall_score = min(100, (
                score.retention_score * self.RETENTION_WEIGHT * 100
                + score.ctr_score * self.CTR_WEIGHT * 100
                + min(score.engagement_score, 10) * self.ENGAGEMENT_WEIGHT * 10
                + min(score.growth_score, 5) * self.GROWTH_WEIGHT * 20
            ))

            # Generate flags
            score.flags = self._generate_flags(score, analytics, niche_ctr)

            return score

    async def analyze_channel(self, channel_id: int) -> ChannelPerformance:
        """Full performance analysis for a channel."""
        perf = ChannelPerformance(channel_id=channel_id)

        async with async_session_factory() as db:
            channel = await db.get(Channel, channel_id)
            if not channel:
                return perf

            # Get all published videos with analytics
            result = await db.execute(
                select(Video)
                .where(Video.channel_id == channel_id)
                .where(Video.status == VideoStatus.PUBLISHED)
            )
            videos = result.scalars().all()

            video_scores = []
            for video in videos:
                score = await self.score_video(video.id)
                if score:
                    video_scores.append(score)

            if not video_scores:
                return perf

            # Channel-level metrics
            avgs = await self._get_channel_averages(db, channel_id)
            perf.avg_retention = avgs["avg_retention"]
            perf.avg_ctr = avgs["avg_ctr"]
            perf.avg_engagement = avgs["avg_engagement"]
            perf.total_views = avgs["total_views"]
            perf.total_subscribers_gained = avgs["total_subs"]
            perf.total_revenue = avgs["total_revenue"]

            # Sort by overall score
            video_scores.sort(key=lambda s: s.overall_score, reverse=True)
            perf.top_videos = video_scores[:5]
            perf.underperformers = [s for s in video_scores if s.overall_score < 40]

            # Channel-level optimization flags
            niche = channel.niche.lower()
            niche_ctr = self._get_niche_ctr(niche)
            if perf.avg_ctr < niche_ctr * 0.7:
                perf.optimization_flags.append(
                    f"Channel CTR ({perf.avg_ctr:.1f}%) is below niche benchmark ({niche_ctr:.1f}%). "
                    "Consider revamping thumbnail and title strategies."
                )
            if perf.avg_retention < 40:
                perf.optimization_flags.append(
                    f"Average retention ({perf.avg_retention:.1f}%) is low. "
                    "Focus on stronger hooks and tighter pacing in scripts."
                )
            if len(perf.underperformers) > len(video_scores) * 0.5:
                perf.optimization_flags.append(
                    "Over 50% of videos are underperforming. "
                    "Consider pivoting topic selection strategy."
                )

        return perf

    async def get_performance_summary_for_ai(self, channel_id: int) -> str:
        """Generate a human-readable performance summary for AI prompts."""
        perf = await self.analyze_channel(channel_id)

        lines = [
            f"Channel Performance Summary (last 30 days):",
            f"- Average Retention: {perf.avg_retention:.1f}%",
            f"- Average CTR: {perf.avg_ctr:.1f}%",
            f"- Total Views: {perf.total_views:,}",
            f"- Subscribers Gained: {perf.total_subscribers_gained:,}",
            f"- Estimated Revenue: ${perf.total_revenue:.2f}",
            "",
        ]

        if perf.top_videos:
            lines.append("Top Performers:")
            for v in perf.top_videos[:3]:
                lines.append(f"  - '{v.title}' (score: {v.overall_score:.0f}/100)")

        if perf.optimization_flags:
            lines.append("")
            lines.append("Issues to Address:")
            for flag in perf.optimization_flags:
                lines.append(f"  - {flag}")

        return "\n".join(lines)

    async def _get_channel_averages(self, db: AsyncSession, channel_id: int) -> dict:
        """Get aggregate analytics for a channel."""
        result = await db.execute(
            select(
                func.avg(VideoAnalytics.avg_view_percentage).label("avg_retention"),
                func.avg(VideoAnalytics.ctr).label("avg_ctr"),
                func.sum(VideoAnalytics.views).label("total_views"),
                func.sum(VideoAnalytics.subscribers_gained).label("total_subs"),
                func.sum(VideoAnalytics.estimated_revenue).label("total_revenue"),
                func.avg(
                    (VideoAnalytics.likes + VideoAnalytics.comments * 3 + VideoAnalytics.shares * 5)
                    * 100.0 / func.nullif(VideoAnalytics.views, 0)
                ).label("avg_engagement"),
            )
            .join(Video, Video.id == VideoAnalytics.video_id)
            .where(Video.channel_id == channel_id)
        )
        row = result.one()

        return {
            "avg_retention": float(row.avg_retention or 0),
            "avg_ctr": float(row.avg_ctr or 0),
            "avg_engagement": float(row.avg_engagement or 0),
            "total_views": int(row.total_views or 0),
            "total_subs": int(row.total_subs or 0),
            "total_revenue": float(row.total_revenue or 0),
        }

    def _get_niche_ctr(self, niche: str) -> float:
        """Get CTR benchmark for a niche."""
        for keyword, benchmark in NICHE_CTR_BENCHMARKS.items():
            if keyword in niche:
                return benchmark
        return 5.0  # default

    @staticmethod
    def _generate_flags(score: VideoScore, analytics: VideoAnalytics, niche_ctr: float) -> list[str]:
        """Generate optimization flags for a video."""
        flags = []

        if float(analytics.ctr) < 3.0:
            flags.append("LOW_CTR: Thumbnail and title need improvement (CTR < 3%)")

        if float(analytics.avg_view_percentage) < 40:
            flags.append("LOW_RETENTION: Script pacing or hook needs work (retention < 40%)")

        if float(analytics.avg_view_percentage) > 60 and float(analytics.ctr) < niche_ctr:
            flags.append("HIGH_RETENTION_LOW_CTR: Great content but poor packaging — fix thumbnail/title")

        if analytics.views > 0:
            engagement_rate = (analytics.likes + analytics.comments) / analytics.views
            if engagement_rate > 0.08:
                flags.append("HIGH_ENGAGEMENT: Make more content on this topic (engagement > 8%)")
            if engagement_rate < 0.02:
                flags.append("LOW_ENGAGEMENT: Topic may not resonate with audience")

        if analytics.subscribers_gained > 0 and analytics.views > 0:
            sub_rate = analytics.subscribers_gained / analytics.views
            if sub_rate > 0.005:
                flags.append("HIGH_SUB_RATE: This topic converts viewers to subscribers well")

        return flags
