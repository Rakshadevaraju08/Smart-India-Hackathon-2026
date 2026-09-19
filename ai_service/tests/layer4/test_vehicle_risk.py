import pytest
import math
from ai_service.layer4.vehicle_risk import VehicleRiskConfig, FloodHazardEvaluator

def test_dry_road():
    # length=100m, speed=36km/h (10m/s). Baseline time = 10s.
    res = FloodHazardEvaluator.evaluate(0.0, "passenger_car", 100.0, 36.0)
    assert res["hazard_ratio"] == 0.0
    assert res["is_passable"] is True
    assert res["hazard_cost_seconds"] == 10.0

def test_shallow_flood():
    # Limit for car is 18cm. Depth is 4.5cm. r = 0.25
    # cost = 10 * (1 + 5 * 0.25^2) = 10 * (1 + 5 * 0.0625) = 10 * 1.3125 = 13.125
    res = FloodHazardEvaluator.evaluate(4.5, "passenger_car", 100.0, 36.0, k=5.0, p=2.0)
    assert res["hazard_ratio"] == 0.25
    assert res["is_passable"] is True
    assert math.isclose(res["hazard_cost_seconds"], 13.125)
    
def test_moderate_flood():
    # Depth 9cm. r = 0.5
    # cost = 10 * (1 + 5 * 0.5^2) = 10 * (1 + 1.25) = 22.5
    res = FloodHazardEvaluator.evaluate(9.0, "passenger_car", 100.0, 36.0, k=5.0, p=2.0)
    assert res["hazard_ratio"] == 0.5
    assert res["is_passable"] is True
    assert math.isclose(res["hazard_cost_seconds"], 22.5)
    
def test_flood_close_to_limit():
    # Limit = 18cm. Depth = 17.1cm. r = 0.95
    # cost = 10 * (1 + 5 * 0.95^2) = 10 * (1 + 5 * 0.9025) = 10 * 5.5125 = 55.125
    res = FloodHazardEvaluator.evaluate(17.1, "passenger_car", 100.0, 36.0, k=5.0, p=2.0)
    assert res["hazard_ratio"] == 0.95
    assert res["is_passable"] is True
    assert math.isclose(res["hazard_cost_seconds"], 55.125)

def test_depth_exactly_equal_to_limit():
    # Exactly r=1 MUST be blocked
    res = FloodHazardEvaluator.evaluate(18.0, "passenger_car", 100.0, 36.0)
    assert res["hazard_ratio"] == 1.0
    assert res["is_passable"] is False
    assert res["status"] == "BLOCKED"
    assert math.isinf(res["hazard_cost_seconds"])

def test_depth_above_limit():
    res = FloodHazardEvaluator.evaluate(27.0, "passenger_car", 100.0, 36.0)
    assert res["hazard_ratio"] == 1.5
    assert res["is_passable"] is False
    assert res["status"] == "BLOCKED"
    assert math.isinf(res["hazard_cost_seconds"])

def test_different_k_values():
    # depth=9cm, car=18cm -> r=0.5. baseline=10s.
    # k=10, p=2 -> cost = 10 * (1 + 10 * 0.5^2) = 10 * 3.5 = 35.0
    res = FloodHazardEvaluator.evaluate(9.0, "passenger_car", 100.0, 36.0, k=10.0, p=2.0)
    assert math.isclose(res["hazard_cost_seconds"], 35.0)

def test_different_p_values():
    # k=5, p=3 -> cost = 10 * (1 + 5 * 0.5^3) = 10 * (1 + 5 * 0.125) = 10 * 1.625 = 16.25
    res = FloodHazardEvaluator.evaluate(9.0, "passenger_car", 100.0, 36.0, k=5.0, p=3.0)
    assert math.isclose(res["hazard_cost_seconds"], 16.25)

def test_every_vehicle_type():
    # base=100m, 36km/h -> 10s
    res1 = FloodHazardEvaluator.evaluate(5.0, "two_wheeler", 100.0, 36.0)
    assert res1["hazard_ratio"] == 0.5
    
    res2 = FloodHazardEvaluator.evaluate(9.0, "passenger_car", 100.0, 36.0)
    assert res2["hazard_ratio"] == 0.5
    
    res3 = FloodHazardEvaluator.evaluate(30.0, "ambulance", 100.0, 36.0)
    assert res3["hazard_ratio"] == 1.0
    assert res3["is_passable"] is False
    
    res4 = FloodHazardEvaluator.evaluate(90.0, "ndrf_heavy_rescue", 100.0, 36.0)
    assert res4["hazard_ratio"] == 2.0
    assert res4["is_passable"] is False

def test_unknown_vehicle_type():
    with pytest.raises(ValueError, match="Unknown vehicle type"):
        FloodHazardEvaluator.evaluate(10.0, "hovercraft", 100.0, 36.0)

def test_negative_depth():
    with pytest.raises(ValueError, match="cannot be negative"):
        FloodHazardEvaluator.evaluate(-5.0, "ambulance", 100.0, 36.0)

def test_nan_values():
    with pytest.raises(ValueError, match="cannot be NaN"):
        FloodHazardEvaluator.evaluate(float("nan"), "two_wheeler", 100.0, 36.0)
    with pytest.raises(ValueError, match="cannot be NaN"):
        FloodHazardEvaluator.evaluate(5.0, "two_wheeler", float("nan"), 36.0)

def test_infinite_values():
    with pytest.raises(ValueError, match="cannot be infinite"):
        FloodHazardEvaluator.evaluate(float("inf"), "ndrf_heavy_rescue", 100.0, 36.0)

def test_invalid_length():
    with pytest.raises(ValueError, match="must be strictly positive"):
        FloodHazardEvaluator.evaluate(5.0, "passenger_car", 0.0, 36.0)
    with pytest.raises(ValueError, match="must be strictly positive"):
        FloodHazardEvaluator.evaluate(5.0, "passenger_car", -10.0, 36.0)

def test_invalid_speed():
    with pytest.raises(ValueError, match="must be strictly positive"):
        FloodHazardEvaluator.evaluate(5.0, "passenger_car", 100.0, 0.0)

def test_invalid_k_p():
    with pytest.raises(TypeError, match="must be strictly numeric"):
        FloodHazardEvaluator.evaluate(5.0, "passenger_car", 100.0, 36.0, k="5")
