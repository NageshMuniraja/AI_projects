import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class VideoStatus(str, enum.Enum):
    RESEARCHING = "researching"
    SCRIPTING = "scripting"
    VOICEOVER = "voiceover"
    COLLECTING_ASSETS = "collecting_assets"
    GENERATING_CAPTIONS = "generating_captions"
    GENERATING_THUMBNAIL = "generating_thumbnail"
    ASSEMBLING = "assembling"
    OPTIMIZING_SEO = "optimizing_seo"
    UPLOADING = "uploading"
    PUBLISHED = "published"
    FAILED = "failed"
    QUEUED = "queued"


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), nullable=False)
    topic: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[VideoStatus] = mapped_column(
        Enum(VideoStatus), default=VideoStatus.QUEUED
    )
    pipeline_step: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)

    # Content
    script_text: Mapped[str | None] = mapped_column(Text)
    voiceover_path: Mapped[str | None] = mapped_column(String(500))
    thumbnail_path: Mapped[str | None] = mapped_column(String(500))
    final_video_path: Mapped[str | None] = mapped_column(String(500))

    # YouTube metadata
    youtube_video_id: Mapped[str | None] = mapped_column(String(50))
    title: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list | None] = mapped_column(JSONB)

    # Scheduling
    scheduled_publish_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Metrics
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    word_count: Mapped[int | None] = mapped_column(Integer)
    api_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    channel: Mapped["Channel"] = relationship(back_populates="videos")
    analytics: Mapped[list["VideoAnalytics"]] = relationship(
        back_populates="video", lazy="selectin"
    )
    assets: Mapped[list["Asset"]] = relationship(back_populates="video", lazy="selectin")
