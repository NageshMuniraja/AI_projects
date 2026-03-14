"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ─── Auth ─────────────────────────────────────────────────────────

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    business_name: str = Field(min_length=1, max_length=255)
    industry: str = Field(min_length=1, max_length=50)
    phone: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ─── Tenant ───────────────────────────────────────────────────────

class TenantResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    industry: str
    plan: str
    status: str
    business_name: Optional[str] = None
    business_phone: Optional[str] = None
    business_email: Optional[str] = None
    ai_persona_name: Optional[str] = None
    ai_tone: Optional[str] = None
    greeting_message: Optional[str] = None
    primary_color: Optional[str] = None
    monthly_message_limit: int
    monthly_messages_used: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TenantUpdateRequest(BaseModel):
    business_name: Optional[str] = None
    business_phone: Optional[str] = None
    business_email: Optional[str] = None
    business_address: Optional[str] = None
    business_hours: Optional[dict] = None
    ai_persona_name: Optional[str] = None
    ai_tone: Optional[str] = None
    ai_instructions: Optional[str] = None
    greeting_message: Optional[str] = None
    fallback_message: Optional[str] = None
    primary_color: Optional[str] = None
    widget_position: Optional[str] = None


# ─── Conversations ───────────────────────────────────────────────

class MessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    channel: str = "web"


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    channel: Optional[str] = None
    tokens_used: Optional[int] = None
    confidence: Optional[float] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    channel: str
    status: str
    ai_enabled: bool
    sentiment: Optional[str] = None
    intent: Optional[str] = None
    summary: Optional[str] = None
    started_at: datetime
    last_message_at: Optional[datetime] = None
    messages: list[MessageResponse] = []

    model_config = {"from_attributes": True}


class ConversationListResponse(BaseModel):
    id: UUID
    channel: str
    status: str
    sentiment: Optional[str] = None
    intent: Optional[str] = None
    last_message_at: Optional[datetime] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    last_message_preview: Optional[str] = None

    model_config = {"from_attributes": True}


# ─── Services ────────────────────────────────────────────────────

class ServiceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=5, le=480)
    price: Optional[float] = Field(None, ge=0)
    currency: str = "INR"
    category: Optional[str] = None


class ServiceResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    price: Optional[float] = None
    currency: str
    category: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Appointments ────────────────────────────────────────────────

class AppointmentCreate(BaseModel):
    service_id: Optional[UUID] = None
    customer_name: str
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    scheduled_at: datetime
    duration_minutes: Optional[int] = 30
    notes: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: UUID
    customer_name: str
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    scheduled_at: datetime
    duration_minutes: Optional[int] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Leads ────────────────────────────────────────────────────────

class LeadResponse(BaseModel):
    id: UUID
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    source: Optional[str] = None
    status: str
    score: int
    interest: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LeadUpdateRequest(BaseModel):
    status: Optional[str] = None
    score: Optional[int] = Field(None, ge=0, le=100)
    notes: Optional[str] = None


# ─── Knowledge Base ──────────────────────────────────────────────

class KnowledgeDocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    category: Optional[str] = "general"
    source_type: str = "manual"


class KnowledgeDocumentResponse(BaseModel):
    id: UUID
    title: str
    source_type: Optional[str] = None
    category: Optional[str] = None
    chunk_count: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Analytics ───────────────────────────────────────────────────

class AnalyticsSummary(BaseModel):
    total_conversations: int
    active_conversations: int
    total_messages: int
    ai_messages: int
    appointments_booked: int
    leads_captured: int
    avg_response_time_seconds: Optional[float] = None
    satisfaction_score: Optional[float] = None
    top_intents: list[dict] = []
    messages_by_channel: dict = {}
    messages_by_day: list[dict] = []


# ─── WebSocket ───────────────────────────────────────────────────

class WSMessage(BaseModel):
    type: str  # message, typing, status
    conversation_id: Optional[str] = None
    content: Optional[str] = None
    data: Optional[dict] = None
