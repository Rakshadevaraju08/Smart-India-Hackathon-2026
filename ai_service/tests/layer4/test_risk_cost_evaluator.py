import pytest
import math
from ai_service.layer4.risk_cost_evaluator import VehicleRiskConfig, FloodHazardEvaluator

def test_dry_road():
    # length=100m, speed=36km/h (10m/s). Baseline time = 10s.
    res = FloodHazardEvaluator.evaluate_road_risk("SEG_1", 100.0, 36.0, 0.0, "passenger_car")
    assert res["segment_id"] == "SEG_1"
    assert res["hazard_ratio"] == 0.0
    assert res["is_passable"] is True
    assert res["free_flow_speed_m_per_s"] == 10.0
    assert res["adjusted_speed_m_per_s"] == 10.0
    assert res["free_flow_travel_time_seconds"] == 10.0
    assert res["actual_travel_time_seconds"] == 10.0
    assert res["hazard_cost_seconds"] == 10.0

def test_shallow_flood():
    # Limit for car is 18cm. Depth is 4.5cm. r = 0.25
    # speed = 10 * (1 - 0.7 * 0.25) = 10 * (1 - 0.175) = 8.25 m/s
    # time = 100 / 8.25 = 12.12 s
    res = FloodHazardEvaluator.evaluate_road_risk("SEG_1", 100.0, 36.0, 4.5, "passenger_car", k=5.0, p=2.0)
    assert res["hazard_ratio"] == 0.25
    assert res["is_passable"] is True
    assert math.isclose(res["adjusted_speed_m_per_s"], 8.25)
    assert math.isclose(res["actual_travel_time_seconds"], 12.12, rel_tol=1e-2)
    assert math.isclose(res["hazard_cost_seconds"], 13.125)
    
def test_moderate_flood():
    # Depth 9cm. r = 0.5
    # speed = 10 * (1 - 0.7 * 0.5) = 10 * 0.65 = 6.5 m/s
    # time = 100 / 6.5 = 15.38 s
    res = FloodHazardEvaluator.evaluate_road_risk("SEG_1", 100.0, 36.0, 9.0, "passenger_car", k=5.0, p=2.0)
    assert res["hazard_ratio"] == 0.5
    assert res["is_passable"] is True
    assert math.isclose(res["adjusted_speed_m_per_s"], 6.5)
    assert math.isclose(res["actual_travel_time_seconds"], 15.38, rel_tol=1e-2)
    assert math.isclose(res["hazard_cost_seconds"], 22.5)
    
def test_flood_close_to_limit():
    # Limit = 18cm. Depth = 17.1cm. r = 0.95
    # speed = 10 * (1 - 0.7 * 0.95) = 10 * (1 - 0.665) = 3.35 m/s
    res = FloodHazardEvaluator.evaluate_road_risk("SEG_1", 100.0, 36.0, 17.1, "passenger_car", k=5.0, p=2.0)
    assert res["hazard_ratio"] == 0.95
    assert res["is_passable"] is True
    assert math.isclose(res["adjusted_speed_m_per_s"], 3.35)

def test_depth_exactly_equal_to_limit():
    # Exactly r=1 MUST be blocked
    res = FloodHazardEvaluator.evaluate_road_risk("SEG_1", 100.0, 36.0, 18.0, "passenger_car")
    assert res["hazard_ratio"] == 1.0
    assert res["is_passable"] is False
    assert res["status"] == "BLOCKED"
    assert res["adjusted_speed_m_per_s"] is None
    assert math.isinf(res["actual_travel_time_seconds"])
    assert math.isinf(res["hazard_cost_seconds"])

def test_depth_above_limit():
    res = FloodHazardEvaluator.evaluate_road_risk("SEG_1", 100.0, 36.0, 27.0, "passenger_car")
    assert res["hazard_ratio"] == 1.5
    assert res["is_passable"] is False
    assert res["status"] == "BLOCKED"
    assert res["adjusted_speed_m_per_s"] is None
    assert math.isinf(res["actual_travel_time_seconds"])

