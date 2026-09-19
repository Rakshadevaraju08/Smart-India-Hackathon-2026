from abc import ABC, abstractmethod

class UncertaintyModel(ABC):
    """
    Abstract interface for flood depth uncertainty models.
    """
    @abstractmethod
    def get_uncertainty_cm(self, minutes_from_departure: float, predicted_depth_cm: float) -> float:
        """
        Calculates the uncertainty margin in centimeters based on forecast lead time and predicted depth.
        """
        pass


class SyntheticUncertaintyModel(UncertaintyModel):
    """
    MOCK / SYNTHETIC UNCERTAINTY POLICY.
    
    This does NOT represent measured error from real Layer 3 ML models. 
    It is purely an engineering assumption allowing Layer 4 development to handle 
    deteriorating confidence horizons safely.
    
    Policy: The uncertainty margin increases monotonically with forecast lead time.
    """
    def __init__(self):
        # Configuration mapping: Lead time (minutes) -> Uncertainty Margin (cm)
        # This is strictly a configurable synthetic policy and is highly modular.
        self.margin_config = {
            15: 2.0,
            30: 5.0,
            60: 10.0,
            90: 15.0,
            120: 20.0,
            180: 30.0
        }
        self.horizons = sorted(self.margin_config.keys())
        
    def get_uncertainty_cm(self, minutes_from_departure: float, predicted_depth_cm: float) -> float:
        if minutes_from_departure < 0:
            raise ValueError("minutes_from_departure cannot be negative")
            
        # Boundary Policy Before T+15
        if minutes_from_departure <= self.horizons[0]:
            return self.margin_config[self.horizons[0]]
            
        # Boundary Policy After T+180
        if minutes_from_departure >= self.horizons[-1]:
            return self.margin_config[self.horizons[-1]]
            
        # Linear interpolation for intermediate times
        for i in range(len(self.horizons) - 1):
            t1 = self.horizons[i]
            t2 = self.horizons[i+1]
            
            if t1 <= minutes_from_departure <= t2:
                m1 = self.margin_config[t1]
                m2 = self.margin_config[t2]
                
                fraction = (minutes_from_departure - t1) / (t2 - t1)
                margin = m1 + fraction * (m2 - m1)
                return round(margin, 2)
                
        return self.margin_config[self.horizons[-1]]
