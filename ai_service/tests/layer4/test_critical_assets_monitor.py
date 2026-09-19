import pytest
import os
import csv
from unittest.mock import MagicMock
from ai_service.layer4.critical_assets_monitor import (
    CriticalAssetsMonitor, 
    SubstationMonitoringResult,
    STATUS_SAFE, STATUS_AT_RISK, STATUS_CRITICAL, STATUS_UNKNOWN
)
from ai_service.layer4.temporal_flood import TemporalFloodDepthService

# Create a dummy CSV for testing
TEST_CSV_PATH = "ai_service/tests/layer4/dummy_substations.csv"

@pytest.fixture(scope="module", autouse=True)
def setup_dummy_csv():
    os.makedirs(os.path.dirname(TEST_CSV_PATH), exist_ok=True)
    rows = [
        {"substation_id": "SS-001", "name": "Valid Sub", "voltage_kv": "230.0", "latitude": "13.0", "longitude": "80.0", "road_segment_id": "SEG_1", "ground_elevation_m": "2.0", "plinth_height_m": "0.60"},
        {"substation_id": "SS-002", "name": "Unknown Plinth", "voltage_kv": "110.0", "latitude": "13.0", "longitude": "80.0", "road_segment_id": "SEG_2", "ground_elevation_m": "2.0", "plinth_height_m": ""},
        {"substation_id": "SS-003", "name": "Missing Segment", "voltage_kv": "110.0", "latitude": "13.0", "longitude": "80.0", "road_segment_id": "", "ground_elevation_m": "2.0", "plinth_height_m": "0.60"},
        {"substation_id": "SS-004", "name": "Missing Elevation", "voltage_kv": "110.0", "latitude": "13.0", "longitude": "80.0", "road_segment_id": "SEG_4", "ground_elevation_m": "", "plinth_height_m": "0.60"},
    ]
    with open(TEST_CSV_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        
    yield
    if os.path.exists(TEST_CSV_PATH):
        os.remove(TEST_CSV_PATH)

def test_load_all_substations():
    monitor = CriticalAssetsMonitor(TEST_CSV_PATH)
    assert len(monitor.substations) == 4

def test_monitor_valid_data_safe():
    monitor = CriticalAssetsMonitor(TEST_CSV_PATH)
    mock_temp_service = MagicMock(spec=TemporalFloodDepthService)
    mock_temp_service.get_effective_depth.return_value = {"effective_depth_cm": 10.0}
    
    results = monitor.evaluate_substations(mock_temp_service)
    res = next(r for r in results if r.substation_id == "SS-001")
    
    assert res.flood_status == STATUS_SAFE
    assert res.maximum_effective_depth == 10.0
    assert "clearance" in res.explanation
    assert res.plinth_height_known is True
    assert res.uncertainty_flag == ""

def test_monitor_valid_data_critical():
    monitor = CriticalAssetsMonitor(TEST_CSV_PATH)
    mock_temp_service = MagicMock(spec=TemporalFloodDepthService)
    mock_temp_service.get_effective_depth.return_value = {"effective_depth_cm": 70.0}
    
    results = monitor.evaluate_substations(mock_temp_service)
    res = next(r for r in results if r.substation_id == "SS-001")
    
    assert res.flood_status == STATUS_CRITICAL
    assert res.maximum_effective_depth == 70.0
    assert "exceeding the known plinth height" in res.explanation

def test_monitor_unknown_plinth_does_not_become_zero_or_safe():
    monitor = CriticalAssetsMonitor(TEST_CSV_PATH)
    mock_temp_service = MagicMock(spec=TemporalFloodDepthService)
    mock_temp_service.get_effective_depth.return_value = {"effective_depth_cm": 10.0}
    
    results = monitor.evaluate_substations(mock_temp_service)
    res = next(r for r in results if r.substation_id == "SS-002")
    
    assert res.plinth_height_known is False
    assert res.flood_status == STATUS_UNKNOWN
    assert res.uncertainty_flag == "PLINTH_UNKNOWN"
    assert "authoritative plinth height is unavailable" in res.explanation

def test_monitor_missing_road_segment():
    monitor = CriticalAssetsMonitor(TEST_CSV_PATH)
    mock_temp_service = MagicMock(spec=TemporalFloodDepthService)
    
    results = monitor.evaluate_substations(mock_temp_service)
    res = next(r for r in results if r.substation_id == "SS-003")
    
    assert res.flood_status == STATUS_UNKNOWN
    assert res.uncertainty_flag == "NO_ROAD_MAPPING"
    assert "not mapped to a valid Layer 4 road segment" in res.explanation

def test_monitor_missing_layer3_data():
    monitor = CriticalAssetsMonitor(TEST_CSV_PATH)
    mock_temp_service = MagicMock(spec=TemporalFloodDepthService)
    # Raise ValueError to simulate missing Layer 3 prediction
    mock_temp_service.get_effective_depth.side_effect = ValueError("Missing segment")
    
    results = monitor.evaluate_substations(mock_temp_service)
    res = next(r for r in results if r.substation_id == "SS-001")
    
    assert res.flood_status == STATUS_UNKNOWN
    assert res.uncertainty_flag == "DATA_UNAVAILABLE"
    assert "Layer 3 data is unavailable" in res.explanation

def test_forecast_horizon_handling():
    monitor = CriticalAssetsMonitor(TEST_CSV_PATH)
    mock_temp_service = MagicMock(spec=TemporalFloodDepthService)
    
    def mock_get_depth(seg_id, t):
        return {"effective_depth_cm": t * 0.1}
        
    mock_temp_service.get_effective_depth.side_effect = mock_get_depth
    
    results = monitor.evaluate_substations(mock_temp_service)
    res = next(r for r in results if r.substation_id == "SS-001")
    
    assert res.maximum_effective_depth == 18.0
    assert res.maximum_forecast_horizon_affected == "T+180"
    
def test_missing_ground_elevation():
    monitor = CriticalAssetsMonitor(TEST_CSV_PATH)
    mock_temp_service = MagicMock()
    mock_temp_service.get_effective_depth.return_value = {"effective_depth_cm": 5.0}
    
    results = monitor.evaluate_substations(mock_temp_service)
    res = next(r for r in results if r.substation_id == "SS-004")
    
    assert res.ground_elevation_m == ""
    # Should still evaluate flood risk using plinth correctly
    assert res.flood_status == STATUS_SAFE
