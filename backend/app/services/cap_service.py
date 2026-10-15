"""
backend/app/services/cap_service.py
OASIS Common Alerting Protocol (CAP v1.2) Standard Generator.
Converts Flood and Heavy Rain Early Warnings into internationally compliant CAP XML/JSON messages
for dissemination to Civil Protection, NDMA, and emergency first responders.
"""

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid


class CAPService:
    """
    Common Alerting Protocol (CAP v1.2) serialization and evacuation zone engine.
    """

    CAP_XMLNS = "urn:oasis:names:tc:emergency:cap:1.2"

    @classmethod
    def generate_cap_xml(
        cls,
        alert_id: str,
        headline: str,
        description: str,
        severity: str,
        urgency: str = "Immediate",
        certainty: str = "Observed",
        event_code: str = "FLW",  # Flood Warning
        polygon_coords: Optional[List[List[float]]] = None,
        sender: str = "FloodAI.Operations.CommandCenter@gov.in",
        contact: str = "Emergency Operations Command (Toll-Free 1070)",
    ) -> str:
        """
        Generates standard OASIS CAP v1.2 XML string.
        """
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        
        root = ET.Element("alert", xmlns=cls.CAP_XMLNS)
        
        ET.SubElement(root, "identifier").text = f"FLOOD-AI-CAP-{alert_id}"
        ET.SubElement(root, "sender").text = sender
        ET.SubElement(root, "sent").text = now
        ET.SubElement(root, "status").text = "Actual"
        ET.SubElement(root, "msgType").text = "Alert"
        ET.SubElement(root, "scope").text = "Public"
        
        info = ET.SubElement(root, "info")
        ET.SubElement(info, "category").text = "Met"
        ET.SubElement(info, "event").text = "Heavy Rainfall & Inundation Warning"
        ET.SubElement(info, "urgency").text = urgency
        ET.SubElement(info, "severity").text = severity
        ET.SubElement(info, "certainty").text = certainty
        
        event_code_el = ET.SubElement(info, "eventCode")
        ET.SubElement(event_code_el, "valueName").text = "SAME"
        ET.SubElement(event_code_el, "value").text = event_code
        
        ET.SubElement(info, "headline").text = headline
        ET.SubElement(info, "description").text = description
        ET.SubElement(info, "instruction").text = (
            "Move valuable assets and livestock to elevated ground. "
            "Avoid low-lying subways and riverbanks. Do not drive through flooded roadways. "
            "Follow instructions from local disaster management personnel."
        )
        ET.SubElement(info, "contact").text = contact
        
        # Area Geo-fencing
        area = ET.SubElement(info, "area")
        ET.SubElement(area, "areaDesc").text = "High-Risk Hydro-Geomorphic Catchment Basin"
        
        if polygon_coords and len(polygon_coords) >= 3:
            # CAP format is "lat,lon lat,lon ..."
            poly_str = " ".join([f"{p[0]:.4f},{p[1]:.4f}" for p in polygon_coords])
            ET.SubElement(area, "polygon").text = poly_str
            
        return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

    @classmethod
    def generate_cap_json(
        cls,
        alert_id: str,
        headline: str,
        description: str,
        severity: str,
        polygon_coords: Optional[List[List[float]]] = None,
    ) -> Dict[str, Any]:
        """
        Generates standard CAP v1.2 JSON payload.
        """
        now = datetime.now(timezone.utc).isoformat()
        return {
            "identifier": f"FLOOD-AI-CAP-{alert_id}",
            "sender": "FloodAI.Operations.CommandCenter@gov.in",
            "sent": now,
            "status": "Actual",
            "msgType": "Alert",
            "scope": "Public",
            "info": [
                {
                    "category": ["Met", "Safety"],
                    "event": "Heavy Rainfall & Inundation Warning",
                    "urgency": "Immediate",
                    "severity": severity,
                    "certainty": "Observed",
                    "headline": headline,
                    "description": description,
                    "instruction": "Evacuate designated low-lying zones immediately. Follow emergency protocols.",
                    "area": [
                        {
                            "areaDesc": "Flood Vulnerability Zone",
                            "polygon": polygon_coords or [],
                        }
                    ],
                }
            ],
        }

    @classmethod
    def compute_evacuation_zones(cls, center_lat: float, center_lon: float, inundation_depth_m: float) -> Dict[str, Any]:
        """
        Computes multi-tier evacuation polygons and population vulnerability estimate based on inundation depth.
        """
        # Define radius scale based on depth
        scale = max(0.015, min(0.05, inundation_depth_m * 0.025))
        
        # Red Tier (Immediate Evacuation: > 1.0m depth)
        red_poly = [
            [center_lat + scale, center_lon + scale],
            [center_lat + scale, center_lon - scale],
            [center_lat - scale, center_lon - scale],
            [center_lat - scale, center_lon + scale],
            [center_lat + scale, center_lon + scale],
        ]
        
        # Yellow Tier (Caution / Standby: 0.3m - 1.0m depth)
        yellow_scale = scale * 1.6
        yellow_poly = [
            [center_lat + yellow_scale, center_lon + yellow_scale],
            [center_lat + yellow_scale, center_lon - yellow_scale],
            [center_lat - yellow_scale, center_lon - yellow_scale],
            [center_lat - yellow_scale, center_lon + yellow_scale],
            [center_lat + yellow_scale, center_lon + yellow_scale],
        ]

        est_population_at_risk = int(inundation_depth_m * 14500) if inundation_depth_m > 0.1 else 0

        return {
            "critical_evacuation_polygon": red_poly,
            "caution_standby_polygon": yellow_poly,
            "estimated_population_at_risk": est_population_at_risk,
            "critical_infrastructure_at_risk": [
                {"name": "District General Hospital", "distance_m": 420, "vulnerability": "HIGH" if inundation_depth_m > 0.5 else "LOW"},
                {"name": "Central Power Substation 220kV", "distance_m": 850, "vulnerability": "CRITICAL" if inundation_depth_m > 0.8 else "MODERATE"},
                {"name": "Metro Transit Interchange", "distance_m": 310, "vulnerability": "HIGH" if inundation_depth_m > 0.3 else "LOW"},
            ]
        }
