"""Layer 1: Hydro-Conditioner Module - Stream Burning & Underpass Breach Engine.

Hydro-conditions raw satellite elevation models by:
  1. Burning authentic drainage canals, storm conduits, and rivers with multi-tiered
     depth relief so flow reaches true gravity outfalls (Buckingham Canal, Adyar, Cooum, Bay of Bengal).
  2. Enforcing 353 railway/road underpass depressions (-2.0m) to model critical urban flood sags.
  3. Preserving urban flood drainage pathways against artificial digital damming.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import geopandas as gpd
import rasterio
from rasterio.features import rasterize

from .dem_builder import find_or_extract_file
from .swd_network import SWDNetworkManager

logger = logging.getLogger(__name__)


class HydroConditioner:
    """Performs hydraulic feature enforcement on base digital elevation grids."""

    def __init__(self,
                 extracted_dir: Optional[Path] = None,
                 output_dir: Optional[Path] = None,
                 base_dir: Optional[Path] = None,
                 custom_swd_path: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).resolve().parent.parent.parent.parent
        self.datasets_dir = self.base_dir / "Datasets"
        self.output_dir = output_dir or (self.datasets_dir / "processed_dem")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.swd_manager = SWDNetworkManager(base_dir=self.base_dir, custom_swd_path=custom_swd_path)

    def condition_dem(
        self,
        base_dem: np.ndarray,
        meta: Dict[str, Any],
        transform: rasterio.Affine,
        canal_burn_depth_m: Optional[float] = None,
        underpass_depth_m: Optional[float] = None
    ) -> Tuple[np.ndarray, Path]:
        """Apply multi-tiered canal burning and underpass sag enforcement, then save raster."""
        h, w = base_dem.shape
        hydro_dem = base_dem.copy()
        crs = meta.get("crs", "EPSG:32644")

        # 1. Use SWDNetworkManager for differentiated depth burning
        try:
            burn_shapes = self.swd_manager.get_burn_shapes(target_crs=str(crs))
            if burn_shapes:
                # If explicit depths passed, override default classifications
                if canal_burn_depth_m is not None or underpass_depth_m is not None:
                    c_depth = canal_burn_depth_m or 2.0
                    u_depth = underpass_depth_m or 1.8
                    mod_shapes = []
                    for geom, orig_d in burn_shapes:
                        d = u_depth if orig_d == 2.0 else c_depth
                        mod_shapes.append((geom, d))
                    burn_shapes = mod_shapes

                burn_mask = rasterize(
                    shapes=burn_shapes,
                    out_shape=(h, w),
                    transform=transform,
                    fill=0.0,
                    dtype=np.float32
                )
                hydro_dem = np.maximum(0.0, hydro_dem - burn_mask)
                logger.info("Hydro-conditioned DEM with %d SWD & underpass shapes", len(burn_shapes))
            else:
                logger.warning("No burn shapes generated; hydro-conditioning skipped")
        except Exception as e:
            logger.warning("SWD burning failed: %s; falling back to direct geojson parsing", e)
            hydro_dem = self._fallback_burn(hydro_dem, h, w, transform, crs, canal_burn_depth_m, underpass_depth_m)

        hydro_path = self.output_dir / "chennai_dem_hydro_conditioned.tif"
        with rasterio.open(hydro_path, "w", **meta) as dest:
            dest.write(hydro_dem.astype(np.float32), 1)

        logger.info("Saved Hydro-Conditioned DEM to %s", hydro_path)
        return hydro_dem, hydro_path

    def _fallback_burn(
        self,
        dem: np.ndarray,
        h: int,
        w: int,
        transform: rasterio.Affine,
        crs: Any,
        canal_depth: Optional[float],
        up_depth: Optional[float]
    ) -> np.ndarray:
        """Fallback direct shape burning if SWDManager encountered errors."""
        c_depth = canal_depth or 2.0
        u_depth = up_depth or 1.8
        zip_drainage = self.datasets_dir / "02_Drainage_Rithesh" / "drainage_data(Rithesh).zip"

        # Drainage canals
        try:
            drain_geojson = find_or_extract_file(self.base_dir, "drainage network.geojson", zip_drainage)
            gdf_drain = gpd.read_file(drain_geojson).to_crs(crs)
            shapes = ((geom, c_depth) for geom in gdf_drain.geometry if geom is not None and not geom.is_empty)
            burn_mask = rasterize(shapes=shapes, out_shape=(h, w), transform=transform, fill=0.0, dtype=np.float32)
            dem = np.maximum(0.0, dem - burn_mask)
        except Exception as e:
            logger.warning("Fallback drain burn skipped: %s", e)

        # Underpasses
        try:
            up_geojson = find_or_extract_file(self.base_dir, "underpasses data.geojson", zip_drainage)
            gdf_up = gpd.read_file(up_geojson).to_crs(crs)
            up_buffers = [geom.buffer(30.0) for geom in gdf_up.geometry if geom is not None and not geom.is_empty]
            shapes_up = ((geom, u_depth) for geom in up_buffers)
            up_mask = rasterize(shapes=shapes_up, out_shape=(h, w), transform=transform, fill=0.0, dtype=np.float32)
            dem = np.maximum(0.0, dem - up_mask)
        except Exception as e:
            logger.warning("Fallback underpass breach skipped: %s", e)

        return dem
