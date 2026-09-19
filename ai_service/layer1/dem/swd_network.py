"""Layer 1: Stormwater Drainage (SWD) Network & Underpass Manager.

Ingests, classifies, and prepares Greater Chennai Corporation (GCC) stormwater
drainage networks, natural river corridors, masonry box culverts, and subway
underpass depressions for physical hydro-conditioning.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import geopandas as gpd
from shapely.geometry import base, shape

from .dem_builder import find_or_extract_file

logger = logging.getLogger(__name__)


def safe_read_geojson(file_path: Path, default_crs: str = "EPSG:4326") -> gpd.GeoDataFrame:
    """Safely load GeoJSON using standard json and shapely, avoiding pyogrio C-level crashes on Python 3.14."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        records = []
        for feat in data.get("features", []):
            geom = shape(feat["geometry"]) if feat.get("geometry") else None
            props = dict(feat.get("properties", {}) or {})
            props["geometry"] = geom
            records.append(props)
        gdf = gpd.GeoDataFrame(records, crs=default_crs)
        return gdf
    except Exception as e:
        logger.debug("Falling back to gpd.read_file for %s: %s", file_path, e)
        return gpd.read_file(file_path)

# Multi-tier hydraulic stream burning depths (in meters)
DEFAULT_BURN_DEPTHS = {
    "major_river": 2.5,       # Adyar, Cooum, Kosasthalaiyar, Buckingham Canal
    "primary_canal": 2.0,     # Otteri Nullah, Captain Cotton, Mambalam Canal
    "storm_drain": 1.5,       # Primary underground RCC / masonry box drains
    "ditch_stream": 0.8,      # Roadside open ditches & seasonal streamlets
    "underpass_sag": 2.0,     # Railway subways and low grade-separators
}

MAJOR_RIVER_KEYWORDS = [
    "adyar", "cooum", "buckingham", "kosasthalaiyar",
    "otteri", "mambalam", "captain cotton", "virugambakkam"
]


class SWDNetworkManager:
    """Manages Chennai SWD networks, culverts, and underpasses for hydraulic DEM conditioning."""

    def __init__(self,
                 base_dir: Optional[Path] = None,
                 custom_swd_path: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).resolve().parent.parent.parent.parent
        self.datasets_dir = self.base_dir / "Datasets"
        self.custom_swd_path = custom_swd_path
        self._cached_swd_gdf: Optional[gpd.GeoDataFrame] = None
        self._cached_underpass_gdf: Optional[gpd.GeoDataFrame] = None

    def load_drainage_network(self, target_crs: str = "EPSG:32644") -> gpd.GeoDataFrame:
        """Load and classify the stormwater drainage network from local GeoJSON or custom path."""
        if self._cached_swd_gdf is not None:
            return self._cached_swd_gdf

        # 1. Custom path if provided
        drain_file: Optional[Path] = None
        if self.custom_swd_path and self.custom_swd_path.exists():
            drain_file = self.custom_swd_path
        else:
            # 2. Check local dataset
            zip_drainage = self.datasets_dir / "02_Drainage_Rithesh" / "drainage_data(Rithesh).zip"
            try:
                drain_file = find_or_extract_file(self.base_dir, "drainage network.geojson", zip_drainage)
            except Exception as e:
                logger.warning("Could not locate drainage network geojson: %s", e)

        if not drain_file or not drain_file.exists():
            logger.warning("No drainage network file found; generating empty GeoDataFrame")
            gdf = gpd.GeoDataFrame(columns=["waterway", "name", "burn_depth_m", "geometry"], crs="EPSG:4326")
            self._cached_swd_gdf = gdf.to_crs(target_crs)
            return self._cached_swd_gdf

        gdf = safe_read_geojson(drain_file)
        if gdf.crs is None:
            gdf.set_crs("EPSG:4326", inplace=True)

        # Classify multi-tier burning depths
        burn_depths = []
        for _, row in gdf.iterrows():
            ww = str(row.get("waterway", "")).lower()
            name = str(row.get("name", "")).lower() + " " + str(row.get("name:en", "")).lower()

            if any(k in name for k in MAJOR_RIVER_KEYWORDS) or ww in ("river",):
                burn_depths.append(DEFAULT_BURN_DEPTHS["major_river"])
            elif ww in ("canal",):
                burn_depths.append(DEFAULT_BURN_DEPTHS["primary_canal"])
            elif ww in ("drain", "culvert"):
                burn_depths.append(DEFAULT_BURN_DEPTHS["storm_drain"])
            else:
                burn_depths.append(DEFAULT_BURN_DEPTHS["ditch_stream"])

        gdf = gdf.assign(burn_depth_m=burn_depths)
        gdf_proj = gdf.to_crs(target_crs)
        self._cached_swd_gdf = gdf_proj
        logger.info("Loaded SWD network: %d features classified with depth modulation", len(gdf_proj))
        return self._cached_swd_gdf

    def load_underpasses(self, target_crs: str = "EPSG:32644", buffer_radius_m: float = 30.0) -> gpd.GeoDataFrame:
        """Load railway/road underpasses and buffer them into depression polygons."""
        if self._cached_underpass_gdf is not None:
            return self._cached_underpass_gdf

        zip_drainage = self.datasets_dir / "02_Drainage_Rithesh" / "drainage_data(Rithesh).zip"
        up_file: Optional[Path] = None
        try:
            up_file = find_or_extract_file(self.base_dir, "underpasses data.geojson", zip_drainage)
        except Exception as e:
            logger.warning("Could not locate underpasses data geojson: %s", e)

        if not up_file or not up_file.exists():
            gdf = gpd.GeoDataFrame(columns=["name", "geometry"], crs="EPSG:4326")
            self._cached_underpass_gdf = gdf.to_crs(target_crs)
            return self._cached_underpass_gdf

        gdf = safe_read_geojson(up_file)
        if gdf.crs is None:
            gdf.set_crs("EPSG:4326", inplace=True)

        gdf_proj = gdf.to_crs(target_crs)
        buffered_geom = gdf_proj.geometry.buffer(buffer_radius_m)
        gdf_proj = gdf_proj.assign(
            orig_geom=gdf_proj.geometry,
            geometry=buffered_geom,
            burn_depth_m=DEFAULT_BURN_DEPTHS["underpass_sag"]
        )
        gdf_proj = gdf_proj.set_geometry("geometry")

        self._cached_underpass_gdf = gdf_proj
        logger.info("Loaded %d urban underpass sags (buffered %.1fm, sag %.1fm)",
                    len(gdf_proj), buffer_radius_m, DEFAULT_BURN_DEPTHS["underpass_sag"])
        return self._cached_underpass_gdf

    def get_burn_shapes(self, target_crs: str = "EPSG:32644") -> List[Tuple[base.BaseGeometry, float]]:
        """Extract tuple list of (geometry, burn_depth_m) for rasterio.features.rasterize."""
        shapes: List[Tuple[base.BaseGeometry, float]] = []

        # 1. Drainage channels
        gdf_swd = self.load_drainage_network(target_crs=target_crs)
        for _, row in gdf_swd.iterrows():
            geom = row.geometry
            depth = float(row.get("burn_depth_m", 1.5))
            if geom is not None and not geom.is_empty:
                shapes.append((geom, depth))

        # 2. Underpass depressions
        gdf_up = self.load_underpasses(target_crs=target_crs)
        for _, row in gdf_up.iterrows():
            geom = row.geometry
            depth = float(row.get("burn_depth_m", 2.0))
            if geom is not None and not geom.is_empty:
                shapes.append((geom, depth))

        return shapes
