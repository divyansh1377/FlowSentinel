"""
FlowSentinel - Team 2 (Backend & Architecture)
Async WebSocket Connection Manager & Broadcast Hub
"""

import json
from typing import List, Set
from fastapi import WebSocket

class WebSocketHub:
    """
    Manages active client connections and dispatches broadcast frames.
    """

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        print(f"🔌 [WebSocketHub] Client connected. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"🔌 [WebSocketHub] Client disconnected. Total active: {len(self.active_connections)}")

    async def broadcast_json(self, message_type: str, data: dict):
        """
        Broadcast structured message to all connected clients.
        """
        if not self.active_connections:
            return

        payload = {
            "type": message_type,
            "data": data
        }
        text_data = json.dumps(payload)

        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(text_data)
            except Exception:
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)

    async def send_direct_json(self, websocket: WebSocket, message_type: str, data: dict):
        """
        Send direct reply to a specific websocket client.
        """
        payload = {
            "type": message_type,
            "data": data
        }
        await websocket.send_text(json.dumps(payload))

ws_hub = WebSocketHub()

