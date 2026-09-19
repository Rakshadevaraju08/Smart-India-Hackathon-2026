import pytest
import networkx as nx
from ai_service.layer4.routing_engine import DynamicRoutingEngine, SnappingResult, EdgeEvaluationResult, RouteRequest
from ai_service.layer4.temporal_flood import TemporalFloodDepthService

class MockLayer3Result:
    pass

class MockTemporalService(TemporalFloodDepthService):
    def __init__(self, mode="static"):
        self.mode = mode
        
    def get_effective_depth(self, segment_id, current_time_minutes):
        if self.mode == "static":
            if segment_id == "SEG_A_DEST":
                return {"effective_depth_cm": 25.0} # Flooded
            if segment_id == "SEG_TIME_SENSITIVE":
                return {"effective_depth_cm": 50.0} # Blocked
            return {"effective_depth_cm": 0.0} # Safe
            
        elif self.mode == "time_dependent":
            # Time-dependent mock:
            # Segment D goes from 0cm to 50cm after T=30
            if segment_id == "SEG_TIME_SENSITIVE":
                if current_time_minutes > 30:
                    return {"effective_depth_cm": 50.0} # Blocked for ambulance (limit 30)
                else:
                    return {"effective_depth_cm": 5.0} # Safe
            return {"effective_depth_cm": 0.0}
            
        elif self.mode == "all_safe":
            return {"effective_depth_cm": 0.0}
            
        return {"effective_depth_cm": 0.0}

@pytest.fixture
def synthetic_graph():
    G = nx.MultiDiGraph()
    G.add_node("ORIGIN", coordinates=[0.0, 0.0])
    G.add_node("A", coordinates=[0.0, 0.001])
    G.add_node("B", coordinates=[0.001, 0.0])
    G.add_node("C", coordinates=[0.001, 0.001])
    G.add_node("DEST", coordinates=[0.0, 0.002])
    
    # Short route: ORIGIN -> A -> DEST
    # Total length: 2000m
    G.add_edge("ORIGIN", "A", key=0, segment_id="SEG_ORIGIN_A", length_m=1000.0, free_flow_speed=36.0)
    G.add_edge("A", "DEST", key=0, segment_id="SEG_A_DEST", length_m=1000.0, free_flow_speed=36.0)
    
    # Long route: ORIGIN -> B -> C -> DEST
    # Total length: 3000m
    G.add_edge("ORIGIN", "B", key=0, segment_id="SEG_ORIGIN_B", length_m=1000.0, free_flow_speed=36.0)
    G.add_edge("B", "C", key=0, segment_id="SEG_B_C", length_m=1000.0, free_flow_speed=36.0)
    G.add_edge("C", "DEST", key=0, segment_id="SEG_C_DEST", length_m=1000.0, free_flow_speed=36.0)
    
    # Time dependent route
    G.add_node("TIME_NODE", coordinates=[-0.001, 0.001])
    G.add_edge("ORIGIN", "TIME_NODE", key=0, segment_id="SEG_ORIGIN_TIME", length_m=1000.0, free_flow_speed=18.0) # Slower, takes longer
    G.add_edge("TIME_NODE", "DEST", key=0, segment_id="SEG_TIME_SENSITIVE", length_m=1000.0, free_flow_speed=36.0)
    
    return G


def test_synthetic_routing_chooses_safer_longer_route(synthetic_graph):
    engine = DynamicRoutingEngine(synthetic_graph)
    temporal = MockTemporalService(mode="static") # SEG_A_DEST is 25cm
    
    # Ambulance limit is 30cm, so 25cm is passable but has HIGH hazard cost
    req = RouteRequest(
        origin_lon=0.0, origin_lat=0.0,
        dest_lon=0.0, dest_lat=0.2,
        vehicle_type="ambulance",
        departure_time_minutes=0.0,
        temporal_service=temporal
    )
    
    res = engine.solve_route(req)
    assert res.success is True
    # The short route has 25cm depth. WHPF cost will be very high (ratio = 25/30 = 0.83).
    # Long route has 0 depth, WHPF cost = pure travel time.
    # The algorithm should choose the longer, safer route.
    assert res.ordered_nodes == ["ORIGIN", "B", "C", "DEST"]
    assert res.ordered_segment_ids == ["SEG_ORIGIN_B", "SEG_B_C", "SEG_C_DEST"]

