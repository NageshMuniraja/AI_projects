"""Tenant management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.models import Tenant
from app.schemas.schemas import TenantResponse, TenantUpdateRequest

router = APIRouter(prefix="/tenant", tags=["Tenant"])


@router.get("/", response_model=TenantResponse)
async def get_tenant(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current tenant details."""
    result = await db.execute(
        select(Tenant).where(Tenant.id == current_user["tenant_id"])
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.patch("/", response_model=TenantResponse)
async def update_tenant(
    update: TenantUpdateRequest,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update tenant configuration."""
    result = await db.execute(
        select(Tenant).where(Tenant.id == current_user["tenant_id"])
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)

    await db.flush()
    return tenant
