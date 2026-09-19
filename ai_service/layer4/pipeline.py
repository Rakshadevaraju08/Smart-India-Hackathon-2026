"""
Layer 4: Pipeline - Dynamic Safe Emergency Navigation & Critical Assets Safeguarding.

Orchestrates:
1. Routing Graph loading (Part 1)
2. Layer 3 Flood Depth fetching (Part 2 Mock)
3. Time-dependent A* Routing (Parts 3, 4, 5)
4. Critical Asset Monitoring (TANGEDCO Substations & Oxygen Depots)
"""
import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

from ai_service.layer4.road_graph import load_graph
from ai_service.layer4.layer3_mock import MockLayer3Provider
from ai_service.layer4.temporal_flood import TemporalFloodDepthService
from ai_service.layer4.routing_engine import DynamicRoutingEngine, RouteRequest
from ai_service.layer4.critical_assets_monitor import CriticalAssetsMonitor

logger = logging.getLogger(__name__)

class Layer4Pipeline:
    def __init__(self, graph_path: str):
        logger.info(f"Loading routing graph from {graph_path}...")
        self.graph = load_graph(graph_path)
        
        logger.info("Initializing routing engine and asset monitor...")
        self.routing_engine = DynamicRoutingEngine(self.graph)
        
        # Asset monitor is now completely independent and decoupled from routing graph
        self.asset_monitor = CriticalAssetsMonitor()

    def run_routing(
        self,
        origin_lon: float,
        origin_lat: float,
        dest_lon: float,
        dest_lat: float,
        vehicle_type: str,
        departure_time_minutes: float = 0.0
    ):
        """Orchestrates the routing pipeline."""
        logger.info("Fetching Layer 3 flood predictions...")
        provider = MockLayer3Provider(self.graph)
        layer3_result = provider.get_predictions()
        
        temporal_service = TemporalFloodDepthService(layer3_result)
        
        req = RouteRequest(
            origin_lon=origin_lon,
            origin_lat=origin_lat,
            dest_lon=dest_lon,
            dest_lat=dest_lat,
            vehicle_type=vehicle_type,
            departure_time_minutes=departure_time_minutes,
            temporal_service=temporal_service
        )
        
        logger.info(f"Solving safe route for {vehicle_type}...")
        res = self.routing_engine.solve_route(req)
        return res

    def run_asset_monitor(self):
        """Orchestrates the independent asset monitoring pipeline."""
        logger.info("Fetching Layer 3 flood predictions for Asset Monitor...")
        provider = MockLayer3Provider(self.graph)
        layer3_result = provider.get_predictions()
        temporal_service = TemporalFloodDepthService(layer3_result)
        
        subs_results = self.asset_monitor.evaluate_substations(temporal_service)
        return subs_results


def main():
    parser = argparse.ArgumentParser(description="Layer 4 Master Pipeline Demo")
    parser.add_argument("--graph", type=str, default="ai_service/layer4/data/routing_graph.pkl")
    parser.add_argument("--vehicle", type=str, default="ambulance", choices=["ambulance", "passenger_car", "two_wheeler"])
    args = parser.parse_args()

    if not os.path.exists(args.graph):
        print(f"Error: Routing graph not found at {args.graph}")
        print("Please run road_graph.py to generate it first.")
        return

    pipeline = Layer4Pipeline(args.graph)

    # Demo Corridor: T. Nagar to Apollo
    orig_lon, orig_lat = 80.2341, 13.0418
    dest_lon, dest_lat = 80.2514, 13.0604

    print("\n" + "=" * 80)
    print("LAYER 4: SAFE EMERGENCY NAVIGATION & ASSET SAFEGUARDING DEMO")
    print("=" * 80)

    # 1. Asset Monitoring (Independent)
    subs = pipeline.run_asset_monitor()
    
    print(f"\n[Critical Assets] Substations Monitored: {len(subs)}")
    for res in subs:
        if res.flood_status != "UNKNOWN":
            print(f"  [{res.flood_status}] {res.name} (Max Depth: {res.maximum_effective_depth}cm)")
        else:
            print(f"  [{res.flood_status}] {res.name} (Uncertainty: {res.uncertainty_flag})")
            
    # Show detailed demo for first 3
    print("\n--- Detailed Output (First 3) ---")
    for res in subs[:3]:
        print(json.dumps(res.__dict__, indent=2))
        
    print("-" * 80)

    # 2. Routing Comparison
    vehicles_to_test = ["two_wheeler", "passenger_car", "ambulance"]
    
    for v_type in vehicles_to_test:
        print(f"\nDispatching {v_type.upper()} at T=0 minutes...")
        res = pipeline.run_routing(
            origin_lon=orig_lon,
            origin_lat=orig_lat,
            dest_lon=dest_lon,
            dest_lat=dest_lat,
            vehicle_type=v_type,
            departure_time_minutes=0.0
        )
        
        if res.success:
            print(f"  Status: SUCCESS")
            print(f"  Nodes Explored: {res.nodes_explored}")
            print(f"  Physical Travel Time: {res.total_physical_travel_time_seconds / 60.0:.2f} minutes")
        else:
            print(f"  Status: FAILED")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
