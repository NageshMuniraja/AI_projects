"""Knowledge base management endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.models import KnowledgeDocument
from app.schemas.schemas import KnowledgeDocumentCreate, KnowledgeDocumentResponse
from app.ai_engine.rag import rag_pipeline

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])


@router.get("/", response_model=list[KnowledgeDocumentResponse])
async def list_documents(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all knowledge base documents."""
    result = await db.execute(
        select(KnowledgeDocument)
        .where(KnowledgeDocument.tenant_id == current_user["tenant_id"])
        .order_by(KnowledgeDocument.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=KnowledgeDocumentResponse, status_code=201)
async def create_document(
    request: KnowledgeDocumentCreate,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Add a new document to the knowledge base."""
    doc = await rag_pipeline.ingest_document(
        db=db,
        tenant_id=current_user["tenant_id"],
        title=request.title,
        content=request.content,
        category=request.category or "general",
        source_type=request.source_type,
    )
    return doc


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: uuid.UUID,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Remove a document from the knowledge base."""
    result = await db.execute(
        select(KnowledgeDocument).where(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.tenant_id == current_user["tenant_id"],
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.is_active = False
    await db.flush()