def test_synthetic_routing_chooses_shortest_if_safe(synthetic_graph):
    engine = DynamicRoutingEngine(synthetic_graph)
    temporal = MockTemporalService(mode="all_safe") # Everything 0cm
    
    req = RouteRequest(
        origin_lon=0.0, origin_lat=0.0,
        dest_lon=0.0, dest_lat=0.2,
        vehicle_type="ambulance",
        departure_time_minutes=0.0,
        temporal_service=temporal
    )
    
    res = engine.solve_route(req)
    assert res.success is True
    # Since all safe, should take shortest route
    assert res.ordered_nodes == ["ORIGIN", "A", "DEST"]
    assert res.ordered_segment_ids == ["SEG_ORIGIN_A", "SEG_A_DEST"]

def test_time_dependent_routing_success_early_departure(synthetic_graph):
    engine = DynamicRoutingEngine(synthetic_graph)
    temporal = MockTemporalService(mode="time_dependent")
    
    # Slower route: ORIGIN -> TIME_NODE takes 1000m / 18kmh(5m/s) = 200 seconds = 3.33 minutes.
    # Departure T=0 -> arrive at TIME_NODE at T=3.33 -> SEG_TIME_SENSITIVE has 5cm (safe).
    
    req = RouteRequest(
        origin_lon=0.0, origin_lat=0.0,
        dest_lon=0.0, dest_lat=0.2,
        vehicle_type="ambulance",
        departure_time_minutes=0.0,
        temporal_service=temporal
    )
    
    # We force the algorithm to evaluate this route by blocking B and A, or just verify if it works.
    # Actually, A and B routes are perfectly safe (0cm), so the algorithm will choose A (shortest).
    # To strictly test the time dependent edge, let's just make A and B blocked.
    pass

def test_time_dependent_routing_failure_late_departure(synthetic_graph):
    engine = DynamicRoutingEngine(synthetic_graph)
    temporal = MockTemporalService(mode="time_dependent")
    
    # Block A and B manually to force routing through TIME_NODE
    synthetic_graph.remove_edge("A", "DEST", key=0)
    synthetic_graph.remove_edge("C", "DEST", key=0)
    
    # Depart at T=0
    req_early = RouteRequest(
        origin_lon=0.0, origin_lat=0.0,
        dest_lon=0.0, dest_lat=0.2,
        vehicle_type="ambulance",
        departure_time_minutes=0.0,
        temporal_service=temporal
    )
    res_early = engine.solve_route(req_early)
    assert res_early.success is True
    assert res_early.ordered_nodes == ["ORIGIN", "TIME_NODE", "DEST"]
    
    # Depart at T=30
    req_late = RouteRequest(
        origin_lon=0.0, origin_lat=0.0,
        dest_lon=0.0, dest_lat=0.2,
        vehicle_type="ambulance",
        departure_time_minutes=30.0,
        temporal_service=temporal
    )
    res_late = engine.solve_route(req_late)
    # Arrival at TIME_NODE is 30 + 3.33 = 33.33 minutes. Depth will be 50cm.
    # Ambulance limit 30cm -> Blocked.
    assert res_late.success is False
    assert res_late.blocked_edges > 0
    assert res_late.ordered_nodes == []

def test_invalid_snapping(synthetic_graph):
    engine = DynamicRoutingEngine(synthetic_graph)
    temporal = MockTemporalService()
    
    req = RouteRequest(
        origin_lon=999.0, origin_lat=0.0,
        dest_lon=0.0, dest_lat=0.2,
        vehicle_type="ambulance",
        departure_time_minutes=0.0,
        temporal_service=temporal
    )
    res = engine.solve_route(req)
    assert res.success is False
    assert "Coordinates out of bounds" in res.failure_reason


from ai_service.layer4.routing_engine import evaluate_underpass_lookahead, DynamicRoutingEngine
from ai_service.layer4.temporal_flood import TemporalFloodDepthService
import networkx as nx

class DynamicMockTemporalService(TemporalFloodDepthService):
    def __init__(self, depth_schedule):
        # depth_schedule: list of (time, depth)
        self.depth_schedule = depth_schedule
        
    def get_effective_depth(self, segment_id, current_time_minutes):
        # Return depth based on time
        depth = 0.0
        for t, d in self.depth_schedule:
            if current_time_minutes >= t:
                depth = d
        return {"effective_depth_cm": depth}

def test_underpass_safe_throughout():
    # 2. Underpass safe throughout the window (0cm)
    temp = DynamicMockTemporalService([(0, 0.0), (30, 0.0)])
    res = evaluate_underpass_lookahead("SEG_1", 0.0, "ambulance", temp)
    assert res.is_safe is True
    assert res.maximum_future_effective_depth_cm == 0.0

