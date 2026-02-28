import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CalendarStatus(str, enum.Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class ContentCalendar(Base):
    __tablename__ = "content_calendar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), nullable=False)
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[CalendarStatus] = mapped_column(
        Enum(CalendarStatus), default=CalendarStatus.PLANNED
    )
    priority_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    niche_category: Mapped[str | None] = mapped_column(String(100))
    is_trending: Mapped[bool] = mapped_column(Boolean, default=False)
    is_evergreen: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    channel: Mapped["Channel"] = relationship(back_populates="content_calendar")
