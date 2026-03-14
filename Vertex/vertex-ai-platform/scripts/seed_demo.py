"""Seed script — creates a demo tenant with industry template data."""

import asyncio
import uuid
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.core.database import AsyncSessionLocal, engine, Base
from app.core.security import hash_password
from app.models.models import Tenant, User
from app.services.template_service import apply_template


async def seed():
    """Create demo tenants for each industry."""
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        industries = ["dental", "salon", "clinic", "real_estate"]

        for industry in industries:
            slug = f"demo-{industry}"

            # Create tenant
            tenant = Tenant(
                id=uuid.uuid4(),
                name=f"Demo {industry.replace('_', ' ').title()}",
                slug=slug,
                industry=industry,
                plan="growth",
                business_name=f"Demo {industry.replace('_', ' ').title()}",
                business_email=f"demo@{industry}.vertex.ai",
                business_phone="+91 98765 43210",
                monthly_message_limit=5000,
            )
            db.add(tenant)
            await db.flush()

            # Create owner user
            user = User(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                email=f"admin@{industry}.demo",
                hashed_password=hash_password("demo1234"),
                full_name=f"Demo Admin ({industry.title()})",
                role="owner",
            )
            db.add(user)

            # Apply industry template
            await apply_template(db, tenant, industry)

            print(f"Created demo tenant: {slug}")
            print(f"  Login: admin@{industry}.demo / demo1234")

        await db.commit()
        print("\nDemo seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
