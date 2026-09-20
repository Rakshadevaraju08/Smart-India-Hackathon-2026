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
    def evaluate_road_risk(segment_id: str, length_m: float, free_flow_speed_kmh: float, effective_depth_cm: float, vehicle_type: str, k: float = 5.0, p: float = 2.0) -> dict:
        """
        Calculates the complete road-risk evaluation for a specific vehicle on a specific road segment.
        
        Cost Formula for passable roads:
        cost = (L / v0) * (1 + k * r^p)
        where v0 is converted to m/s.
        """
        # 1. Validate segment_id
        if not segment_id:
            raise ValueError("Segment ID cannot be empty.")
            
        # 2. Validate vehicle type
        limit_cm = VehicleRiskConfig.get_limit_cm(vehicle_type)
        if limit_cm <= 0:
            raise ValueError(f"Vehicle depth limit must be strictly positive, got {limit_cm}cm")
            
        # 3. Validate numeric inputs and thresholds
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
            
        # 4. Calculate hazard ratio (r)
        hazard_ratio = float(effective_depth_cm) / float(limit_cm)
        
        # 5. Blocking decision
        is_passable = hazard_ratio < 1.0
        status = "PASSABLE" if is_passable else "BLOCKED"
        
        # 6. WHPF Hazard Cost and Travel Time Calculation
        # EXPLICIT UNIT CONVERSION:
        # The routing graph stores free_flow_speed in km/h.
        # We must convert this to meters per second to match length_m.
        # 1 km/h = 1000m / 3600s = 1 / 3.6 m/s
        speed_m_per_second = free_flow_speed_kmh / 3.6
        baseline_time_seconds = length_m / speed_m_per_second
        
        if is_passable:
            # v = v0 * (1 - 0.7*r)
            # Ensure speed does not drop below zero in edge cases
            adjusted_speed_m_per_second = max(0.0, speed_m_per_second * (1.0 - 0.7 * hazard_ratio))
            
            # t = L / v
            if adjusted_speed_m_per_second > 0:
                actual_travel_time_seconds = length_m / adjusted_speed_m_per_second
            else:
                actual_travel_time_seconds = float("inf")
                
            # cost = (L / v0) * (1 + k * r^p)
            hazard_cost_seconds = baseline_time_seconds * (1.0 + k * math.pow(hazard_ratio, p))
        else:
            # Do not calculate normal WHPF cost or speed for a blocked edge.
            adjusted_speed_m_per_second = None
            actual_travel_time_seconds = float("inf")
            hazard_cost_seconds = float("inf")
        
        return {
            "segment_id": segment_id,
            "vehicle_type": vehicle_type,
            "vehicle_depth_limit_cm": limit_cm,
            "effective_depth_cm": float(effective_depth_cm),
            "hazard_ratio": round(hazard_ratio, 4),
            "is_passable": is_passable,
            "status": status,
            "free_flow_speed_kmh": float(free_flow_speed_kmh),
            "free_flow_speed_m_per_s": round(speed_m_per_second, 3),
            "adjusted_speed_m_per_s": round(adjusted_speed_m_per_second, 3) if adjusted_speed_m_per_second is not None else None,
            "free_flow_travel_time_seconds": round(baseline_time_seconds, 2),
            "actual_travel_time_seconds": round(actual_travel_time_seconds, 2) if not math.isinf(actual_travel_time_seconds) else float('inf'),
            "hazard_cost_seconds": float(hazard_cost_seconds) if not math.isinf(hazard_cost_seconds) else float('inf'),
            "k": float(k),
            "p": float(p)
        }
