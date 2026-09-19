from abc import ABC, abstractmethod
import hashlib
import networkx as nx


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

class Layer3ProviderInterface(ABC):
    """
    Abstract interface for Layer 3 Flood Prediction providers.
    Layer 4 routing components must depend on this interface, never concrete implementations.
    """
    @abstractmethod
    def get_predictions(self) -> Layer3Result:
        """Returns the fully validated flood predictions for the road network."""
        pass


class MockLayer3Provider(Layer3ProviderInterface):
    """
    MOCK / SYNTHETIC DATA PROVIDER ONLY.
    
    This does NOT generate real flood predictions for Chennai.
    It deterministically generates valid Layer3Result objects containing synthetic 
    flood conditions (low, moderate, severe) tied to actual road segment IDs 
    for the purpose of developing and testing Layer 4 independently of Layer 3.
    """
    def __init__(self, routing_graph: nx.MultiDiGraph):
        if not isinstance(routing_graph, nx.MultiDiGraph):
            raise TypeError("Expected a NetworkX MultiDiGraph")
        self.G = routing_graph
        self.impassable_threshold_cm = 20.0
        
    def get_predictions(self) -> Layer3Result:
        predictions = []
        
        # We need a unique list of segment IDs. The graph guarantees unique segment IDs per edge.
        for u, v, k, data in self.G.edges(keys=True, data=True):
            seg_id = data.get("segment_id")
            if not seg_id:
                continue
                
            # Guarantee absolute determinism by using a fixed hash of the unique segment string
            h = int(hashlib.md5(seg_id.encode('utf-8')).hexdigest(), 16)
            severity_roll = h % 100
            
            # Synthetic scenarios
            if severity_roll < 80:
                # 80% chance: Low/No flooding (Puddles, safe to drive)
                depths = [0.0, 2.0, 5.0, 10.0, 5.0, 0.0]
            elif severity_roll < 95:
                # 15% chance: Moderate flooding (Some horizons may cross impassable threshold)
                depths = [10.0, 18.0, 25.0, 30.0, 15.0, 5.0]
            else:
                # 5% chance: Severe flooding (Highly impassable flash floods)
                depths = [30.0, 80.0, 150.0, 180.0, 100.0, 40.0]
                
            # Add synthetic noise tied to the hash to make values look natural
            noise = (h % 50) / 10.0 # 0.0 to 4.9 cm of noise
            
            pred = {
                "segment_id": seg_id
            }
            
            horizons = ["T+15m", "T+30m", "T+60m", "T+90m", "T+120m", "T+180m"]
            for i, h_name in enumerate(horizons):
                # Apply noise but floor at 0.0
                final_depth = max(0.0, depths[i] + noise)
                
                pred[f"depth_{h_name}_cm"] = round(final_depth, 2)
                pred[f"is_impassable_{h_name}"] = final_depth > self.impassable_threshold_cm
                
            predictions.append(pred)
            
        return Layer3Result(predictions)

