from ai_service.layer4.layer3_mock import Layer3Result
from ai_service.layer4.temporal_flood import SyntheticUncertaintyModel
from ai_service.layer4.temporal_flood import TemporalFloodDepthService
import math
import pytest


def test_uncertainty_horizons():
    model = SyntheticUncertaintyModel()
    
    # Check bounds
    assert model.get_uncertainty_cm(15.0, 10.0) == 2.0
    assert model.get_uncertainty_cm(30.0, 10.0) == 5.0
    assert model.get_uncertainty_cm(60.0, 10.0) == 10.0
    assert model.get_uncertainty_cm(90.0, 10.0) == 15.0
    assert model.get_uncertainty_cm(120.0, 10.0) == 20.0
    assert model.get_uncertainty_cm(180.0, 10.0) == 30.0
    
def test_monotonicity():
    model = SyntheticUncertaintyModel()
    
    prev = -1.0
    for m in [15.0, 30.0, 60.0, 90.0, 120.0, 180.0]:
        val = model.get_uncertainty_cm(m, 10.0)
        assert val >= prev
        prev = val

def test_interpolation():
    model = SyntheticUncertaintyModel()
    # Halfway between 30 (5.0) and 60 (10.0) -> 45
    assert model.get_uncertainty_cm(45.0, 10.0) == 7.5

def test_boundary_behavior():
    model = SyntheticUncertaintyModel()
    
    # Before 15 -> caps at 2.0
    assert model.get_uncertainty_cm(0.0, 10.0) == 2.0
    
    # After 180 -> caps at 30.0
    assert model.get_uncertainty_cm(200.0, 10.0) == 30.0

def test_invalid_input():
    model = SyntheticUncertaintyModel()
    
    with pytest.raises(ValueError):
        model.get_uncertainty_cm(-10.0, 10.0)

@pytest.fixture
def valid_layer3_result():
    prediction = {
        "segment_id": "CHN_SEG_TEST",
        "depth_T+15m_cm": 0.0,
        "depth_T+30m_cm": 10.0,
        "depth_T+60m_cm": 20.0,
        "depth_T+90m_cm": 30.0,
        "depth_T+120m_cm": 15.0,
        "depth_T+180m_cm": 5.0,
        "is_impassable_T+15m": False,
        "is_impassable_T+30m": False,
        "is_impassable_T+60m": False,
        "is_impassable_T+90m": True,
        "is_impassable_T+120m": False,
        "is_impassable_T+180m": False
    }
    return Layer3Result([prediction])

@pytest.fixture
def temporal_service(valid_layer3_result):
    return TemporalFloodDepthService(valid_layer3_result)

# --- Exact Horizon Tests ---

def test_exact_horizons(temporal_service):
    # T+15
    assert temporal_service.get_effective_depth("CHN_SEG_TEST", 15.0)["predicted_depth_cm"] == 0.0
    # T+30
    assert temporal_service.get_effective_depth("CHN_SEG_TEST", 30.0)["predicted_depth_cm"] == 10.0
    # T+60
    assert temporal_service.get_effective_depth("CHN_SEG_TEST", 60.0)["predicted_depth_cm"] == 20.0
    # T+90
    assert temporal_service.get_effective_depth("CHN_SEG_TEST", 90.0)["predicted_depth_cm"] == 30.0
    # T+120
    assert temporal_service.get_effective_depth("CHN_SEG_TEST", 120.0)["predicted_depth_cm"] == 15.0
    # T+180
    assert temporal_service.get_effective_depth("CHN_SEG_TEST", 180.0)["predicted_depth_cm"] == 5.0

# --- Interpolation Tests ---

def test_interpolation_between_horizons(temporal_service):
    # Exactly halfway between T+30 (10cm) and T+60 (20cm) -> T+45 should be 15cm
    res = temporal_service.get_effective_depth("CHN_SEG_TEST", 45.0)
    assert res["predicted_depth_cm"] == 15.0
    assert res["interpolation_source_horizons"] == (30, 60)
    assert res["is_clamped_before_T15"] is False
    assert res["is_clamped_after_T180"] is False
    
    # 1/3 of the way between T+60 (20cm) and T+90 (30cm) -> T+70 should be 23.33cm
    assert temporal_service.get_effective_depth("CHN_SEG_TEST", 70.0)["predicted_depth_cm"] == 23.33
    
    # Halfway between T+90 (30cm) and T+120 (15cm) -> T+105 should be 22.5cm
    assert temporal_service.get_effective_depth("CHN_SEG_TEST", 105.0)["predicted_depth_cm"] == 22.5

# --- Boundary Behavior Tests ---

def test_time_before_t15(temporal_service):
    # The policy snaps to T+15 (0.0cm) rather than failing or returning unknown
    res = temporal_service.get_effective_depth("CHN_SEG_TEST", 0.0)
    assert res["predicted_depth_cm"] == 0.0
    assert res["is_clamped_before_T15"] is True
    
    res2 = temporal_service.get_effective_depth("CHN_SEG_TEST", 5.0)
    assert res2["predicted_depth_cm"] == 0.0
    assert res2["is_clamped_before_T15"] is True

