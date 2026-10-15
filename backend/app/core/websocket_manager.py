"""
backend/app/core/websocket_manager.py
Connection manager for real-time WebSocket communication.
Handles client connections, channel subscriptions, heartbeats, and broadcasting.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Set
from fastapi import WebSocket

logger = logging.getLogger("WebSocketManager")


class ConnectionManager:
    """
    Manages active WebSocket connections, channel topics, and message broadcasting.
    """

    def __init__(self):
        # Map channel name -> set of active WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "all": set(),
            "alerts": set(),
            "telemetry": set(),
            "simulations": set(),
        }
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, channel: str = "all"):
        """Accepts WebSocket connection and subscribes to specified channel."""
        await websocket.accept()
        async with self._lock:
            if channel not in self.active_connections:
                self.active_connections[channel] = set()
            self.active_connections[channel].add(websocket)
            self.active_connections["all"].add(websocket)
        logger.info(f"WebSocket client connected to channel '{channel}'. Total active: {len(self.active_connections['all'])}")

    async def disconnect(self, websocket: WebSocket, channel: str = "all"):
        """Removes disconnected WebSocket from channels."""
        async with self._lock:
            if channel in self.active_connections:
                self.active_connections[channel].discard(websocket)
            self.active_connections["all"].discard(websocket)
        logger.info(f"WebSocket client disconnected from '{channel}'. Total active: {len(self.active_connections['all'])}")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Sends JSON message to a single WebSocket client."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as exc:
            logger.warning(f"Failed to send personal WS message: {exc}")

    async def broadcast(self, message: Dict[str, Any], channel: str = "all"):
        """Broadcasts a JSON message to all subscribers of a channel."""
        targets = list(self.active_connections.get(channel, set()))
        if channel != "all":
            # Also include clients subscribed to 'all'
            targets = list(set(targets).union(self.active_connections.get("all", set())))

        dead_connections: List[WebSocket] = []
        payload = json.dumps(message)

        for connection in targets:
            try:
                await connection.send_text(payload)
            except Exception as exc:
                logger.warning(f"Error broadcasting to WS client: {exc}")
                dead_connections.append(connection)

        if dead_connections:
            async with self._lock:
                for dead in dead_connections:
                    for ch in self.active_connections.values():
                        ch.discard(dead)


# Global singleton instance
ws_manager = ConnectionManager()
