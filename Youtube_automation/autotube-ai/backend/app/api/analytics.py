from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.analytics import VideoAnalytics
from app.models.channel import Channel
from app.models.video import Video
from app.schemas.analytics import AnalyticsResponse, ChannelAnalyticsSummary

router = APIRouter()


@router.get("/video/{video_id}", response_model=list[AnalyticsResponse])
async def get_video_analytics(video_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(VideoAnalytics)
        .where(VideoAnalytics.video_id == video_id)
        .order_by(VideoAnalytics.date.desc())
    )
    return result.scalars().all()


@router.get("/channel/{channel_id}", response_model=ChannelAnalyticsSummary)
async def get_channel_analytics(
    channel_id: int,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    channel = await db.get(Channel, channel_id)
    period_start = date.today() - timedelta(days=days)
    period_end = date.today()

    # Aggregate analytics for the channel's videos
    result = await db.execute(
        select(
            func.count(func.distinct(VideoAnalytics.video_id)),
            func.coalesce(func.sum(VideoAnalytics.views), 0),
            func.coalesce(func.sum(VideoAnalytics.watch_time_hours), 0),
            func.coalesce(func.sum(VideoAnalytics.estimated_revenue), 0),
            func.coalesce(func.avg(VideoAnalytics.ctr), 0),
        )
        .join(Video, Video.id == VideoAnalytics.video_id)
        .where(Video.channel_id == channel_id)
        .where(VideoAnalytics.date >= period_start)
    )
    row = result.one()

    # Top video
    top_result = await db.execute(
        select(Video.title, func.sum(VideoAnalytics.views).label("total_views"))
        .join(Video, Video.id == VideoAnalytics.video_id)
        .where(Video.channel_id == channel_id)
        .where(VideoAnalytics.date >= period_start)
        .group_by(Video.id, Video.title)
        .order_by(func.sum(VideoAnalytics.views).desc())
        .limit(1)
    )
    top_video = top_result.first()

    return ChannelAnalyticsSummary(
        channel_id=channel_id,
        channel_name=channel.name if channel else "Unknown",
        total_videos=row[0],
        total_views=row[1],
        total_watch_time_hours=row[2],
        total_revenue=row[3],
        avg_ctr=row[4],
        top_video_title=top_video[0] if top_video else None,
        top_video_views=top_video[1] if top_video else 0,
        period_start=period_start,
        period_end=period_end,
    )
