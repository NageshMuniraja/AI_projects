"""Authentication endpoints."""

import uuid
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from app.models.models import User, Tenant
from app.schemas.schemas import (
    SignUpRequest, LoginRequest, TokenResponse, RefreshTokenRequest,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "-", slug).strip("-")


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignUpRequest, db: AsyncSession = Depends(get_db)):
    """Register a new business account."""
    # Check if email exists
    existing = await db.execute(select(User).where(User.email == request.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create tenant
    slug = slugify(request.business_name) + "-" + str(uuid.uuid4())[:6]
    tenant = Tenant(
        id=uuid.uuid4(),
        name=request.business_name,
        slug=slug,
        industry=request.industry,
        business_name=request.business_name,
        business_phone=request.phone,
        business_email=request.email,
    )
    db.add(tenant)
    await db.flush()

    # Create user
    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email=request.email,
        hashed_password=hash_password(request.password),
        full_name=request.full_name,
        role="owner",
    )
    db.add(user)
    await db.flush()

    # Generate tokens
    token_data = {
        "sub": str(user.id),
        "tenant_id": str(tenant.id),
        "email": user.email,
        "role": user.role,
    }

    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        expires_in=60 * 24 * 60,  # 24 hours in seconds
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email and password."""
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)

    token_data = {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id),
        "email": user.email,
        "role": user.role,
    }

    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        expires_in=60 * 24 * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token."""
    payload = decode_token(request.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    token_data = {
        "sub": payload["sub"],
        "tenant_id": payload.get("tenant_id"),
        "email": payload.get("email"),
        "role": payload.get("role"),
    }

    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        expires_in=60 * 24 * 60,
    )