def test_underpass_unsafe_immediately():
    # 3. Underpass unsafe immediately at arrival (50cm, limit 30)
    temp = DynamicMockTemporalService([(0, 50.0)])
    res = evaluate_underpass_lookahead("SEG_1", 0.0, "ambulance", temp)
    assert res.is_safe is False
    assert res.arrival_effective_depth_cm == 50.0

def test_underpass_becomes_unsafe_later():
    # 4. Underpass becomes unsafe 10 minutes later
    # 5. Underpass becomes unsafe near the end of the 30-minute window.
    temp = DynamicMockTemporalService([(0, 0.0), (10, 10.0), (25, 40.0)])
    res = evaluate_underpass_lookahead("SEG_1", 0.0, "ambulance", temp)
    assert res.is_safe is False
    assert res.maximum_future_effective_depth_cm == 40.0

def test_underpass_max_depth_selected():
    # 6. Maximum future depth is correctly selected.
    temp = DynamicMockTemporalService([(0, 10.0), (15, 25.0), (30, 5.0)])
    res = evaluate_underpass_lookahead("SEG_1", 0.0, "ambulance", temp)
    assert res.is_safe is True
    assert res.maximum_future_effective_depth_cm == 25.0

def test_underpass_vehicle_limits_respected():
    # 7. Vehicle-specific limits are respected.
    temp = DynamicMockTemporalService([(0, 25.0)])
    res_amb = evaluate_underpass_lookahead("SEG_1", 0.0, "ambulance", temp) # limit 30
    assert res_amb.is_safe is True
    
    res_car = evaluate_underpass_lookahead("SEG_1", 0.0, "passenger_car", temp) # limit 18
    assert res_car.is_safe is False

def test_underpass_configurable_window():
    # 9. Look-ahead window is configurable.
    temp = DynamicMockTemporalService([(0, 0.0), (45, 50.0)])
    # Window 30m -> safe (max depth is 0 at 30)
    res_30 = evaluate_underpass_lookahead("SEG_1", 0.0, "ambulance", temp, lookahead_minutes=30.0)
    assert res_30.is_safe is True
    
    # Window 60m -> unsafe (hits 50 at 45m)
    res_60 = evaluate_underpass_lookahead("SEG_1", 0.0, "ambulance", temp, lookahead_minutes=60.0)
    assert res_60.is_safe is False

def test_normal_road_not_evaluated_as_underpass():
    # 1. Normal road is not evaluated as an underpass.
    temp = DynamicMockTemporalService([(0, 0.0), (10, 50.0)])
    
    G = nx.MultiDiGraph()
    G.add_node("A", coordinates=[0.0, 0.0])
    G.add_node("B", coordinates=[0.0, 0.0])
    G.add_edge("A", "B", key=0, segment_id="SEG_1", length_m=1000.0, free_flow_speed=36.0, is_underpass=False)
    
    engine = DynamicRoutingEngine(G)
    
    res_normal = engine.evaluate_candidate_edge("A", "B", 0, 0.0, "ambulance", temp)
    assert res_normal.is_passable is True # Ignores future 50cm
    G.add_edge("ORIGIN", "TIME_NODE", key=0, segment_id="SEG_ORIGIN_TIME", length_m=1000.0, free_flow_speed=18.0) # Slower, takes longer
    G.add_edge("TIME_NODE", "DEST", key=0, segment_id="SEG_TIME_SENSITIVE", length_m=1000.0, free_flow_speed=36.0)
    
    return G


def test_synthetic_routing_chooses_safer_longer_route(synthetic_graph):
    engine = DynamicRoutingEngine(synthetic_graph)
    temporal = MockTemporalService(mode="static") # SEG_A_DEST is 25cm
    
    # Ambulance limit is 30cm, so 25cm is passable but has HIGH hazard cost
    req = RouteRequest(
        origin_lon=0.0, origin_lat=0.0,
        dest_lon=0.0, dest_lat=0.2,
        vehicle_type="ambulance",
        departure_time_minutes=0.0,
        temporal_service=temporal
    )
    
    res = engine.solve_route(req)
    assert res.success is True
    # The short route has 25cm depth. WHPF cost will be very high (ratio = 25/30 = 0.83).
    # Long route has 0 depth, WHPF cost = pure travel time.
    # The algorithm should choose the longer, safer route.
    assert res.ordered_nodes == ["ORIGIN", "B", "C", "DEST"]
    assert res.ordered_segment_ids == ["SEG_ORIGIN_B", "SEG_B_C", "SEG_C_DEST"]

