"""Layer 2: Inlet Capture Module - Curb Drop-Inlet & Catch-Pit Grate Hydraulics.

Models rainfall runoff ingress from 2D road surface into 1D underground conduits:
  1. Unsubmerged Curb Weir Flow:  Q_weir = C_w * L_grate * (h)^1.5
  2. Submerged Orifice Grate Flow: Q_orifice = C_d * A_grate * sqrt(2 * g * h)
  3. Street Surface Debris Clogging Factor on inlet bars
"""

import logging
import math
from typing import Dict, Any

logger = logging.getLogger(__name__)


class InletCaptureEngine:
    """Calculates capture efficiency and bypass flow for street curb drop-inlets."""

    def __init__(self,
                 c_weir: float = 1.66,
                 c_orifice: float = 0.60,
                 gravity: float = 9.80665):
        self.c_weir = c_weir
        self.c_orifice = c_orifice
        self.g = gravity

    def compute_inlet_capture(
        self,
        q_surface_inflow_m3_s: float,
        water_depth_at_curb_m: float,
        grate_length_m: float = 1.0,
        grate_width_m: float = 0.5,
        debris_blockage_pct: float = 0.20
    ) -> Dict[str, Any]:
        """
        Calculates captured discharge Q_inlet (m^3/s) and bypass surface flow Q_bypass.

        Parameters:
          q_surface_inflow_m3_s: Total overland flow arriving at curb gutter
          water_depth_at_curb_m: Water ponding depth h at curb (meters)
          grate_length_m: Longitudinal length of grate along road curb (default 1.0m)
          grate_width_m: Transverse width of grate (default 0.5m)
          debris_blockage_pct: Proportion of grate covered by plastic/leaves (0.0 to 0.70)
        """
        h = max(0.001, float(water_depth_at_curb_m))
        blockage = max(0.0, min(0.80, float(debris_blockage_pct)))
        effective_factor = 1.0 - blockage

        a_grate = (grate_length_m * grate_width_m) * effective_factor
        l_perimeter = (grate_length_m + 2.0 * grate_width_m) * effective_factor

        # Unsubmerged weir regime (shallow ponding h < 0.12m)
        q_weir = self.c_weir * l_perimeter * (h ** 1.5)

        # Submerged orifice regime (deep ponding h >= 0.12m)
        q_orifice = self.c_orifice * a_grate * math.sqrt(2.0 * self.g * h)

        # Smooth transition between regimes
        q_cap_potential = min(q_weir, q_orifice) if h < 0.12 else q_orifice

        # Captured flow cannot exceed arriving surface flow
        q_captured = min(q_surface_inflow_m3_s, q_cap_potential)
        q_bypass = max(0.0, q_surface_inflow_m3_s - q_captured)
        capture_efficiency = (q_captured / max(1e-4, q_surface_inflow_m3_s)) * 100.0

        return {
            "q_surface_m3_s": round(q_surface_inflow_m3_s, 3),
            "q_captured_m3_s": round(q_captured, 3),
            "q_bypass_m3_s": round(q_bypass, 3),
            "capture_efficiency_pct": round(min(100.0, capture_efficiency), 1),
            "regime": "SUBMERGED_ORIFICE" if h >= 0.12 else "UNSUBMERGED_WEIR",
            "effective_grate_area_m2": round(a_grate, 3)
        }
