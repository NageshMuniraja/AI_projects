"""Service/product management endpoints."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.models import Service
from app.schemas.schemas import ServiceCreate, ServiceResponse

router = APIRouter(prefix="/services", tags=["Services"])


@router.get("/", response_model=list[ServiceResponse])
async def list_services(
    category: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all services for the tenant."""
    query = select(Service).where(
        Service.tenant_id == current_user["tenant_id"],
        Service.is_active == True,
    )
    if category:
        query = query.where(Service.category == category)

    result = await db.execute(query.order_by(Service.name))
    return result.scalars().all()


@router.post("/", response_model=ServiceResponse, status_code=201)
async def create_service(
    request: ServiceCreate,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new service."""
    service = Service(
        id=uuid.uuid4(),
        tenant_id=current_user["tenant_id"],
        **request.model_dump(),
    )
    db.add(service)
    await db.flush()
    return service


@router.patch("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: uuid.UUID,
    request: ServiceCreate,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a service."""
    result = await db.execute(
        select(Service).where(
            Service.id == service_id,
            Service.tenant_id == current_user["tenant_id"],
        )
    )
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(service, field, value)

    await db.flush()
    return service


@router.delete("/{service_id}", status_code=204)
async def delete_service(
    service_id: uuid.UUID,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a service."""
    result = await db.execute(
        select(Service).where(
            Service.id == service_id,
            Service.tenant_id == current_user["tenant_id"],
        )
    )
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    service.is_active = False
    await db.flush()
