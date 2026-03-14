"""Appointment management endpoints."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import Appointment
from app.schemas.schemas import AppointmentCreate, AppointmentResponse

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.get("/", response_model=list[AppointmentResponse])
async def list_appointments(
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List appointments for the tenant."""
    query = (
        select(Appointment)
        .where(Appointment.tenant_id == current_user["tenant_id"])
        .order_by(Appointment.scheduled_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if status:
        query = query.where(Appointment.status == status)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=AppointmentResponse, status_code=201)
async def create_appointment(
    request: AppointmentCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually create an appointment."""
    appointment = Appointment(
        id=uuid.uuid4(),
        tenant_id=current_user["tenant_id"],
        **request.model_dump(),
    )
    db.add(appointment)
    await db.flush()
    return appointment


@router.patch("/{appointment_id}/status")
async def update_appointment_status(
    appointment_id: uuid.UUID,
    status: str = Query(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update appointment status."""
    valid_statuses = {"pending", "confirmed", "completed", "cancelled", "no_show"}
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    result = await db.execute(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.tenant_id == current_user["tenant_id"],
        )
    )
    appointment = result.scalar_one_or_none()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment.status = status
    await db.flush()
    return {"status": "updated", "appointment_id": str(appointment_id)}
