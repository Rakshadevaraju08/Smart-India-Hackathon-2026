"""
Layer 4: Service Orchestrator - Dynamic Safe Emergency Navigation & Critical Assets Safeguarding.

Connects routing algorithms, depth interpolation, risk evaluation, and critical asset monitoring
under a single unified orchestration service.
"""

import logging
from typing import Any, Dict, List, Optional
import networkx as nx

from ai_service.layer4.road_graph import load_graph
from ai_service.layer4.layer3_mock import Layer3ProviderInterface, MockLayer3Provider
from ai_service.layer4.temporal_flood import TemporalFloodDepthService
from ai_service.layer4.routing_engine import DynamicRoutingEngine, RouteRequest, RouteResult
from ai_service.layer4.critical_assets_monitor import CriticalAssetsMonitor, SubstationMonitoringResult

logger = logging.getLogger(__name__)

class Layer4Service:
    """Unified Orchestration Service for Layer 4 Flood Nowcasting."""
    
    def __init__(
        self,
        graph_path: Optional[str] = None,
        routing_graph: Optional[nx.MultiDiGraph] = None,
        layer3_provider: Optional[Layer3ProviderInterface] = None,
        asset_monitor: Optional[CriticalAssetsMonitor] = None
    ):
        """Initializes the Layer 4 Service via dependency injection."""
        logger.info("Initializing Layer 4 Service Orchestrator...")
        
        # 1. Road Graph
        if routing_graph is not None:
            self.graph = routing_graph
        elif graph_path is not None:
            self.graph = load_graph(graph_path)
        else:
            raise ValueError("Must provide either routing_graph or graph_path")
            
        # 2. Layer 3 Provider (Dependency Injected)
        self.layer3_provider = layer3_provider or MockLayer3Provider(self.graph)
        
        # 3. Routing Engine
        self.routing_engine = DynamicRoutingEngine(self.graph)
        
        # 4. Critical Asset Monitor
        self.asset_monitor = asset_monitor or CriticalAssetsMonitor()
        
    def route(
        self,
        vehicle_type: str,
        origin_lon: float,
        origin_lat: float,
        dest_lon: float,
        dest_lat: float,
        departure_time_minutes: float = 0.0
    ) -> Dict[str, Any]:
        """
        Public operation: Orchestrates the time-dependent A* routing algorithm.
        """
        try:
            # 1. Fetch live or mocked Layer 3 predictions using the injected provider contract
            layer3_result = self.layer3_provider.get_predictions()
            
            # 2. Initialize depth interpolator with the result
            temporal_service = TemporalFloodDepthService(layer3_result)
            
            # 3. Prepare strict request
            req = RouteRequest(
                origin_lon=origin_lon,
                origin_lat=origin_lat,
                dest_lon=dest_lon,
                dest_lat=dest_lat,
                vehicle_type=vehicle_type,
                departure_time_minutes=departure_time_minutes,
                temporal_service=temporal_service
            )
            
            # 4. Execute safe A*
            res = self.routing_engine.solve_route(req)
            
            # Handle infinite hazard cost for JSON serialization
            hazard_cost = getattr(res, 'total_hazard_cost_seconds', 0.0)
            import math
            if math.isinf(hazard_cost):
                hazard_cost = -1.0
                
            # 5. Format return struct matching required contract
            return {
                "status": "SUCCESS" if res.success else "FAILED",
                "route_geometry": getattr(res, 'route_geometry', []),
                "ordered_segment_ids": getattr(res, 'ordered_segment_ids', []),
                "ordered_node_ids": getattr(res, 'ordered_nodes', []),
                "total_distance_m": getattr(res, 'total_distance_m', 0.0),
                "physical_travel_time_min": getattr(res, 'total_physical_travel_time_seconds', 0.0) / 60.0 if res.success else 0.0,
                "eta_min": getattr(res, 'arrival_time', 0.0) if res.success else 0.0,
                "hazard_cost": hazard_cost,
                "maximum_effective_depth": getattr(res, 'maximum_effective_depth', 0.0),
                "maximum_hazard_ratio": getattr(res, 'maximum_hazard_ratio', 0.0),
                "minimum_clearance": getattr(res, 'minimum_clearance', 0.0),
                "hazard_category": getattr(res, 'hazard_category', 'UNKNOWN'),
                "underpasses_used": getattr(res, 'underpasses_used', []),
                "underpasses_avoided": getattr(res, 'underpasses_avoided', []),
                "nodes_explored": getattr(res, 'nodes_explored', 0),
                "blocked_edges": getattr(res, 'blocked_edges', 0),
                "failure_reason": getattr(res, 'failure_reason', None)
            }
            
        except Exception as e:
            logger.error(f"Routing failed due to internal error: {e}")
            return {
                "status": "FAILED",
                "failure_reason": f"Internal Error: {str(e)}"
            }

    def get_asset_status(self) -> Dict[str, Any]:
        """
        Public operation: Orchestrates critical asset flood risk monitoring.
        """
        try:
            # 1. Fetch Layer 3 predictions
            layer3_result = self.layer3_provider.get_predictions()
            
            # 2. Initialize temporal interpolator
            temporal_service = TemporalFloodDepthService(layer3_result)
            
            # 3. Evaluate risk across all assets
            subs_results = self.asset_monitor.evaluate_substations(temporal_service)
            
            # 4. Serialize struct
            assets_out = []
            for res in subs_results:
                assets_out.append({
                    "substation_id": res.substation_id,
                    "name": res.name,
                    "voltage_kv": res.voltage_kv,
                    "latitude": res.latitude,
                    "longitude": res.longitude,
                    "status": res.flood_status,
                    "maximum_site_depth_cm": res.maximum_effective_depth,
                    "supporting_road_segment_ids": [res.road_segment_id] if res.road_segment_id else [],
                    "uncertainty": res.uncertainty_flag,
                    "explanation": res.explanation
                })
                
            return {
                "status": "SUCCESS",
                "total_monitored": len(assets_out),
                "assets": assets_out
            }
            
        except Exception as e:
            logger.error(f"Asset monitoring failed due to internal error: {e}")
            return {
                "status": "FAILED",
                "error": str(e)
            }
