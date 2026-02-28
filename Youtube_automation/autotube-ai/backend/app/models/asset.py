import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AssetType(str, enum.Enum):
    STOCK_VIDEO = "stock_video"
    AI_IMAGE = "ai_image"
    MUSIC = "music"
    SFX = "sfx"
    FONT = "font"


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"), nullable=False)
    type: Mapped[AssetType] = mapped_column(Enum(AssetType), nullable=False)
    source: Mapped[str] = mapped_column(String(100))
    source_url: Mapped[str | None] = mapped_column(Text)
    local_path: Mapped[str | None] = mapped_column(String(500))
    license_type: Mapped[str | None] = mapped_column(String(100))
    attribution: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    video: Mapped["Video"] = relationship(back_populates="assets")
