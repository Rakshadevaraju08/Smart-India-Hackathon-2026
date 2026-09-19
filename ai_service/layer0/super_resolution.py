"""Layer 0: Super Resolution Module - Physics-Guided 1 km -> 100m Precipitation Downscaling.

Implements physics-informed topographical downscaling from coarse 1 km radar grids
to 100m micro-topographical cells, conditioned on:
  1. Coarse 1 km precipitation intensity
  2. Topographical elevation (DEM) & slope gradient (orographic uplift proxy)
  3. Surface imperviousness (urban heat island convergence proxy)
  4. Distance to Bay of Bengal coastline (sea-breeze front proxy)

Strict Mathematical Mass Conservation:
Enforces a cell-wise volume conservation normalization layer guaranteeing:
    | V_100m - V_1km | / V_1km <= 1e-5 (0.0000% numerical water hallucination).
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from scipy import ndimage

logger = logging.getLogger(__name__)

@dataclass
class SuperResolutionResult:
    """Encapsulates 100m downscaling results."""
    grid_100m: np.ndarray             # Shape: (10*H, 10*W) in mm/hr
    shape_100m: Tuple[int, int]
    mass_conservation_error_pct: float
    mean_rain_1km: float
    mean_rain_100m: float
    orographic_gain_applied: bool


class TopographicSuperResolutionEngine:
    """Downscales 1 km radar rainfall grids to 100m with physical mass conservation."""

    def __init__(
        self,
        scale_factor: int = 10,  # 1 km -> 100m (10x10 sub-pixels per 1km cell)
        orographic_uplift_coeff: float = 0.015,
        coastal_convergence_coeff: float = 0.08
    ):
        self.scale = scale_factor
        self.k_orog = orographic_uplift_coeff
        self.k_coast = coastal_convergence_coeff

    def synthesize_chennai_dem_100m(self, target_shape: Tuple[int, int]) -> np.ndarray:
        """Synthesizes normalized Chennai elevation topography (sea level 0.5m to 25m hills)."""
        H_100, W_100 = target_shape
        # Coordinate ramps
        y_norm = np.linspace(0.0, 1.0, H_100) # South to North
        x_norm = np.linspace(0.0, 1.0, W_100) # West to East
        X, Y = np.meshgrid(x_norm, y_norm)

        # Baseline gentle coastal plain (slopes eastwards toward Bay of Bengal)
        dem = (1.0 - X) * 12.0 + 2.0  # West ~14m MSL, East Coast ~2m MSL

        # St. Thomas Mount / Pallavaram isolated ridge feature in Southwest quadrant
        hill_x, hill_y = 0.25, 0.35
        hill_dist_sq = (X - hill_x)**2 + (Y - hill_y)**2
        ridge = 22.0 * np.exp(-hill_dist_sq / 0.008)
        dem = dem + ridge

        return np.maximum(0.5, dem).astype(np.float32)

    def downscale(
        self,
        coarse_grid_1km: np.ndarray,
        dem_100m: Optional[np.ndarray] = None,
        apply_mass_conservation: bool = True
    ) -> SuperResolutionResult:
        """Downscales 1 km radar grid to 100m micro-resolution with strict mass conservation.

        Parameters:
            coarse_grid_1km: 2D array (H, W) of rain rate (mm/hr)
            dem_100m: Optional 2D array (10*H, 10*W) of elevation in meters
            apply_mass_conservation: If True, forces sum(100m) == sum(1km) per parent cell
        """
        coarse_clean = np.nan_to_num(coarse_grid_1km, nan=0.0, posinf=500.0, neginf=0.0).astype(np.float32)
        H, W = coarse_clean.shape
        target_shape = (H * self.scale, W * self.scale)

        if dem_100m is None:
            dem_100m = self.synthesize_chennai_dem_100m(target_shape)
        elif dem_100m.shape != target_shape:
            # Resize provided DEM to match target shape
            dem_100m = ndimage.zoom(dem_100m, (target_shape[0] / dem_100m.shape[0], target_shape[1] / dem_100m.shape[1]), order=1)

        # 1. Bicubic base interpolation to 100m grid
        raw_interpolated = ndimage.zoom(coarse_clean, self.scale, order=3)
        raw_interpolated = np.maximum(0.0, raw_interpolated)

        # 2. Compute Topographical Gradient & Orographic Uplift Gain
        # Terrain slope: ||grad(DEM)||
        grad_y, grad_x = np.gradient(dem_100m)
        slope_magnitude = np.sqrt(grad_x**2 + grad_y**2)

        # Easterly moisture flux collision factor (Bay of Bengal easterlies hit eastward-facing slopes)
        orographic_modifier = 1.0 + self.k_orog * slope_magnitude

        # 3. Coastal Sea-Breeze Front (SBF) convergence line along Eastern corridor (Buckingham Canal)
        W_100 = target_shape[1]
        coast_dist_ratio = np.linspace(1.0, 0.0, W_100)[None, :] # 0 at coast, 1 inland
        coastal_convergence_modifier = 1.0 + self.k_coast * np.exp(-((coast_dist_ratio - 0.15)**2) / 0.02)

        # Apply physical micro-topographical modulation
        modulated_100m = raw_interpolated * orographic_modifier * coastal_convergence_modifier

        # 4. Strict Block-Wise Mass Conservation Layer
        # For every 10x10 block in the 100m grid, the mean must equal the parent 1km pixel
        if apply_mass_conservation:
            conserved_100m = np.zeros_like(modulated_100m)
            for i in range(H):
                for j in range(W):
                    r_slice = slice(i * self.scale, (i + 1) * self.scale)
                    c_slice = slice(j * self.scale, (j + 1) * self.scale)
                    block = modulated_100m[r_slice, c_slice]
                    parent_val = coarse_clean[i, j]

                    block_mean = float(np.mean(block))
                    if block_mean > 1e-4 and parent_val > 1e-4:
                        gamma = parent_val / block_mean
                        conserved_100m[r_slice, c_slice] = block * gamma
                    else:
                        conserved_100m[r_slice, c_slice] = parent_val
        else:
            conserved_100m = modulated_100m

        conserved_100m = np.maximum(0.0, conserved_100m).astype(np.float32)

        # Verification metrics
        vol_coarse = float(np.sum(coarse_clean))
        vol_100m = float(np.sum(conserved_100m)) / (self.scale ** 2)

        if vol_coarse > 1e-4:
            err_pct = abs(vol_100m - vol_coarse) / vol_coarse * 100.0
        else:
            err_pct = 0.0

        return SuperResolutionResult(
            grid_100m=conserved_100m,
            shape_100m=target_shape,
            mass_conservation_error_pct=round(err_pct, 6),
            mean_rain_1km=round(float(np.mean(coarse_clean)), 4),
            mean_rain_100m=round(float(np.mean(conserved_100m)), 4),
            orographic_gain_applied=True
        )
