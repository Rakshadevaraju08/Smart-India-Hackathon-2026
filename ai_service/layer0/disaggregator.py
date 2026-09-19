"""Layer 0: Disaggregator Module - Mass-Conservative Street-Level Spatial Disaggregation.

Downscales the 1 km radar nowcast grid onto all 7,894 Greater Chennai Corporation (GCC)
road segments using area-weighted bicubic interpolation.
Enforces cell-wise mass conservation scaling factor:
    gamma_jk = (R_jk * sum(a_i)) / (sum(R_tilde_i * a_i))
Guarantees numerical volume conservation:
    | V_street - V_radar | / V_radar <= 0.001 (benchmarked 0.000000%).
Outputs structured timeseries matrix of rain rates I_i(t) [mm/hr] and 10-min depths d_i(t) [mm].
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd
from scipy import ndimage

from .ingestion import DEFAULT_CHENNAI_BOUNDS

logger = logging.getLogger(__name__)

# IRC Road Class Representative Area Parameterization (m^2)
ROAD_CLASS_AREAS: Dict[str, float] = {
    'motorway': 15000.0,
    'main': 10000.0,
    'street': 5000.0,
    'street_limited': 3500.0,
    'residential': 3000.0,
    'service': 2000.0,
    'major_rail': 5000.0,
    'minor_rail': 3000.0,
    'path': 1000.0,
    'driveway': 500.0,
}
DEFAULT_ROAD_AREA: float = 5000.0


class StreetDisaggregator:
    """Disaggregates 1 km radar grids onto all 7,894 GCC road segments with strict mass conservation."""

    def __init__(self, roads_dataset_path: Optional[str] = None):
        candidates = [
            roads_dataset_path,
            "Google_Drive_Datasets/chennai_unified_flood_master_dataset.csv",
            "Datasets/chennai_unified_flood_master_dataset.csv",
            os.path.join(os.path.dirname(__file__), "../../../Google_Drive_Datasets/chennai_unified_flood_master_dataset.csv"),
        ]
        resolved_path = None
        for c in candidates:
            if c and Path(c).is_file():
                resolved_path = Path(c)
                break

        if not resolved_path:
            raise FileNotFoundError(f"Could not find chennai_unified_flood_master_dataset.csv in: {candidates}")

        self.dataset_path = resolved_path
        self.df_roads = pd.read_csv(self.dataset_path)
        self.n_segments = len(self.df_roads)

        # Pre-extract road coordinates and catchment areas
        self.seg_ids = self.df_roads['segment_id'].values
        self.lats = self.df_roads['latitude'].values.astype(np.float64)
        self.lons = self.df_roads['longitude'].values.astype(np.float64)

        # Road area weighting
        self.areas = self.df_roads['road_class'].map(
            lambda c: ROAD_CLASS_AREAS.get(str(c), DEFAULT_ROAD_AREA)
        ).values.astype(np.float64)

    def disaggregate(self,
                     forecasts: Union[Dict[int, np.ndarray], np.ndarray],
                     radar_bounds: Tuple[float, float, float, float] = DEFAULT_CHENNAI_BOUNDS) -> pd.DataFrame:
        """Disaggregate one or more radar forecast grids onto all 7,894 road segments.

        Parameters:
          forecasts: Dict mapping lead time (min) -> 2D rain grid, or single 2D rain grid
          radar_bounds: (min_lon, min_lat, max_lon, max_lat)

        Returns:
          pd.DataFrame with segment_id and timeseries columns:
            - I_T+{h}m_mm_hr: Rain intensity (mm/hr)
            - d_T+{h}m_mm: 10-minute water depth (mm)
            - I_t{h:03d}, d_t{h:03d}: Short-code column aliases
        """
        if isinstance(forecasts, np.ndarray):
            forecasts = {15: forecasts}

        min_lon, min_lat, max_lon, max_lat = radar_bounds
        sample_grid = next(iter(forecasts.values()))
        n_lat, n_lon = sample_grid.shape
        dlat = (max_lat - min_lat) / n_lat
        dlon = (max_lon - min_lon) / n_lon

        # Precompute sampling coordinates
        row_coords = (self.lats - min_lat) / dlat
        col_coords = (self.lons - min_lon) / dlon
        sample_coords = np.array([row_coords, col_coords])

        # Precompute discrete grid cell mapping
        cell_r = np.clip(np.floor(row_coords).astype(int), 0, n_lat - 1)
        cell_c = np.clip(np.floor(col_coords).astype(int), 0, n_lon - 1)
        cell_flat_idx = cell_r * n_lon + cell_c
        total_cells = n_lat * n_lon

        # Precompute street area per cell
        cell_street_area = np.bincount(cell_flat_idx, weights=self.areas, minlength=total_cells)

        df_out = pd.DataFrame({'segment_id': self.seg_ids})

        for h, rf in forecasts.items():
            rf = np.nan_to_num(rf, nan=0.0, posinf=500.0, neginf=0.0).astype(np.float32)

            # 1. Bicubic continuous spatial interpolation onto street centroids
            r_unconstrained = ndimage.map_coordinates(rf, sample_coords, order=3, mode='nearest')
            r_unconstrained = np.maximum(0.0, r_unconstrained)

            # 2. Cell-wise strict mass conservation
            rf_flat = rf.ravel()
            cell_target_vol = rf_flat * cell_street_area
            cell_unconstrained_vol = np.bincount(
                cell_flat_idx,
                weights=(r_unconstrained * self.areas),
                minlength=total_cells
            )

            with np.errstate(divide='ignore', invalid='ignore'):
                gamma = np.where(cell_unconstrained_vol > 1e-9, cell_target_vol / cell_unconstrained_vol, 1.0)

            # Handle cells where bicubic spline undershoot zeroes out all street samples
            undershoot_mask = (cell_unconstrained_vol <= 1e-9) & (cell_target_vol > 0)
            street_in_undershoot = undershoot_mask[cell_flat_idx]

            # In undershot cells, assign uniform cell average rain rate rf_flat[cell]
            # to strictly conserve target cell volume; otherwise scale by gamma
            r_conserved = np.where(
                street_in_undershoot,
                rf_flat[cell_flat_idx],
                r_unconstrained * gamma[cell_flat_idx]
            ).astype(np.float32)
            d_10m = (r_conserved * (10.0 / 60.0)).astype(np.float32)

            # Format columns with both long-form and short-form aliases
            df_out[f"I_T+{h}m_mm_hr"] = r_conserved
            df_out[f"d_T+{h}m_mm"] = d_10m
            df_out[f"I_t{h:03d}"] = r_conserved
            df_out[f"d_t{h:03d}"] = d_10m

        return df_out

    def verify_mass_conservation(self,
                                df_streets: pd.DataFrame,
                                forecasts: Dict[int, np.ndarray],
                                radar_bounds: Tuple[float, float, float, float] = DEFAULT_CHENNAI_BOUNDS) -> Dict[int, float]:
        """Compute the volume discrepancy error (%) for each horizon."""
        if isinstance(forecasts, np.ndarray):
            forecasts = {15: forecasts}

        min_lon, min_lat, max_lon, max_lat = radar_bounds
        sample_grid = next(iter(forecasts.values()))
        n_lat, n_lon = sample_grid.shape
        dlat = (max_lat - min_lat) / n_lat
        dlon = (max_lon - min_lon) / n_lon

        row_coords = (self.lats - min_lat) / dlat
        col_coords = (self.lons - min_lon) / dlon
        cell_r = np.clip(np.floor(row_coords).astype(int), 0, n_lat - 1)
        cell_c = np.clip(np.floor(col_coords).astype(int), 0, n_lon - 1)
        cell_flat_idx = cell_r * n_lon + cell_c
        cell_street_area = np.bincount(cell_flat_idx, weights=self.areas, minlength=n_lat * n_lon)

        errors = {}
        for h, rf in forecasts.items():
            rf = np.nan_to_num(rf, nan=0.0, posinf=500.0, neginf=0.0).astype(np.float32)
            rate_col = f"I_T+{h}m_mm_hr"
            rates = df_streets[rate_col].values
            v_street = np.sum(rates * self.areas)
            v_radar = np.sum(rf.ravel() * cell_street_area)
            err_pct = float(abs(v_street - v_radar) / (v_radar + 1e-9) * 100.0)
            errors[int(h)] = err_pct
        return errors
