"""Layer 4: Critical Assets Monitor - Substation Plinth Safeguarding & Medical Oxygen Depots.

Monitors critical urban energy and healthcare lifeline installations across Chennai:
  1. 20 TANGEDCO 230kV / 110kV Electrical Substations
     - Risk Assessment: Real-time Flood Depth z_flood vs Plinth Elevation z_plinth (40 - 65 cm)
     - Margin Criterion: Delta z = z_plinth - z_flood
     - Automated Predictive De-Energization Alert triggered when Delta z < 15 cm (z_flood > z_plinth - 15cm)
     - Circuit Breaker Tripping Protocol to avoid explosive oil flashover & urban electrocution
  2. Critical Medical Oxygen Depots & Hospital Cryogenic Yards
     - RGGGH, Stanley, KMC, Apollo Greams Road, MIOT International
     - Safeguarding ambient vaporizers and pressure manifolds from cryogenic freezing collapse
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

try:
    from ai_service.layer3.graph_builder import StreetDrainageGraph
except ImportError:
    from ..layer3.graph_builder import StreetDrainageGraph


logger = logging.getLogger(__name__)


# TANGEDCO Substation Catalog (Greater Chennai Corporation Core Grid)
CHENNAI_SUBSTATIONS = [
    {"id": "SS-001", "name": "Mylapore Substation", "voltage_kv": 230, "plinth_cm": 60.0, "lat": 13.0384, "lon": 80.2612, "zone": "Zone 9 - Mylapore"},
    {"id": "SS-002", "name": "T. Nagar Substation", "voltage_kv": 110, "plinth_cm": 45.0, "lat": 13.0418, "lon": 80.2341, "zone": "Zone 10 - Kodambakkam"},
    {"id": "SS-003", "name": "Guindy Industrial Grid", "voltage_kv": 230, "plinth_cm": 55.0, "lat": 13.0067, "lon": 80.2036, "zone": "Zone 13 - Guindy"},
    {"id": "SS-004", "name": "Koyambedu Substation", "voltage_kv": 110, "plinth_cm": 50.0, "lat": 13.0694, "lon": 80.1948, "zone": "Zone 8 - Anna Nagar"},
    {"id": "SS-005", "name": "Velachery Substation", "voltage_kv": 110, "plinth_cm": 40.0, "lat": 12.9815, "lon": 80.2180, "zone": "Zone 13 - Velachery"},
    {"id": "SS-006", "name": "Alandur Substation", "voltage_kv": 110, "plinth_cm": 45.0, "lat": 13.0031, "lon": 80.1989, "zone": "Zone 12 - Alandur"},
    {"id": "SS-007", "name": "Adyar Substation", "voltage_kv": 110, "plinth_cm": 50.0, "lat": 13.0064, "lon": 80.2575, "zone": "Zone 13 - Adyar"},
    {"id": "SS-008", "name": "Kilpauk Water Works Grid", "voltage_kv": 110, "plinth_cm": 60.0, "lat": 13.0782, "lon": 80.2415, "zone": "Zone 8 - Kilpauk"},
    {"id": "SS-009", "name": "Perambur Railway Substation", "voltage_kv": 110, "plinth_cm": 45.0, "lat": 13.1075, "lon": 80.2334, "zone": "Zone 6 - Thiru Vi Ka Nagar"},
    {"id": "SS-010", "name": "Anna Nagar West Substation", "voltage_kv": 230, "plinth_cm": 65.0, "lat": 13.0878, "lon": 80.2052, "zone": "Zone 8 - Anna Nagar"},
    {"id": "SS-011", "name": "Royapettah Substation", "voltage_kv": 110, "plinth_cm": 50.0, "lat": 13.0535, "lon": 80.2608, "zone": "Zone 9 - Royapettah"},
    {"id": "SS-012", "name": "Saidapet Substation", "voltage_kv": 110, "plinth_cm": 45.0, "lat": 13.0211, "lon": 80.2229, "zone": "Zone 10 - Saidapet"},
    {"id": "SS-013", "name": "Egmore Substation", "voltage_kv": 110, "plinth_cm": 55.0, "lat": 13.0732, "lon": 80.2609, "zone": "Zone 5 - Royapuram"},
    {"id": "SS-014", "name": "Tondiarpet Grid", "voltage_kv": 230, "plinth_cm": 50.0, "lat": 13.1280, "lon": 80.2872, "zone": "Zone 4 - Tondiarpet"},
    {"id": "SS-015", "name": "Thiruvanmiyur Substation", "voltage_kv": 110, "plinth_cm": 45.0, "lat": 12.9830, "lon": 80.2594, "zone": "Zone 13 - Thiruvanmiyur"},
    {"id": "SS-016", "name": "Pallavaram Substation", "voltage_kv": 110, "plinth_cm": 45.0, "lat": 12.9675, "lon": 80.1491, "zone": "Zone 12 - Pallavaram"},
    {"id": "SS-017", "name": "Tambaram Substation", "voltage_kv": 230, "plinth_cm": 60.0, "lat": 12.9249, "lon": 80.1165, "zone": "Zone 14 - Perungudi"},
    {"id": "SS-018", "name": "Madhavaram Substation", "voltage_kv": 110, "plinth_cm": 50.0, "lat": 13.1482, "lon": 80.2314, "zone": "Zone 3 - Madhavaram"},
    {"id": "SS-019", "name": "Ambattur Industrial Substation", "voltage_kv": 230, "plinth_cm": 60.0, "lat": 13.1143, "lon": 80.1548, "zone": "Zone 7 - Ambattur"},
    {"id": "SS-020", "name": "Porur Substation", "voltage_kv": 110, "plinth_cm": 45.0, "lat": 13.0382, "lon": 80.1565, "zone": "Zone 11 - Valasaravakkam"},
]

# Medical Oxygen Depots & Tertiary Healthcare Facilities
MEDICAL_OXYGEN_DEPOTS = [
    {
        "id": "O2-001",
        "name": "RGGGH Liquid Cryogenic Oxygen Depot (20 KL Tank)",
        "type": "Cryogenic Oxygen Plant",
        "plinth_cm": 75.0,
        "lat": 13.0805,
        "lon": 80.2785,
        "facility": "Rajiv Gandhi Govt General Hospital",
        "critical_capacity_kl": 20.0
    },
    {
        "id": "O2-002",
        "name": "Stanley Hospital LMO Vaporizer Yard (15 KL Tank)",
        "type": "Cryogenic Oxygen Plant",
        "plinth_cm": 65.0,
        "lat": 13.1070,
        "lon": 80.2870,
        "facility": "Government Stanley Medical College Hospital",
        "critical_capacity_kl": 15.0
    },
    {
        "id": "O2-003",
        "name": "Kilpauk Medical College (KMC) Oxygen Farm (10 KL Tank)",
        "type": "Cryogenic Oxygen Plant",
        "plinth_cm": 60.0,
        "lat": 13.0784,
        "lon": 80.2425,
        "facility": "Govt Kilpauk Medical College Hospital",
        "critical_capacity_kl": 10.0
    },
    {
        "id": "O2-004",
        "name": "Apollo Hospitals Greams Road Medical Gas Depot (13 KL)",
        "type": "Cryogenic Oxygen Plant",
        "plinth_cm": 70.0,
        "lat": 13.0604,
        "lon": 80.2514,
        "facility": "Apollo Hospitals Main Facility",
        "critical_capacity_kl": 13.0
    },
    {
        "id": "O2-005",
        "name": "MIOT International Flood Wall Cryogenic Depot (10 KL)",
        "type": "Cryogenic Oxygen Plant",
        "plinth_cm": 50.0,
        "lat": 13.0185,
        "lon": 80.1856,
        "facility": "MIOT International Manapakkam",
        "critical_capacity_kl": 10.0
    },
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
    """Monitors flood hazards at vital energy substations and medical oxygen depots."""

    def __init__(self, graph: Optional[StreetDrainageGraph] = None):
        self.graph = graph or StreetDrainageGraph()
        self.substations = CHENNAI_SUBSTATIONS
        self.oxygen_depots = MEDICAL_OXYGEN_DEPOTS
        self.facilities = CRITICAL_FACILITIES

        # Map each substation to its nearest road node
        self._substation_nodes = [
            self.graph.kdtree.query([ss["lon"], ss["lat"]])[1]
            for ss in self.substations
        ]

        # Map each oxygen depot to its nearest road node
        self._oxygen_nodes = [
            self.graph.kdtree.query([depot["lon"], depot["lat"]])[1]
            for depot in self.oxygen_depots
        ]

    def compute_plinth_vulnerability(
        self,
        z_flood_cm: float,
        z_plinth_cm: float,
        margin_threshold_cm: float = 15.0
    ) -> Dict[str, Any]:
        """
        Calculates Plinth Vulnerability Index (PVI) and early warning action state.

        Mathematical Formulation:
          Delta z = z_plinth - z_flood
          PVI = z_flood / z_plinth
          Trigger: z_flood > z_plinth - 15 cm  <=>  Delta z < 15 cm

        Alert States:
          - NORMAL: Delta z >= 25 cm (PVI <= 0.50)
          - WARNING: 15 cm < Delta z < 25 cm (Deploy dewatering pumps)
          - CRITICAL_TRIP_RISK: 0 cm < Delta z <= 15 cm (Automated SCADA de-energization warning)
          - BREAKER_TRIPPED_EMERGENCY: Delta z <= 0 cm (Water reached plinth, arc flash danger)
        """
        margin_cm = z_plinth_cm - z_flood_cm
        pvi = round(z_flood_cm / max(1.0, z_plinth_cm), 3)

        if margin_cm <= 0.0:
            status = "BREAKER_TRIPPED_EMERGENCY"
            action_code = "TRIP_NOW"
            alert_text = (
                f"SUBMERGED PLINTH (Depth: {z_flood_cm:.1f} cm / Plinth: {z_plinth_cm:.0f} cm). "
                f"Negative margin ({margin_cm:.1f} cm). Breakers tripped to prevent catastrophic explosion."
            )
        elif margin_cm <= margin_threshold_cm:
            status = "CRITICAL_TRIP_RISK"
            action_code = "PREDICTIVE_TRIP_WARNING"
            alert_text = (
                f"PREDICTIVE DE-ENERGIZATION TRIGGERED! Flood depth {z_flood_cm:.1f} cm exceeds plinth margin "
                f"(Clearance: {margin_cm:.1f} cm <= {margin_threshold_cm:.0f} cm). Pre-emptive trip warning dispatched to SLDC."
            )
        elif margin_cm < 25.0:
            status = "WARNING"
            action_code = "DEPLOY_PUMPS"
            alert_text = (
                f"Elevated flood water ({z_flood_cm:.1f} cm). Margin: {margin_cm:.1f} cm. "
                f"Deploy high-capacity mobile dewatering pumps."
            )
        else:
            status = "NORMAL"
            action_code = "MONITOR"
            alert_text = f"Secure ({z_flood_cm:.1f} cm). Plinth clearance margin: {margin_cm:.1f} cm."

        return {
            "water_depth_cm": round(z_flood_cm, 1),
            "plinth_cm": z_plinth_cm,
            "margin_cm": round(margin_cm, 1),
            "pvi": pvi,
            "status": status,
            "action_code": action_code,
            "alert_text": alert_text,
            "trip_warning_active": margin_cm <= margin_threshold_cm
        }

    def evaluate_substation_risks(self, depths_cm: np.ndarray) -> Dict[str, Any]:
        """
        Assesses electrical substation plinth vulnerability and circuit breaker trip risks.
        """
        results = []
        critical_count = 0
        warning_count = 0
        normal_count = 0

        for i, ss in enumerate(self.substations):
            node_idx = self._substation_nodes[i]
            water_depth = float(depths_cm[node_idx])
            plinth = ss["plinth_cm"]

            vuln = self.compute_plinth_vulnerability(water_depth, plinth, margin_threshold_cm=15.0)

            if vuln["status"] in ("CRITICAL_TRIP_RISK", "BREAKER_TRIPPED_EMERGENCY"):
                critical_count += 1
            elif vuln["status"] == "WARNING":
                warning_count += 1
            else:
                normal_count += 1

            results.append({
                "id": ss["id"],
                "name": ss["name"],
                "voltage_kv": ss["voltage_kv"],
                "zone": ss.get("zone", "GCC"),
                "plinth_cm": plinth,
                "water_depth_cm": vuln["water_depth_cm"],
                "plinth_clearance_cm": vuln["margin_cm"],
                "pvi_ratio": vuln["pvi"],
                "status": vuln["status"],
                "action_alert": vuln["alert_text"],
                "trip_warning_active": vuln["trip_warning_active"],
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

    def evaluate_medical_oxygen_depots(self, depths_cm: np.ndarray) -> Dict[str, Any]:
        """
        Assesses flood vulnerability for hospital liquid medical oxygen (LMO) tanks & vaporizer skids.
        """
        results = []
        critical_count = 0
        warning_count = 0
        normal_count = 0

        for i, depot in enumerate(self.oxygen_depots):
            node_idx = self._oxygen_nodes[i]
            water_depth = float(depths_cm[node_idx])
            plinth = depot["plinth_cm"]

            vuln = self.compute_plinth_vulnerability(water_depth, plinth, margin_threshold_cm=15.0)

            if vuln["status"] in ("CRITICAL_TRIP_RISK", "BREAKER_TRIPPED_EMERGENCY"):
                critical_count += 1
                depot_action = (
                    f"CRITICAL: Flood depth {water_depth:.1f} cm threatens cryogenic vaporizer. "
                    f"Switch hospital ICU to emergency secondary oxygen cylinder manifold!"
                )
            elif vuln["status"] == "WARNING":
                warning_count += 1
                depot_action = f"WARNING: Water {water_depth:.1f} cm approaching O2 pad. Deploy sandbag bunds."
            else:
                normal_count += 1
                depot_action = f"SECURE: Oxygen pad clear. Margin {vuln['margin_cm']:.1f} cm."

            results.append({
                "id": depot["id"],
                "name": depot["name"],
                "facility": depot["facility"],
                "capacity_kl": depot["critical_capacity_kl"],
                "plinth_cm": plinth,
                "water_depth_cm": vuln["water_depth_cm"],
                "margin_cm": vuln["margin_cm"],
                "pvi_ratio": vuln["pvi"],
                "status": vuln["status"],
                "action_alert": depot_action,
                "trip_warning_active": vuln["trip_warning_active"],
                "lat": depot["lat"],
                "lon": depot["lon"]
            })

        return {
            "total_depots": len(self.oxygen_depots),
            "critical_count": critical_count,
            "warning_count": warning_count,
            "normal_count": normal_count,
            "oxygen_depots": results
        }

