"""
Layer 4: Routing Engine
Foundations for time-dependent safe emergency routing.
"""
import math
import heapq
import itertools
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
class SnappingResult:
    requested_lon: float
    requested_lat: float
    snapped_node_id: str
    snapping_distance_m: float

@dataclass
class EdgeEvaluationResult:
    source_node: str
    target_node: str
    segment_id: str
    arrival_time_at_edge_minutes: float
    effective_depth_cm: float
    hazard_ratio: float
    is_passable: bool
    hazard_cost_seconds: float
    physical_travel_time_seconds: float
    adjusted_speed_m_per_s: Optional[float]
    next_arrival_time_minutes: float
    length_m: float

@dataclass
class UnderpassEvaluationResult:
    segment_id: str
    is_underpass: bool
    arrival_time_minutes: float
    lookahead_minutes: float
    arrival_effective_depth_cm: float
    maximum_future_effective_depth_cm: float
    vehicle_type: str
    vehicle_limit_cm: float
    maximum_future_hazard_ratio: float
    is_safe: bool

def evaluate_underpass_lookahead(
    segment_id: str,
    arrival_time_minutes: float,
    vehicle_type: str,
    temporal_service: TemporalFloodDepthService,
    lookahead_minutes: float = 30.0,
    sample_interval_minutes: float = 15.0
) -> UnderpassEvaluationResult:
    """
    Evaluates flood risk for an underpass over a configurable future window.
    Samples the forecast at regular intervals (default 15m) to capture flash flooding.
    """
    from ai_service.layer4.risk_cost_evaluator import VehicleRiskConfig
    
    limit_cm = VehicleRiskConfig.get_limit_cm(vehicle_type)
    
    # Helper for safe depth query
    def safe_get_depth(t_min: float) -> float:
        try:
            return temporal_service.get_effective_depth(segment_id, t_min)["effective_depth_cm"]
        except Exception as e:
            logger.warning(f"Underpass depth query failed for {segment_id} at T={t_min}: {e}")
            return 0.0
            
    # 1. Evaluate immediate arrival depth
    arrival_depth = safe_get_depth(arrival_time_minutes)
    
    # 2. Sample future depths over the lookahead window
    max_future_depth = arrival_depth
    
    current_sample_time = arrival_time_minutes + sample_interval_minutes
    end_time = arrival_time_minutes + lookahead_minutes
    
    while current_sample_time <= end_time:
        max_future_depth = max(max_future_depth, safe_get_depth(current_sample_time))
        current_sample_time += sample_interval_minutes
        
    # Ensure the exact end of the window is also sampled if not exactly aligned
    if (current_sample_time - sample_interval_minutes) < end_time:
        max_future_depth = max(max_future_depth, safe_get_depth(end_time))
        
    hazard_ratio = max_future_depth / limit_cm
    is_safe = hazard_ratio < 1.0
    
    return UnderpassEvaluationResult(
        segment_id=segment_id,
        is_underpass=True,
        arrival_time_minutes=arrival_time_minutes,
        lookahead_minutes=lookahead_minutes,
        arrival_effective_depth_cm=arrival_depth,
        maximum_future_effective_depth_cm=max_future_depth,
        vehicle_type=vehicle_type,
        vehicle_limit_cm=limit_cm,
        maximum_future_hazard_ratio=round(hazard_ratio, 4),
        is_safe=is_safe
    )

@dataclass
class RouteRequest:
    origin_lon: float
    origin_lat: float
    dest_lon: float
    dest_lat: float
    vehicle_type: str
    departure_time_minutes: float
    temporal_service: TemporalFloodDepthService

