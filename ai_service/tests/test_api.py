import pytest
import sys
from unittest.mock import MagicMock, patch

# Mock cv2 (OpenCV) which is required by Layer 0 but not installed in this env
sys.modules['cv2'] = MagicMock()

from fastapi.testclient import TestClient
from ai_service.api import app

client = TestClient(app)

# Helper mock for Layer4Service
def get_mock_service():
    mock_service = MagicMock()
    # Default successful route response
    mock_service.route.return_value = {
        "status": "SUCCESS",
        "route_geometry": [[13.1, 80.1], [13.2, 80.2]],
        "total_distance_m": 1500.0,
        "eta_min": 5.0
    }
    
    # Default successful assets response
    mock_service.get_asset_status.return_value = {
        "status": "SUCCESS",
        "total_monitored": 20,
        "assets": [
            {
                "substation_id": f"SS-{i}",
                "status": "UNKNOWN",
                "uncertainty": "PLINTH_UNKNOWN",
                "maximum_site_depth_cm": 15.0
            } for i in range(1, 21)
        ]
    }
    return mock_service

@pytest.fixture
def mock_layer4():
    with patch("ai_service.api.get_layer4_service", return_value=get_mock_service()) as mock:
        yield mock

# --- POST /route Tests ---

def test_route_valid(mock_layer4):
    # 1. valid route
    response = client.post(
        "/route",
        json={
            "vehicle_type": "ambulance",
            "origin": {"latitude": 13.0, "longitude": 80.0},
            "destination": {"latitude": 13.1, "longitude": 80.1}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert "route_geometry" in data

def test_route_invalid_vehicle(mock_layer4):
    # 2. invalid vehicle (simulate failure in engine)
    mock_layer4.return_value.route.return_value = {
        "status": "FAILED",
        "failure_reason": "Invalid vehicle type"
    }
    response = client.post(
        "/route",
        json={
            "vehicle_type": "invalid_boat",
            "origin": {"latitude": 13.0, "longitude": 80.0},
            "destination": {"latitude": 13.1, "longitude": 80.1}
        }
    )
    assert response.status_code == 400
    assert "invalid vehicle" in response.json()["detail"]["failure_reason"].lower()

def test_route_invalid_coordinates(mock_layer4):
    # 3. invalid coordinates
    response = client.post(
        "/route",
        json={
            "vehicle_type": "ambulance",
            "origin": {"latitude": "invalid", "longitude": 80.0},
            "destination": {"latitude": 13.1, "longitude": 80.1}
        }
    )
    # FastAPI/Pydantic returns 422 for unparseable floats
    assert response.status_code == 422

def test_route_missing_origin(mock_layer4):
    # 4. missing origin
    response = client.post(
        "/route",
        json={
            "vehicle_type": "ambulance",
            "destination": {"latitude": 13.1, "longitude": 80.1}
        }
    )
    assert response.status_code == 422

def test_route_missing_destination(mock_layer4):
    # 5. missing destination
    response = client.post(
        "/route",
        json={
            "vehicle_type": "ambulance",
            "origin": {"latitude": 13.0, "longitude": 80.0}
        }
    )
    assert response.status_code == 422

def test_route_invalid_departure_time(mock_layer4):
    # 6. invalid departure time
    response = client.post(
        "/route",
        json={
            "vehicle_type": "ambulance",
            "origin": {"latitude": 13.0, "longitude": 80.0},
            "destination": {"latitude": 13.1, "longitude": 80.1},
            "departure_time": "not_a_time"
        }
    )
    assert response.status_code == 422

def test_route_blocked_no_route(mock_layer4):
    # 7. blocked/no route
    mock_layer4.return_value.route.return_value = {
        "status": "FAILED",
        "failure_reason": "no safe route found"
    }
    response = client.post(
        "/route",
        json={
            "vehicle_type": "ambulance",
            "origin": {"latitude": 13.0, "longitude": 80.0},
            "destination": {"latitude": 13.1, "longitude": 80.1}
        }
    )
    assert response.status_code == 404
    assert "no safe route found" in response.json()["detail"]["failure_reason"].lower()

def test_route_layer3_unavailable(mock_layer4):
    # 8. Layer 3 unavailable/invalid response
    mock_layer4.return_value.route.side_effect = Exception("Layer 3 timeout")
    response = client.post(
        "/route",
        json={
            "vehicle_type": "ambulance",
            "origin": {"latitude": 13.0, "longitude": 80.0},
            "destination": {"latitude": 13.1, "longitude": 80.1}
        }
    )
    assert response.status_code == 500
    assert "Layer 3 timeout" in response.json()["detail"]


# --- GET /assets/status Tests ---

def test_assets_successful(mock_layer4):
    # 1. successful response
    response = client.get("/assets/status")
    assert response.status_code == 200
    assert response.json()["status"] == "SUCCESS"

def test_assets_all_20_returned(mock_layer4):
    # 2. all 20 substations returned
    response = client.get("/assets/status")
    assert response.json()["total_monitored"] == 20
    assert len(response.json()["assets"]) == 20

def test_assets_unknown_plinth_remains_unknown(mock_layer4):
    # 3. unknown plinth remains unknown
    response = client.get("/assets/status")
    assets = response.json()["assets"]
    # We mocked them all to be PLINTH_UNKNOWN
    assert assets[0]["uncertainty"] == "PLINTH_UNKNOWN"
    assert assets[0]["status"] == "UNKNOWN"

def test_assets_missing_flood_data_not_zero(mock_layer4):
    # 4. missing flood data is not treated as zero
    mock_layer4.return_value.get_asset_status.return_value = {
        "status": "SUCCESS",
        "total_monitored": 1,
        "assets": [{
            "substation_id": "SS-1",
            "status": "UNKNOWN",
            "uncertainty": "DATA_UNAVAILABLE",
            "maximum_site_depth_cm": 0.0
        }]
    }
    response = client.get("/assets/status")
    asset = response.json()["assets"][0]
    assert asset["uncertainty"] == "DATA_UNAVAILABLE"
    assert asset["status"] == "UNKNOWN"

def test_assets_monitor_failure(mock_layer4):
    # 5. monitor failure is handled correctly
    mock_layer4.return_value.get_asset_status.return_value = {
        "status": "FAILED",
        "error": "Asset DB offline"
    }
    response = client.get("/assets/status")
    assert response.status_code == 500
    assert "Asset DB offline" in response.json()["detail"]
