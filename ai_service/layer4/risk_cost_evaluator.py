"""Layer 4: Risk Cost Evaluator - Dynamic Hydrodynamic Traversal Impedance.

Computes vehicle-specific traversal impedances across road segments as a function of:
  - Real-time flood depth d_e(t) in centimeters from Layer 3 PI-GNN Surrogate
  - Overland flow velocity v_e(t) in m/s (from shallow water / Manning's equation)
  - Vehicle water-fording threshold d_c (Ambulance 30cm, Rescue Truck 60cm, Car 18cm, Two-Wheeler 10cm)
  - Hydrodynamic drag and quadratic speed degradation:
      V_eff = V_base * (1 - (d_e / d_c)^2)
  - Inundation risk penalty for trauma/sensitive patient transit
  - Critical hydrodynamic momentum stability limit (depth * velocity)

Mathematical Formulation:
  For edge e of length L_e with water depth d_e(t) and flow velocity v_e(t):
    If d_e(t) >= d_c or (d_e/100 * v_e) >= (d*v)_crit:
        C(e, t) = infinity (Catastrophic Impassability / Severed Corridor)
    Else:
        V_eff(e, t) = V_base * [1 - (d_e / d_c)^2]
        T_traversal(e, t) = L_e / V_eff(e, t)
        Pi_inund(e, t) = alpha * ((d_e - d_safe) / (d_c - d_safe))^gamma * (L_e / V_base)   [for d_e > d_safe]
        Pi_velocity(e, t) = beta_v * (((d_e/100) * v_e) / (d*v)_crit)^2 * (L_e / V_base)
        C(e, t) = T_traversal(e, t) + Pi_inund(e, t) + Pi_velocity(e, t)
"""

import logging
import math
from dataclasses import dataclass
from typing import Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class VehicleProfile:
    """Hydrodynamic parameters for emergency vehicle classes."""
    name: str
    d_safe_cm: float          # Comfortable wading threshold without speed loss
    d_critical_cm: float      # Absolute cutoff depth (air intake / exhaust hydrolock)
    base_speed_kmh: float     # Free-flow velocity in dry conditions
    critical_dv_m2_s: float   # Hydrodynamic stability limit (depth * velocity) [m^2/s]
    alpha: float              # Risk penalty scaling coefficient
    gamma: float              # Exponential non-linearity exponent
    beta_v: float             # Velocity momentum hazard scaling coefficient
    description: str = ""


# Standard Chennai Emergency Fleet Profiles (MoES / GCC Disaster Protocol)
VEHICLE_PROFILES: Dict[str, VehicleProfile] = {
    "ambulance": VehicleProfile(
        name="Emergency Ambulance (108)",
        d_safe_cm=10.0,
        d_critical_cm=30.0,
        base_speed_kmh=45.0,
        critical_dv_m2_s=0.45,
        alpha=3.5,
        gamma=2.0,
        beta_v=2.5,
        description="Force Traveller / Tata Winger 108 Emergency Ambulance. Critical clearance 30 cm (air intake/exhaust hydrolock). Priority: Zero-submersion green corridor."
    ),
    "rescue_truck": VehicleProfile(
        name="NDRF / TNFRS Heavy Rescue Truck",
        d_safe_cm=25.0,
        d_critical_cm=60.0,
        base_speed_kmh=35.0,
        critical_dv_m2_s=1.05,
        alpha=1.8,
        gamma=1.6,
        beta_v=1.5,
        description="Ashok Leyland 4x4 / BharatBenz Heavy Rescue Vehicle / GCC JCB. Critical clearance 60 cm (raised wading snorkel). Capable of high hydrodynamic breach."
    ),
    "civilian_car": VehicleProfile(
        name="Civilian Passenger Car (Sedan / Hatchback)",
        d_safe_cm=8.0,
        d_critical_cm=18.0,
        base_speed_kmh=30.0,
        critical_dv_m2_s=0.30,
        alpha=4.0,
        gamma=2.2,
        beta_v=3.0,
        description="Civilian passenger sedan/hatchback/compact SUV. Critical clearance 18 cm. Hydrodynamic floatation and loss of traction at 0.30 m2/s."
    ),
    "two_wheeler": VehicleProfile(
        name="Civilian Two-Wheeler (Motorcycle / Scooter)",
        d_safe_cm=3.0,
        d_critical_cm=10.0,
        base_speed_kmh=20.0,
        critical_dv_m2_s=0.15,
        alpha=6.0,
        gamma=2.5,
        beta_v=4.0,
        description="Motorcycle / Scooter. Critical clearance 10 cm (exhaust backflow, spark plug short). Extreme vulnerability to lateral flow destabilization."
    ),
}

# Backward compatibility alias
VEHICLE_PROFILES["civilian_evac"] = VEHICLE_PROFILES["civilian_car"]


