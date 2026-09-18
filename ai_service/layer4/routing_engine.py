"""Layer 4: Routing Engine - Priority-Queue Flood-Aware Shortest & Safe Path Solver.

Solves:
  1. Naive Direct Route (Dry-weather baseline, shortest geographic distance)
  2. Dynamic Safe Route (Flood-aware route detour avoiding water >= d_critical)

Calculates comparative telemetry:
  - Bottlenecks avoided (e.g., submerged underpass or sag)
  - Distance detour penalty (km)
  - ETA overhead vs safety trade-off (min)
  - Path linestring coordinates for GIS map rendering
"""

import heapq
import logging
import math
import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

try:
    from ai_service.layer3.graph_builder import StreetDrainageGraph
    from ai_service.layer4.risk_cost_evaluator import RiskCostEvaluator, VEHICLE_PROFILES
except ImportError:
    from ..layer3.graph_builder import StreetDrainageGraph
    from .risk_cost_evaluator import RiskCostEvaluator, VEHICLE_PROFILES



logger = logging.getLogger(__name__)


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two points on earth in meters."""
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0)**2
    return 2.0 * R * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


class DynamicRoutingEngine:
    """Solves flood-aware emergency dispatch routes over the 7,894-node street network."""

    def __init__(self, graph: Optional[StreetDrainageGraph] = None):
        self.graph = graph or StreetDrainageGraph()
        self.nodes_df = self.graph.nodes_df
        self.n_nodes = len(self.nodes_df)
        self.kdtree = self.graph.kdtree

        # Precompute edge lengths for adjacency
        self._precompute_graph_edges()

    def _precompute_graph_edges(self):
        """Constructs weighted edge representation from spatial adjacency."""
        lats = self.nodes_df["latitude"].values
        lons = self.nodes_df["longitude"].values

        self.adj_with_lengths: Dict[int, List[Tuple[int, float]]] = {i: [] for i in range(self.n_nodes)}

        for u, neighbors in self.graph.adjacency_list.items():
            u_lat, u_lon = lats[u], lons[u]
            for v in neighbors:
                v_lat, v_lon = lats[v], lons[v]
                dist = haversine_m(u_lat, u_lon, v_lat, v_lon)
                # Keep distance bounded between 20m and 1200m
                dist = max(25.0, min(1200.0, dist))
                self.adj_with_lengths[u].append((v, dist))

    def find_nearest_node(self, lat: float, lon: float) -> int:
        """Finds nearest street node index for a given coordinate."""
        _, idx = self.kdtree.query([lon, lat])
        return int(idx)

    def _dijkstra(
        self,
        start_idx: int,
        target_idx: int,
        edge_weight_fn
    ) -> Tuple[Optional[List[int]], float]:
        """Classic Dijkstra shortest path using min-heap priority queue."""
        distances = {start_idx: 0.0}
        previous = {}
        pq = [(0.0, start_idx)]
        visited = set()

        while pq:
            cur_dist, u = heapq.heappop(pq)
            if u == target_idx:
                break
            if u in visited:
                continue
            visited.add(u)

            for v, length_m in self.adj_with_lengths.get(u, []):
                weight = edge_weight_fn(u, v, length_m)
                if math.isinf(weight):
                    continue

                new_dist = cur_dist + weight
                if v not in distances or new_dist < distances[v]:
                    distances[v] = new_dist
                    previous[v] = u
                    heapq.heappush(pq, (new_dist, v))

        if target_idx not in distances:
            return None, float("inf")

        # Reconstruct path
        path = []
        curr = target_idx
        while curr in previous:
            path.append(curr)
            curr = previous[curr]
        path.append(start_idx)
        path.reverse()

        return path, distances[target_idx]

    def solve_route(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        depths_cm: np.ndarray,
        vehicle_type: str = "ambulance"
    ) -> Dict[str, Any]:
        """
        Computes both Direct (naive) and Safe (flood-aware) emergency routes.

        Parameters:
          origin_lat, origin_lon: Origin GPS coordinates
          dest_lat, dest_lon: Destination GPS coordinates
          depths_cm: Vector of current flood depths across all 7,894 road segments
          vehicle_type: 'ambulance', 'rescue_truck', or 'civilian_evac'
        """
        t0 = time.perf_counter()
        evaluator = RiskCostEvaluator(vehicle_type)

        u_start = self.find_nearest_node(origin_lat, origin_lon)
        v_dest = self.find_nearest_node(dest_lat, dest_lon)

        # 1. Solve Naive Shortest Route (Dry Distance Only)
        direct_path, _ = self._dijkstra(
            u_start, v_dest,
            edge_weight_fn=lambda u, v, length: length
        )

        # 2. Solve Dynamic Safe Route (Flood Impedance with Critical Cutoff)
        def safe_weight_fn(u: int, v: int, length: float) -> float:
            # Traversal depth is max of connecting nodes
            depth = max(depths_cm[u], depths_cm[v])
            if depth >= evaluator.profile.d_critical_cm:
                return float("inf")
            # Apply dynamic impedance
            p = evaluator.profile
            if depth <= p.d_safe_cm:
                return length
            ratio = (depth - p.d_safe_cm) / max(1.0, p.d_safe_cm)
            return length * (1.0 + p.alpha * (ratio ** p.gamma))

        safe_path, _ = self._dijkstra(u_start, v_dest, edge_weight_fn=safe_weight_fn)

        # Fallback if strict cutoff disconnects target completely
        if safe_path is None:
            # Soft penalty without strict infinity
            def soft_weight_fn(u: int, v: int, length: float) -> float:
                depth = max(depths_cm[u], depths_cm[v])
                return length * (1.0 + 10.0 * (depth / 10.0)**2)

            safe_path, _ = self._dijkstra(u_start, v_dest, edge_weight_fn=soft_weight_fn)

        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        # Assemble route analytics
        direct_res = self._analyze_path(direct_path, depths_cm, evaluator) if direct_path else None
        safe_res = self._analyze_path(safe_path, depths_cm, evaluator) if safe_path else None

        # Compare overhead
        if direct_res and safe_res:
            detour_extra_km = max(0.0, round(safe_res["distance_km"] - direct_res["distance_km"], 2))
            detour_extra_min = max(0.0, round(safe_res["eta_min"] - direct_res["eta_min"], 1))
        else:
            detour_extra_km = 0.0
            detour_extra_min = 0.0

        return {
            "origin": {"lat": origin_lat, "lon": origin_lon, "nearest_node": u_start},
            "destination": {"lat": dest_lat, "lon": dest_lon, "nearest_node": v_dest},
            "vehicle_type": vehicle_type,
            "vehicle_name": evaluator.profile.name,
            "latency_ms": round(elapsed_ms, 2),
            "direct_route": direct_res,
            "safe_route": safe_res,
            "detour_extra_km": detour_extra_km,
            "detour_extra_min": detour_extra_min,
            "safety_gain": {
                "bottlenecks_avoided": (direct_res["impassable_segments"] if direct_res else 0) - (safe_res["impassable_segments"] if safe_res else 0),
                "depth_reduction_cm": round((direct_res["max_depth_cm"] if direct_res else 0) - (safe_res["max_depth_cm"] if safe_res else 0), 1)
            }
        }

    def _analyze_path(
        self,
        path: List[int],
        depths_cm: np.ndarray,
        evaluator: RiskCostEvaluator
    ) -> Dict[str, Any]:
        """Extracts detailed segment statistics and linestring coordinates along a path."""
        lats = self.nodes_df["latitude"].values
        lons = self.nodes_df["longitude"].values
        names = self.nodes_df.get("road_name", pd.Series(["Street"] * self.n_nodes)).values

        coords = []
        total_dist_m = 0.0
        total_time_min = 0.0
        max_depth = 0.0
        impassable_count = 0
        bottleneck_info = None

        for i in range(len(path)):
            u = path[i]
            lat, lon = float(lats[u]), float(lons[u])
            coords.append([lat, lon])
            d = float(depths_cm[u])
            if d > max_depth:
                max_depth = d
                bottleneck_info = {
                    "node_idx": u,
                    "name": str(names[u]),
                    "depth_cm": round(d, 1),
                    "lat": lat,
                    "lon": lon
                }

            if d >= evaluator.profile.d_critical_cm:
                impassable_count += 1

            if i < len(path) - 1:
                v = path[i + 1]
                dist = haversine_m(lat, lon, float(lats[v]), float(lons[v]))
                total_dist_m += dist
                seg_time = evaluator.estimate_travel_time_min(dist, d)
                if not math.isinf(seg_time):
                    total_time_min += seg_time

        is_safe = impassable_count == 0
        status = "SAFE_PASSABLE" if is_safe else "IMPASSABLE_HAZARD"

        return {
            "status": status,
            "is_safe": is_safe,
            "distance_km": round(total_dist_m / 1000.0, 2),
            "eta_min": round(total_time_min, 1),
            "max_depth_cm": round(max_depth, 1),
            "impassable_segments": impassable_count,
            "total_nodes": len(path),
            "bottleneck": bottleneck_info,
            "coords": coords
        }
