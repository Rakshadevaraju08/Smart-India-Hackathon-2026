"""Unit & Precision Benchmark Tests for Layer 4: Emergency Routing & Critical Asset Safeguarding.

Tests:
  1. Vehicle Clearance Matrix (Ambulance 30cm, NDRF Truck 60cm, Civilian Car 18cm, Two-Wheeler 10cm)
  2. Hydrodynamic Traversal Cost Function C(e, t) with Quadratic Speed Degradation & Momentum Cutoff
  3. Plinth Vulnerability Index (PVI) & 15cm Safety Margin Automated De-Energization Triggers
  4. Medical Oxygen Depots & Cryogenic Vaporizer Safeguarding
  5. A* Heuristic & Water Hazard Potential Field (WHPF) Green Corridors
  6. Routing Algorithm Benchmarks & Sub-50ms Latency Verification
"""

import math
import unittest
import numpy as np

from ai_service.layer4.risk_cost_evaluator import (
    RiskCostEvaluator,
    VEHICLE_PROFILES,
    VehicleProfile
)
from ai_service.layer4.critical_assets_monitor import (
    CriticalAssetsMonitor,
    CHENNAI_SUBSTATIONS,
    MEDICAL_OXYGEN_DEPOTS
)
from ai_service.layer4.routing_engine import DynamicRoutingEngine, haversine_m
from ai_service.layer4.pipeline import Layer4Pipeline, Layer4Result


