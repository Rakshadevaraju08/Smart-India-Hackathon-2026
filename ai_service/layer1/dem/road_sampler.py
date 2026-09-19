"""Layer 1: Road Sampler Module - Street-Level Elevation & Slope Attribution.

Maps DEM surface elevation Z_ground, terrain slope S_0, aspect, catchment
accumulation, and TWI onto all 7,894 Greater Chennai Corporation road segments.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio

logger = logging.getLogger(__name__)


class RoadElevationSampler:
    """Samples terrain elevation and hydraulic slope for all GCC road segments."""

    def __init__(self,
                 datasets_dir: Optional[Path] = None,
                 output_dir: Optional[Path] = None,
                 base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).resolve().parent.parent.parent.parent
        self.datasets_dir = datasets_dir or (self.base_dir / "Datasets")
        self.output_dir = output_dir or (self.datasets_dir / "processed_dem")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def sample_roads(
        self,
        dem: np.ndarray,
        slope: np.ndarray,
        aspect: np.ndarray,
        flow_acc: np.ndarray,
        transform: rasterio.Affine,
        crs: str = "EPSG:32644",
        twi: Optional[np.ndarray] = None
    ) -> pd.DataFrame:
        """Sample DEM values for 7,894 road centroids and return enriched DataFrame."""
        master_csv = self.datasets_dir / "chennai_unified_flood_master_dataset.csv"
        if not master_csv.exists():
            raise FileNotFoundError(f"Missing master road dataset: {master_csv}")

        df = pd.read_csv(master_csv)
        logger.info("Loaded master road dataset: %d segments", len(df))

        gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs="EPSG:4326")
        gdf_utm = gdf.to_crs(crs)

        # Compute TWI if not passed explicitly
        if twi is None:
            cell_size = abs(transform.a) if hasattr(transform, 'a') else 30.0
            spec_area = np.maximum(1.0, flow_acc * cell_size)
            tan_beta = np.maximum(0.001, slope)
            twi = np.clip(np.log(spec_area / tan_beta), 0.0, 30.0)

        inv_trans = ~transform
        elevations = []
        slopes = []
        aspects = []
        catchment_accs = []
        twis = []
        h, w = dem.shape

        for pt in gdf_utm.geometry:
            col, row = inv_trans @ (pt.x, pt.y)
            r = int(round(row))
            c = int(round(col))
            if 0 <= r < h and 0 <= c < w:
                elevations.append(round(float(dem[r, c]), 2))
                slopes.append(round(float(slope[r, c]), 4))
                aspects.append(round(float(aspect[r, c]), 1))
                catchment_accs.append(round(float(flow_acc[r, c]), 2))
                twis.append(round(float(twi[r, c]), 2))
            else:
                elevations.append(8.0)
                slopes.append(0.002)
                aspects.append(90.0)
                catchment_accs.append(1.0)
                twis.append(8.5)

        df = df.copy()
        df["elevation_ground_m"] = elevations
        df["terrain_slope_m_per_m"] = slopes
        df["terrain_aspect_deg"] = aspects
        df["catchment_flow_acc"] = catchment_accs
        df["terrain_twi"] = twis

        out_csv = self.output_dir / "chennai_roads_with_dem_attributes.csv"
        df.to_csv(out_csv, index=False)
        logger.info("Exported enriched road dataset with TWI to %s", out_csv)
        return df
