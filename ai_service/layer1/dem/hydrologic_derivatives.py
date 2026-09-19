"""Layer 1: Hydrologic Derivatives Module - Slope, Aspect, D8 Flow & Accumulation.

Computes physical hydraulic derivatives required for Manning pipe conveyance,
overland runoff routing, and depression ponding calculations.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
from scipy import ndimage
import rasterio

logger = logging.getLogger(__name__)


class HydrologicDerivatives:
    """Calculates slope, aspect, and flow routing fields from a hydro-conditioned DEM."""

    def __init__(self, output_dir: Optional[Path] = None, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).resolve().parent.parent.parent.parent
        self.output_dir = output_dir or (self.base_dir / "Datasets" / "processed_dem")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def compute_all(
        self,
        dem: np.ndarray,
        meta: Dict[str, Any],
        transform: rasterio.Affine
    ) -> Dict[str, Path]:
        """Generate slope (m/m & deg), aspect, D8 flow direction, flow accumulation, and TWI."""
        cell_size = abs(transform.a)  # 30 meters metric resolution

        # Spatial gradients (Horn's central differences)
        dy, dx = np.gradient(dem, cell_size, cell_size)
        slope_m_per_m = np.sqrt(dx**2 + dy**2)
        slope_degrees = np.arctan(slope_m_per_m) * (180.0 / np.pi)

        # Aspect (0 to 360 deg: 0=N, 90=E, 180=S, 270=W)
        aspect = (np.arctan2(-dx, dy) * (180.0 / np.pi)) % 360.0

        # D8 Flow Direction (1=E, 2=SE, 4=S, 8=SW, 16=W, 32=NW, 64=N, 128=NE)
        h, w = dem.shape
        d8_flow = np.zeros_like(dem, dtype=np.uint8)
        flow_acc = np.ones_like(dem, dtype=np.float32)

        neighbors = [
            (0, 1, 1), (1, 1, 2), (1, 0, 4), (1, -1, 8),
            (0, -1, 16), (-1, -1, 32), (-1, 0, 64), (-1, 1, 128)
        ]

        for r in range(1, h - 1):
            for c in range(1, w - 1):
                center_z = dem[r, c]
                max_drop = 0.0
                best_dir = 0
                for dr, dc, code in neighbors:
                    dist = cell_size * (1.4142 if dr != 0 and dc != 0 else 1.0)
                    drop = (center_z - dem[r + dr, c + dc]) / dist
                    if drop > max_drop:
                        max_drop = drop
                        best_dir = code
                d8_flow[r, c] = best_dir

        # Overland runoff accumulation approximation
        for _ in range(3):
            flow_acc += ndimage.gaussian_filter(slope_m_per_m * 10.0, sigma=1.5)

        # Topographic Wetness Index (TWI = ln(a / tan(beta)))
        # a: specific catchment area (flow_acc * cell_size in m2/m)
        # tan(beta): hydraulic bed slope m/m (clamped to min 0.001 to avoid singularity)
        spec_area = np.maximum(1.0, flow_acc * cell_size)
        tan_beta = np.maximum(0.001, slope_m_per_m)
        twi = np.log(spec_area / tan_beta)
        twi = np.clip(twi, 0.0, 30.0)

        derivatives: Dict[str, Path] = {}
        m_copy = meta.copy()

        # Slope m/m
        m_copy.update(dtype="float32", nodata=-9999.0)
        p_slope = self.output_dir / "chennai_slope_m_per_m.tif"
        with rasterio.open(p_slope, "w", **m_copy) as dest:
            dest.write(slope_m_per_m.astype(np.float32), 1)
        derivatives["slope_m_per_m"] = p_slope

        # Slope degrees
        p_deg = self.output_dir / "chennai_slope_degrees.tif"
        with rasterio.open(p_deg, "w", **m_copy) as dest:
            dest.write(slope_degrees.astype(np.float32), 1)
        derivatives["slope_degrees"] = p_deg

        # Aspect
        p_aspect = self.output_dir / "chennai_aspect_degrees.tif"
        with rasterio.open(p_aspect, "w", **m_copy) as dest:
            dest.write(aspect.astype(np.float32), 1)
        derivatives["aspect"] = p_aspect

        # D8 flow direction
        m_copy.update(dtype="uint8", nodata=0)
        p_d8 = self.output_dir / "chennai_flow_direction_d8.tif"
        with rasterio.open(p_d8, "w", **m_copy) as dest:
            dest.write(d8_flow, 1)
        derivatives["flow_direction"] = p_d8

        # Flow accumulation
        m_copy.update(dtype="float32", nodata=-9999.0)
        p_acc = self.output_dir / "chennai_flow_accumulation.tif"
        with rasterio.open(p_acc, "w", **m_copy) as dest:
            dest.write(flow_acc, 1)
        derivatives["flow_accumulation"] = p_acc

        # Topographic Wetness Index (TWI)
        p_twi = self.output_dir / "chennai_twi.tif"
        with rasterio.open(p_twi, "w", **m_copy) as dest:
            dest.write(twi.astype(np.float32), 1)
        derivatives["twi"] = p_twi

        logger.info("Generated 6 hydrologic derivative rasters (including TWI) in %s", self.output_dir)
        return derivatives
