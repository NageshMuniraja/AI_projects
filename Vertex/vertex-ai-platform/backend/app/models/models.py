"""SQLAlchemy models for the Vertex AI Platform."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float, DateTime,
    ForeignKey, Enum, JSON, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def new_uuid():
    return uuid.uuid4()


# ─── Tenant / Organization ───────────────────────────────────────

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    industry = Column(String(50), nullable=False)  # dental, salon, clinic, etc.
    plan = Column(String(20), default="starter")  # starter, growth, enterprise
    status = Column(String(20), default="active")  # active, suspended, cancelled

    # Business Config
    business_name = Column(String(255))
    business_phone = Column(String(20))
    business_email = Column(String(255))
    business_address = Column(Text)
    business_hours = Column(JSONB, default={})
    timezone = Column(String(50), default="Asia/Kolkata")
    language = Column(String(10), default="en")

    # AI Config
    ai_persona_name = Column(String(100), default="AI Assistant")
    ai_tone = Column(String(20), default="professional")  # professional, friendly, casual
    ai_instructions = Column(Text)  # Custom instructions from business owner
    greeting_message = Column(Text)
    fallback_message = Column(Text, default="Let me connect you with a team member for this.")

    # Branding
    logo_url = Column(String(500))
    primary_color = Column(String(7), default="#6366f1")
    widget_position = Column(String(20), default="bottom-right")

    # Limits
    monthly_message_limit = Column(Integer, default=1000)
    monthly_messages_used = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    trial_ends_at = Column(DateTime(timezone=True))

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="tenant", cascade="all, delete-orphan")
    knowledge_docs = relationship("KnowledgeDocument", back_populates="tenant", cascade="all, delete-orphan")
    services = relationship("Service", back_populates="tenant", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="tenant", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="tenant", cascade="all, delete-orphan")


# ─── Users ────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(20), default="member")  # owner, admin, member
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utcnow)

    tenant = relationship("Tenant", back_populates="users")

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_tenant_email"),
        Index("ix_users_email", "email"),
    )


# ─── Contacts / Customers ────────────────────────────────────────

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    phone = Column(String(20))
    email = Column(String(255))
    name = Column(String(255))
    whatsapp_id = Column(String(50))
    channel = Column(String(20))  # whatsapp, web, voice
    metadata = Column(JSONB, default={})
    tags = Column(ARRAY(String), default=[])
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    conversations = relationship("Conversation", back_populates="contact")

    __table_args__ = (
        Index("ix_contacts_tenant_phone", "tenant_id", "phone"),
        Index("ix_contacts_tenant_whatsapp", "tenant_id", "whatsapp_id"),
    )


# ─── Conversations ───────────────────────────────────────────────

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"))
    channel = Column(String(20), nullable=False)  # whatsapp, web, voice
    status = Column(String(20), default="active")  # active, resolved, escalated
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))

    # AI Context
    ai_enabled = Column(Boolean, default=True)
    sentiment = Column(String(20))  # positive, neutral, negative
    intent = Column(String(100))  # booking, inquiry, complaint, etc.
    summary = Column(Text)

    # Metadata
    metadata = Column(JSONB, default={})
    started_at = Column(DateTime(timezone=True), default=utcnow)
    resolved_at = Column(DateTime(timezone=True))
    last_message_at = Column(DateTime(timezone=True), default=utcnow)

    tenant = relationship("Tenant", back_populates="conversations")
    contact = relationship("Contact", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan",
                          order_by="Message.created_at")

    __table_args__ = (
        Index("ix_conversations_tenant_status", "tenant_id", "status"),
        Index("ix_conversations_last_message", "tenant_id", "last_message_at"),
    )


# ─── Messages ────────────────────────────────────────────────────

class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    channel = Column(String(20))  # whatsapp, web, voice

    # AI metadata
    ai_model = Column(String(50))
    tokens_used = Column(Integer)
    confidence = Column(Float)
    tool_calls = Column(JSONB)

    # WhatsApp specific
    whatsapp_message_id = Column(String(100))
    media_url = Column(String(500))
    media_type = Column(String(50))

    # Delivery status
    status = Column(String(20), default="sent")  # sent, delivered, read, failed
    created_at = Column(DateTime(timezone=True), default=utcnow)

    conversation = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        Index("ix_messages_conversation", "conversation_id", "created_at"),
    )


# ─── Knowledge Base ──────────────────────────────────────────────

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    source_type = Column(String(20))  # upload, url, manual
    content = Column(Text)
    file_url = Column(String(500))
    category = Column(String(50))  # faq, services, policies, general
    is_active = Column(Boolean, default=True)
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    tenant = relationship("Tenant", back_populates="knowledge_docs")
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    document_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer)
    token_count = Column(Integer)
    metadata = Column(JSONB, default={})
    embedding = Column(Vector(1536))  # pgvector for similarity search
    created_at = Column(DateTime(timezone=True), default=utcnow)

    document = relationship("KnowledgeDocument", back_populates="chunks")

    __table_args__ = (
        Index("ix_knowledge_chunks_tenant", "tenant_id"),
    )


# ─── Services / Products ─────────────────────────────────────────

class Service(Base):
    __tablename__ = "services"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    duration_minutes = Column(Integer)
    price = Column(Float)
    currency = Column(String(3), default="INR")
    category = Column(String(100))
    is_active = Column(Boolean, default=True)
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=utcnow)

    tenant = relationship("Tenant", back_populates="services")


# ─── Appointments ─────────────────────────────────────────────────

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"))
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id", ondelete="SET NULL"))
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"))

    customer_name = Column(String(255))
    customer_phone = Column(String(20))
    customer_email = Column(String(255))

    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer)
    status = Column(String(20), default="pending")  # pending, confirmed, completed, cancelled, no_show
    notes = Column(Text)
    reminder_sent = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    tenant = relationship("Tenant", back_populates="appointments")

    __table_args__ = (
        Index("ix_appointments_tenant_date", "tenant_id", "scheduled_at"),
    )


# ─── Leads ────────────────────────────────────────────────────────

class Lead(Base):
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"))
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"))

    name = Column(String(255))
    phone = Column(String(20))
    email = Column(String(255))
    source = Column(String(50))  # whatsapp, web, voice
    status = Column(String(20), default="new")  # new, contacted, qualified, converted, lost
    score = Column(Integer, default=0)  # 0-100
    interest = Column(String(255))
    notes = Column(Text)
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    tenant = relationship("Tenant", back_populates="leads")

    __table_args__ = (
        Index("ix_leads_tenant_status", "tenant_id", "status"),
    )


# ─── Analytics Events ────────────────────────────────────────────

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(50), nullable=False)  # message_sent, appointment_booked, lead_captured, etc.
    event_data = Column(JSONB, default={})
    channel = Column(String(20))
    created_at = Column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        Index("ix_analytics_tenant_type_date", "tenant_id", "event_type", "created_at"),
    )
