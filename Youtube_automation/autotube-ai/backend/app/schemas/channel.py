from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChannelCreate(BaseModel):
    name: str
    niche: str
    youtube_channel_id: str | None = None
    voice_id: str | None = None
    caption_style: str = "hormozi"
    thumbnail_style: str = "bold"
    posting_frequency: str = "daily"
    optimal_post_times: dict | None = None


class ChannelUpdate(BaseModel):
    name: str | None = None
    niche: str | None = None
    youtube_channel_id: str | None = None
    voice_id: str | None = None
    caption_style: str | None = None
    thumbnail_style: str | None = None
    posting_frequency: str | None = None
    optimal_post_times: dict | None = None
    is_active: bool | None = None


class ChannelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    niche: str
    youtube_channel_id: str | None
    voice_id: str | None
    caption_style: str
    thumbnail_style: str
    posting_frequency: str
    optimal_post_times: dict | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
