"""Layer 4: Critical Assets Monitor - Substation Plinth Safeguarding & Relief Facilities.

Monitors critical urban infrastructure:
  1. 20 TANGEDCO 230kV / 110kV Electrical Substations
     - Risk Assessment: Water depth vs Plinth elevation (45 - 60 cm)
     - Circuit Breaker Tripping Protocol to avoid transformer explosions
  2. GCC Relief Shelters and Tier-1 Hospitals (RGGGH, Stanley, Apollo, MIOT)
     - Evacuation Corridor Availability
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

try:
    from ai_service.layer3.graph_builder import StreetDrainageGraph
except ImportError:
    from ..layer3.graph_builder import StreetDrainageGraph



logger = logging.getLogger(__name__)


# Standard TANGEDCO Substation Catalog (Greater Chennai Corporation Core)
CHENNAI_SUBSTATIONS = [
    {"id": "SS-001", "name": "Mylapore Substation", "voltage_kv": 230, "plinth_cm": 60.0, "lat": 13.0384, "lon": 80.2612},
    {"id": "SS-002", "name": "T. Nagar Substation", "voltage_kv": 110, "plinth_cm": 45.0, "lat": 13.0418, "lon": 80.2341},
    {"id": "SS-003", "name": "Guindy Industrial Grid", "voltage_kv": 230, "plinth_cm": 55.0, "lat": 13.0067, "lon": 80.2036},
    {"id": "SS-004", "name": "Koyambedu Substation", "voltage_kv": 110, "plinth_cm": 50.0, "lat": 13.0694, "lon": 80.1948},
    {"id": "SS-005", "name": "Velachery Substation", "voltage_kv": 110, "plinth_cm": 40.0, "lat": 12.9815, "lon": 80.2180},
    {"id": "SS-006", "name": "Alandur Substation", "voltage_kv": 110, "plinth_cm": 45.0, "lat": 13.0031, "lon": 80.1989},
    {"id": "SS-007", "name": "Adyar Substation", "voltage_kv": 110, "plinth_cm": 50.0, "lat": 13.0064, "lon": 80.2575},
    {"id": "SS-008", "name": "Kilpauk Water Works Grid", "voltage_kv": 110, "plinth_cm": 60.0, "lat": 13.0782, "lon": 80.2415},
    {"id": "SS-009", "name": "Perambur Railway Substation", "voltage_kv": 110, "plinth_cm": 45.0, "lat": 13.1075, "lon": 80.2334},
    {"id": "SS-010", "name": "Anna Nagar West Substation", "voltage_kv": 230, "plinth_cm": 65.0, "lat": 13.0878, "lon": 80.2052},
    {"id": "SS-011", "name": "Royapettah Substation", "voltage_kv": 110, "plinth_cm": 50.0, "lat": 13.0535, "lon": 80.2608},
    {"id": "SS-012", "name": "Saidapet Substation", "voltage_kv": 110, "plinth_cm": 45.0, "lat": 13.0211, "lon": 80.2229},
    {"id": "SS-013", "name": "Egmore Substation", "voltage_kv": 110, "plinth_cm": 55.0, "lat": 13.0732, "lon": 80.2609},
    {"id": "SS-014", "name": "Tondiarpet Grid", "voltage_kv": 230, "plinth_cm": 50.0, "lat": 13.1280, "lon": 80.2872},
    {"id": "SS-015", "name": "Thiruvanmiyur Substation", "voltage_kv": 110, "plinth_cm": 45.0, "lat": 12.9830, "lon": 80.2594},
    {"id": "SS-016", "name": "Pallavaram Substation", "voltage_kv": 110, "plinth_cm": 45.0, "lat": 12.9675, "lon": 80.1491},
    {"id": "SS-017", "name": "Tambaram Substation", "voltage_kv": 230, "plinth_cm": 60.0, "lat": 12.9249, "lon": 80.1165},
    {"id": "SS-018", "name": "Madhavaram Substation", "voltage_kv": 110, "plinth_cm": 50.0, "lat": 13.1482, "lon": 80.2314},
    {"id": "SS-019", "name": "Ambattur Industrial Substation", "voltage_kv": 230, "plinth_cm": 60.0, "lat": 13.1143, "lon": 80.1548},
    {"id": "SS-020", "name": "Porur Substation", "voltage_kv": 110, "plinth_cm": 45.0, "lat": 13.0382, "lon": 80.1565},
]

# Major Hospitals and Relief Centers
CRITICAL_FACILITIES = [
    {"id": "HOSP-01", "name": "Rajiv Gandhi Govt General Hospital (RGGGH)", "type": "Hospital", "lat": 13.0805, "lon": 80.2785},
    {"id": "HOSP-02", "name": "Government Stanley Hospital", "type": "Hospital", "lat": 13.1070, "lon": 80.2870},
    {"id": "HOSP-03", "name": "Kilpauk Medical College (KMC)", "type": "Hospital", "lat": 13.0784, "lon": 80.2425},
    {"id": "HOSP-04", "name": "Apollo Hospitals Greams Road", "type": "Hospital", "lat": 13.0604, "lon": 80.2514},
    {"id": "HOSP-05", "name": "MIOT International Manapakkam", "type": "Hospital", "lat": 13.0185, "lon": 80.1856},
    {"id": "CAMP-01", "name": "Jawaharlal Nehru Stadium Relief Hub", "type": "Relief Center", "lat": 13.0841, "lon": 80.2742},
    {"id": "CAMP-02", "name": "Chepauk Community Flood Shelter", "type": "Relief Center", "lat": 13.0628, "lon": 80.2789},
    {"id": "CAMP-03", "name": "Guindy Race Course High Ground Shelter", "type": "Relief Center", "lat": 13.0112, "lon": 80.2114},
]


class CriticalAssetsMonitor:
    """Monitors flood hazards at vital energy and medical installations."""

    def __init__(self, graph: Optional[StreetDrainageGraph] = None):
        self.graph = graph or StreetDrainageGraph()
        self.substations = CHENNAI_SUBSTATIONS
        self.facilities = CRITICAL_FACILITIES

        # Map each substation to its nearest road node
        self._substation_nodes = [
            self.graph.kdtree.query([ss["lon"], ss["lat"]])[1]
            for ss in self.substations
        ]

    def evaluate_substation_risks(self, depths_cm: np.ndarray) -> Dict[str, Any]:
        """
        Assesses electrical plinth water depths and circuit breaker risk.

        Status:
          - CRITICAL: depth >= 0.8 * plinth_cm (immediate de-energization advised)
          - WARNING: depth >= 15.0 cm (mobile dewatering pumps required)
          - NORMAL: depth < 15.0 cm (secure operations)
        """
        results = []
        critical_count = 0
        warning_count = 0
        normal_count = 0

        for i, ss in enumerate(self.substations):
            node_idx = self._substation_nodes[i]
            water_depth = float(depths_cm[node_idx])
            plinth = ss["plinth_cm"]
            ratio = water_depth / plinth

            if water_depth >= 0.80 * plinth:
                status = "CRITICAL_TRIP_RISK"
                alert_text = f"WATER AT PLINTH ({water_depth:.1f} cm / {plinth:.0f} cm). Tripping breakers advised."
                critical_count += 1
            elif water_depth >= 15.0:
                status = "WARNING"
                alert_text = f"Elevated surface water ({water_depth:.1f} cm). Deploy dewatering pump."
                warning_count += 1
            else:
                status = "NORMAL"
                alert_text = f"Secure ({water_depth:.1f} cm). Below safety threshold."
                normal_count += 1

            results.append({
                "id": ss["id"],
                "name": ss["name"],
                "voltage_kv": ss["voltage_kv"],
                "plinth_cm": plinth,
                "water_depth_cm": round(water_depth, 1),
                "plinth_clearance_cm": round(max(0.0, plinth - water_depth), 1),
                "status": status,
                "action_alert": alert_text,
                "lat": ss["lat"],
                "lon": ss["lon"]
            })

        return {
            "total_substations": len(self.substations),
            "critical_count": critical_count,
            "warning_count": warning_count,
            "normal_count": normal_count,
            "substations": results
        }
