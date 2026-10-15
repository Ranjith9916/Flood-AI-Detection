"""
backend/tests/test_flood_api.py
API tests for flood and inundation prediction endpoints.
"""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_get_flood_predictions():
    response = client.get("/predictions/flood?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert isinstance(data["data"], list)


def test_get_inundation_predictions():
    response = client.get("/predictions/inundation?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert isinstance(data["data"], list)


def test_get_heavy_rain_predictions():
    response = client.get("/predictions/heavy-rain")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["success", "unavailable"]
    assert "data" in data
    assert isinstance(data["data"], list)
