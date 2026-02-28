from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.video import VideoStatus


class VideoCreate(BaseModel):
    channel_id: int
    topic: str | None = None
    scheduled_publish_at: datetime | None = None


class VideoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel_id: int
    topic: str | None
    status: VideoStatus
    pipeline_step: int
    error_message: str | None
    title: str | None
    description: str | None
    tags: list | None
    youtube_video_id: str | None
    duration_seconds: int | None
    word_count: int | None
    api_cost: Decimal | None
    scheduled_publish_at: datetime | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class VideoListResponse(BaseModel):
    videos: list[VideoResponse]
    total: int


class PipelineStatusResponse(BaseModel):
    video_id: int
    status: VideoStatus
    pipeline_step: int
    error_message: str | None
    steps: list[dict]


class PipelineTriggerRequest(BaseModel):
    channel_id: int
    topic: str | None = None
    count: int = 1
