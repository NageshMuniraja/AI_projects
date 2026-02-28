from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class VideoAnalytics(Base):
    __tablename__ = "video_analytics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)

    # Engagement
    views: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    dislikes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)

    # Watch metrics
    watch_time_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    avg_view_duration: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    avg_view_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)

    # Discovery
    ctr: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    subscribers_gained: Mapped[int] = mapped_column(Integer, default=0)

    # Revenue
    estimated_revenue: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0)

    # Breakdowns
    traffic_sources: Mapped[dict | None] = mapped_column(JSONB)
    demographics: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    video: Mapped["Video"] = relationship(back_populates="analytics")