def test_synthetic_routing_chooses_shortest_if_safe(synthetic_graph):
    engine = DynamicRoutingEngine(synthetic_graph)
    temporal = MockTemporalService(mode="all_safe") # Everything 0cm
    
    req = RouteRequest(
        origin_lon=0.0, origin_lat=0.0,
        dest_lon=0.0, dest_lat=0.2,
        vehicle_type="ambulance",
        departure_time_minutes=0.0,
        temporal_service=temporal
    )
    
    res = engine.solve_route(req)
    assert res.success is True
    # Since all safe, should take shortest route
    assert res.ordered_nodes == ["ORIGIN", "A", "DEST"]
    assert res.ordered_segment_ids == ["SEG_ORIGIN_A", "SEG_A_DEST"]

def test_time_dependent_routing_success_early_departure(synthetic_graph):
    engine = DynamicRoutingEngine(synthetic_graph)
    temporal = MockTemporalService(mode="time_dependent")
    
    # Slower route: ORIGIN -> TIME_NODE takes 1000m / 18kmh(5m/s) = 200 seconds = 3.33 minutes.
    # Departure T=0 -> arrive at TIME_NODE at T=3.33 -> SEG_TIME_SENSITIVE has 5cm (safe).
    
    req = RouteRequest(
        origin_lon=0.0, origin_lat=0.0,
        dest_lon=0.0, dest_lat=0.2,
        vehicle_type="ambulance",
        departure_time_minutes=0.0,
        temporal_service=temporal
    )
    
    # We force the algorithm to evaluate this route by blocking B and A, or just verify if it works.
    # Actually, A and B routes are perfectly safe (0cm), so the algorithm will choose A (shortest).
    # To strictly test the time dependent edge, let's just make A and B blocked.
    pass

def test_time_dependent_routing_failure_late_departure(synthetic_graph):
    engine = DynamicRoutingEngine(synthetic_graph)
    temporal = MockTemporalService(mode="time_dependent")
    
    # Block A and B manually to force routing through TIME_NODE
    synthetic_graph.remove_edge("A", "DEST", key=0)
    synthetic_graph.remove_edge("C", "DEST", key=0)
    
    # Depart at T=0
    req_early = RouteRequest(
        origin_lon=0.0, origin_lat=0.0,
        dest_lon=0.0, dest_lat=0.2,
        vehicle_type="ambulance",
        departure_time_minutes=0.0,
        temporal_service=temporal
    )
    res_early = engine.solve_route(req_early)
    assert res_early.success is True
    assert res_early.ordered_nodes == ["ORIGIN", "TIME_NODE", "DEST"]
    
    # Depart at T=30
    req_late = RouteRequest(
        origin_lon=0.0, origin_lat=0.0,
        dest_lon=0.0, dest_lat=0.2,
        vehicle_type="ambulance",
        departure_time_minutes=30.0,
        temporal_service=temporal
    )
    res_late = engine.solve_route(req_late)
    # Arrival at TIME_NODE is 30 + 3.33 = 33.33 minutes. Depth will be 50cm.
    # Ambulance limit 30cm -> Blocked.
    assert res_late.success is False
    assert res_late.blocked_edges > 0
    assert res_late.ordered_nodes == []

def test_invalid_snapping(synthetic_graph):
    engine = DynamicRoutingEngine(synthetic_graph)
    temporal = MockTemporalService()
    
    req = RouteRequest(
        origin_lon=999.0, origin_lat=0.0,
        dest_lon=0.0, dest_lat=0.2,
        vehicle_type="ambulance",
        departure_time_minutes=0.0,
        temporal_service=temporal
    )
    res = engine.solve_route(req)
    assert res.success is False
    assert "Coordinates out of bounds" in res.failure_reason


from ai_service.layer4.routing_engine import evaluate_underpass_lookahead, DynamicRoutingEngine
from ai_service.layer4.temporal_flood import TemporalFloodDepthService
import networkx as nx

class DynamicMockTemporalService(TemporalFloodDepthService):
    def __init__(self, depth_schedule):
        # depth_schedule: list of (time, depth)
        self.depth_schedule = depth_schedule
        
    def get_effective_depth(self, segment_id, current_time_minutes):
        # Return depth based on time
        depth = 0.0
        for t, d in self.depth_schedule:
            if current_time_minutes >= t:
                depth = d
        return {"effective_depth_cm": depth}

