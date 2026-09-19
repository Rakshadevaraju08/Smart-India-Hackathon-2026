import pytest
import networkx as nx
import math
from ai_service.layer4.routing_engine import DynamicRoutingEngine, RouteRequest

class MockLayer3Result:
    pass

class MockTemporalService:
    def __init__(self, result):
        pass
    def get_effective_depth(self, segment_id, current_time_minutes):
        # Time-dependent mock: if time > 30, depth jumps to 50cm
        if current_time_minutes > 30:
            return {"effective_depth_cm": 50.0}
        return {"effective_depth_cm": 10.0}

def test_kdtree_snapping(monkeypatch):
    # Mocking out external services
    G = nx.MultiDiGraph()
    G.add_node("NODE_A", coordinates=[80.0, 13.0])
    G.add_node("NODE_B", coordinates=[80.1, 13.1])
    
    engine = DynamicRoutingEngine(G)
    
    # Should snap to NODE_A
    snapped = engine.find_nearest_node(80.01, 13.01)
    assert snapped == "NODE_A"

def test_solve_route_success(monkeypatch):
    # Patch TemporalFloodDepthService
    import ai_service.layer4.routing_engine as re_module
    monkeypatch.setattr(re_module, "TemporalFloodDepthService", MockTemporalService)

    G = nx.MultiDiGraph()
    G.add_node("A", coordinates=[80.0, 13.0])
    G.add_node("B", coordinates=[80.1, 13.0])
    G.add_node("C", coordinates=[80.2, 13.0])
    
    G.add_edge("A", "B", segment_id="SEG_1", length_m=1000.0, free_flow_speed=36.0)
    G.add_edge("B", "C", segment_id="SEG_2", length_m=1000.0, free_flow_speed=36.0)
    
    engine = DynamicRoutingEngine(G)
    
    req = RouteRequest(
        origin_lon=80.0, origin_lat=13.0,
        dest_lon=80.2, dest_lat=13.0,
        vehicle_type="ambulance", # Limit 30cm
        departure_time_minutes=0,
        layer3_result=MockLayer3Result()
    )
    
    result = engine.solve_route(req)
    assert result.diagnostics["success"] is True
    assert result.ordered_nodes == ["A", "B", "C"]
    assert result.ordered_segments == ["SEG_1", "SEG_2"]
    
def test_solve_route_time_dependent_blockage(monkeypatch):
    # Patch TemporalFloodDepthService
    import ai_service.layer4.routing_engine as re_module
    monkeypatch.setattr(re_module, "TemporalFloodDepthService", MockTemporalService)

    G = nx.MultiDiGraph()
    G.add_node("A", coordinates=[80.0, 13.0])
    G.add_node("B", coordinates=[80.1, 13.0])
    G.add_node("C", coordinates=[80.2, 13.0])
    
    G.add_edge("A", "B", segment_id="SEG_1", length_m=1000.0, free_flow_speed=36.0)
    G.add_edge("B", "C", segment_id="SEG_2", length_m=1000.0, free_flow_speed=36.0)
    
    engine = DynamicRoutingEngine(G)
    
    req = RouteRequest(
        origin_lon=80.0, origin_lat=13.0,
        dest_lon=80.2, dest_lat=13.0,
        vehicle_type="ambulance", # Limit 30cm
        departure_time_minutes=40, # Departs at T+40, so depth is 50cm > 30cm limit -> BLOCKED
        layer3_result=MockLayer3Result()
    )
    
    result = engine.solve_route(req)
    assert result.diagnostics["success"] is False
    assert result.diagnostics["blocked_edges_encountered"] > 0
    assert result.ordered_nodes == []
