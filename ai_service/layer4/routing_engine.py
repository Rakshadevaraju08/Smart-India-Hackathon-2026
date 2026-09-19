"""
Layer 4: Routing Engine
Implements Time-Dependent A* algorithm for safe emergency routing.
"""
import heapq
import itertools
import math
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import networkx as nx
from scipy.spatial import cKDTree

from ai_service.layer4.temporal_flood import TemporalFloodDepthService
from ai_service.layer4.risk_cost_evaluator import FloodHazardEvaluator

logger = logging.getLogger(__name__)

def haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Calculates great-circle distance between two points on earth in meters."""
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0)**2
    return 2.0 * R * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

@dataclass
class RouteRequest:
    origin_lon: float
    origin_lat: float
    dest_lon: float
    dest_lat: float
    vehicle_type: str
    departure_time_minutes: int
    layer3_result: Any  # Expected to be Layer3Result interface

@dataclass
class RouteResult:
    ordered_nodes: List[str]
    ordered_segments: List[str]
    route_geometry: List[Tuple[float, float]]
    total_distance_km: float
    total_physical_time_minutes: float
    arrival_time_minutes: float
    accumulated_hazard_cost_seconds: float
    vehicle_type: str
    departure_time_minutes: int
    diagnostics: Dict[str, Any]

class DynamicRoutingEngine:
    def __init__(self, G: nx.MultiDiGraph):
        if not isinstance(G, nx.MultiDiGraph):
            raise TypeError("Expected a NetworkX MultiDiGraph")
        self.G = G
        self.nodes_list = list(self.G.nodes(data=True))
        self.node_ids = [n for n, _ in self.nodes_list]
        self._build_spatial_index()
        
        # Max speed in graph (for admissible heuristic)
        self.max_speed_m_per_s = 1.0
        for u, v, k, d in self.G.edges(data=True, keys=True):
            speed_kmh = d.get("free_flow_speed", 15.0)
            if speed_kmh > 0:
                self.max_speed_m_per_s = max(self.max_speed_m_per_s, speed_kmh / 3.6)

    def _build_spatial_index(self):
        coords = []
        for n, data in self.nodes_list:
            coord = data.get("coordinates")
            if coord and len(coord) >= 2:
                # Scipy KDTree expects (x, y) = (lon, lat)
                coords.append([coord[0], coord[1]])
            else:
                coords.append([0.0, 0.0]) # Fallback (should not happen in valid graph)
        self.kdtree = cKDTree(coords)

    def find_nearest_node(self, lon: float, lat: float) -> str:
        """Finds nearest node ID for given lon/lat."""
        _, idx = self.kdtree.query([lon, lat])
        return self.node_ids[idx]
        
    def solve_route(self, req: RouteRequest) -> RouteResult:
        u_start = self.find_nearest_node(req.origin_lon, req.origin_lat)
        v_dest = self.find_nearest_node(req.dest_lon, req.dest_lat)
        
        temporal_service = TemporalFloodDepthService(req.layer3_result)
        
        dest_data = self.G.nodes[v_dest]
        dest_lon, dest_lat = dest_data["coordinates"][0], dest_data["coordinates"][1]
        
        def heuristic(u_node: str) -> float:
            u_data = self.G.nodes[u_node]
            u_lon, u_lat = u_data["coordinates"][0], u_data["coordinates"][1]
            dist_m = haversine_m(u_lon, u_lat, dest_lon, dest_lat)
            # Minimum possible hazard cost is free flow travel time (hazard ratio = 0)
            return dist_m / self.max_speed_m_per_s

        # Priority queue stores: (f_score, counter, node_id, current_hazard_cost, current_actual_time_seconds)
        pq = []
        counter = itertools.count()
        
        # We track best known hazard cost to reach a node
        g_scores = {u_start: 0.0}
        
        # came_from[node] = (prev_node, edge_key, segment_id, edge_hazard_cost, edge_actual_time_sec)
        came_from = {}
        
        heapq.heappush(pq, (heuristic(u_start), next(counter), u_start, 0.0, 0.0))
        
        nodes_expanded = 0
        blocked_edges = 0
        
        while pq:
            f_cur, _, u, cur_hazard, cur_actual_time = heapq.heappop(pq)
            
            if u == v_dest:
                break
                
            # If we already found a strictly better path to u, skip
            if cur_hazard > g_scores.get(u, float('inf')):
                continue
                
            nodes_expanded += 1
            
            # Arrival time at u in minutes since forecast start
            arrival_time_u_min = req.departure_time_minutes + (cur_actual_time / 60.0)
            
            # Explore neighbors
            for v, edge_keys in self.G[u].items():
                for k, edge_data in edge_keys.items():
                    segment_id = edge_data.get("segment_id")
                    length_m = edge_data.get("length_m", 1.0)
                    speed_kmh = edge_data.get("free_flow_speed", 15.0)
                    
                    if not segment_id:
                        continue
                        
                    # 1. Get Effective Depth at Arrival Time
                    try:
                        temp_res = temporal_service.get_effective_depth(segment_id, arrival_time_u_min)
                        effective_depth_cm = temp_res["effective_depth_cm"]
                    except Exception as e:
                        logger.warning(f"Depth query failed for {segment_id}: {e}")
                        effective_depth_cm = 0.0
                        
                    # 2. Get Vehicle Risk and Cost
                    try:
                        risk_res = FloodHazardEvaluator.evaluate_road_risk(
                            segment_id=segment_id,
                            length_m=length_m,
                            free_flow_speed_kmh=speed_kmh,
                            effective_depth_cm=effective_depth_cm,
                            vehicle_type=req.vehicle_type
                        )
                    except Exception as e:
                        logger.warning(f"Risk evaluation failed for {segment_id}: {e}")
                        continue
                        
                    if not risk_res["is_passable"]:
                        blocked_edges += 1
                        continue
                        
                    edge_hazard = risk_res["hazard_cost_seconds"]
                    edge_actual = risk_res["actual_travel_time_seconds"]
                    
                    tentative_hazard = cur_hazard + edge_hazard
                    
                    if tentative_hazard < g_scores.get(v, float('inf')):
                        g_scores[v] = tentative_hazard
                        came_from[v] = (u, k, segment_id, edge_hazard, edge_actual, length_m)
                        
                        f_score = tentative_hazard + heuristic(v)
                        heapq.heappush(pq, (f_score, next(counter), v, tentative_hazard, cur_actual_time + edge_actual))
        
        # Path reconstruction
        ordered_nodes = []
        ordered_segments = []
        route_geom = []
        total_dist_m = 0.0
        
        if v_dest in came_from:
            curr = v_dest
            while curr != u_start:
                ordered_nodes.append(curr)
                prev, k, seg_id, h_cost, a_cost, length = came_from[curr]
                ordered_segments.append(seg_id)
                total_dist_m += length
                
                curr_node_data = self.G.nodes[curr]
                route_geom.append((curr_node_data["coordinates"][0], curr_node_data["coordinates"][1]))
                
                curr = prev
            
            ordered_nodes.append(u_start)
            start_node_data = self.G.nodes[u_start]
            route_geom.append((start_node_data["coordinates"][0], start_node_data["coordinates"][1]))
            
            ordered_nodes.reverse()
            ordered_segments.reverse()
            route_geom.reverse()
            
            success = True
            failure_reason = None
        else:
            success = False
            failure_reason = "No path found."
            
        final_hazard = g_scores.get(v_dest, float('inf'))
        
        # Compute final physical time
        final_physical_sec = 0.0
        if success:
            curr = v_dest
            while curr != u_start:
                prev, k, seg_id, h_cost, a_cost, length = came_from[curr]
                final_physical_sec += a_cost
                curr = prev
                
        final_physical_min = final_physical_sec / 60.0
        
        return RouteResult(
            ordered_nodes=ordered_nodes,
            ordered_segments=ordered_segments,
            route_geometry=route_geom,
            total_distance_km=total_dist_m / 1000.0,
            total_physical_time_minutes=final_physical_min,
            arrival_time_minutes=req.departure_time_minutes + final_physical_min,
            accumulated_hazard_cost_seconds=final_hazard if success else float('inf'),
            vehicle_type=req.vehicle_type,
            departure_time_minutes=req.departure_time_minutes,
            diagnostics={
                "nodes_expanded": nodes_expanded,
                "blocked_edges_encountered": blocked_edges,
                "origin_snapped_node": u_start,
                "dest_snapped_node": v_dest,
                "success": success,
                "failure_reason": failure_reason
            }
        )