class TestLayer4Precision(unittest.TestCase):
    """Rigorous scientific test suite for Layer 4 mathematical formulations."""

    def test_01_vehicle_clearance_matrix_specifications(self):
        """Verify strict vehicle clearance limits and hydrodynamic stability parameters."""
        expected_specs = {
            "ambulance": {"d_c": 30.0, "d_safe": 10.0, "dv_crit": 0.45, "speed": 45.0},
            "rescue_truck": {"d_c": 60.0, "d_safe": 25.0, "dv_crit": 1.05, "speed": 35.0},
            "civilian_car": {"d_c": 18.0, "d_safe": 8.0, "dv_crit": 0.30, "speed": 30.0},
            "two_wheeler": {"d_c": 10.0, "d_safe": 3.0, "dv_crit": 0.15, "speed": 20.0},
        }

        for v_key, specs in expected_specs.items():
            self.assertIn(v_key, VEHICLE_PROFILES)
            p = VEHICLE_PROFILES[v_key]
            self.assertEqual(p.d_critical_cm, specs["d_c"], f"Failed d_c for {v_key}")
            self.assertEqual(p.d_safe_cm, specs["d_safe"], f"Failed d_safe for {v_key}")
            self.assertEqual(p.critical_dv_m2_s, specs["dv_crit"], f"Failed dv_crit for {v_key}")
            self.assertEqual(p.base_speed_kmh, specs["speed"], f"Failed speed for {v_key}")

    def test_02_hydrodynamic_traversal_cost_function(self):
        """Verify C(e, t) cost function properties: dry, safe, moderate, and catastrophic cutoff."""
        evaluator = RiskCostEvaluator("ambulance")
        length_m = 100.0
        v_base = (45.0 * 1000.0) / 3600.0  # 12.5 m/s
        t_dry_expected = length_m / v_base   # 8.0 seconds

        # 1. Dry conditions (depth = 0)
        c_dry = evaluator.compute_edge_traversal_cost(length_m, depth_cm=0.0, velocity_mps=0.0)
        self.assertAlmostEqual(c_dry, t_dry_expected, places=3)

        # 2. Safe wading (depth = 5 cm <= 10 cm d_safe)
        # V_eff = 12.5 * (1 - (5/30)^2) = 12.5 * (1 - 1/36) = 12.1527 m/s
        c_safe = evaluator.compute_edge_traversal_cost(length_m, depth_cm=5.0, velocity_mps=0.0)
        self.assertGreater(c_safe, t_dry_expected)
        self.assertLess(c_safe, t_dry_expected * 1.05)  # Less than 5% penalty

        # 3. Moderate wading with risk penalty (depth = 20 cm > 10 cm d_safe)
        # V_eff = 12.5 * (1 - (20/30)^2) = 12.5 * (1 - 4/9) = 6.944 m/s
        c_mod = evaluator.compute_edge_traversal_cost(length_m, depth_cm=20.0, velocity_mps=0.0)
        self.assertGreater(c_mod, 14.0)  # Significantly higher due to quadratic drag + non-linear risk penalty

        # 4. Catastrophic cutoff depth (depth = 30 cm == d_c)
        c_cutoff = evaluator.compute_edge_traversal_cost(length_m, depth_cm=30.0, velocity_mps=0.0)
        self.assertTrue(math.isinf(c_cutoff), "Cost must be infinite when depth reaches d_c")

        c_over = evaluator.compute_edge_traversal_cost(length_m, depth_cm=35.0, velocity_mps=0.0)
        self.assertTrue(math.isinf(c_over), "Cost must be infinite when depth exceeds d_c")

        # 5. Hydrodynamic momentum hazard cutoff (d * v >= 0.45 m2/s)
        # depth = 20 cm (0.2 m), velocity = 2.5 m/s -> dv = 0.50 m2/s > 0.45
        c_momentum_cutoff = evaluator.compute_edge_traversal_cost(length_m, depth_cm=20.0, velocity_mps=2.5)
        self.assertTrue(math.isinf(c_momentum_cutoff), "Cost must be infinite when momentum hazard exceeds limit")

    def test_03_plinth_vulnerability_index_and_15cm_margin_rule(self):
        """Verify Plinth Vulnerability Index (PVI) and the 15cm margin automated de-energization rule."""
        monitor = CriticalAssetsMonitor()

        # Test Substation: Velachery Substation (Plinth = 40.0 cm)
        z_plinth = 40.0

        # Scenario A: Normal (z_flood = 10 cm, margin = 30 cm >= 25 cm)
        vuln_a = monitor.compute_plinth_vulnerability(z_flood_cm=10.0, z_plinth_cm=z_plinth)
        self.assertEqual(vuln_a["status"], "NORMAL")
        self.assertEqual(vuln_a["action_code"], "MONITOR")
        self.assertFalse(vuln_a["trip_warning_active"])
        self.assertEqual(vuln_a["margin_cm"], 30.0)
        self.assertEqual(vuln_a["pvi"], 0.25)

        # Scenario B: Warning / Dewatering (z_flood = 20 cm, margin = 20 cm in (15, 25))
        vuln_b = monitor.compute_plinth_vulnerability(z_flood_cm=20.0, z_plinth_cm=z_plinth)
        self.assertEqual(vuln_b["status"], "WARNING")
        self.assertEqual(vuln_b["action_code"], "DEPLOY_PUMPS")
        self.assertFalse(vuln_b["trip_warning_active"])
        self.assertEqual(vuln_b["margin_cm"], 20.0)

        # Scenario C: Predictive De-energization Triggered (z_flood = 26 cm, margin = 14 cm <= 15 cm)
        # Exactly: z_flood > z_plinth - 15 cm (26 > 40 - 15 = 25)
        vuln_c = monitor.compute_plinth_vulnerability(z_flood_cm=26.0, z_plinth_cm=z_plinth)
        self.assertEqual(vuln_c["status"], "CRITICAL_TRIP_RISK")
        self.assertEqual(vuln_c["action_code"], "PREDICTIVE_TRIP_WARNING")
        self.assertTrue(vuln_c["trip_warning_active"])
        self.assertEqual(vuln_c["margin_cm"], 14.0)

        # Scenario D: Submerged / Breaker Tripped Emergency (z_flood = 42 cm, margin = -2 cm <= 0)
        vuln_d = monitor.compute_plinth_vulnerability(z_flood_cm=42.0, z_plinth_cm=z_plinth)
        self.assertEqual(vuln_d["status"], "BREAKER_TRIPPED_EMERGENCY")
        self.assertEqual(vuln_d["action_code"], "TRIP_NOW")
        self.assertTrue(vuln_d["trip_warning_active"])
        self.assertEqual(vuln_d["margin_cm"], -2.0)

    def test_04_critical_assets_catalog_coverage(self):
        """Verify monitoring coverage across TANGEDCO 230kV/110kV substations and medical oxygen depots."""
        monitor = CriticalAssetsMonitor()
        self.assertEqual(len(monitor.substations), 20)
        self.assertEqual(len(monitor.oxygen_depots), 5)

        sub_names = [s["name"] for s in monitor.substations]
        self.assertTrue(any("Koyambedu" in n for n in sub_names))
        self.assertTrue(any("Mylapore" in n for n in sub_names))
        self.assertTrue(any("Velachery" in n for n in sub_names))
        self.assertTrue(any("T. Nagar" in n for n in sub_names))
        self.assertTrue(any("Guindy" in n for n in sub_names))

        o2_names = [d["name"] for d in monitor.oxygen_depots]
        self.assertTrue(any("RGGGH" in n for n in o2_names))
        self.assertTrue(any("Stanley" in n for n in o2_names))
        self.assertTrue(any("Kilpauk" in n for n in o2_names))
        self.assertTrue(any("Apollo" in n for n in o2_names))
        self.assertTrue(any("MIOT" in n for n in o2_names))

    def test_05_water_hazard_potential_field_and_astar(self):
        """Verify Water Hazard Potential Field generation and A* search space reduction."""
        engine = DynamicRoutingEngine()
        n_nodes = engine.n_nodes
        depths = np.zeros(n_nodes, dtype=np.float32)

        # Place artificial flood pool near central corridor (node 100 to 120, 25 cm)
        depths[100:130] = 25.0

        whpf = engine.compute_water_hazard_potential_field(depths, d_critical_cm=30.0)
        self.assertEqual(len(whpf), n_nodes)
        # Inundated nodes must have strong positive potential
        self.assertGreater(whpf[110], 0.0)

        # Test A* routing
        origin_lat, origin_lon = 13.0418, 80.2341
        dest_lat, dest_lon = 13.0604, 80.2514
        route = engine.solve_route(
            origin_lat, origin_lon, dest_lat, dest_lon,
            depths_cm=depths, vehicle_type="ambulance",
            use_hazard_potential=True
        )

        self.assertIn("safe_route", route)
        self.assertTrue(route["safe_route"]["is_safe"])
        self.assertEqual(route["safe_route"]["impassable_segments"], 0)
        self.assertLess(route["latency_ms"], 50.0, "A* solver must run in < 50 ms")

    def test_06_routing_algorithm_benchmark_suite(self):
        """Verify 4-algorithm benchmark comparison suite execution."""
        engine = DynamicRoutingEngine()
        depths = np.full(engine.n_nodes, 8.0, dtype=np.float32)

        benchmark = engine.benchmark_routing_algorithms(
            origin_lat=13.0418, origin_lon=80.2341,
            dest_lat=13.0604, dest_lon=80.2514,
            depths_cm=depths, vehicle_type="ambulance"
        )

        self.assertIn("benchmark_results", benchmark)
        results = benchmark["benchmark_results"]
        self.assertEqual(len(results), 4)

        algo_names = [r["algorithm"] for r in results]
        self.assertIn("Dijkstra Naive Shortest Distance", algo_names)
        self.assertIn("Dijkstra Binary Cutoff", algo_names)
        self.assertIn("Standard A* Hydrodynamic", algo_names)
        self.assertIn("Kairos Green Corridor A* (A* + WHPF)", algo_names)

        for res in results:
            self.assertLess(res["latency_ms"], 100.0)
            self.assertGreater(res["distance_km"], 0.0)


if __name__ == "__main__":
    unittest.main()
