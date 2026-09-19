"""Layer 3: Graph Builder Module - Road & Drainage Coupled Network Graph.

Constructs unified spatial multigraph G = (V, E):
  - 7,894 Road Segment Nodes (centroids, catchment area, road class)
  - Node Features: Ground Elevation Z_ground (m MSL) and Terrain Slope S_0 from Layer 1 DEM
  - Drainage Conduits: Effective pipe conveyance Q_cap and clogging penalties from Layer 2
  - Edge Topology: Overland surface drainage neighbors and subsurface pipe linkages
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
import scipy.sparse as sp

logger = logging.getLogger(__name__)


class StreetDrainageGraph:
    """Builds and manages the coupled 7,894-node hydrodynamic street network graph."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).resolve().parent.parent.parent
        self.datasets_dir = self.base_dir / "Datasets"
        self.nodes_df: pd.DataFrame = pd.DataFrame()
        self.adjacency_list: Dict[int, List[int]] = {}
        self.kdtree: Optional[cKDTree] = None
        self.A_hat_csr: Optional[sp.csr_matrix] = None
        self.edge_src: Optional[np.ndarray] = None
        self.edge_dst: Optional[np.ndarray] = None
        self.edge_lengths_m: Optional[np.ndarray] = None
        self.edge_slopes: Optional[np.ndarray] = None
        self._build_graph()

    def _build_graph(self):
        """Loads enriched road attributes and builds spatial connectivity."""
        # 1. Prefer Layer 1 DEM-enriched roads, fallback to master dataset
        roads_csv = self.datasets_dir / "processed_dem" / "chennai_roads_with_dem_attributes.csv"
        if not roads_csv.exists():
            roads_csv = self.datasets_dir / "chennai_unified_flood_master_dataset.csv"

        if not roads_csv.exists():
            raise FileNotFoundError(f"Missing road network dataset at {roads_csv}")

        df = pd.read_csv(roads_csv)
        self.nodes_df = df.copy()

        # Ensure ground elevation and terrain slope exist
        if "elevation_ground_m" not in self.nodes_df.columns:
            if "elevation_m" in self.nodes_df.columns:
                self.nodes_df["elevation_ground_m"] = self.nodes_df["elevation_m"].astype(np.float32)
            else:
                self.nodes_df["elevation_ground_m"] = 8.5

        if "terrain_slope_m_per_m" not in self.nodes_df.columns:
            if "slope_degrees" in self.nodes_df.columns:
                self.nodes_df["terrain_slope_m_per_m"] = np.tan(np.radians(self.nodes_df["slope_degrees"].astype(np.float32)))
            else:
                self.nodes_df["terrain_slope_m_per_m"] = 0.002

        if "effective_drain_capacity_cumecs" not in self.nodes_df.columns:
            if "theoretical_drain_capacity_cumecs" in self.nodes_df.columns:
                self.nodes_df["effective_drain_capacity_cumecs"] = self.nodes_df["theoretical_drain_capacity_cumecs"].astype(np.float32)
            else:
                self.nodes_df["effective_drain_capacity_cumecs"] = 0.20

        # 2. Build spatial k-d tree for fast spatial querying (Lat/Lon)
        coords = np.column_stack([self.nodes_df["longitude"].values, self.nodes_df["latitude"].values])
        self.kdtree = cKDTree(coords)

        # 3. Spatial adjacency: Connect road segments within 450 meters (approx 0.004 degrees)
        pairs = np.array(list(self.kdtree.query_pairs(r=0.004)), dtype=np.int32)
        n_nodes = len(self.nodes_df)
        for i in range(n_nodes):
            self.adjacency_list[i] = []

        for u, v in pairs:
            self.adjacency_list[u].append(v)
            self.adjacency_list[v].append(u)

        # 4. Formulate Directed Hydraulic Gradient Adjacency Operator A_hat
        self._build_directed_hydraulic_operator(pairs, n_nodes)

        logger.info("Constructed spatial street graph: %d nodes, %d pairs, A_hat nnz=%d",
                    n_nodes, len(pairs), self.A_hat_csr.nnz if self.A_hat_csr is not None else 0)

    def _build_directed_hydraulic_operator(self, pairs: np.ndarray, n_nodes: int):
        """
        Formulates the row-stochastic directed hydraulic gradient adjacency operator:
          W_ij = sigma( (z_i - z_j) / tau ) * [ sqrt(max(S_0,ij, 1e-4))/L_ij + alpha_pipe * Q_cap,ij / L_ij ]
          A_hat = D_inv * W  where sum_j A_hat_ij = 1.0 (analytical mass-conserving Markov transfer)
        """
        elev = self.nodes_df["elevation_ground_m"].values.astype(np.float32)
        q_cap = self.nodes_df["effective_drain_capacity_cumecs"].values.astype(np.float32)
        coords = np.column_stack([self.nodes_df["longitude"].values, self.nodes_df["latitude"].values])

        if len(pairs) == 0:
            # Fallback identity operator
            self.A_hat_csr = sp.eye(n_nodes, format="csr", dtype=np.float32)
            self.edge_src = np.arange(n_nodes, dtype=np.int32)
            self.edge_dst = np.arange(n_nodes, dtype=np.int32)
            self.edge_lengths_m = np.full(n_nodes, 50.0, dtype=np.float32)
            self.edge_slopes = np.full(n_nodes, 0.002, dtype=np.float32)
            return

        u = pairs[:, 0]
        v = pairs[:, 1]

        # Metric distance in meters around Chennai (~13.04 deg N)
        cos_lat = np.cos(np.radians(13.04))
        dx = (coords[v, 0] - coords[u, 0]) * 111320.0 * cos_lat
        dy = (coords[v, 1] - coords[u, 1]) * 110540.0
        L = np.maximum(20.0, np.sqrt(dx * dx + dy * dy)).astype(np.float32)

        # Forward edge: u -> v
        dz_uv = elev[u] - elev[v]
        s0_uv = np.maximum(0.0, dz_uv) / L
        # Directed smooth logistic transfer gate (tau = 0.05m)
        sigma_uv = 1.0 / (1.0 + np.exp(-np.clip(dz_uv / 0.05, -20.0, 20.0)))
        k_surf_uv = np.sqrt(np.maximum(s0_uv, 1e-4)) / L
        q_cap_uv = np.minimum(q_cap[u], q_cap[v])
        w_uv = sigma_uv * (k_surf_uv + 0.35 * (q_cap_uv / L))

        # Reverse edge: v -> u
        dz_vu = -dz_uv
        s0_vu = np.maximum(0.0, dz_vu) / L
        sigma_vu = 1.0 / (1.0 + np.exp(-np.clip(dz_vu / 0.05, -20.0, 20.0)))
        k_surf_vu = np.sqrt(np.maximum(s0_vu, 1e-4)) / L
        w_vu = sigma_vu * (k_surf_vu + 0.35 * (q_cap_uv / L))

        # Self-loop retention storage inertia
        self_loop_idx = np.arange(n_nodes, dtype=np.int32)
        self_loop_weight = np.full(n_nodes, 0.005, dtype=np.float32)

        # Assemble full directed edge list
        src = np.concatenate([u, v, self_loop_idx])
        dst = np.concatenate([v, u, self_loop_idx])
        weights = np.concatenate([w_uv, w_vu, self_loop_weight])

        # Store explicit edge attributes for physics loss evaluation
        self.edge_src = np.concatenate([u, v])
        self.edge_dst = np.concatenate([v, u])
        self.edge_lengths_m = np.concatenate([L, L])
        self.edge_slopes = np.concatenate([s0_uv, s0_vu])

        # Build Sparse Weight Matrix W and Row-Normalize to produce A_hat
        W = sp.csr_matrix((weights, (src, dst)), shape=(n_nodes, n_nodes), dtype=np.float32)
        row_sums = np.array(W.sum(axis=1)).flatten()
        row_sums[row_sums == 0] = 1.0
        D_inv = sp.diags(1.0 / row_sums, dtype=np.float32)
        self.A_hat_csr = (D_inv @ W).tocsr()

    def get_directed_adjacency_operator(self) -> sp.csr_matrix:
        """Returns the row-stochastic directed hydraulic adjacency operator A_hat."""
        return self.A_hat_csr

    def get_edge_tensors(self) -> Dict[str, np.ndarray]:
        """Returns directed edge indices, lengths, and slopes for momentum loss evaluation."""
        return {
            "edge_src": self.edge_src,
            "edge_dst": self.edge_dst,
            "edge_lengths_m": self.edge_lengths_m,
            "edge_slopes": self.edge_slopes,
        }

    def get_node_feature_matrix(self) -> Dict[str, np.ndarray]:
        """Returns structured numpy arrays for high-speed tensor operations."""
        return {
            "segment_ids": self.nodes_df["segment_id"].values if "segment_id" in self.nodes_df.columns else np.arange(len(self.nodes_df)),
            "elevations": self.nodes_df["elevation_ground_m"].values.astype(np.float32),
            "slopes": self.nodes_df["terrain_slope_m_per_m"].values.astype(np.float32),
            "q_cap": self.nodes_df["effective_drain_capacity_cumecs"].values.astype(np.float32),
            "latitudes": self.nodes_df["latitude"].values.astype(np.float64),
            "longitudes": self.nodes_df["longitude"].values.astype(np.float64),
        }