def test_speed_conversion():
    # 72 km/h = 20 m/s
    res = FloodHazardEvaluator.evaluate_road_risk("SEG_1", 200.0, 72.0, 0.0, "passenger_car")
    assert res["free_flow_speed_m_per_s"] == 20.0
    assert res["free_flow_travel_time_seconds"] == 10.0

def test_different_k_values():
    res = FloodHazardEvaluator.evaluate_road_risk("SEG_1", 100.0, 36.0, 9.0, "passenger_car", k=10.0, p=2.0)
    assert math.isclose(res["hazard_cost_seconds"], 35.0)

def test_different_p_values():
    res = FloodHazardEvaluator.evaluate_road_risk("SEG_1", 100.0, 36.0, 9.0, "passenger_car", k=5.0, p=3.0)
    assert math.isclose(res["hazard_cost_seconds"], 16.25)

def test_every_vehicle_type():
    res1 = FloodHazardEvaluator.evaluate_road_risk("SEG_1", 100.0, 36.0, 5.0, "two_wheeler")
    assert res1["hazard_ratio"] == 0.5
    
    res2 = FloodHazardEvaluator.evaluate_road_risk("SEG_1", 100.0, 36.0, 9.0, "passenger_car")
    assert res2["hazard_ratio"] == 0.5
    
    res3 = FloodHazardEvaluator.evaluate_road_risk("SEG_1", 100.0, 36.0, 30.0, "ambulance")
    assert res3["hazard_ratio"] == 1.0
    assert res3["is_passable"] is False
    
    res4 = FloodHazardEvaluator.evaluate_road_risk("SEG_1", 100.0, 36.0, 90.0, "ndrf_heavy_rescue")
    assert res4["hazard_ratio"] == 2.0
    assert res4["is_passable"] is False

def test_empty_segment_id():
    with pytest.raises(ValueError, match="Segment ID cannot be empty"):
        FloodHazardEvaluator.evaluate_road_risk("", 100.0, 36.0, 10.0, "passenger_car")

def test_unknown_vehicle_type():
    with pytest.raises(ValueError, match="Unknown vehicle type"):
        FloodHazardEvaluator.evaluate_road_risk("SEG_1", 100.0, 36.0, 10.0, "hovercraft")

def test_negative_depth():
    with pytest.raises(ValueError, match="cannot be negative"):
        FloodHazardEvaluator.evaluate_road_risk("SEG_1", 100.0, 36.0, -5.0, "ambulance")

def test_nan_values():
    with pytest.raises(ValueError, match="cannot be NaN"):
        FloodHazardEvaluator.evaluate_road_risk("SEG_1", 100.0, 36.0, float("nan"), "two_wheeler")

def test_infinite_values():
    with pytest.raises(ValueError, match="cannot be infinite"):
        FloodHazardEvaluator.evaluate_road_risk("SEG_1", 100.0, 36.0, float("inf"), "ndrf_heavy_rescue")

def test_invalid_length():
    with pytest.raises(ValueError, match="must be strictly positive"):
        FloodHazardEvaluator.evaluate_road_risk("SEG_1", 0.0, 36.0, 5.0, "passenger_car")
    with pytest.raises(ValueError, match="must be strictly positive"):
        FloodHazardEvaluator.evaluate_road_risk("SEG_1", -10.0, 36.0, 5.0, "passenger_car")

def test_invalid_speed():
    with pytest.raises(ValueError, match="must be strictly positive"):
        FloodHazardEvaluator.evaluate_road_risk("SEG_1", 100.0, 0.0, 5.0, "passenger_car")

def test_invalid_k_p():
    with pytest.raises(TypeError, match="must be strictly numeric"):
        FloodHazardEvaluator.evaluate_road_risk("SEG_1", 100.0, 36.0, 5.0, "passenger_car", k="5")
