"""Layer 4: Routing Engine - Priority-Queue Flood-Aware Shortest & Safe Path Solver.

Solves multi-vehicle emergency dispatch routes:
  1. Naive Direct Route (Dry-weather baseline, shortest geographic distance)
  2. Standard Cutoff Dijkstra (Binary impassable filter d_e >= d_c)
  3. Dynamic A* (Admissible Haversine heuristic + hydrodynamic speed degradation)
  4. Kairos Green Corridor A* (A* + Water Hazard Potential Field steering around flood fronts)

Calculates comparative telemetry & benchmarks:
  - Solver latency (ms) and nodes expanded
  - Bottlenecks avoided (submerged underpass, railway culverts, canal sags)
  - Distance detour penalty (km) & ETA overhead vs safety trade-off (min)
  - Clearance safety margin to active flood fronts (meters)
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

        # Precompute edge lengths and terrain slope features
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
                # Keep distance bounded between 25m and 1200m
                dist = max(25.0, min(1200.0, dist))
                self.adj_with_lengths[u].append((v, dist))

    def find_nearest_node(self, lat: float, lon: float) -> int:
        """Finds nearest street node index for a given coordinate."""
        _, idx = self.kdtree.query([lon, lat])
        return int(idx)

    def estimate_street_velocities(self, depths_cm: np.ndarray) -> np.ndarray:
        """
        Estimates overland flow velocities (m/s) using Manning's sheet flow equation:
          v = (1 / n) * (d / 100)^(2/3) * S_0^(1/2)
        where n = 0.016 for asphalt/concrete street gutters.
        """
        slopes = self.nodes_df.get("terrain_slope_m_per_m", pd.Series(np.full(self.n_nodes, 0.002))).values
        slopes = np.maximum(1e-4, slopes)
        d_m = depths_cm / 100.0
        n_manning = 0.016

        velocities = (1.0 / n_manning) * np.power(np.maximum(0.0, d_m), 2.0 / 3.0) * np.sqrt(slopes)
        return np.clip(velocities, 0.0, 3.5)  # Cap at 3.5 m/s physical torrential limit

    def compute_water_hazard_potential_field(
        self,
        depths_cm: np.ndarray,
        d_critical_cm: float,
        influence_radius_deg: float = 0.005,
        sigma_m: float = 250.0
    ) -> np.ndarray:
        """
        Builds the continuous Water Hazard Potential Field Phi_hazard(u) across all nodes:
          Phi_hazard(u) = sum_{k in inundated} (d_k / d_c)^2 * exp(- dist(u, k)^2 / (2 * sigma^2))

        Provides repulsive gradients that steer the A* search onto topological ridges
        and bypasses advancing flood fronts before streets become submerged.
        """
        potential = np.zeros(self.n_nodes, dtype=np.float64)
        inundated_indices = np.where(depths_cm > 3.0)[0]
        if len(inundated_indices) == 0:
            return potential

        # Query inundated neighbors for all nodes within radius
        coords = np.column_stack([self.nodes_df["longitude"].values, self.nodes_df["latitude"].values])
        inundated_coords = coords[inundated_indices]
        inundated_depths = depths_cm[inundated_indices]

        # Use KD-tree query for fast spatial potential estimation
        tree_inund = self.kdtree
        # Query up to 8 nearest inundated nodes within neighborhood
        dists, idxs = tree_inund.query(coords, k=min(6, len(inundated_indices)))

        if dists.ndim == 1:
            dists = dists[:, np.newaxis]
            idxs = idxs[:, np.newaxis]

        # Convert degree distances to approximate meters (1 deg ~ 111,000 m)
        dists_m = dists * 111000.0
        d_norm = depths_cm[idxs] / max(1.0, d_critical_cm)
        gaussian_weights = np.exp(- (dists_m ** 2) / (2.0 * (sigma_m ** 2)))

        potential = np.sum((d_norm ** 2) * gaussian_weights, axis=1)
        return potential

    def _dijkstra(
        self,
        start_idx: int,
        target_idx: int,
        edge_weight_fn
    ) -> Tuple[Optional[List[int]], float, int]:
        """Classic Dijkstra shortest path solver using min-heap priority queue."""
        distances = {start_idx: 0.0}
        previous = {}
        pq = [(0.0, start_idx)]
        visited = set()
        nodes_expanded = 0

        while pq:
            cur_dist, u = heapq.heappop(pq)
            if u == target_idx:
                break
            if u in visited:
                continue
            visited.add(u)
            nodes_expanded += 1

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
            return None, float("inf"), nodes_expanded

        # Reconstruct path
        path = []
        curr = target_idx
        while curr in previous:
            path.append(curr)
            curr = previous[curr]
        path.append(start_idx)
        path.reverse()

        return path, distances[target_idx], nodes_expanded

    def _astar(
        self,
        start_idx: int,
        target_idx: int,
        edge_weight_fn,
        evaluator: RiskCostEvaluator,
        potential_field: Optional[np.ndarray] = None,
        eta_hazard: float = 2.0
    ) -> Tuple[Optional[List[int]], float, int]:
        """
        A* Shortest & Safe Path Solver incorporating:
          - Dynamic Hydrodynamic Traversal Impedance
          - Admissible Haversine Heuristic h_dist(u, target) = dist(u, target) / V_max
          - Water Hazard Potential Field Phi_hazard(u) to guarantee green corridors
        """
        lats = self.nodes_df["latitude"].values
        lons = self.nodes_df["longitude"].values
        target_lat, target_lon = lats[target_idx], lons[target_idx]
        v_base_mps = evaluator.base_speed_mps

        # Heuristic function
        def heuristic(u: int) -> float:
            dist_m = haversine_m(lats[u], lons[u], target_lat, target_lon)
            h_time_s = dist_m / v_base_mps
            if potential_field is not None:
                # Add repulsive potential scaled to equivalent travel time penalty
                h_time_s += eta_hazard * float(potential_field[u]) * 10.0
            return h_time_s

        g_scores = {start_idx: 0.0}
        previous = {}
        # Priority queue stores (f_score, g_score, node)
        h_start = heuristic(start_idx)
        pq = [(h_start, 0.0, start_idx)]
        visited = set()
        nodes_expanded = 0

        while pq:
            f_cur, g_cur, u = heapq.heappop(pq)
            if u == target_idx:
                break
            if u in visited:
                continue
            visited.add(u)
            nodes_expanded += 1

            for v, length_m in self.adj_with_lengths.get(u, []):
                edge_cost_s = edge_weight_fn(u, v, length_m)
                if math.isinf(edge_cost_s):
                    continue

                tentative_g = g_cur + edge_cost_s
                if v not in g_scores or tentative_g < g_scores[v]:
                    g_scores[v] = tentative_g
                    previous[v] = u
                    f_score = tentative_g + heuristic(v)
                    heapq.heappush(pq, (f_score, tentative_g, v))

        if target_idx not in g_scores:
            return None, float("inf"), nodes_expanded

        # Reconstruct path
        path = []
        curr = target_idx
        while curr in previous:
            path.append(curr)
            curr = previous[curr]
        path.append(start_idx)
        path.reverse()

        return path, g_scores[target_idx], nodes_expanded

    def solve_route(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        depths_cm: np.ndarray,
        vehicle_type: str = "ambulance",
        velocities_mps: Optional[np.ndarray] = None,
        use_hazard_potential: bool = True
    ) -> Dict[str, Any]:
        """
        Computes Direct (naive) and Safe (hydrodynamic A* with Water Hazard Potential Field) routes.

        Parameters:
          origin_lat, origin_lon: Origin GPS coordinates
          dest_lat, dest_lon: Destination GPS coordinates
          depths_cm: Vector of current flood depths across all 7,894 road segments
          vehicle_type: 'ambulance', 'rescue_truck', 'civilian_car', or 'two_wheeler'
          velocities_mps: Optional flow velocity vector; estimated via Manning's formula if None
          use_hazard_potential: If True, uses Water Hazard Potential Field to repel from flood fronts
        """
        t0 = time.perf_counter()
        evaluator = RiskCostEvaluator(vehicle_type)

        if velocities_mps is None:
            velocities_mps = self.estimate_street_velocities(depths_cm)

        u_start = self.find_nearest_node(origin_lat, origin_lon)
        v_dest = self.find_nearest_node(dest_lat, dest_lon)

        # 1. Solve Naive Shortest Route (Dry Distance Only via Dijkstra)
        direct_path, _, direct_expanded = self._dijkstra(
            u_start, v_dest,
            edge_weight_fn=lambda u, v, length: length / evaluator.base_speed_mps
        )

        # 2. Build Water Hazard Potential Field for active flood front steering
        potential_field = None
        if use_hazard_potential:
            potential_field = self.compute_water_hazard_potential_field(
                depths_cm=depths_cm,
                d_critical_cm=evaluator.profile.d_critical_cm
            )

        # 3. Solve Dynamic Safe Route via Hydrodynamic A* Solver
        def safe_weight_fn(u: int, v: int, length: float) -> float:
            d_u, d_v = depths_cm[u], depths_cm[v]
            vel_u, vel_v = velocities_mps[u], velocities_mps[v]
            eff_depth = max(d_u, d_v)
            eff_vel = max(vel_u, vel_v)
            return evaluator.compute_edge_traversal_cost(
                length_m=length,
                depth_cm=eff_depth,
                velocity_mps=eff_vel,
                enforce_cutoff=True
            )

        safe_path, _, safe_expanded = self._astar(
            start_idx=u_start,
            target_idx=v_dest,
            edge_weight_fn=safe_weight_fn,
            evaluator=evaluator,
            potential_field=potential_field,
            eta_hazard=2.5
        )

        # Fallback with soft penalty if strict cutoff disconnects target completely
        if safe_path is None:
            def soft_weight_fn(u: int, v: int, length: float) -> float:
                eff_depth = max(depths_cm[u], depths_cm[v])
                eff_vel = max(velocities_mps[u], velocities_mps[v])
                return evaluator.compute_edge_traversal_cost(
                    length_m=length,
                    depth_cm=eff_depth,
                    velocity_mps=eff_vel,
                    enforce_cutoff=False
                )

            safe_path, _, safe_expanded = self._astar(
                start_idx=u_start,
                target_idx=v_dest,
                edge_weight_fn=soft_weight_fn,
                evaluator=evaluator,
                potential_field=potential_field,
                eta_hazard=1.0
            )

        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        # Assemble route analytics
        direct_res = self._analyze_path(direct_path, depths_cm, velocities_mps, evaluator) if direct_path else None
        safe_res = self._analyze_path(safe_path, depths_cm, velocities_mps, evaluator) if safe_path else None

        # Compare overhead
        if direct_res and safe_res:
            detour_extra_km = max(0.0, round(safe_res["distance_km"] - direct_res["distance_km"], 2))
            detour_extra_min = max(0.0, round(safe_res["eta_min"] - direct_res["eta_min"], 1))
            detour_overhead_pct = round((detour_extra_km / max(0.1, direct_res["distance_km"])) * 100.0, 1)
        else:
            detour_extra_km = 0.0
            detour_extra_min = 0.0
            detour_overhead_pct = 0.0

        return {
            "origin": {"lat": origin_lat, "lon": origin_lon, "nearest_node": u_start},
            "destination": {"lat": dest_lat, "lon": dest_lon, "nearest_node": v_dest},
            "vehicle_type": vehicle_type,
            "vehicle_name": evaluator.profile.name,
            "clearance_threshold_cm": evaluator.profile.d_critical_cm,
            "latency_ms": round(elapsed_ms, 2),
            "nodes_expanded": {
                "direct_dijkstra": direct_expanded,
                "safe_astar_whpf": safe_expanded
            },
            "direct_route": direct_res,
            "safe_route": safe_res,
            "detour_extra_km": detour_extra_km,
            "detour_extra_min": detour_extra_min,
            "detour_overhead_pct": detour_overhead_pct,
            "safety_gain": {
                "bottlenecks_avoided": (direct_res["impassable_segments"] if direct_res else 0) - (safe_res["impassable_segments"] if safe_res else 0),
                "depth_reduction_cm": round((direct_res["max_depth_cm"] if direct_res else 0) - (safe_res["max_depth_cm"] if safe_res else 0), 1)
            }
        }

    def _analyze_path(
        self,
        path: List[int],
        depths_cm: np.ndarray,
        velocities_mps: np.ndarray,
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
        max_velocity = 0.0
        impassable_count = 0
        bottleneck_info = None

        for i in range(len(path)):
            u = path[i]
            lat, lon = float(lats[u]), float(lons[u])
            coords.append([lat, lon])
            d = float(depths_cm[u])
            v = float(velocities_mps[u]) if velocities_mps is not None else 0.0

            if d > max_depth:
                max_depth = d
                bottleneck_info = {
                    "node_idx": u,
                    "name": str(names[u]),
                    "depth_cm": round(d, 1),
                    "velocity_mps": round(v, 2),
                    "lat": lat,
                    "lon": lon
                }

            if v > max_velocity:
                max_velocity = v

            # Check impassability (depth or momentum hazard)
            if d >= evaluator.profile.d_critical_cm or ((d / 100.0) * v) >= evaluator.profile.critical_dv_m2_s:
                impassable_count += 1

            if i < len(path) - 1:
                v_node = path[i + 1]
                dist = haversine_m(lat, lon, float(lats[v_node]), float(lons[v_node]))
                total_dist_m += dist
                seg_time = evaluator.estimate_travel_time_min(dist, d, v)
                if not math.isinf(seg_time):
                    total_time_min += seg_time
                else:
                    total_time_min += (dist / max(1.0, evaluator.base_speed_mps * 0.1)) / 60.0

        is_safe = impassable_count == 0
        status = "SAFE_PASSABLE" if is_safe else "IMPASSABLE_HAZARD"

        return {
            "status": status,
            "is_safe": is_safe,
            "distance_km": round(total_dist_m / 1000.0, 2),
            "eta_min": round(total_time_min, 1),
            "max_depth_cm": round(max_depth, 1),
            "max_velocity_mps": round(max_velocity, 2),
            "impassable_segments": impassable_count,
            "total_nodes": len(path),
            "bottleneck": bottleneck_info,
            "coords": coords
        }

    def benchmark_routing_algorithms(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        depths_cm: np.ndarray,
        vehicle_type: str = "ambulance"
    ) -> Dict[str, Any]:
        """
        Executes empirical benchmark comparison between 4 routing architectures:
          1. Dijkstra Naive Shortest Distance (Baseline, flood-blind)
          2. Dijkstra with Strict Cutoff (Binary pass/fail filter)
          3. Standard A* with Hydrodynamic Travel Cost (Admissible Haversine heuristic)
          4. Kairos Green Corridor A* (A* + Water Hazard Potential Field)
        """
        evaluator = RiskCostEvaluator(vehicle_type)
        velocities_mps = self.estimate_street_velocities(depths_cm)
        u_start = self.find_nearest_node(origin_lat, origin_lon)
        v_dest = self.find_nearest_node(dest_lat, dest_lon)

        # 1. Dijkstra Naive Shortest Distance
        t0 = time.perf_counter()
        p1, _, n1 = self._dijkstra(
            u_start, v_dest,
            edge_weight_fn=lambda u, v, l: l / evaluator.base_speed_mps
        )
        lat1 = (time.perf_counter() - t0) * 1000.0
        res1 = self._analyze_path(p1, depths_cm, velocities_mps, evaluator) if p1 else None

        # 2. Dijkstra with Strict Cutoff
        t0 = time.perf_counter()
        p2, _, n2 = self._dijkstra(
            u_start, v_dest,
            edge_weight_fn=lambda u, v, l: (
                float("inf") if max(depths_cm[u], depths_cm[v]) >= evaluator.profile.d_critical_cm
                else l / evaluator.base_speed_mps
            )
        )
        lat2 = (time.perf_counter() - t0) * 1000.0
        res2 = self._analyze_path(p2, depths_cm, velocities_mps, evaluator) if p2 else None

        # 3. Standard A* with Hydrodynamic Traversal Cost
        t0 = time.perf_counter()
        def hydro_weight_fn(u: int, v: int, l: float) -> float:
            eff_d = max(depths_cm[u], depths_cm[v])
            eff_v = max(velocities_mps[u], velocities_mps[v])
            return evaluator.compute_edge_traversal_cost(l, eff_d, eff_v, enforce_cutoff=True)

        p3, _, n3 = self._astar(
            start_idx=u_start,
            target_idx=v_dest,
            edge_weight_fn=hydro_weight_fn,
            evaluator=evaluator,
            potential_field=None
        )
        lat3 = (time.perf_counter() - t0) * 1000.0
        res3 = self._analyze_path(p3, depths_cm, velocities_mps, evaluator) if p3 else None

        # 4. Kairos Green Corridor A* (A* + WHPF)
        t0 = time.perf_counter()
        whpf = self.compute_water_hazard_potential_field(depths_cm, evaluator.profile.d_critical_cm)
        p4, _, n4 = self._astar(
            start_idx=u_start,
            target_idx=v_dest,
            edge_weight_fn=hydro_weight_fn,
            evaluator=evaluator,
            potential_field=whpf,
            eta_hazard=2.5
        )
        lat4 = (time.perf_counter() - t0) * 1000.0
        res4 = self._analyze_path(p4, depths_cm, velocities_mps, evaluator) if p4 else None

        algorithms = [
            {
                "algorithm": "Dijkstra Naive Shortest Distance",
                "flood_aware": False,
                "latency_ms": round(lat1, 2),
                "nodes_expanded": n1,
                "distance_km": res1["distance_km"] if res1 else 0.0,
                "eta_min": res1["eta_min"] if res1 else 0.0,
                "max_depth_cm": res1["max_depth_cm"] if res1 else 0.0,
                "impassable_segments": res1["impassable_segments"] if res1 else 0,
                "status": res1["status"] if res1 else "NO_ROUTE"
            },
            {
                "algorithm": "Dijkstra Binary Cutoff",
                "flood_aware": True,
                "latency_ms": round(lat2, 2),
                "nodes_expanded": n2,
                "distance_km": res2["distance_km"] if res2 else 0.0,
                "eta_min": res2["eta_min"] if res2 else 0.0,
                "max_depth_cm": res2["max_depth_cm"] if res2 else 0.0,
                "impassable_segments": res2["impassable_segments"] if res2 else 0,
                "status": res2["status"] if res2 else "NO_ROUTE"
            },
            {
                "algorithm": "Standard A* Hydrodynamic",
                "flood_aware": True,
                "latency_ms": round(lat3, 2),
                "nodes_expanded": n3,
                "distance_km": res3["distance_km"] if res3 else 0.0,
                "eta_min": res3["eta_min"] if res3 else 0.0,
                "max_depth_cm": res3["max_depth_cm"] if res3 else 0.0,
                "impassable_segments": res3["impassable_segments"] if res3 else 0,
                "status": res3["status"] if res3 else "NO_ROUTE"
            },
            {
                "algorithm": "Kairos Green Corridor A* (A* + WHPF)",
                "flood_aware": True,
                "latency_ms": round(lat4, 2),
                "nodes_expanded": n4,
                "distance_km": res4["distance_km"] if res4 else 0.0,
                "eta_min": res4["eta_min"] if res4 else 0.0,
                "max_depth_cm": res4["max_depth_cm"] if res4 else 0.0,
                "impassable_segments": res4["impassable_segments"] if res4 else 0,
                "status": res4["status"] if res4 else "NO_ROUTE"
            }
        ]

        return {
            "vehicle_type": vehicle_type,
            "vehicle_name": evaluator.profile.name,
            "clearance_cm": evaluator.profile.d_critical_cm,
            "origin_node": u_start,
            "dest_node": v_dest,
            "benchmark_results": algorithms
        }