class RiskCostEvaluator:
    """Evaluates dynamic routing impedance weights and hydrodynamic traversal travel times."""

    def __init__(self, vehicle_type: str = "ambulance"):
        v_key = vehicle_type.lower()
        if v_key not in VEHICLE_PROFILES:
            raise ValueError(f"Unknown vehicle type '{vehicle_type}'. Valid: {list(VEHICLE_PROFILES.keys())}")
        self.profile = VEHICLE_PROFILES[v_key]
        self.base_speed_mps = (self.profile.base_speed_kmh * 1000.0) / 3600.0

    def compute_effective_velocity(self, depth_cm: float) -> float:
        """
        Calculates effective velocity under hydrodynamic drag:
          V_eff = V_base * (1 - (d / d_c)^2)
        """
        p = self.profile
        if depth_cm >= p.d_critical_cm:
            return 0.0
        if depth_cm <= 0.0:
            return self.base_speed_mps

        ratio = depth_cm / p.d_critical_cm
        degradation = max(0.05, 1.0 - (ratio * ratio))
        return self.base_speed_mps * degradation

    def compute_edge_traversal_cost(
        self,
        length_m: float,
        depth_cm: float,
        velocity_mps: float = 0.0,
        enforce_cutoff: bool = True
    ) -> float:
        """
        Computes dynamic hydrodynamic traversal cost C(e, t) in seconds.

        Formulation:
          C(e, t) = Length / (Speed * (1 - (d / d_c)^2)) + Inundation Risk Penalty + Velocity Drag Penalty
        """
        p = self.profile
        d_m = depth_cm / 100.0
        dv_product = d_m * abs(velocity_mps)

        # 1. Catastrophic Cutoff Check (Engine Hydrolock or Hydrodynamic Overturning)
        if enforce_cutoff:
            if depth_cm >= p.d_critical_cm or dv_product >= p.critical_dv_m2_s:
                return float("inf")

        # 2. Hydrodynamic Speed Degradation Traversal Time
        v_eff = self.compute_effective_velocity(depth_cm)
        if v_eff <= 1e-3:
            return float("inf")

        base_traversal_time_s = length_m / v_eff

        # 3. Non-Linear Inundation Risk Penalty
        inundation_penalty_s = 0.0
        if depth_cm > p.d_safe_cm:
            depth_span = max(1.0, p.d_critical_cm - p.d_safe_cm)
            norm_excess = (depth_cm - p.d_safe_cm) / depth_span
            inundation_penalty_s = p.alpha * (norm_excess ** p.gamma) * (length_m / self.base_speed_mps)

        # 4. Hydrodynamic Momentum Hazard Penalty
        velocity_penalty_s = 0.0
        if dv_product > 0.0:
            norm_dv = min(1.0, dv_product / p.critical_dv_m2_s)
            velocity_penalty_s = p.beta_v * (norm_dv ** 2) * (length_m / self.base_speed_mps)

        return base_traversal_time_s + inundation_penalty_s + velocity_penalty_s

    def compute_edge_impedance(
        self,
        lengths_m: np.ndarray,
        depths_cm: np.ndarray,
        velocities_mps: Optional[np.ndarray] = None,
        enforce_cutoff: bool = True
    ) -> np.ndarray:
        """
        Vectorized computation of dynamic edge traversal weights (in meters equivalent).

        Returns:
          Vector of impedance weights W_e.
        """
        p = self.profile
        weights = lengths_m.astype(np.float64).copy()

        # Moderate water speed degradation: factor = 1 / (1 - (d/d_c)^2)
        valid_mask = depths_cm < p.d_critical_cm
        safe_ratios = np.clip(depths_cm[valid_mask] / p.d_critical_cm, 0.0, 0.98)
        drag_factors = 1.0 / np.maximum(0.04, 1.0 - (safe_ratios ** 2))
        weights[valid_mask] *= drag_factors

        # Risk penalty for depths above d_safe
        risk_mask = valid_mask & (depths_cm > p.d_safe_cm)
        if np.any(risk_mask):
            depth_span = max(1.0, p.d_critical_cm - p.d_safe_cm)
            norm_excess = (depths_cm[risk_mask] - p.d_safe_cm) / depth_span
            weights[risk_mask] += lengths_m[risk_mask] * p.alpha * np.power(norm_excess, p.gamma)

        # Velocity momentum penalty if velocities provided
        if velocities_mps is not None:
            d_m = depths_cm / 100.0
            dv = d_m * np.abs(velocities_mps)
            v_mask = valid_mask & (dv > 0.0)
            if np.any(v_mask):
                norm_dv = np.clip(dv[v_mask] / p.critical_dv_m2_s, 0.0, 1.0)
                weights[v_mask] += lengths_m[v_mask] * p.beta_v * np.square(norm_dv)

            # Impassable velocity cutoff
            if enforce_cutoff:
                weights[dv >= p.critical_dv_m2_s] = np.inf

        # Impassable depth cutoff
        if enforce_cutoff:
            weights[depths_cm >= p.d_critical_cm] = np.inf

        return weights

    def estimate_travel_time_min(
        self,
        length_m: float,
        depth_cm: float,
        velocity_mps: float = 0.0
    ) -> float:
        """Estimates traversal duration in minutes considering water speed degradation."""
        p = self.profile
        if depth_cm >= p.d_critical_cm:
            return float("inf")

        d_m = depth_cm / 100.0
        if (d_m * abs(velocity_mps)) >= p.critical_dv_m2_s:
            return float("inf")

        v_eff = self.compute_effective_velocity(depth_cm)
        if v_eff <= 1e-3:
            return float("inf")

        return (length_m / v_eff) / 60.0

