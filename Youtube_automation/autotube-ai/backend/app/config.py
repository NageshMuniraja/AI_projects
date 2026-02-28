from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---
    APP_ENV: Literal["development", "production", "testing"] = "development"
    SECRET_KEY: str = "change-me-to-a-random-64-char-string"
    LOG_LEVEL: str = "INFO"

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://autotube:autotube_secret@localhost:5432/autotube"
    DATABASE_URL_SYNC: str = "postgresql://autotube:autotube_secret@localhost:5432/autotube"

    # --- Redis ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- AI APIs ---
    ANTHROPIC_API_KEY: str = ""
    STABILITY_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # --- Stock Media ---
    PEXELS_API_KEY: str = ""
    PIXABAY_API_KEY: str = ""

    # --- YouTube ---
    YOUTUBE_CLIENT_ID: str = ""
    YOUTUBE_CLIENT_SECRET: str = ""
    YOUTUBE_REDIRECT_URI: str = "http://localhost:8000/api/auth/youtube/callback"

    # --- Video Defaults ---
    MEDIA_DIR: Path = Path("/app/media")
    MAX_CONCURRENT_PIPELINES: int = 3
    DEFAULT_VIDEO_RESOLUTION: str = "1080p"
    DEFAULT_CAPTION_STYLE: str = "hormozi"
    DEFAULT_FPS: int = 30
    DEFAULT_VIDEO_BITRATE: str = "10M"

    # --- Derived paths ---
    @property
    def voiceovers_dir(self) -> Path:
        return self.MEDIA_DIR / "voiceovers"

    @property
    def footage_dir(self) -> Path:
        return self.MEDIA_DIR / "footage"

    @property
    def thumbnails_dir(self) -> Path:
        return self.MEDIA_DIR / "thumbnails"

    @property
    def final_videos_dir(self) -> Path:
        return self.MEDIA_DIR / "final_videos"

    @property
    def temp_dir(self) -> Path:
        return self.MEDIA_DIR / "temp"

    def ensure_media_dirs(self) -> None:
        for d in [
            self.voiceovers_dir,
            self.footage_dir,
            self.thumbnails_dir,
            self.final_videos_dir,
            self.temp_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
