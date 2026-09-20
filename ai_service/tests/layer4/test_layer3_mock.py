from ai_service.layer4.layer3_mock import Layer3Result
from ai_service.layer4.layer3_mock import Layer3Result, InvalidLayer3ContractError
from ai_service.layer4.layer3_mock import MockLayer3Provider
import networkx as nx
import pytest


def create_valid_prediction(seg_id="CHN_SEG_123"):
    return {
        "segment_id": seg_id,
        "depth_T+15m_cm": 0.0,
        "depth_T+30m_cm": 15.5,
        "depth_T+60m_cm": 30.0,
        "depth_T+90m_cm": 45.2,
        "depth_T+120m_cm": 20.0,
        "depth_T+180m_cm": 5.0,
        "is_impassable_T+15m": False,
        "is_impassable_T+30m": True,
        "is_impassable_T+60m": True,
        "is_impassable_T+90m": True,
        "is_impassable_T+120m": True,
        "is_impassable_T+180m": False
    }

def test_valid_contract():
    data = [create_valid_prediction("SEG_1"), create_valid_prediction("SEG_2")]
    result = Layer3Result(data)
    
    assert result.has_prediction("SEG_1")
    assert result.get_prediction("SEG_1")["depth_T+30m_cm"] == 15.5

def test_duplicate_segment_id():
    data = [create_valid_prediction("SEG_1"), create_valid_prediction("SEG_1")]
    with pytest.raises(InvalidLayer3ContractError, match="Duplicate segment_id"):
        Layer3Result(data)

def test_missing_segment_id():
    p = create_valid_prediction()
    del p["segment_id"]
    with pytest.raises(InvalidLayer3ContractError, match="Missing 'segment_id'"):
        Layer3Result([p])

def test_empty_segment_id():
    p = create_valid_prediction("")
    with pytest.raises(InvalidLayer3ContractError, match="Empty or null"):
        Layer3Result([p])

def test_missing_depth_horizon():
    import re
    # Verify missing each required prediction horizon is rejected
    horizons = ["T+15m", "T+30m", "T+60m", "T+90m", "T+120m", "T+180m"]
    for h in horizons:
        p = create_valid_prediction()
        del p[f"depth_{h}_cm"]
        with pytest.raises(InvalidLayer3ContractError, match=re.escape(f"Missing required depth field 'depth_{h}_cm'")):
            Layer3Result([p])

def test_missing_impassable_horizon():
    p = create_valid_prediction()
    del p["is_impassable_T+120m"]
    with pytest.raises(InvalidLayer3ContractError, match="Missing required impassability field"):
        Layer3Result([p])

def test_extra_columns_accepted():
    p = create_valid_prediction()
    p["extra_column_ignore_me"] = "some data"
    result = Layer3Result([p])
    assert result.get_prediction("CHN_SEG_123")["extra_column_ignore_me"] == "some data"

def test_negative_depth():
    p = create_valid_prediction()
    p["depth_T+30m_cm"] = -5.0
    with pytest.raises(InvalidLayer3ContractError, match="cannot be negative"):
        Layer3Result([p])

def test_invalid_depth_type():
    p = create_valid_prediction()
    p["depth_T+15m_cm"] = "None"
    with pytest.raises(InvalidLayer3ContractError, match="must be numeric"):
        Layer3Result([p])

def test_nan_depth():
    import math
    p = create_valid_prediction()
    p["depth_T+30m_cm"] = float("nan")
    with pytest.raises(InvalidLayer3ContractError, match="cannot be NaN"):
        Layer3Result([p])

def test_invalid_impassability_type():
    p = create_valid_prediction()
    p["is_impassable_T+60m"] = "Yes"
    with pytest.raises(InvalidLayer3ContractError, match="strict boolean"):
        Layer3Result([p])
        
def test_no_silent_conversion():
    p = create_valid_prediction()
    p["is_impassable_T+60m"] = 1  # 1 is truthy but not a strict bool instance (wait, in python isinstance(1, bool) is False)
    with pytest.raises(InvalidLayer3ContractError, match="strict boolean"):
        Layer3Result([p])

def test_non_list_input():
    with pytest.raises(InvalidLayer3ContractError, match="list of dictionaries"):
        Layer3Result({"segment_id": "123"})

@pytest.fixture
def mock_graph():
    G = nx.MultiDiGraph()
    G.add_node("N1")
    G.add_node("N2")
    
    # Adding three realistic edges
    G.add_edge("N1", "N2", key=0, segment_id="CHN_SEG_00001", length_m=10.0)
    G.add_edge("N1", "N2", key=1, segment_id="CHN_SEG_00002", length_m=15.0)
    G.add_edge("N2", "N1", key=0, segment_id="CHN_SEG_00003", length_m=5.0)
    
    # Add an edge without a segment ID (should be ignored safely by the mock)
    G.add_edge("N2", "N2", key=0, length_m=0.0)
    
    return G

def test_mock_returns_valid_contract(mock_graph):
    provider = MockLayer3Provider(mock_graph)
    
    # Prove the provider honors the contract interface natively
    result = provider.get_predictions()
    assert isinstance(result, Layer3Result)
    
    # Ensure it only mocked edges with segment IDs (3 edges)
    assert len(result.predictions) == 3

def test_mock_is_deterministic(mock_graph):
    # Running multiple times on the same graph must yield perfectly identical arrays
    provider1 = MockLayer3Provider(mock_graph)
    result1 = provider1.get_predictions()
    
    provider2 = MockLayer3Provider(mock_graph)
    result2 = provider2.get_predictions()
    
    pred1 = result1.get_prediction("CHN_SEG_00001")
    pred2 = result2.get_prediction("CHN_SEG_00001")
    
    assert pred1["depth_T+60m_cm"] == pred2["depth_T+60m_cm"]
    assert pred1["is_impassable_T+30m"] == pred2["is_impassable_T+30m"]

def test_mock_contains_all_horizons(mock_graph):
    provider = MockLayer3Provider(mock_graph)
    result = provider.get_predictions()
    
    pred = result.get_prediction("CHN_SEG_00002")
    
    expected_horizons = ["T+15m", "T+30m", "T+60m", "T+90m", "T+120m", "T+180m"]
    for horizon in expected_horizons:
        assert f"depth_{horizon}_cm" in pred
        assert f"is_impassable_{horizon}" in pred
        
        assert isinstance(pred[f"depth_{horizon}_cm"], float)
        assert isinstance(pred[f"is_impassable_{horizon}"], bool)

def test_mock_impassability_threshold(mock_graph):
    provider = MockLayer3Provider(mock_graph)
    result = provider.get_predictions()
    
    pred = result.get_prediction("CHN_SEG_00003")
    
    # Impassability should perfectly match depth > 20.0
    for horizon in ["T+15m", "T+30m", "T+60m", "T+90m", "T+120m", "T+180m"]:
        depth = pred[f"depth_{horizon}_cm"]
        is_impassable = pred[f"is_impassable_{horizon}"]
        
        if depth > 20.0:
            assert is_impassable is True
        else:
            assert is_impassable is False

