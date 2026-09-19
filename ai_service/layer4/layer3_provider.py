from abc import ABC, abstractmethod
import hashlib
import networkx as nx
from ai_service.layer4.layer3_contract import Layer3Result

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
