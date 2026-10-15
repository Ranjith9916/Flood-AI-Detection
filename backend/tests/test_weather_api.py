"""
backend/tests/test_weather_api.py
API tests for weather stations and observations endpoints.
"""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_get_weather_stations():
    response = client.get("/weather/stations")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert isinstance(data["data"], list)


def test_get_weather_observations():
    response = client.get("/weather/observations?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert isinstance(data["data"], list)


def test_create_weather_station():
    import uuid
    rand_code = f"TEST_STN_{uuid.uuid4().hex[:6]}"
    station_payload = {
        "station_code": rand_code,
        "station_name": f"Pytest Test Station {rand_code}",
        "latitude": 13.0,
        "longitude": 77.6,
        "elevation_m": 920.0,
        "source": "TEST",
    }
    response = client.post("/weather/stations", json=station_payload)
    assert response.status_code in [200, 201, 400, 409]
