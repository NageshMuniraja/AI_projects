"""WebSocket connection manager for real-time messaging."""

import json
from typing import Optional
from fastapi import WebSocket
import structlog

logger = structlog.get_logger()


class ConnectionManager:
    """Manages active WebSocket connections per tenant and conversation."""

    def __init__(self):
        # {tenant_id: {conversation_id: [WebSocket]}}
        self.active_connections: dict[str, dict[str, list[WebSocket]]] = {}
        # {tenant_id: [WebSocket]} — dashboard connections
        self.dashboard_connections: dict[str, list[WebSocket]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        tenant_id: str,
        conversation_id: Optional[str] = None,
        is_dashboard: bool = False,
    ):
        """Accept a WebSocket connection."""
        await websocket.accept()

        if is_dashboard:
            self.dashboard_connections.setdefault(tenant_id, []).append(websocket)
            logger.info("Dashboard WS connected", tenant=tenant_id)
        elif conversation_id:
            self.active_connections.setdefault(tenant_id, {})
            self.active_connections[tenant_id].setdefault(conversation_id, []).append(websocket)
            logger.info("Chat WS connected", tenant=tenant_id, conversation=conversation_id)

    def disconnect(
        self,
        websocket: WebSocket,
        tenant_id: str,
        conversation_id: Optional[str] = None,
        is_dashboard: bool = False,
    ):
        """Remove a WebSocket connection."""
        if is_dashboard:
            conns = self.dashboard_connections.get(tenant_id, [])
            if websocket in conns:
                conns.remove(websocket)
        elif conversation_id:
            conns = self.active_connections.get(tenant_id, {}).get(conversation_id, [])
            if websocket in conns:
                conns.remove(websocket)

    async def send_to_conversation(
        self,
        tenant_id: str,
        conversation_id: str,
        message: dict,
    ):
        """Send a message to all connections in a conversation."""
        connections = self.active_connections.get(tenant_id, {}).get(conversation_id, [])
        disconnected = []
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)

        for ws in disconnected:
            self.disconnect(ws, tenant_id, conversation_id)

    async def send_to_dashboard(self, tenant_id: str, event: dict):
        """Send a real-time event to the tenant's dashboard."""
        connections = self.dashboard_connections.get(tenant_id, [])
        disconnected = []
        for ws in connections:
            try:
                await ws.send_json(event)
            except Exception:
                disconnected.append(ws)

        for ws in disconnected:
            self.disconnect(ws, tenant_id, is_dashboard=True)

    async def broadcast_typing(
        self,
        tenant_id: str,
        conversation_id: str,
        is_typing: bool,
        sender: str = "assistant",
    ):
        """Broadcast typing indicator."""
        await self.send_to_conversation(
            tenant_id,
            conversation_id,
            {"type": "typing", "is_typing": is_typing, "sender": sender},
        )


# Singleton
ws_manager = ConnectionManager()
