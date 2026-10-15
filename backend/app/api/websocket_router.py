"""
backend/app/api/websocket_router.py
FastAPI WebSocket endpoints for live telemetry, early warnings, and simulation streaming.
"""

import asyncio
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from backend.app.core.websocket_manager import ws_manager

logger = logging.getLogger("WebSocketRouter")
router = APIRouter(tags=["WebSockets"])


@router.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket, channel: str = Query("all")):
    """
    Bidirectional WebSocket connection for live telemetry heartbeats and real-time alert broadcasts.
    Supports channel subscriptions: 'all', 'alerts', 'telemetry', 'simulations'.
    """
    await ws_manager.connect(websocket, channel=channel)
    try:
        # Send initial connection handshake
        await ws_manager.send_personal_message(
            {
                "type": "HANDSHAKE",
                "status": "CONNECTED",
                "channel": channel,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": "Connected to Flood AI Real-Time Telemetry & Warning Stream",
            },
            websocket,
        )

        # Listen for client messages / pings
        while True:
            data = await websocket.receive_text()
            # Respond to client ping with pong heartbeat
            if "ping" in data.lower():
                await ws_manager.send_personal_message(
                    {
                        "type": "PONG",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    websocket,
                )
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, channel=channel)
    except Exception as exc:
        logger.warning(f"WebSocket connection error: {exc}")
        await ws_manager.disconnect(websocket, channel=channel)


@router.websocket("/ws/alerts")
async def websocket_alerts_endpoint(websocket: WebSocket):
    """
    Dedicated channel exclusively for emergency flood warnings and heavy rain alarm dispatches.
    """
    await ws_manager.connect(websocket, channel="alerts")
    try:
        await ws_manager.send_personal_message(
            {
                "type": "HANDSHAKE",
                "channel": "alerts",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": "Subscribed to Emergency Alert Dispatch Channel",
            },
            websocket,
        )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, channel="alerts")
    except Exception:
        await ws_manager.disconnect(websocket, channel="alerts")
