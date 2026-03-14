"""Analytics endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.schemas import AnalyticsSummary
from app.services.analytics_service import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=AnalyticsSummary)
async def get_dashboard(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard analytics summary."""
    return await analytics_service.get_dashboard_summary(
        db=db,
        tenant_id=current_user["tenant_id"],
        days=days,
    )
