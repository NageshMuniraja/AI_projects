import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    niche: Mapped[str] = mapped_column(String(100), nullable=False)
    youtube_channel_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    oauth_credentials_encrypted: Mapped[str | None] = mapped_column(Text)
    voice_id: Mapped[str | None] = mapped_column(String(100))
    caption_style: Mapped[str] = mapped_column(String(50), default="hormozi")
    thumbnail_style: Mapped[str] = mapped_column(String(50), default="bold")
    posting_frequency: Mapped[str] = mapped_column(String(50), default="daily")
    optimal_post_times: Mapped[dict | None] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    videos: Mapped[list["Video"]] = relationship(back_populates="channel", lazy="selectin")
    content_calendar: Mapped[list["ContentCalendar"]] = relationship(
        back_populates="channel", lazy="selectin"
    )
