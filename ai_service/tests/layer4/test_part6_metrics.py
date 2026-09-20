import pytest
import networkx as nx
from ai_service.layer4.routing_engine import DynamicRoutingEngine, RouteRequest
from ai_service.layer4.temporal_flood import TemporalFloodDepthService

class MockTemporalServiceMetrics(TemporalFloodDepthService):
    def __init__(self, segment_depths):
        self.segment_depths = segment_depths
        
    def get_effective_depth(self, segment_id, current_time_minutes):
        if segment_id not in self.segment_depths:
            return {"effective_depth_cm": 0.0}
        return {"effective_depth_cm": self.segment_depths[segment_id]}

@pytest.fixture
def metrics_graph():
    G = nx.MultiDiGraph()
    # A straight line of 3 segments
    G.add_node("N0", coordinates=[0.0, 0.0])
    G.add_node("N1", coordinates=[0.0, 0.01])
    G.add_node("N2", coordinates=[0.0, 0.02])
    G.add_node("N3", coordinates=[0.0, 0.03])
    
    G.add_edge("N0", "N1", key=0, segment_id="SEG_1", length_m=1000.0, free_flow_speed=36.0, is_underpass=False)
    G.add_edge("N1", "N2", key=0, segment_id="SEG_2", length_m=1000.0, free_flow_speed=36.0, is_underpass=True)
    G.add_edge("N2", "N3", key=0, segment_id="SEG_3", length_m=1000.0, free_flow_speed=36.0, is_underpass=False)
    
    return G

def test_dry_route(metrics_graph):
    engine = DynamicRoutingEngine(metrics_graph)
    temp = MockTemporalServiceMetrics({}) # All 0
    req = RouteRequest(0.0, 0.0, 0.0, 0.03, "ambulance", 0.0, temp)
    res = engine.solve_route(req)
    
    assert res.success is True
    assert res.maximum_effective_depth == 0.0
    assert res.maximum_hazard_ratio == 0.0
    assert res.minimum_clearance == 30.0 # Ambulance limit is 30.0
    assert res.hazard_category == "GREEN"
    assert "SEG_2" in res.underpasses_used
    assert len(res.underpasses_avoided) == 0

def test_shallow_flood_amber_route(metrics_graph):
    engine = DynamicRoutingEngine(metrics_graph)
    # SEG_1: 5cm, SEG_2: 20cm, SEG_3: 10cm
    temp = MockTemporalServiceMetrics({"SEG_1": 5.0, "SEG_2": 20.0, "SEG_3": 10.0})
    req = RouteRequest(0.0, 0.0, 0.0, 0.03, "ambulance", 0.0, temp)
    res = engine.solve_route(req)
    
    assert res.success is True
    assert res.maximum_effective_depth == 20.0
    # Ambulance limit 30. Max ratio = 20/30 = 0.666...
    assert 0.66 < res.maximum_hazard_ratio < 0.67
    assert res.minimum_clearance == 10.0 # 30 - 20
    assert res.hazard_category == "AMBER" # 0.5 <= 0.666 <= 0.8
    assert "SEG_2" in res.underpasses_used

def test_high_hazard_red_route(metrics_graph):
    engine = DynamicRoutingEngine(metrics_graph)
    # SEG_1: 0cm, SEG_2: 26cm, SEG_3: 0cm
    # Ambulance limit 30, ratio = 26/30 = 0.866
    temp = MockTemporalServiceMetrics({"SEG_2": 26.0})
    req = RouteRequest(0.0, 0.0, 0.0, 0.03, "ambulance", 0.0, temp)
    res = engine.solve_route(req)
    
    assert res.success is True
    assert res.maximum_effective_depth == 26.0
    assert res.minimum_clearance == 4.0
    assert res.hazard_category == "RED"

def test_unsafe_underpass_avoided():
    # Construct a custom graph with detour for this specific test
    G = nx.MultiDiGraph()
    G.add_node("N0", coordinates=[0.0, 0.0])
    G.add_node("N1", coordinates=[0.0, 0.01])
    G.add_node("N2", coordinates=[0.0, 0.02])
    G.add_node("N3", coordinates=[0.0, 0.03])
    G.add_edge("N0", "N1", key=0, segment_id="SEG_1", length_m=1000.0, free_flow_speed=36.0, is_underpass=False)
    G.add_edge("N1", "N2", key=0, segment_id="SEG_2", length_m=1000.0, free_flow_speed=36.0, is_underpass=True)
    G.add_edge("N2", "N3", key=0, segment_id="SEG_3", length_m=1000.0, free_flow_speed=36.0, is_underpass=False)
    
    G.add_node("N_DETOUR", coordinates=[0.01, 0.015])
    G.add_edge("N1", "N_DETOUR", key=0, segment_id="SEG_DETOUR_1", length_m=1500.0, free_flow_speed=36.0, is_underpass=False)
    G.add_edge("N_DETOUR", "N2", key=0, segment_id="SEG_DETOUR_2", length_m=1500.0, free_flow_speed=36.0, is_underpass=True)

    engine = DynamicRoutingEngine(G)
    # SEG_2 is 35cm (Blocked for ambulance)
    # SEG_DETOUR_1 and 2 are 0cm
    temp = MockTemporalServiceMetrics({"SEG_2": 35.0})
    req = RouteRequest(0.0, 0.0, 0.0, 0.03, "ambulance", 0.0, temp)
    res = engine.solve_route(req)
    
    assert res.success is True
    assert "SEG_DETOUR_2" in res.ordered_segment_ids
    assert "SEG_2" not in res.ordered_segment_ids
    
    # SEG_2 was evaluated and found unsafe, so it is in avoided
    assert "SEG_2" in res.underpasses_avoided
    # SEG_DETOUR_2 is an underpass that was used
    assert "SEG_DETOUR_2" in res.underpasses_used
    assert res.hazard_category == "GREEN"

def test_blocked_route(metrics_graph):
    engine = DynamicRoutingEngine(metrics_graph)
    # Everything blocked
    temp = MockTemporalServiceMetrics({"SEG_1": 50.0})
    req = RouteRequest(0.0, 0.0, 0.0, 0.03, "ambulance", 0.0, temp)
    res = engine.solve_route(req)
    
    assert res.success is False
    assert res.maximum_effective_depth == 0.0
    assert res.maximum_hazard_ratio == 0.0
    assert res.minimum_clearance == 0.0
    assert res.hazard_category == "UNKNOWN"
    assert res.underpasses_used == []
