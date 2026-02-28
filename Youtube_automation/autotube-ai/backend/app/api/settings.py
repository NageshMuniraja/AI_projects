from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/")
async def get_settings():
    """Return non-sensitive application settings."""
    return {
        "app_env": settings.APP_ENV,
        "default_video_resolution": settings.DEFAULT_VIDEO_RESOLUTION,
        "default_caption_style": settings.DEFAULT_CAPTION_STYLE,
        "default_fps": settings.DEFAULT_FPS,
        "max_concurrent_pipelines": settings.MAX_CONCURRENT_PIPELINES,
        "media_dir": str(settings.MEDIA_DIR),
        "apis_configured": {
            "anthropic": bool(settings.ANTHROPIC_API_KEY),
            "elevenlabs": bool(settings.ELEVENLABS_API_KEY),
            "stability": bool(settings.STABILITY_API_KEY),
            "pexels": bool(settings.PEXELS_API_KEY),
            "pixabay": bool(settings.PIXABAY_API_KEY),
            "youtube": bool(settings.YOUTUBE_CLIENT_ID),
        },
    }
