import pytest
from ai_service.layer4.uncertainty_model import SyntheticUncertaintyModel

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
