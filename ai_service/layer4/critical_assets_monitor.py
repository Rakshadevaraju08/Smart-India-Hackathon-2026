"""Layer 4: Critical Assets Monitor - Substation Plinth Safeguarding.

Monitors critical urban energy infrastructure by connecting geospatial assets
to Layer 3 flood predictions via the Layer 4 road network.
"""

import csv
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import math

from ai_service.layer4.temporal_flood import TemporalFloodDepthService

logger = logging.getLogger(__name__)

# Configurable thresholds
STATUS_SAFE = "SAFE"
STATUS_AT_RISK = "AT_RISK"
STATUS_CRITICAL = "CRITICAL"
STATUS_UNKNOWN = "UNKNOWN"

# We assume a default critical clearance margin of 15cm if plinth is known
CRITICAL_MARGIN_CM = 15.0

@dataclass
class SubstationMonitoringResult:
    substation_id: str
    name: str
    voltage_kv: str
    latitude: str
    longitude: str
    road_segment_id: str
    ground_elevation_m: str
    plinth_height_m: str
    plinth_height_known: bool
    source_information: str
    forecast_depths: Dict[str, float]
    maximum_effective_depth: float
    maximum_forecast_horizon_affected: str
    flood_status: str
    uncertainty_flag: str
    explanation: str


class CriticalAssetsMonitor:
    def __init__(self, csv_path: str = "ai_service/layer4/data/substations.csv"):
        self.csv_path = csv_path
        self.substations = self._load_substations()

    def _load_substations(self) -> List[Dict[str, str]]:
        subs = []
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    subs.append(row)
        except Exception as e:
            logger.error(f"Failed to load substations from {self.csv_path}: {e}")
        return subs

    def evaluate_substations(self, temporal_service: TemporalFloodDepthService) -> List[SubstationMonitoringResult]:
        results = []
        horizons_min = [15.0, 30.0, 60.0, 90.0, 120.0, 180.0]
        horizon_labels = {
            15.0: "T+15", 30.0: "T+30", 60.0: "T+60", 
            90.0: "T+90", 120.0: "T+120", 180.0: "T+180"
        }

        for sub in self.substations:
            sub_id = sub.get("substation_id", "")
            seg_id = sub.get("road_segment_id", "")
            plinth_str = sub.get("plinth_height_m", "")
            
            plinth_known = bool(plinth_str.strip())
            
            # Defaults
            max_depth = 0.0
            max_horizon = "N/A"
            forecasts = {}
            status = STATUS_UNKNOWN
            uncertainty = ""
            explanation = ""
            
            if not seg_id:
                uncertainty = "NO_ROAD_MAPPING"
                explanation = "Substation is not mapped to a valid Layer 4 road segment. Flood forecast cannot be obtained."
            else:
                try:
                    is_data_available = True
                    for t in horizons_min:
                        try:
                            res_dict = temporal_service.get_effective_depth(seg_id, t)
                            depth = res_dict["effective_depth_cm"]
                        except ValueError:
                            is_data_available = False
                            break
                            
                        forecasts[horizon_labels[t]] = depth
                        if depth > max_depth:
                            max_depth = depth
                            max_horizon = horizon_labels[t]
                            
                    if not is_data_available:
                        status = STATUS_UNKNOWN
                        uncertainty = "DATA_UNAVAILABLE"
                        explanation = f"Substation is associated with road segment {seg_id}, but Layer 3 data is unavailable or missing."
                    else:
                        if not plinth_known:
                            status = STATUS_UNKNOWN
                            uncertainty = "PLINTH_UNKNOWN"
                            explanation = f"Substation is associated with road segment {seg_id}. The Layer 3 forecast reaches {max_depth:.1f} cm effective depth at {max_horizon}. The asset's authoritative plinth height is unavailable, so flood exposure cannot be determined with full confidence."
                        else:
                            plinth_cm = float(plinth_str) * 100.0 # Convert m to cm
                            margin = plinth_cm - max_depth
                            
                            if margin <= 0:
                                status = STATUS_CRITICAL
                                explanation = f"Substation is associated with road segment {seg_id}. The Layer 3 forecast reaches {max_depth:.1f} cm at {max_horizon}, exceeding the known plinth height by {abs(margin):.1f} cm! Flooding is imminent."
                            elif margin <= CRITICAL_MARGIN_CM:
                                status = STATUS_AT_RISK
                                explanation = f"Substation is associated with road segment {seg_id}. The Layer 3 forecast reaches {max_depth:.1f} cm at {max_horizon}. Margin ({margin:.1f} cm) is below critical threshold."
                            else:
                                status = STATUS_SAFE
                                explanation = f"Substation is associated with road segment {seg_id}. Maximum forecast depth {max_depth:.1f} cm at {max_horizon} is safely below plinth margin ({margin:.1f} cm clearance)."
                except Exception as e:
                    status = STATUS_UNKNOWN
                    uncertainty = "EVALUATION_ERROR"
                    explanation = f"Error evaluating risk: {str(e)}"

            res = SubstationMonitoringResult(
                substation_id=sub_id,
                name=sub.get("name", ""),
                voltage_kv=sub.get("voltage_kv", ""),
                latitude=sub.get("latitude", ""),
                longitude=sub.get("longitude", ""),
                road_segment_id=seg_id,
                ground_elevation_m=sub.get("ground_elevation_m", ""),
                plinth_height_m=plinth_str,
                plinth_height_known=plinth_known,
                source_information=sub.get("source_name", ""),
                forecast_depths=forecasts,
                maximum_effective_depth=round(max_depth, 2),
                maximum_forecast_horizon_affected=max_horizon,
                flood_status=status,
                uncertainty_flag=uncertainty,
                explanation=explanation
            )
            results.append(res)
            
        return results