def test_time_after_t180(temporal_service):
    # The policy caps at T+180 (5.0cm) and does not extrapolate
    res = temporal_service.get_effective_depth("CHN_SEG_TEST", 180.1)
    assert res["predicted_depth_cm"] == 5.0
    assert res["is_clamped_after_T180"] is True
    
    res2 = temporal_service.get_effective_depth("CHN_SEG_TEST", 300.0)
    assert res2["predicted_depth_cm"] == 5.0
    assert res2["is_clamped_after_T180"] is True

def test_effective_depth(temporal_service):
    res = temporal_service.get_effective_depth("CHN_SEG_TEST", 45.0)
    assert res["segment_id"] == "CHN_SEG_TEST"
    assert res["minutes_from_departure"] == 45.0
    assert res["predicted_depth_cm"] == 15.0
    assert res["uncertainty_margin_cm"] == 7.5
    assert res["effective_depth_cm"] == 22.5

# --- Validation and Error Handling Tests ---

def test_missing_segment(temporal_service):
    with pytest.raises(ValueError, match="No Layer 3 prediction found"):
        temporal_service.get_effective_depth("INVALID_SEG", 45.0)

def test_empty_segment_id(temporal_service):
    with pytest.raises(ValueError, match="Segment ID cannot be empty"):
        temporal_service.get_effective_depth("", 45.0)

def test_invalid_time_input(temporal_service):
    # Strings
    with pytest.raises(TypeError, match="must be strictly numeric"):
        temporal_service.get_effective_depth("CHN_SEG_TEST", "45")
    # Booleans
    with pytest.raises(TypeError, match="must be strictly numeric"):
        temporal_service.get_effective_depth("CHN_SEG_TEST", True)
    # NaN
    with pytest.raises(ValueError, match="cannot be NaN"):
        temporal_service.get_effective_depth("CHN_SEG_TEST", float("nan"))
    # Negative time
    with pytest.raises(ValueError, match="cannot be negative"):
        temporal_service.get_effective_depth("CHN_SEG_TEST", -10.0)

# The following depth validation tests require tampering with the underlying data directly
# because Layer3Result normally protects against this, but the service must independently validate.
def test_negative_depth():
    from ai_service.layer4.layer3_mock import Layer3Result
    
    # Create valid result, then maliciously alter it
    pred = {
        "segment_id": "TAMPER",
        "depth_T+15m_cm": 0.0, "depth_T+30m_cm": 0.0, "depth_T+60m_cm": 0.0,
        "depth_T+90m_cm": 0.0, "depth_T+120m_cm": 0.0, "depth_T+180m_cm": 0.0,
        "is_impassable_T+15m": False, "is_impassable_T+30m": False, "is_impassable_T+60m": False,
        "is_impassable_T+90m": False, "is_impassable_T+120m": False, "is_impassable_T+180m": False
    }
    l3 = Layer3Result([pred])
    # Bypass protection
    l3._index["TAMPER"]["depth_T+30m_cm"] = -10.0
    
    svc = TemporalFloodDepthService(l3)
    with pytest.raises(ValueError, match="cannot be negative"):
        svc.get_effective_depth("TAMPER", 30.0)

def test_nan_depth():
    pred = {
        "segment_id": "TAMPER",
        "depth_T+15m_cm": 0.0, "depth_T+30m_cm": 0.0, "depth_T+60m_cm": 0.0,
        "depth_T+90m_cm": 0.0, "depth_T+120m_cm": 0.0, "depth_T+180m_cm": 0.0,
        "is_impassable_T+15m": False, "is_impassable_T+30m": False, "is_impassable_T+60m": False,
        "is_impassable_T+90m": False, "is_impassable_T+120m": False, "is_impassable_T+180m": False
    }
    l3 = Layer3Result([pred])
    l3._index["TAMPER"]["depth_T+60m_cm"] = float("nan")
    
    svc = TemporalFloodDepthService(l3)
    with pytest.raises(ValueError, match="cannot be NaN"):
        svc.get_effective_depth("TAMPER", 60.0)

def test_missing_depth_key():
    pred = {
        "segment_id": "TAMPER",
        "depth_T+15m_cm": 0.0, "depth_T+30m_cm": 0.0, "depth_T+60m_cm": 0.0,
        "depth_T+90m_cm": 0.0, "depth_T+120m_cm": 0.0, "depth_T+180m_cm": 0.0,
        "is_impassable_T+15m": False, "is_impassable_T+30m": False, "is_impassable_T+60m": False,
        "is_impassable_T+90m": False, "is_impassable_T+120m": False, "is_impassable_T+180m": False
    }
    l3 = Layer3Result([pred])
    del l3._index["TAMPER"]["depth_T+15m_cm"]
    
    svc = TemporalFloodDepthService(l3)
    with pytest.raises(ValueError, match="Missing required prediction horizon"):
        svc.get_effective_depth("TAMPER", 15.0)

