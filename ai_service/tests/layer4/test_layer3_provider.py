import pytest
import networkx as nx
from ai_service.layer4.layer3_contract import Layer3Result
from ai_service.layer4.layer3_provider import MockLayer3Provider

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
