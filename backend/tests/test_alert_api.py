"""
backend/tests/test_alert_api.py
API tests for alert endpoints.
"""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_get_alerts():
    response = client.get("/alerts/?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert isinstance(data["data"], list)


def test_get_active_alerts():
    response = client.get("/alerts/active")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert isinstance(data["data"], list)
