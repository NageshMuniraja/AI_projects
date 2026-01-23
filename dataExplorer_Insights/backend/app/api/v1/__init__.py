"""
API Routes - Version 1
"""

from fastapi import APIRouter
from app.api.v1.endpoints import chat, database, insights, auth, queries

router = APIRouter()

# Include all endpoint routers
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(database.router, prefix="/database", tags=["Database"])
router.include_router(chat.router, prefix="/chat", tags=["Chat"])
router.include_router(insights.router, prefix="/insights", tags=["Insights"])
router.include_router(queries.router, prefix="/queries", tags=["Queries"])
