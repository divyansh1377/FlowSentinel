"""
FlowSentinel - Team 2 (Backend & Architecture)
Async WebSocket Connection Manager & Broadcast Hub
"""

import json
import logging
from typing import Set, Dict, Any, Optional
from fastapi import WebSocket

logger = logging.getLogger("FlowSentinel.WebSocketHub")


class WebSocketHub:
    """
    Manages active client connections and dispatches broadcast frames.
    Thread-safe and async-safe connection handling with dead socket cleanup.
    """

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    @property
    def client_count(self) -> int:
        return len(self.active_connections)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(
            f"🔌 [WebSocketHub] Client connected. Total active: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(
                f"🔌 [WebSocketHub] Client disconnected. Total active: {len(self.active_connections)}"
            )

    async def broadcast_json(self, message_type: str, data: Dict[str, Any]):
        """
        Broadcast structured message to all connected clients.
        Automatically purges stale or dropped connections.
        """
        if not self.active_connections:
            return

        payload = {"type": message_type, "data": data}
        text_data = json.dumps(payload)

        dead_connections = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(text_data)
            except Exception as e:
                logger.warning(
                    f"⚠️ [WebSocketHub] Failed to send to client, marking for cleanup: {e}"
                )
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)

    async def send_direct_json(
        self, websocket: WebSocket, message_type: str, data: Dict[str, Any]
    ):
        """
        Send direct reply to a specific websocket client.
        """
        payload = {"type": message_type, "data": data}
        await websocket.send_text(json.dumps(payload))


ws_hub = WebSocketHub()