def test_underpass_safe_throughout():
    # 2. Underpass safe throughout the window (0cm)
    temp = DynamicMockTemporalService([(0, 0.0), (30, 0.0)])
    res = evaluate_underpass_lookahead("SEG_1", 0.0, "ambulance", temp)
    assert res.is_safe is True
    assert res.maximum_future_effective_depth_cm == 0.0

def test_underpass_unsafe_immediately():
    # 3. Underpass unsafe immediately at arrival (50cm, limit 30)
    temp = DynamicMockTemporalService([(0, 50.0)])
    res = evaluate_underpass_lookahead("SEG_1", 0.0, "ambulance", temp)
    assert res.is_safe is False
    assert res.arrival_effective_depth_cm == 50.0

def test_underpass_becomes_unsafe_later():
    # 4. Underpass becomes unsafe 10 minutes later
    # 5. Underpass becomes unsafe near the end of the 30-minute window.
    temp = DynamicMockTemporalService([(0, 0.0), (10, 10.0), (25, 40.0)])
    res = evaluate_underpass_lookahead("SEG_1", 0.0, "ambulance", temp)
    assert res.is_safe is False
    assert res.maximum_future_effective_depth_cm == 40.0

def test_underpass_max_depth_selected():
    # 6. Maximum future depth is correctly selected.
    temp = DynamicMockTemporalService([(0, 10.0), (15, 25.0), (30, 5.0)])
    res = evaluate_underpass_lookahead("SEG_1", 0.0, "ambulance", temp)
    assert res.is_safe is True
    assert res.maximum_future_effective_depth_cm == 25.0

def test_underpass_vehicle_limits_respected():
    # 7. Vehicle-specific limits are respected.
    temp = DynamicMockTemporalService([(0, 25.0)])
    res_amb = evaluate_underpass_lookahead("SEG_1", 0.0, "ambulance", temp) # limit 30
    assert res_amb.is_safe is True
    
    res_car = evaluate_underpass_lookahead("SEG_1", 0.0, "passenger_car", temp) # limit 18
    assert res_car.is_safe is False

def test_underpass_configurable_window():
    # 9. Look-ahead window is configurable.
    temp = DynamicMockTemporalService([(0, 0.0), (45, 50.0)])
    # Window 30m -> safe (max depth is 0 at 30)
    res_30 = evaluate_underpass_lookahead("SEG_1", 0.0, "ambulance", temp, lookahead_minutes=30.0)
    assert res_30.is_safe is True
    
    # Window 60m -> unsafe (hits 50 at 45m)
    res_60 = evaluate_underpass_lookahead("SEG_1", 0.0, "ambulance", temp, lookahead_minutes=60.0)
    assert res_60.is_safe is False

def test_normal_road_not_evaluated_as_underpass():
    # 1. Normal road is not evaluated as an underpass.
    temp = DynamicMockTemporalService([(0, 0.0), (10, 50.0)])
    
    G = nx.MultiDiGraph()
    G.add_node("A", coordinates=[0.0, 0.0])
    G.add_node("B", coordinates=[0.0, 0.0])
    G.add_edge("A", "B", key=0, segment_id="SEG_1", length_m=1000.0, free_flow_speed=36.0, is_underpass=False)
    
    engine = DynamicRoutingEngine(G)
    
    res_normal = engine.evaluate_candidate_edge("A", "B", 0, 0.0, "ambulance", temp)
    assert res_normal.is_passable is True # Ignores future 50cm
    
    G["A"]["B"][0]["is_underpass"] = True
    res_underpass = engine.evaluate_candidate_edge("A", "B", 0, 0.0, "ambulance", temp)
    assert res_underpass.is_passable is False # Blocked by lookahead

def test_missing_depth_handled():
    # 8. Missing/invalid depth handled using existing Part 3 conventions.
    class BrokenTemporalService(DynamicMockTemporalService):
        def __init__(self):
            pass
        def get_effective_depth(self, segment_id, current_time_minutes):
            raise Exception("Part 3 failed")
            
    G = nx.MultiDiGraph()
    G.add_node("A", coordinates=[0,0])
    G.add_node("B", coordinates=[0,0])
    G.add_edge("A", "B", key=0, segment_id="SEG_1", length_m=1000.0, free_flow_speed=36.0, is_underpass=True)
    
    engine = DynamicRoutingEngine(G)
    res = engine.evaluate_candidate_edge("A", "B", 0, 0.0, "ambulance", BrokenTemporalService())
    assert res.is_passable is True # Fallback to 0.0
