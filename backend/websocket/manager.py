"""WebSocket manager."""
import asyncio
import logging
from typing import Dict, Optional

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        """Accept and track a WebSocket connection."""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected: {session_id}")

    def disconnect(self, session_id: str):
        """Remove a WebSocket connection."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected: {session_id}")

    async def send(self, session_id: str, data: dict | bytes):
        """Send data to a specific session."""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            if isinstance(data, bytes):
                await websocket.send_bytes(data)
            else:
                await websocket.send_json(data)

    async def broadcast(self, data: dict | bytes):
        """Broadcast to all connected sessions."""
        for session_id, websocket in self.active_connections.items():
            try:
                if isinstance(data, bytes):
                    await websocket.send_bytes(data)
                else:
                    await websocket.send_json(data)
            except Exception as e:
                logger.error(f"Error broadcasting to {session_id}: {e}")


# Global connection manager instance
manager = ConnectionManager()