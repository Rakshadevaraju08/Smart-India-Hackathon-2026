class InvalidLayer3ContractError(Exception):
    """Exception raised when the provided Layer 3 result violates the contract schema."""
    pass


class Layer3Result:
    """
    Clean interface and validation layer for Layer 3 flood predictions.
    
    Expected external schema per segment:
    {
        "segment_id": str,
        "depth_T+15m_cm": float,
        "depth_T+30m_cm": float,
        "depth_T+60m_cm": float,
        "depth_T+90m_cm": float,
        "depth_T+120m_cm": float,
        "depth_T+180m_cm": float,
        "is_impassable_T+15m": bool,
        "is_impassable_T+30m": bool,
        "is_impassable_T+60m": bool,
        "is_impassable_T+90m": bool,
        "is_impassable_T+120m": bool,
        "is_impassable_T+180m": bool
    }
    """
    
    REQUIRED_HORIZONS = [
        "T+15m", 
        "T+30m", 
        "T+60m", 
        "T+90m", 
        "T+120m", 
        "T+180m"
    ]
    
    def __init__(self, predictions: list[dict]):
        self.predictions = predictions
        self._index = {}
        self._validate()
        
    def _validate(self):
        seen_segments = set()
        
        if not isinstance(self.predictions, list):
            raise InvalidLayer3ContractError("Predictions must be provided as a list of dictionaries.")
            
        for p in self.predictions:
            if not isinstance(p, dict):
                raise InvalidLayer3ContractError("Each prediction must be a dictionary.")
                
            if "segment_id" not in p:
                raise InvalidLayer3ContractError("Missing 'segment_id' in prediction.")
            
            seg_id = p["segment_id"]
            if not seg_id:
                raise InvalidLayer3ContractError("Empty or null 'segment_id' in prediction.")
                
            if seg_id in seen_segments:
                raise InvalidLayer3ContractError(f"Duplicate segment_id found: {seg_id}")
            seen_segments.add(seg_id)
            
            for horizon in self.REQUIRED_HORIZONS:
                depth_key = f"depth_{horizon}_cm"
                impassable_key = f"is_impassable_{horizon}"
                
                # Check column existence
                if depth_key not in p:
                    raise InvalidLayer3ContractError(f"Missing required depth field '{depth_key}' for segment {seg_id}")
                
                if impassable_key not in p:
                    raise InvalidLayer3ContractError(f"Missing required impassability field '{impassable_key}' for segment {seg_id}")
                    
                # Validate numeric depths
                depth_val = p[depth_key]
                if not isinstance(depth_val, (int, float)) or isinstance(depth_val, bool):
                    raise InvalidLayer3ContractError(f"Depth '{depth_key}' must be numeric for segment {seg_id}")
                    
                import math
                if math.isnan(depth_val):
                    raise InvalidLayer3ContractError(f"Depth '{depth_key}' cannot be NaN for segment {seg_id}")
                    
                # Validate non-negative
                if depth_val < 0:
                    raise InvalidLayer3ContractError(f"Depth '{depth_key}' cannot be negative for segment {seg_id}. Got: {depth_val}")
                    
                # Validate boolean impassability
                impassable_val = p[impassable_key]
                if not isinstance(impassable_val, bool):
                    raise InvalidLayer3ContractError(f"Impassability '{impassable_key}' must be a strict boolean for segment {seg_id}")
                    
            # Build quick-lookup index
            self._index[seg_id] = p
            
    def get_prediction(self, segment_id: str) -> dict:
        """Returns the fully validated prediction dict for a segment ID, or None if not found."""
        return self._index.get(segment_id)
        
    def has_prediction(self, segment_id: str) -> bool:
        return segment_id in self._index
