"""
backend/tests/test_simulation_and_cap.py
Unit and integration tests for Phase 7 features:
- Interactive 'What-If' Simulation Engine
- OASIS Common Alerting Protocol (CAP v1.2)
- Multi-channel Emergency Alert Dispatcher
- Executive Disaster Incident Report Generator
"""

import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.alert import Alert
from backend.app.services.cap_service import CAPService
from backend.app.services.simulation_service import SimulationEngine
from backend.app.services.report_service import ReportService

client = TestClient(app)


def test_simulation_presets():
    """Test retrieving standard extreme weather simulation presets."""
    response = client.get("/simulations/presets")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "100_year_cloudburst" in data["data"]
    assert "cyclone_heavy_band" in data["data"]
    assert data["count"] >= 4


def test_run_simulation_engine():
    """Test running on-demand hydrological runoff and inundation contour simulation."""
    payload = {
        "rainfall_intensity_mmh": 100.0,
        "duration_hours": 3,
        "antecedent_moisture_condition": "AMC-III",
        "reservoir_discharge_cumecs": 500.0,
        "urban_drainage_blockage_pct": 25.0,
        "center_lat": 13.0827,
        "center_lon": 80.2707,
    }
    response = client.post("/simulations/run", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "success"
    sim = res["data"]
    assert sim["inputs"]["total_precipitation_mm"] == 300.0
    assert sim["hydrology_summary"]["peak_water_depth_m"] > 0.5
    assert len(sim["timeline"]) == 6  # T+0 to T+6h
    # Verify GeoJSON contours exist for T+3h
    t3 = [step for step in sim["timeline"] if step["timestep_hours"] == 3][0]
    assert len(t3["geojson_features"]) > 0


def test_cap_service_xml_and_zones():
    """Test CAP v1.2 XML generation and evacuation zone computation."""
    evac = CAPService.compute_evacuation_zones(center_lat=13.0827, center_lon=80.2707, inundation_depth_m=1.2)
    assert len(evac["critical_evacuation_polygon"]) >= 4
    assert evac["estimated_population_at_risk"] > 0
    assert len(evac["critical_infrastructure_at_risk"]) >= 3

    xml = CAPService.generate_cap_xml(
        alert_id="TEST-ALERT-001",
        headline="CRITICAL Flood Warning",
        description="Extreme inundation approaching urban sectors.",
        severity="Extreme",
        polygon_coords=evac["critical_evacuation_polygon"],
    )
    assert "<alert" in xml
    assert "urn:oasis:names:tc:emergency:cap:1.2" in xml
    assert "TEST-ALERT-001" in xml
    assert "<polygon>" in xml


def test_executive_report_generation():
    """Test post-event executive disaster briefing generator."""
    report = ReportService.generate_incident_report(
        event_name="Test Monsoon Surge",
        peak_rainfall_mm=210.0,
        peak_depth_m=1.35,
        affected_area_km2=15.0,
    )
    assert "REP-INCIDENT-" in report["report_id"]
    assert report["meteorological_summary"]["24h_peak_accumulation_mm"] == 210.0
    assert len(report["recommendations"]) >= 3


def test_historical_api_and_report_endpoint():
    """Test historical events catalog and report generation API."""
    # 1. Catalog
    resp = client.get("/historical/events")
    assert resp.status_code == 200
    catalog = resp.json()
    assert catalog["status"] == "success"
    assert catalog["count"] > 0

    # 2. Executive report
    rep_resp = client.get("/historical/reports/generate?peak_rainfall_mm=190&peak_depth_m=1.1")
    assert rep_resp.status_code == 200
    assert rep_resp.json()["status"] == "success"


def test_alert_cap_and_dispatch_endpoints():
    """Test CAP XML export and alert dispatch endpoints with a test alert in DB."""
    session = SessionLocal()
    alert_id = uuid.uuid4()
    test_alert = Alert(
        id=alert_id,
        alert_type="FLOOD_WARNING",
        severity="SEVERE_WARNING",
        message="Simulated rapid inundation test alert.",
        is_active=True,
        alert_time=datetime.now(timezone.utc),
    )
    try:
        session.add(test_alert)
        session.commit()

        # 1. Test CAP XML endpoint
        cap_resp = client.get(f"/alerts/{alert_id}/cap.xml")
        assert cap_resp.status_code == 200
        assert "application/xml" in cap_resp.headers["content-type"]
        assert f"FLOOD-AI-CAP-{alert_id}" in cap_resp.text

        # 2. Test Multi-channel dispatch endpoint
        disp_resp = client.post(f"/alerts/{alert_id}/dispatch")
        assert disp_resp.status_code == 200
        disp_data = disp_resp.json()
        assert disp_data["status"] == "success"
        assert disp_data["data"]["status"] == "DISPATCHED"
    finally:
        session.query(Alert).filter(Alert.id == alert_id).delete()
        session.commit()
        session.close()