@dataclass
class RouteResult:
    success: bool
    ordered_nodes: List[str]
    ordered_segment_ids: List[str]
    route_geometry: List[Tuple[float, float]]
    total_distance_m: float
    total_physical_travel_time_seconds: float
    total_hazard_cost_seconds: float
    departure_time: float
    arrival_time: float
    vehicle_type: str
    origin_requested: Tuple[float, float]
    origin_snapped: str
    destination_requested: Tuple[float, float]
    destination_snapped: str
    nodes_explored: int
    blocked_edges: int
    failure_reason: Optional[str]


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

    def snap_to_node(self, node_id_or_lon: Any, lat: Optional[float] = None) -> SnappingResult:
        """
        Snaps an origin/destination to the nearest valid routing graph node.
        Accepts either an explicit node ID (string) or (lon, lat) coordinates.
        """
        if isinstance(node_id_or_lon, str) and lat is None:
            node_id = node_id_or_lon
            if node_id not in self.G.nodes:
                raise ValueError(f"Invalid node ID requested: {node_id}")
            node_data = self.G.nodes[node_id]
            lon, lat_val = node_data["coordinates"][0], node_data["coordinates"][1]
            return SnappingResult(
                requested_lon=lon,
                requested_lat=lat_val,
                snapped_node_id=node_id,
                snapping_distance_m=0.0
            )
            
        if not isinstance(node_id_or_lon, (int, float)) or not isinstance(lat, (int, float)):
            raise ValueError("Invalid coordinates provided.")
            
        lon = float(node_id_or_lon)
        lat = float(lat)
        
        if not (-180.0 <= lon <= 180.0) or not (-90.0 <= lat <= 90.0):
            raise ValueError("Coordinates out of bounds.")
            
        _, idx = self.kdtree.query([lon, lat])
        snapped_node_id = self.node_ids[idx]
        
        node_data = self.G.nodes[snapped_node_id]
        snapped_lon, snapped_lat = node_data["coordinates"][0], node_data["coordinates"][1]
        
        distance_m = haversine_m(lon, lat, snapped_lon, snapped_lat)
        
        return SnappingResult(
            requested_lon=lon,
            requested_lat=lat,
            snapped_node_id=snapped_node_id,
            snapping_distance_m=distance_m
        )
        
    def evaluate_candidate_edge(
        self, 
        u_node: str, 
        v_node: str, 
        edge_key: int, 
        arrival_time_minutes: float, 
        vehicle_type: str, 
        temporal_service: TemporalFloodDepthService
    ) -> EdgeEvaluationResult:
        """
        Evaluates a single candidate edge at a specific arrival time.
        Delegates flood prediction to Part 3 and hazard evaluation to Part 4.
        """
        if u_node not in self.G or v_node not in self.G[u_node] or edge_key not in self.G[u_node][v_node]:
            raise ValueError("Invalid edge specified.")
            
        edge_data = self.G[u_node][v_node][edge_key]
        segment_id = edge_data.get("segment_id")
        length_m = edge_data.get("length_m", 1.0)
        speed_kmh = edge_data.get("free_flow_speed", 15.0)
        
        if not segment_id:
            raise ValueError("Edge is missing segment_id.")
            
        # 1. Ask Part 3 for effective depth at the precise arrival time
        try:
            temp_res = temporal_service.get_effective_depth(segment_id, arrival_time_minutes)
            effective_depth_cm = temp_res["effective_depth_cm"]
        except Exception as e:
            logger.warning(f"Depth query failed for {segment_id}: {e}")
            effective_depth_cm = 0.0
            
        # 2. Ask Part 4 to evaluate the vehicle risk and WHPF cost
        risk_res = FloodHazardEvaluator.evaluate_road_risk(
            segment_id=segment_id,
            length_m=length_m,
            free_flow_speed_kmh=speed_kmh,
            effective_depth_cm=effective_depth_cm,
            vehicle_type=vehicle_type
        )
        
        # 3. Underpass Future-Window Check
        is_underpass = edge_data.get("is_underpass", False)
        if is_underpass and risk_res["is_passable"]:
            underpass_eval = evaluate_underpass_lookahead(
                segment_id=segment_id,
                arrival_time_minutes=arrival_time_minutes,
                vehicle_type=vehicle_type,
                temporal_service=temporal_service,
                lookahead_minutes=30.0,
                sample_interval_minutes=15.0
            )
            if not underpass_eval.is_safe:
                # If unsafe in the future window, treat as immediately blocked
                risk_res["is_passable"] = False
                risk_res["hazard_cost_seconds"] = float('inf')
                risk_res["actual_travel_time_seconds"] = float('inf')
        
        # 4. Calculate next arrival time
        if risk_res["is_passable"]:
            next_arrival_time = arrival_time_minutes + (risk_res["actual_travel_time_seconds"] / 60.0)
        else:
            next_arrival_time = float('inf')
            
        return EdgeEvaluationResult(
            source_node=u_node,
            target_node=v_node,
            segment_id=segment_id,
            arrival_time_at_edge_minutes=arrival_time_minutes,
            effective_depth_cm=effective_depth_cm,
            hazard_ratio=risk_res["hazard_ratio"],
            is_passable=risk_res["is_passable"],
            hazard_cost_seconds=risk_res["hazard_cost_seconds"],
            physical_travel_time_seconds=risk_res["actual_travel_time_seconds"],
            adjusted_speed_m_per_s=risk_res.get("adjusted_speed_m_per_s"),
            next_arrival_time_minutes=next_arrival_time,
            length_m=length_m
        )

    def solve_route(self, req: RouteRequest) -> RouteResult:
        """
        Time-dependent A* safe routing algorithm.
        Minimizes Accumulated WHPF Hazard Cost.
        """
        # 1. Origin / Destination Snapping
        try:
            origin_snap = self.snap_to_node(req.origin_lon, req.origin_lat)
            dest_snap = self.snap_to_node(req.dest_lon, req.dest_lat)
        except ValueError as e:
            return self._build_failure_result(req, str(e))

        start_node = origin_snap.snapped_node_id
        target_node = dest_snap.snapped_node_id
        
        if start_node == target_node:
            return self._build_failure_result(req, "Origin and Destination snapped to the same node.")

        dest_data = self.G.nodes[target_node]
        dest_lon, dest_lat = dest_data["coordinates"][0], dest_data["coordinates"][1]

        # 2. Heuristic
        def heuristic(u_node: str) -> float:
            u_data = self.G.nodes[u_node]
            dist_m = haversine_m(u_data["coordinates"][0], u_data["coordinates"][1], dest_lon, dest_lat)
            # Admissible heuristic: time to travel straight line at maximum theoretical network speed
            # Since g is hazard_cost (which is bounded below by physical travel time when r=0)
            # This heuristic in seconds is highly admissible.
            return dist_m / self.max_speed_m_per_s

        # 3. Time-Dependent A* State Initialization
        # Priority Queue: (f_score, counter, node, hazard_cost_g, arrival_time_t, path_head)
        # path_head is a linked list tuple: (current_node, segment_id, edge_geom, length, physical_time, prev_path_head)
        pq = []
        counter = itertools.count()
        
        # State dominance strategy: keep pareto front of (hazard_cost, arrival_time) for each node
        # A state (g, t) dominates (g', t') if g <= g' and t <= t'.
        best_states = {start_node: [(0.0, req.departure_time_minutes)]}
        
        start_path_head = (start_node, None, None, 0.0, 0.0, None)
        heapq.heappush(pq, (heuristic(start_node), next(counter), start_node, 0.0, req.departure_time_minutes, start_path_head))

        nodes_explored = 0
        blocked_edges = 0
        best_target_path = None
        best_target_cost = float('inf')

        # 4. A* Search Loop
        while pq:
            f, _, u, g, t, path_head = heapq.heappop(pq)

            if u == target_node:
                if g < best_target_cost:
                    best_target_cost = g
                    best_target_path = path_head
                # We do not immediately break because another path might arrive earlier with slightly worse hazard cost? 
                # A* guarantees first popped target has lowest f, and since h(target)=0, lowest f = lowest g.
                # So we can safely break and return the lowest hazard cost path.
                break

            # If this state is strictly dominated by another popped state, it is redundant, 
            # but since we filter on push, we just proceed.
            nodes_explored += 1

            for v, edge_keys in self.G[u].items():
                for k in edge_keys:
                    # Time-dependent evaluation of candidate edge
                    try:
                        edge_eval = self.evaluate_candidate_edge(
                            u_node=u,
                            v_node=v,
                            edge_key=k,
                            arrival_time_minutes=t,
                            vehicle_type=req.vehicle_type,
                            temporal_service=req.temporal_service
                        )
                    except ValueError:
                        continue
                        
                    if not edge_eval.is_passable:
                        blocked_edges += 1
                        continue
                        
                    next_g = g + edge_eval.hazard_cost_seconds
                    next_t = edge_eval.next_arrival_time_minutes
                    
                    # Dominance check
                    v_states = best_states.get(v, [])
                    is_dominated = False
                    for existing_g, existing_t in v_states:
                        if existing_g <= next_g and existing_t <= next_t:
                            is_dominated = True
                            break
                            
                    if not is_dominated:
                        # Keep this state
                        v_states.append((next_g, next_t))
                        best_states[v] = v_states
                        
                        edge_geom = self.G[u][v][k].get("geometry")
                        new_path_head = (v, edge_eval.segment_id, edge_geom, edge_eval.length_m, edge_eval.physical_travel_time_seconds, path_head)
                        
                        next_f = next_g + heuristic(v)
                        heapq.heappush(pq, (next_f, next(counter), v, next_g, next_t, new_path_head))

        # 5. Route Reconstruction
        if best_target_path is None:
            return self._build_failure_result(req, "No safe route found.", origin_snap, dest_snap, nodes_explored, blocked_edges)

        ordered_nodes = []
        ordered_segment_ids = []
        route_geometry = []
        total_dist_m = 0.0
        total_physical_time_sec = 0.0
        
        curr = best_target_path
        while curr is not None:
            node_id, seg_id, geom, length, phys_time, prev = curr
            ordered_nodes.append(node_id)
            if seg_id is not None:
                ordered_segment_ids.append(seg_id)
                total_dist_m += length
                total_physical_time_sec += phys_time
                if geom is not None and hasattr(geom, "coords"):
                    # Append coords in reverse order because we are traversing from target to origin
                    for coord in reversed(list(geom.coords)):
                        route_geometry.append(coord)
                else:
                    # Fallback to node coordinates
                    node_coords = self.G.nodes[node_id]["coordinates"]
                    route_geometry.append((node_coords[0], node_coords[1]))
            else:
                # Origin node fallback
                node_coords = self.G.nodes[node_id]["coordinates"]
                route_geometry.append((node_coords[0], node_coords[1]))
                
            curr = prev

        ordered_nodes.reverse()
        ordered_segment_ids.reverse()
        route_geometry.reverse()
        
        # Deduplicate sequential identical coordinates in geometry
        clean_geom = []
        for coord in route_geometry:
            if not clean_geom or clean_geom[-1] != coord:
                clean_geom.append(coord)

        return RouteResult(
            success=True,
            ordered_nodes=ordered_nodes,
            ordered_segment_ids=ordered_segment_ids,
            route_geometry=clean_geom,
            total_distance_m=total_dist_m,
            total_physical_travel_time_seconds=total_physical_time_sec,
            total_hazard_cost_seconds=best_target_cost,
            departure_time=req.departure_time_minutes,
            arrival_time=req.departure_time_minutes + (total_physical_time_sec / 60.0),
            vehicle_type=req.vehicle_type,
            origin_requested=(req.origin_lon, req.origin_lat),
            origin_snapped=start_node,
            destination_requested=(req.dest_lon, req.dest_lat),
            destination_snapped=target_node,
            nodes_explored=nodes_explored,
            blocked_edges=blocked_edges,
            failure_reason=None
        )

    def _build_failure_result(self, req: RouteRequest, reason: str, origin_snap: Optional[SnappingResult] = None, dest_snap: Optional[SnappingResult] = None, explored: int = 0, blocked: int = 0) -> RouteResult:
        return RouteResult(
            success=False,
            ordered_nodes=[],
            ordered_segment_ids=[],
            route_geometry=[],
            total_distance_m=0.0,
            total_physical_travel_time_seconds=0.0,
            total_hazard_cost_seconds=float('inf'),
            departure_time=req.departure_time_minutes,
            arrival_time=float('inf'),
            vehicle_type=req.vehicle_type,
            origin_requested=(req.origin_lon, req.origin_lat),
            origin_snapped=origin_snap.snapped_node_id if origin_snap else "",
            destination_requested=(req.dest_lon, req.dest_lat),
            destination_snapped=dest_snap.snapped_node_id if dest_snap else "",
            nodes_explored=explored,
            blocked_edges=blocked,
            failure_reason=reason
        )
