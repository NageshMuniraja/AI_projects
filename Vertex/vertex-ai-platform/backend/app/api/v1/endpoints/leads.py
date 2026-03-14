"""Lead management endpoints."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import Lead
from app.schemas.schemas import LeadResponse, LeadUpdateRequest

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.get("/", response_model=list[LeadResponse])
async def list_leads(
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List leads for the tenant."""
    query = (
        select(Lead)
        .where(Lead.tenant_id == current_user["tenant_id"])
        .order_by(Lead.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if status:
        query = query.where(Lead.status == status)

    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: uuid.UUID,
    request: LeadUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a lead."""
    result = await db.execute(
        select(Lead).where(
            Lead.id == lead_id,
            Lead.tenant_id == current_user["tenant_id"],
        )
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)

    await db.flush()
    return lead
