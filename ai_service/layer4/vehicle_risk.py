import math

class VehicleRiskConfig:
    """
    Centralized configuration for vehicle-specific flood tolerances.
    NOTE: These values are PROJECT ASSUMPTIONS for KAIROS, not universal engineering standards.
    They represent the maximum effective flood depth (in cm) a vehicle can safely traverse.
    """
    TOLERANCES_CM = {
        "two_wheeler": 10.0,
        "passenger_car": 18.0,
        "ambulance": 30.0,
        "ndrf_heavy_rescue": 45.0
    }
    
    @classmethod
    def get_limit_cm(cls, vehicle_type: str) -> float:
        if vehicle_type not in cls.TOLERANCES_CM:
            raise ValueError(f"Unknown vehicle type: '{vehicle_type}'. Supported: {list(cls.TOLERANCES_CM.keys())}")
        return cls.TOLERANCES_CM[vehicle_type]


class FloodHazardEvaluator:
    """
    Evaluates the hazard ratio and passability of a road segment for a specific vehicle.
    """
    @staticmethod
    def evaluate(effective_depth_cm: float, vehicle_type: str, length_m: float, free_flow_speed_kmh: float, k: float = 5.0, p: float = 2.0) -> dict:
        """
        Calculates the hazard ratio (r) and passability for a given flood depth and vehicle,
        and computes the WHPF (Water Hazard Penalty Factor) hazard cost.
        
        Cost Formula for passable roads:
        cost = (L / v0) * (1 + k * r^p)
        where v0 is converted to m/s.
        """
        # 1. Validate vehicle type
        limit_cm = VehicleRiskConfig.get_limit_cm(vehicle_type)
        if limit_cm <= 0:
            raise ValueError(f"Vehicle depth limit must be strictly positive, got {limit_cm}cm")
            
        # 2. Validate numeric inputs and thresholds
        for val, name in [(effective_depth_cm, "effective_depth_cm"), 
                          (length_m, "length_m"), 
                          (free_flow_speed_kmh, "free_flow_speed_kmh"),
                          (k, "k"), 
                          (p, "p")]:
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                raise TypeError(f"{name} must be strictly numeric.")
            if math.isnan(val):
                raise ValueError(f"{name} cannot be NaN.")
            if math.isinf(val):
                raise ValueError(f"{name} cannot be infinite.")
                
        if effective_depth_cm < 0:
            raise ValueError(f"effective_depth_cm cannot be negative, got {effective_depth_cm}cm")
        if length_m <= 0:
            raise ValueError(f"length_m must be strictly positive, got {length_m}m")
        if free_flow_speed_kmh <= 0:
            raise ValueError(f"free_flow_speed_kmh must be strictly positive, got {free_flow_speed_kmh}km/h")
            
        # 3. Calculate hazard ratio (r)
        hazard_ratio = float(effective_depth_cm) / float(limit_cm)
        
        # 4. Blocking decision
        is_passable = hazard_ratio < 1.0
        status = "PASSABLE" if is_passable else "BLOCKED"
        
        # 5. WHPF Hazard Cost Calculation
        if is_passable:
            # EXPLICIT UNIT CONVERSION:
            # The routing graph stores free_flow_speed in km/h.
            # We must convert this to meters per second to match length_m.
            # 1 km/h = 1000m / 3600s = 1 / 3.6 m/s
            speed_m_per_second = free_flow_speed_kmh / 3.6
            
            baseline_time_seconds = length_m / speed_m_per_second
            
            # cost = (L / v0) * (1 + k * r^p)
            hazard_cost_seconds = baseline_time_seconds * (1.0 + k * math.pow(hazard_ratio, p))
        else:
            # Do not calculate a normal WHPF cost for a blocked edge.
            hazard_cost_seconds = float("inf")
        
        return {
            "vehicle_type": vehicle_type,
            "vehicle_depth_limit_cm": limit_cm,
            "effective_depth_cm": float(effective_depth_cm),
            "hazard_ratio": round(hazard_ratio, 4),
            "is_passable": is_passable,
            "status": status,
            "hazard_cost_seconds": float(hazard_cost_seconds) if not math.isinf(hazard_cost_seconds) else float('inf')
        }
