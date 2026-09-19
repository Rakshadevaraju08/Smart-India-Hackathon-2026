import math
from ai_service.layer4.layer3_contract import Layer3Result
from ai_service.layer4.uncertainty_model import UncertaintyModel, SyntheticUncertaintyModel

class TemporalFloodDepthService:
    """
    Handles temporal queries and interpolation for flood depths extracted from a Layer3Result.
    Provides mathematically continuous depth values in centimeters across the forecast horizons.
    Incorporates an UncertaintyModel to calculate safe effective depths.
    """
    def __init__(self, layer3_result: Layer3Result, uncertainty_model: UncertaintyModel = None):
        if not isinstance(layer3_result, Layer3Result):
            raise TypeError("layer3_result must be an instance of Layer3Result")
        self.layer3_result = layer3_result
        self.uncertainty_model = uncertainty_model or SyntheticUncertaintyModel()
        self.horizons = [15, 30, 60, 90, 120, 180]
        
    def get_effective_depth(self, segment_id: str, minutes_from_departure: float) -> dict:
        """
        Calculates the predicted flood depth for a specific segment at a specific future time.
        
        Args:
            segment_id: The unique identifier of the road segment.
            minutes_from_departure: The temporal offset into the future in minutes.
            
        Returns:
            A structured dictionary containing segment_id, requested time, calculated depths, 
            and interpolation boundary details.
        """
        # 1. Validate segment_id
        if not segment_id:
            raise ValueError("Segment ID cannot be empty.")
            
        # Validate time input
        if not isinstance(minutes_from_departure, (int, float)) or isinstance(minutes_from_departure, bool):
            raise TypeError("minutes_from_departure must be strictly numeric.")
            
        if math.isnan(minutes_from_departure):
            raise ValueError("minutes_from_departure cannot be NaN.")
            
        if minutes_from_departure < 0:
            raise ValueError("minutes_from_departure cannot be negative.")
            
        # 2. Validate Layer3Result data exists
        pred = self.layer3_result.get_prediction(segment_id)
        if not pred:
            raise ValueError(f"No Layer 3 prediction found for segment {segment_id}")
            
        # Extract and validate depth values
        try:
            depths = [
                self._validate_depth(pred[f"depth_T+{h}m_cm"]) 
                for h in self.horizons
            ]
        except KeyError as e:
            raise ValueError(f"Missing required prediction horizon in Layer 3 data: {e}")
            
        # Helper to compute the full return object
        def _build_response(predicted_depth: float, source_horizons: tuple, is_clamped_before=False, is_clamped_after=False) -> dict:
            predicted_depth = round(predicted_depth, 2)
            margin = self.uncertainty_model.get_uncertainty_cm(minutes_from_departure, predicted_depth)
            
            return {
                "segment_id": segment_id,
                "minutes_from_departure": minutes_from_departure,
                "predicted_depth_cm": predicted_depth,
                "uncertainty_margin_cm": margin,
                "effective_depth_cm": round(predicted_depth + margin, 2),
                "interpolation_source_horizons": source_horizons,
                "is_clamped_before_T15": is_clamped_before,
                "is_clamped_after_T180": is_clamped_after
            }
            
        # Boundary Policy Before T+15
        if minutes_from_departure <= 15.0:
            return _build_response(depths[0], (15, 15), is_clamped_before=(minutes_from_departure < 15.0))
            
        # Boundary Policy After T+180
        if minutes_from_departure >= 180.0:
            return _build_response(depths[-1], (180, 180), is_clamped_after=(minutes_from_departure > 180.0))
            
        # Interpolation Search
        for i in range(len(self.horizons) - 1):
            t1 = self.horizons[i]
            t2 = self.horizons[i+1]
            
            if t1 <= minutes_from_departure <= t2:
                # Exact matches
                if minutes_from_departure == t1:
                    return _build_response(depths[i], (t1, t1))
                if minutes_from_departure == t2:
                    return _build_response(depths[i+1], (t2, t2))
                    
                # Linear interpolation
                d1 = depths[i]
                d2 = depths[i+1]
                
                fraction = (minutes_from_departure - t1) / (t2 - t1)
                depth = d1 + fraction * (d2 - d1)
                
                return _build_response(depth, (t1, t2))
                
        # Unreachable fail-safe
        return _build_response(depths[-1], (180, 180))

    def _validate_depth(self, val) -> float:
        # 3, 4, 5. Validate numeric, non-negative, and not NaN
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            raise TypeError(f"Depth value must be strictly numeric, got {type(val)}")
        if math.isnan(val):
            raise ValueError("Depth value cannot be NaN")
        if val < 0:
            raise ValueError("Depth value cannot be negative")
        return float(val)
