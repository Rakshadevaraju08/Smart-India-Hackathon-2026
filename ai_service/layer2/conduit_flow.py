"""Layer 2: Conduit Flow Module - 1D Subsurface Pipe Hydraulics Engine.

Solves Manning full-pipe and open-channel conveyance capacity:
  Q_cap = (1 / n_eff) * A_eff * (R_h)^(2/3) * sqrt(S_0)

Integrates:
  - Circular RCC Storm Pipes (diameters 300mm to 1800mm)
  - In-Situ Rectangular Box Drains (e.g. 1.5m x 1.2m arterial collectors)
  - Real Bed Slopes S_0 from Layer 1 DEM terrain attributes
  - Dynamic Clogging Penalties from CloggingModel
"""

import logging
import math
from typing import Any, Dict, Optional, Tuple, Union
import numpy as np

logger = logging.getLogger(__name__)


class ConduitFlowEngine:
    """Solves 1D hydraulic conveyance capacity and flow velocities for urban stormwater conduits."""

    def __init__(self, default_manning_n: float = 0.015):
        self.default_n = default_manning_n

    def calculate_circular_pipe(
        self,
        diameter_m: float,
        slope_m_per_m: float,
        mu_clog: float = 0.35,
        base_n: float = 0.013
    ) -> Dict[str, float]:
        """
        Calculates hydraulic capacity for circular pre-cast RCC conduit.

        Parameters:
          diameter_m: Internal pipe diameter (meters)
          slope_m_per_m: Bed slope S0 from Layer 1 DEM (m/m)
          mu_clog: Dynamic solid waste clogging index in [0.0, 0.85]
          base_n: Clean Manning roughness (default 0.013 for smooth RCC)

        Returns:
          Dict containing nominal and effective capacities, velocity, and capacity loss.
        """
        dia = max(0.15, float(diameter_m))
        s0 = max(1e-4, float(slope_m_per_m))
        mu = max(0.0, min(0.85, float(mu_clog)))

        # Clean geometric parameters
        a_0 = math.pi * ((dia / 2.0) ** 2)
        p_0 = math.pi * dia
        r_h0 = dia / 4.0

        # Clogged geometric & hydraulic parameters
        a_eff = a_0 * (1.0 - mu)
        n_eff = base_n * (1.0 + 1.8 * mu)
        r_h_eff = r_h0 * math.sqrt(1.0 - mu)

        # Manning equation: Q = (1/n) * A * R^(2/3) * S^(1/2)
        q_clean = (1.0 / base_n) * a_0 * (r_h0 ** (2.0 / 3.0)) * math.sqrt(s0)
        q_eff = (1.0 / n_eff) * a_eff * (r_h_eff ** (2.0 / 3.0)) * math.sqrt(s0)
        v_eff = q_eff / max(0.01, a_eff)

        return {
            "type": "circular_rcc",
            "diameter_m": round(dia, 3),
            "slope_m_per_m": round(s0, 5),
            "clogging_factor": round(mu, 3),
            "nominal_capacity_m3_s": round(q_clean, 3),
            "effective_capacity_m3_s": round(q_eff, 3),
            "velocity_m_s": round(v_eff, 2),
            "capacity_loss_pct": round((1.0 - (q_eff / max(1e-4, q_clean))) * 100.0, 1),
            "effective_area_m2": round(a_eff, 3),
            "effective_manning_n": round(n_eff, 4)
        }

    def calculate_box_culvert(
        self,
        width_m: float,
        height_m: float,
        slope_m_per_m: float,
        mu_clog: float = 0.35,
        base_n: float = 0.015
    ) -> Dict[str, float]:
        """Calculates hydraulic capacity for rectangular RCC box drain/culvert."""
        w = max(0.30, float(width_m))
        h = max(0.30, float(height_m))
        s0 = max(1e-4, float(slope_m_per_m))
        mu = max(0.0, min(0.85, float(mu_clog)))

        a_0 = w * h
        p_0 = 2.0 * (w + h)
        r_h0 = a_0 / p_0

        a_eff = a_0 * (1.0 - mu)
        n_eff = base_n * (1.0 + 1.8 * mu)
        r_h_eff = r_h0 * (1.0 - 0.5 * mu)

        q_clean = (1.0 / base_n) * a_0 * (r_h0 ** (2.0 / 3.0)) * math.sqrt(s0)
        q_eff = (1.0 / n_eff) * a_eff * (r_h_eff ** (2.0 / 3.0)) * math.sqrt(s0)
        v_eff = q_eff / max(0.01, a_eff)

        return {
            "type": "box_culvert",
            "width_m": round(w, 2),
            "height_m": round(h, 2),
            "slope_m_per_m": round(s0, 5),
            "clogging_factor": round(mu, 3),
            "nominal_capacity_m3_s": round(q_clean, 3),
            "effective_capacity_m3_s": round(q_eff, 3),
            "velocity_m_s": round(v_eff, 2),
            "capacity_loss_pct": round((1.0 - (q_eff / max(1e-4, q_clean))) * 100.0, 1),
            "effective_area_m2": round(a_eff, 3),
            "effective_manning_n": round(n_eff, 4)
        }
