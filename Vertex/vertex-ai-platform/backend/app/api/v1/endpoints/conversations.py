"""Conversation and messaging endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.schemas import (
    MessageRequest, MessageResponse, ConversationResponse,
)
from app.services.conversation_service import conversation_service

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get("/")
async def list_conversations(
    status: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all conversations for the tenant."""
    conversations = await conversation_service.get_conversations(
        db=db,
        tenant_id=current_user["tenant_id"],
        status=status,
        channel=channel,
        limit=limit,
        offset=offset,
    )
    return conversations


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a conversation with all messages."""
    conversation = await conversation_service.get_conversation_with_messages(
        db=db,
        conversation_id=str(conversation_id),
        tenant_id=current_user["tenant_id"],
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: UUID,
    request: MessageRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message in a conversation and get AI response."""
    message = await conversation_service.process_message(
        db=db,
        conversation_id=str(conversation_id),
        content=request.content,
        channel=request.channel,
    )
    return message
