import sys
import logging
from pprint import pprint
from ai_service.layer4.road_graph import load_graph, SegmentLookup
from ai_service.layer4.layer3_mock import MockLayer3Provider
from ai_service.layer4.temporal_flood import TemporalFloodDepthService
from ai_service.layer4.risk_cost_evaluator import FloodHazardEvaluator

logging.basicConfig(level=logging.ERROR)

def run_verification():
    print("--- E2E VERIFICATION ---")
    
    # 1. Load Graph
    graph_path = "ai_service/layer4/data/routing_graph.pkl"
    try:
        G = load_graph(graph_path)
        print(f"Graph nodes: {G.number_of_nodes()}")
        print(f"Graph edges: {G.number_of_edges()}")
    except Exception as e:
        print(f"Failed to load graph: {e}")
        return

    lookup = SegmentLookup(G)
    all_segments = list(lookup.index.keys())
    print(f"Unique segment IDs: {len(all_segments)}")
    
    if not all_segments:
        print("No segments found!")
        return
        
    # 2. Pick a real segment
    test_segment = list(all_segments)[0]
    edge_data = lookup.get_segment(test_segment)
    print(f"\nSelected Segment: {test_segment}")
    print(f"Length: {edge_data.get('length_m')} m")
    print(f"Speed: {edge_data.get('free_flow_speed')} km/h")
    
    # 3. Layer 3 Mock
    provider = MockLayer3Provider(G)
    l3_res = provider.get_predictions()
    
    # 4. Temporal Flood (T+45)
    temporal_service = TemporalFloodDepthService(l3_res)
    t45_res = temporal_service.get_effective_depth(test_segment, 45)
    
    print("\n--- Temporal Depth @ T+45 ---")
    for k, v in t45_res.items():
        print(f"{k}: {v}")
        
    effective_depth = t45_res["effective_depth_cm"]
    
    # 5. Vehicle Risk
    vehicles = ["two_wheeler", "passenger_car", "ambulance", "ndrf_heavy_rescue"]
    print("\n--- Vehicle Risk ---")
    for v in vehicles:
        risk = FloodHazardEvaluator.evaluate_road_risk(
            segment_id=test_segment,
            length_m=edge_data["length_m"],
            free_flow_speed_kmh=edge_data["free_flow_speed"],
            effective_depth_cm=effective_depth,
            vehicle_type=v
        )
        print(f"\nVehicle: {v}")
        print(f"Limit: {risk['vehicle_depth_limit_cm']} cm")
        print(f"Hazard Ratio: {risk['hazard_ratio']}")
        print(f"Passable: {risk['is_passable']}")
        print(f"WHPF Cost (s): {risk['hazard_cost_seconds']}")
        print(f"Adjusted Speed (m/s): {risk['adjusted_speed_m_per_s']}")
        print(f"Actual Time (s): {risk['actual_travel_time_seconds']}")

    print("\n--- NUMERICAL CROSS-CHECK ---")
    cross_check = FloodHazardEvaluator.evaluate_road_risk(
        segment_id="MANUAL_CHECK",
        length_m=1000.0,
        free_flow_speed_kmh=36.0,
        effective_depth_cm=9.0,
        vehicle_type="passenger_car"
    )
    for k, v in cross_check.items():
        print(f"{k}: {v}")

    print("\n--- BLOCKED-ROAD CROSS-CHECK (18cm) ---")
    blocked1 = FloodHazardEvaluator.evaluate_road_risk(
        segment_id="MANUAL_CHECK",
        length_m=1000.0,
        free_flow_speed_kmh=36.0,
        effective_depth_cm=18.0,
        vehicle_type="passenger_car"
    )
    print(f"Ratio: {blocked1['hazard_ratio']}")
    print(f"Passable: {blocked1['is_passable']}")
    print(f"Cost: {blocked1['hazard_cost_seconds']}")
    print(f"Adjusted Speed: {blocked1['adjusted_speed_m_per_s']}")
    
    print("\n--- BLOCKED-ROAD CROSS-CHECK (25cm) ---")
    blocked2 = FloodHazardEvaluator.evaluate_road_risk(
        segment_id="MANUAL_CHECK",
        length_m=1000.0,
        free_flow_speed_kmh=36.0,
        effective_depth_cm=25.0,
        vehicle_type="passenger_car"
    )
    print(f"Ratio: {blocked2['hazard_ratio']}")
    print(f"Passable: {blocked2['is_passable']}")

if __name__ == "__main__":
    run_verification()
