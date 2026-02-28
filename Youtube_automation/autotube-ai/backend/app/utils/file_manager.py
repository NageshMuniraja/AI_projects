import os
import time
from pathlib import Path

from loguru import logger

from app.config import settings


def cleanup_temp_files(max_age_hours: int = 24) -> int:
    """Delete temp files older than max_age_hours. Returns count of deleted files."""
    deleted = 0
    cutoff = time.time() - (max_age_hours * 3600)

    for file_path in settings.temp_dir.rglob("*"):
        if file_path.is_file() and file_path.stat().st_mtime < cutoff:
            try:
                file_path.unlink()
                deleted += 1
            except OSError as e:
                logger.warning(f"Failed to delete {file_path}: {e}")

    logger.info(f"Cleaned up {deleted} temp files older than {max_age_hours}h")
    return deleted


def cleanup_old_videos(max_age_days: int = 30) -> int:
    """Delete final videos older than max_age_days. Returns count of deleted files."""
    deleted = 0
    cutoff = time.time() - (max_age_days * 86400)

    for file_path in settings.final_videos_dir.rglob("*.mp4"):
        if file_path.stat().st_mtime < cutoff:
            try:
                file_path.unlink()
                deleted += 1
            except OSError as e:
                logger.warning(f"Failed to delete {file_path}: {e}")

    logger.info(f"Cleaned up {deleted} final videos older than {max_age_days}d")
    return deleted


def get_unique_path(directory: Path, prefix: str, extension: str) -> Path:
    """Generate a unique file path with timestamp."""
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = int(time.time() * 1000)
    return directory / f"{prefix}_{timestamp}{extension}"


def get_media_disk_usage() -> dict:
    """Return disk usage in bytes for each media subdirectory."""
    usage = {}
    for subdir in ["voiceovers", "footage", "thumbnails", "final_videos", "temp"]:
        path = settings.MEDIA_DIR / subdir
        if path.exists():
            total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
            usage[subdir] = total
        else:
            usage[subdir] = 0
    return usage
