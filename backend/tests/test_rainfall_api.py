"""
backend/tests/test_rainfall_api.py
API tests for rainfall endpoints.
"""

from datetime import datetime, timezone
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_get_rainfall_records():
    response = client.get("/rainfall/?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert isinstance(data["data"], list)


def test_post_rainfall_record():
    payload = {
        "observation_time": datetime.now(timezone.utc).isoformat(),
        "source": "STATION",
        "rainfall_mm": 18.5,
        "duration_minutes": 60,
        "station_code": "BLR_CENTRAL",
        "latitude": 12.9716,
        "longitude": 77.5946,
    }
    response = client.post("/rainfall/", json=payload)
    assert response.status_code in [200, 201]
    res_data = response.json()
    assert res_data["status"] == "success"
    assert "id" in res_data
