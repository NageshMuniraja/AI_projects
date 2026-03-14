"""API v1 router — aggregates all endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth, tenants, conversations, services,
    appointments, leads, knowledge, analytics,
    webhooks, chat,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(tenants.router)
api_router.include_router(conversations.router)
api_router.include_router(services.router)
api_router.include_router(appointments.router)
api_router.include_router(leads.router)
api_router.include_router(knowledge.router)
api_router.include_router(analytics.router)
api_router.include_router(webhooks.router)
api_router.include_router(chat.router)
