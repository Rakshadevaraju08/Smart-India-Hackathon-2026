"""Layer 4: Risk Cost Evaluator - Dynamic Hydrodynamic Traversal Impedance.

Computes vehicle-specific traversal impedances across road segments as a function of:
  - Real-time flood depth d_i(t) in centimeters from Layer 3
  - Vehicle water-fording threshold d_critical (e.g., 20 cm for ambulances, 50 cm for NDRF trucks)
  - Hydrodynamic drag and speed degradation penalty

Mathematical Formulation:
  For edge e of length L_e with water depth d_e:
    If d_e < d_safe:
        W_e = L_e
    If d_safe <= d_e < d_critical:
        W_e = L_e * [1 + alpha * ((d_e - d_safe) / d_safe)^gamma]
    If d_e >= d_critical:
        W_e = infinity (Severed / Impassable)
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class VehicleProfile:
    """Hydrodynamic parameters for emergency vehicle classes."""
    name: str
    d_safe_cm: float        # Comfortable wading threshold without speed loss
    d_critical_cm: float    # Absolute cutoff depth (engine stall / hydroplaning)
    base_speed_kmh: float   # Free-flow velocity in dry conditions
    alpha: float            # Penalty scaling coefficient
    gamma: float            # Exponential non-linearity exponent


VEHICLE_PROFILES: Dict[str, VehicleProfile] = {
    "ambulance": VehicleProfile(
        name="Emergency Ambulance (108)",
        d_safe_cm=5.0,
        d_critical_cm=20.0,
        base_speed_kmh=45.0,
        alpha=3.5,
        gamma=2.0
    ),
    "rescue_truck": VehicleProfile(
        name="NDRF / GCC Heavy Rescue Truck",
        d_safe_cm=15.0,
        d_critical_cm=50.0,
        base_speed_kmh=35.0,
        alpha=2.0,
        gamma=1.8
    ),
    "civilian_evac": VehicleProfile(
        name="Civilian / Two-Wheeler Evacuation",
        d_safe_cm=3.0,
        d_critical_cm=10.0,
        base_speed_kmh=15.0,
        alpha=5.0,
        gamma=2.5
    ),
}


class RiskCostEvaluator:
    """Evaluates dynamic routing impedance weights for the road network."""

    def __init__(self, vehicle_type: str = "ambulance"):
        if vehicle_type not in VEHICLE_PROFILES:
            raise ValueError(f"Unknown vehicle type '{vehicle_type}'. Valid: {list(VEHICLE_PROFILES.keys())}")
        self.profile = VEHICLE_PROFILES[vehicle_type]

    def compute_edge_impedance(
        self,
        lengths_m: np.ndarray,
        depths_cm: np.ndarray,
        enforce_cutoff: bool = True
    ) -> np.ndarray:
        """
        Computes dynamic edge traversal weights.

        Parameters:
          lengths_m: Vector of edge lengths in meters.
          depths_cm: Vector of current flood depths in cm.
          enforce_cutoff: If True, depths >= d_critical become infinite (impassable).

        Returns:
          Vector of impedance weights W_e.
        """
        p = self.profile
        weights = lengths_m.astype(np.float64).copy()

        # Mask for moderate water (d_safe <= d < d_critical)
        moderate_mask = (depths_cm >= p.d_safe_cm) & (depths_cm < p.d_critical_cm)
        if np.any(moderate_mask):
            ratio = (depths_cm[moderate_mask] - p.d_safe_cm) / max(1.0, p.d_safe_cm)
            penalty = 1.0 + p.alpha * np.power(ratio, p.gamma)
            weights[moderate_mask] *= penalty

        # Impassable cutoff (d >= d_critical)
        if enforce_cutoff:
            impassable_mask = depths_cm >= p.d_critical_cm
            weights[impassable_mask] = np.inf

        return weights

    def estimate_travel_time_min(self, length_m: float, depth_cm: float) -> float:
        """Estimates traversal duration in minutes considering water speed degradation."""
        p = self.profile
        base_speed_mps = (p.base_speed_kmh * 1000.0) / 3600.0

        if depth_cm >= p.d_critical_cm:
            return float("inf")

        if depth_cm <= p.d_safe_cm:
            eff_speed_mps = base_speed_mps
        else:
            fraction = (depth_cm - p.d_safe_cm) / (p.d_critical_cm - p.d_safe_cm)
            # Speed drops up to 75% as water approaches critical limit
            eff_speed_mps = base_speed_mps * max(0.25, 1.0 - (0.75 * fraction))

        return (length_m / eff_speed_mps) / 60.0
