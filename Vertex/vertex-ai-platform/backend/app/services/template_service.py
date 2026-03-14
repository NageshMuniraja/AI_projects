"""Industry template loader — seeds new tenants with pre-configured data."""

import json
import uuid
from pathlib import Path
from typing import Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Tenant, Service, KnowledgeDocument
from app.ai_engine.rag import rag_pipeline

logger = structlog.get_logger()

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "industry_templates"


def load_template(industry: str) -> Optional[dict]:
    """Load an industry template configuration."""
    template_path = TEMPLATES_DIR / industry / "config.json"
    if not template_path.exists():
        logger.warning("Template not found", industry=industry)
        return None
    with open(template_path) as f:
        return json.load(f)


async def apply_template(
    db: AsyncSession,
    tenant: Tenant,
    industry: str,
) -> None:
    """Apply an industry template to a tenant — seeds services and knowledge base."""
    template = load_template(industry)
    if not template:
        return

    logger.info("Applying template", industry=industry, tenant=str(tenant.id))

    # Update tenant AI config
    tenant.ai_persona_name = template.get("ai_persona_name", "AI Assistant")
    tenant.ai_tone = template.get("ai_tone", "professional")
    tenant.greeting_message = template.get("greeting_message")
    tenant.fallback_message = template.get("fallback_message")
    tenant.business_hours = template.get("business_hours", {})

    # Seed services
    for svc_data in template.get("services", []):
        service = Service(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            name=svc_data["name"],
            description=svc_data.get("description"),
            duration_minutes=svc_data.get("duration_minutes"),
            price=svc_data.get("price"),
            currency=svc_data.get("currency", "INR"),
            category=svc_data.get("category"),
        )
        db.add(service)

    # Seed knowledge base
    for kb_data in template.get("knowledge_base", []):
        await rag_pipeline.ingest_document(
            db=db,
            tenant_id=str(tenant.id),
            title=kb_data["title"],
            content=kb_data["content"],
            category=kb_data.get("category", "general"),
            source_type="template",
        )

    await db.flush()
    logger.info(
        "Template applied",
        industry=industry,
        services=len(template.get("services", [])),
        knowledge_docs=len(template.get("knowledge_base", [])),
    )
