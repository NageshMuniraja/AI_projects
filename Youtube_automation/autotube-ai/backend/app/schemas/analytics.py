from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class AnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    video_id: int
    date: date
    views: int
    likes: int
    dislikes: int
    comments: int
    shares: int
    watch_time_hours: Decimal
    avg_view_duration: Decimal
    avg_view_percentage: Decimal
    ctr: Decimal
    impressions: int
    subscribers_gained: int
    estimated_revenue: Decimal
    traffic_sources: dict | None
    demographics: dict | None


class ChannelAnalyticsSummary(BaseModel):
    channel_id: int
    channel_name: str
    total_videos: int
    total_views: int
    total_watch_time_hours: Decimal
    total_revenue: Decimal
    avg_ctr: Decimal
    top_video_title: str | None
    top_video_views: int
    period_start: date
    period_end: date
