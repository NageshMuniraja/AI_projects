from fastapi import APIRouter

from app.api.channels import router as channels_router
from app.api.videos import router as videos_router
from app.api.pipeline import router as pipeline_router
from app.api.analytics import router as analytics_router
from app.api.settings import router as settings_router

api_router = APIRouter(prefix="/api")

api_router.include_router(channels_router, prefix="/channels", tags=["channels"])
api_router.include_router(videos_router, prefix="/videos", tags=["videos"])
api_router.include_router(pipeline_router, prefix="/pipeline", tags=["pipeline"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])
