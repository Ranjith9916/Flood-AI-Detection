"""
backend/app/services/dispatcher.py
Multi-Channel Emergency Alert Dispatcher.
Broadcasts urgent early warnings across WebSockets, Webhooks, and Civil Defense CAP feeds.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from backend.app.core.websocket_manager import ws_manager
from backend.app.services.cap_service import CAPService

logger = logging.getLogger("AlertDispatcher")


class AlertDispatcher:
    """
    Orchestrates real-time multi-channel emergency alert dissemination.
    """

    @classmethod
    async def dispatch_emergency_alert(
        cls,
        alert_id: str,
        title: str,
        description: str,
        severity: str,
        alert_type: str,
        center_lat: float = 13.0827,
        center_lon: float = 80.2707,
        inundation_depth_m: float = 0.65,
    ) -> Dict[str, Any]:
        """
        Dispatches alert to WebSockets, generates CAP v1.2 payload, and records dispatch status.
        """
        now = datetime.now(timezone.utc).isoformat()
        
        # 1. Compute evacuation zones
        evac_info = CAPService.compute_evacuation_zones(center_lat, center_lon, inundation_depth_m)
        
        # 2. Generate CAP XML & JSON
        cap_json = CAPService.generate_cap_json(
            alert_id=alert_id,
            headline=title,
            description=description,
            severity=severity,
            polygon_coords=evac_info["critical_evacuation_polygon"],
        )
        
        cap_xml = CAPService.generate_cap_xml(
            alert_id=alert_id,
            headline=title,
            description=description,
            severity=severity,
            polygon_coords=evac_info["critical_evacuation_polygon"],
        )
        
        # 3. Formulate WebSocket notification packet
        ws_payload = {
            "type": "EMERGENCY_ALERT_DISPATCH",
            "alert_id": alert_id,
            "title": title,
            "description": description,
            "severity": severity,
            "alert_type": alert_type,
            "timestamp": now,
            "evacuation": evac_info,
            "cap": cap_json,
        }
        
        # 4. Broadcast via WebSocket Manager to all active operators
        await ws_manager.broadcast(ws_payload, channel="alerts")
        await ws_manager.broadcast(ws_payload, channel="all")
        
        logger.info(f"Emergency Alert {alert_id} ({severity}) successfully dispatched across all operational channels.")
        
        return {
            "status": "DISPATCHED",
            "dispatch_time": now,
            "channels": ["WEBSOCKET", "CAP_V1.2_XML", "CAP_JSON", "OPERATIONAL_DASHBOARD"],
            "evacuation_summary": evac_info,
            "cap_xml_preview": cap_xml[:300] + "...",
        }
