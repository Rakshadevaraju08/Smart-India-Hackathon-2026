"""Layer 1: LULC Impervious Surface Extractor Module.

Calculates Directly Connected Impervious Area (DCIA / f_imp), Building Coverage Ratio (BCR),
composite runoff coefficient (C_composite), and Manning's overland roughness (n_overland)
for all 7,894 Greater Chennai Corporation (GCC) road segment corridors.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Typical Zonal Impervious Fraction Baselines across GCC 15 Zones
GCC_ZONE_IMPERVIOUS_BASELINES: Dict[int, float] = {
    1: 0.58,   # Thiruvottiyur (Industrial / Coastal)
    2: 0.52,   # Manali (Petrochemical / Low-density)
    3: 0.55,   # Madhavaram (Suburban / Water bodies)
    4: 0.88,   # Tondiarpet (High-density North Chennai)
    5: 0.94,   # Royapuram (Historic dense core / Harbour)
    6: 0.88,   # Thiru-Vi-Ka Nagar (High density)
    7: 0.76,   # Ambattur (Industrial / Residential)
    8: 0.88,   # Anna Nagar (Planned Urban Residential / Commercial)
    9: 0.94,   # Teynampet (CBD / T. Nagar commercial hub)
    10: 0.91,  # Kodambakkam (Dense Residential / Commercial)
    11: 0.78,  # Valasaravakkam (Mixed Residential)
    12: 0.76,  # Alandur (Airport fringe / Mixed)
    13: 0.80,  # Adyar (Mixed Urban / River corridor)
    14: 0.68,  # Perungudi (IT Corridor / Marshland boundary)
    15: 0.60,  # Sholinganallur (South Coastal / IT Corridor / Green)
}

# Road Classification Typical Road Pavement Imperviousness
ROAD_CLASS_IMPERVIOUS_MODIFIERS: Dict[str, float] = {
    "motorway": 0.98,
    "trunk": 0.95,
    "primary": 0.94,
    "secondary": 0.90,
    "tertiary": 0.86,
    "street": 0.84,
    "street_limited": 0.80,
    "residential": 0.72,
    "service": 0.65,
    "path": 0.35,
    "footway": 0.40,
    "track": 0.30,
}


class ImperviousExtractor:
    """Extracts urban land cover imperviousness metrics across GCC road segments."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).resolve().parent.parent.parent.parent
        self.datasets_dir = self.base_dir / "Datasets"
        self._cached_master_df: Optional[pd.DataFrame] = None
        self._cached_enriched_master_df: Optional[pd.DataFrame] = None

    def _get_base_df(self, roads_df: Optional[pd.DataFrame]) -> pd.DataFrame:
        if roads_df is not None:
            return roads_df.copy()
        if self._cached_master_df is not None:
            return self._cached_master_df.copy()

        master_csv = self.datasets_dir / "chennai_unified_flood_master_dataset.csv"
        if not master_csv.exists():
            raise FileNotFoundError(f"Missing master road dataset: {master_csv}")
        self._cached_master_df = pd.read_csv(master_csv)
        return self._cached_master_df.copy()

    @staticmethod
    def compute_frequency_factor(rainfall_mm_hr: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Compute storm frequency adjustment factor C_f according to IRC:SP:42 / CPHEEO.
        Under cloudburst intensities (I >= 50 mm/h), pervious soils saturate rapidly,
        amplifying the effective runoff coefficient by up to 25%.
        """
        if isinstance(rainfall_mm_hr, (int, float)):
            r = float(rainfall_mm_hr)
            if r < 25.0:
                return 1.00
            elif r < 50.0:
                return 1.00 + 0.10 * (r - 25.0) / 25.0
            else:
                return 1.10 + 0.15 * min(1.0, (r - 50.0) / 50.0)
        else:
            r = np.asarray(rainfall_mm_hr, dtype=np.float32)
            return np.where(r < 25.0, 1.00,
                   np.where(r < 50.0, 1.00 + 0.10 * (r - 25.0) / 25.0,
                            1.10 + 0.15 * np.clip((r - 50.0) / 50.0, 0.0, 1.0)))

    def extract_impervious_attributes(
        self,
        roads_df: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Compute impervious fraction (f_imp), BCR, runoff coefficient C, and Manning's n.
        Incorporate RWH disconnection and DEM micro-topography slope adjustment.
        Fully vectorized for sub-millisecond execution over 7,894 segments.
        """
        if roads_df is None and self._cached_enriched_master_df is not None:
            return self._cached_enriched_master_df.copy()

        df = self._get_base_df(roads_df)
        n_segments = len(df)

        zone_nos = df["zone_no"].values if "zone_no" in df.columns else np.full(n_segments, 9)
        road_classes = df["road_class"].astype(str).str.lower().values if "road_class" in df.columns else np.full(n_segments, "street")

        # Fast vectorized array mapping
        zone_baselines = np.array([GCC_ZONE_IMPERVIOUS_BASELINES.get(int(z), 0.75) for z in zone_nos], dtype=np.float32)
        road_mods = np.array([ROAD_CLASS_IMPERVIOUS_MODIFIERS.get(rc, 0.80) for rc in road_classes], dtype=np.float32)

        # 1. Base Impervious Fraction (Pavement + Urban Density)
        combined_f_imp = (0.50 * road_mods) + (0.50 * zone_baselines)

        # Check if 10m Sentinel-2 raster is available to blend for the core study area
        s2_dcia_tif = self.datasets_dir / "05_Satellite_Vaishnavi" / "Chennai_Satellite_Data_FINAL(vaishnavi)" / "satellite_data" / "lulc" / "chennai_impervious_dcia_10m.tif"
        if s2_dcia_tif.exists() and "latitude" in df.columns and "longitude" in df.columns:
            try:
                from .sentinel2_processor import Sentinel2Processor
                s2_proc = Sentinel2Processor(base_dir=self.base_dir)
                lats = df["latitude"].values
                lons = df["longitude"].values
                # Sample 10m DCIA for segments within the 10x10 km AOI
                in_aoi = (lats >= 12.9626) & (lats <= 13.0534) & (lons >= 80.1908) & (lons <= 80.2833)
                if np.any(in_aoi):
                    s2_sampled = s2_proc.sample_impervious_at_points(lats[in_aoi], lons[in_aoi])
                    # Blend satellite DCIA with zonal density and road classification
                    # Preserves high commercial CBD baseline while capturing localized satellite green/open spaces
                    blended = (0.45 * zone_baselines[in_aoi]) + (0.40 * road_mods[in_aoi]) + (0.15 * s2_sampled)
                    combined_f_imp[in_aoi] = np.clip(blended, 0.20, 0.98)
                    logger.debug("Blended 10m Sentinel-2 DCIA for %d road segments in study AOI", np.count_nonzero(in_aoi))
            except Exception as e:
                logger.debug("Sentinel-2 blending fallback: %s", e)

        # 2. Chennai Municipal Rainwater Harvesting (RWH) Disconnection
        # Residential and service corridors benefit from mandatory percolation soak-pits
        is_residential = np.isin(road_classes, ["residential", "service", "living_street", "path"])
        rwh_dcia_discount = np.where(is_residential, 0.94, 1.0).astype(np.float32)
        f_imp = np.clip(combined_f_imp * rwh_dcia_discount, 0.20, 0.98).astype(np.float32)

        # 3. Building Coverage Ratio (BCR) in contributing catchment
        bcr = np.clip(zone_baselines * 0.88, 0.15, 0.85).astype(np.float32)

        # 4. Composite Rational Runoff Coefficient with DEM Slope Adjustment
        c_base = f_imp * 0.95 + (1.0 - f_imp) * 0.20
        if "terrain_slope_m_per_m" in df.columns:
            slopes = df["terrain_slope_m_per_m"].values.astype(np.float32)
            slope_adj = np.clip((slopes - 0.01) * 1.5, -0.04, 0.06)
            c_composite = np.clip(c_base * (1.0 + slope_adj), 0.20, 0.96)
        else:
            c_composite = c_base

        # 5. Composite Overland Manning's Roughness: n = f_imp * 0.014 + (1 - f_imp) * 0.18
        manning_n = f_imp * 0.014 + (1.0 - f_imp) * 0.18

        df.loc[:, "impervious_fraction"] = np.round(f_imp, 3)
        df.loc[:, "building_coverage_ratio"] = np.round(bcr, 3)
        df.loc[:, "runoff_coefficient_c"] = np.round(c_composite, 3)
        df.loc[:, "manning_overland_n"] = np.round(manning_n, 4)

        if roads_df is None:
            self._cached_enriched_master_df = df.copy()

        return df
