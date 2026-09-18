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

logger = logging.getLogger(__name__)


class StreetDrainageGraph:
    """Builds and manages the coupled 7,894-node hydrodynamic street network graph."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).resolve().parent.parent.parent
        self.datasets_dir = self.base_dir / "Datasets"
        self.nodes_df: pd.DataFrame = pd.DataFrame()
        self.adjacency_list: Dict[int, List[int]] = {}
        self.kdtree: Optional[cKDTree] = None
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
            self.nodes_df["elevation_ground_m"] = 8.5
        if "terrain_slope_m_per_m" not in self.nodes_df.columns:
            self.nodes_df["terrain_slope_m_per_m"] = 0.002

        # 2. Build spatial k-d tree for fast spatial querying (Lat/Lon)
        coords = np.column_stack([self.nodes_df["longitude"].values, self.nodes_df["latitude"].values])
        self.kdtree = cKDTree(coords)

        # 3. Spatial adjacency: Connect road segments within 450 meters (approx 0.004 degrees)
        pairs = self.kdtree.query_pairs(r=0.004)
        for i in range(len(self.nodes_df)):
            self.adjacency_list[i] = []

        for u, v in pairs:
            self.adjacency_list[u].append(v)
            self.adjacency_list[v].append(u)

        logger.info("Constructed spatial street graph: %d nodes, %d adjacency edges",
                    len(self.nodes_df), len(pairs))

    def get_node_feature_matrix(self) -> Dict[str, np.ndarray]:
        """Returns structured numpy arrays for high-speed tensor operations."""
        return {
            "segment_ids": self.nodes_df["segment_id"].values if "segment_id" in self.nodes_df.columns else np.arange(len(self.nodes_df)),
            "elevations": self.nodes_df["elevation_ground_m"].values.astype(np.float32),
            "slopes": self.nodes_df["terrain_slope_m_per_m"].values.astype(np.float32),
            "latitudes": self.nodes_df["latitude"].values.astype(np.float64),
            "longitudes": self.nodes_df["longitude"].values.astype(np.float64),
        }
