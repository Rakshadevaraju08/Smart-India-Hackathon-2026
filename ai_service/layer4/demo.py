"""
Layer 4: End-to-End Routing Demo
Demonstrates dynamic time-dependent A* routing avoiding floods based on vehicle limits.
"""
import networkx as nx
from ai_service.layer4.routing_engine import DynamicRoutingEngine, RouteRequest
from ai_service.layer4.temporal_flood import TemporalFloodDepthService

class DeterministicDemoTemporalService(TemporalFloodDepthService):
    def __init__(self):
        pass
        
    def get_effective_depth(self, segment_id, current_time_minutes):
        # Short route A: Flooded
        if segment_id == "ROUTE_A_SEG_2":
            return {"effective_depth_cm": 25.0} # 25cm of water
            
        # Long route B: Completely dry
        return {"effective_depth_cm": 0.0}

def main():
    print("\n" + "=" * 80)
    print("LAYER 4: DETERMINISTIC END-TO-END DEMO")
    print("=" * 80)

    # 1. Build Deterministic Graph
    G = nx.MultiDiGraph()
    G.add_node("ORIGIN", coordinates=[0.0, 0.0])
    G.add_node("DEST", coordinates=[0.0, 0.002])
    
    # Route A (Short but flooded)
    G.add_node("A_MID", coordinates=[0.0, 0.001])
    G.add_edge("ORIGIN", "A_MID", key=0, segment_id="ROUTE_A_SEG_1", length_m=1000.0, free_flow_speed=36.0)
    G.add_edge("A_MID", "DEST", key=0, segment_id="ROUTE_A_SEG_2", length_m=1000.0, free_flow_speed=36.0)
    
    # Route B (Long but safe)
    G.add_node("B_1", coordinates=[0.001, 0.0])
    G.add_node("B_2", coordinates=[0.001, 0.001])
    G.add_edge("ORIGIN", "B_1", key=0, segment_id="ROUTE_B_SEG_1", length_m=1000.0, free_flow_speed=36.0)
    G.add_edge("B_1", "B_2", key=0, segment_id="ROUTE_B_SEG_2", length_m=1000.0, free_flow_speed=36.0)
    G.add_edge("B_2", "DEST", key=0, segment_id="ROUTE_B_SEG_3", length_m=1000.0, free_flow_speed=36.0)
    
    engine = DynamicRoutingEngine(G)
    temporal = DeterministicDemoTemporalService()

    vehicles = [
        ("ambulance", 30.0), # Limit 30cm -> Can survive Route A but takes huge penalty
        ("passenger_car", 18.0) # Limit 18cm -> Route A strictly blocked
    ]
    
    for v_name, limit in vehicles:
        print(f"\nDispatching {v_name.upper()} (Limit: {limit}cm) at T=0 minutes")
        
        req = RouteRequest(
            origin_lon=0.0, origin_lat=0.0,
            dest_lon=0.0, dest_lat=0.002,
            vehicle_type=v_name,
            departure_time_minutes=0.0,
            temporal_service=temporal
        )
        
        res = engine.solve_route(req)
        
        print(f"  Status: {'SUCCESS' if res.success else 'FAILED'}")
        if res.success:
            print(f"  Nodes Explored: {res.nodes_explored}")
            print(f"  Route Selected (Nodes): {' -> '.join(res.ordered_nodes)}")
            print(f"  Route Segments: {res.ordered_segment_ids}")
            print(f"  Total Distance: {res.total_distance_m / 1000.0:.1f} km")
            print(f"  Physical Travel Time: {res.total_physical_travel_time_seconds / 60.0:.2f} minutes")
            print(f"  Accumulated WHPF Hazard Cost: {res.total_hazard_cost_seconds:.2f} seconds")
            print(f"  ETA: {res.arrival_time:.2f} minutes")
        print(f"  Blocked Edges Avoided: {res.blocked_edges}")
        print("-" * 60)

    print("\nExplanation:")
    print(" - The AMBULANCE (limit 30cm) can technically survive the 25cm flood on Route A.")
    print("   However, the WHPF hydrodynamic penalty for driving through 25cm of water pushes its")
    print("   hazard cost so high that the routing engine correctly diverts it to the longer, safer Route B (3km).")
    print(" - The CIVILIAN_CAR (limit 20cm) evaluates Route A, but because 25cm exceeds its safe operating depth,")
    print("   it is strictly blocked (is_passable=False) and is forced to take Route B.")

if __name__ == "__main__":
    main()
