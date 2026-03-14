"""Vertex AI Platform — Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import structlog

from app.core.config import get_settings
from app.api.v1.router import api_router
from app.channels.websocket_manager import ws_manager
from app.services.conversation_service import conversation_service
from app.core.database import engine, Base, AsyncSessionLocal

settings = get_settings()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    logger.info("Starting Vertex AI Platform", version=settings.APP_VERSION)
    # Create tables (for development — use Alembic migrations in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    logger.info("Shutting down Vertex AI Platform")
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise Vertical AI Agent Platform — Deploy industry-specific AI assistants across WhatsApp, Web Chat, and Voice.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(api_router, prefix=settings.API_PREFIX)


# ─── Health Check ────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "service": settings.APP_NAME,
    }


# ─── WebSocket: Widget Chat ─────────────────────────────────────

@app.websocket("/ws/chat/{tenant_slug}")
async def websocket_chat(
    websocket: WebSocket,
    tenant_slug: str,
    conversation_id: str = Query(None),
):
    """WebSocket endpoint for real-time widget chat."""
    from sqlalchemy import select
    from app.models.models import Tenant

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Tenant).where(Tenant.slug == tenant_slug, Tenant.status == "active")
        )
        tenant = result.scalar_one_or_none()
        if not tenant:
            await websocket.close(code=4004)
            return

        tenant_id = str(tenant.id)

    # If no conversation_id, create one
    if not conversation_id:
        async with AsyncSessionLocal() as db:
            conv, _ = await conversation_service.get_or_create_conversation(
                db=db, tenant_id=tenant_id, channel="web"
            )
            conversation_id = str(conv.id)
            await db.commit()

    await ws_manager.connect(websocket, tenant_id, conversation_id)

    # Send greeting
    await websocket.send_json({
        "type": "system",
        "content": tenant.greeting_message or f"Hi! I'm {tenant.ai_persona_name}. How can I help you?",
        "conversation_id": conversation_id,
    })

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "message":
                # Show typing indicator
                await ws_manager.broadcast_typing(tenant_id, conversation_id, True)

                # Process message
                async with AsyncSessionLocal() as db:
                    ai_message = await conversation_service.process_message(
                        db=db,
                        conversation_id=conversation_id,
                        content=data["content"],
                        channel="web",
                    )
                    await db.commit()

                    # Stop typing and send response
                    await ws_manager.broadcast_typing(tenant_id, conversation_id, False)
                    await ws_manager.send_to_conversation(
                        tenant_id,
                        conversation_id,
                        {
                            "type": "message",
                            "role": "assistant",
                            "content": ai_message.content,
                            "message_id": str(ai_message.id),
                            "timestamp": ai_message.created_at.isoformat(),
                        },
                    )

                    # Notify dashboard
                    await ws_manager.send_to_dashboard(
                        tenant_id,
                        {
                            "type": "new_message",
                            "conversation_id": conversation_id,
                            "preview": ai_message.content[:100],
                        },
                    )

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, tenant_id, conversation_id)


# ─── WebSocket: Dashboard Real-time ─────────────────────────────

@app.websocket("/ws/dashboard")
async def websocket_dashboard(
    websocket: WebSocket,
    token: str = Query(...),
):
    """WebSocket for real-time dashboard updates."""
    from app.core.security import decode_token

    try:
        payload = decode_token(token)
        tenant_id = payload.get("tenant_id")
        if not tenant_id:
            await websocket.close(code=4001)
            return
    except Exception:
        await websocket.close(code=4001)
        return

    await ws_manager.connect(websocket, tenant_id, is_dashboard=True)

    try:
        while True:
            # Dashboard mostly receives events, but can send commands
            data = await websocket.receive_json()
            # Handle dashboard commands (e.g., take over conversation)
            if data.get("type") == "takeover":
                # Human takeover of AI conversation
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, tenant_id, is_dashboard=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
