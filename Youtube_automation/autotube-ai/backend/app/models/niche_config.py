from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NicheConfig(Base):
    __tablename__ = "niche_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    target_audience: Mapped[str] = mapped_column(String(255))
    tone: Mapped[str] = mapped_column(String(100))
    keywords: Mapped[list] = mapped_column(JSONB, default=list)
    competitor_channels: Mapped[list] = mapped_column(JSONB, default=list)
    content_pillars: Mapped[list] = mapped_column(JSONB, default=list)
    avoid_topics: Mapped[list] = mapped_column(JSONB, default=list)
    preferred_voice_style: Mapped[str | None] = mapped_column(String(100))
    thumbnail_style: Mapped[str] = mapped_column(String(50), default="bold")
    posting_frequency: Mapped[str] = mapped_column(String(50), default="daily")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
