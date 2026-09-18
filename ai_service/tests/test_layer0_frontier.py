"""Automated Test Suite for Layer 0 Frontier AI & Precision Modules.
File: tests/test_layer0_frontier.py

Verifies:
  1. CML Ingestor (ITU-R P.838-3 Power Law Inversion & Chennai Cellular Mesh).
  2. Stochastic Cascade Nowcaster (1-Minute Temporal Sub-Stepping & Probabilistic P10/P50/P90).
  3. Topographic Super-Resolution (1 km -> 100m Downscaling with Strict Mass Conservation).
  4. Multi-Sensor Optimal Interpolation & 2D Spatial Kalman Fusion.
"""

import sys
import unittest
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.layer0.cml_ingestor import CMLLink, CMLPrecipitationEngine, CHENNAI_CML_TOPOLOGY
from src.layer0.stochastic_nowcaster import StochasticCascadeNowcaster, StochasticForecastResult
from src.layer0.super_resolution import TopographicSuperResolutionEngine, SuperResolutionResult
from src.layer0.fusion import MultiSensorKalmanFusion


class TestLayer0FrontierTools(unittest.TestCase):
    """Rigorous test suite for Layer 0 frontier high-precision tools."""

    def setUp(self):
        self.cml_engine = CMLPrecipitationEngine(wet_antenna_attenuation_db=1.8)
        self.stochastic_engine = StochasticCascadeNowcaster(
            n_ensemble_members=10,
            stochastic_noise_std=0.15,
            extreme_threshold_mm_hr=50.0
        )
        self.sr_engine = TopographicSuperResolutionEngine(scale_factor=10)
        self.fusion_engine = MultiSensorKalmanFusion(shape=(20, 20))

        # Synthetic 1km radar grid for testing (20 x 20)
        self.test_grid_1km = np.zeros((20, 20), dtype=np.float32)
        for r in range(20):
            for c in range(20):
                dist_sq = (r - 10)**2 + (c - 10)**2
                self.test_grid_1km[r, c] = max(0.0, float(75.0 * np.exp(-dist_sq / 16.0)))

    def test_cml_power_law_inversion(self):
        """Test ITU-R P.838-3 power law inversion on simulated link."""
        link = CMLLink(
            link_id='TEST-01',
            tx_lat=13.0827, tx_lon=80.2755,
            rx_lat=13.0674, rx_lon=80.2443,
            frequency_ghz=18.0, polarization='H',
            tsl_dbm=15.0, rsl_dbm=-55.0, baseline_dbm=-45.0
        )
        rain_rate = self.cml_engine.invert_link(link)
        self.assertGreater(rain_rate, 10.0, "Expected significant rain rate for 8.2 dB attenuation")
        self.assertLess(rain_rate, 150.0, "Rain rate should remain within realistic tropical bounds")

    def test_cml_mesh_harvesting(self):
        """Test harvesting all 15 simulated Chennai telecom links."""
        telemetry = self.cml_engine.harvest_mesh_telemetry(simulated_storm_intensity=80.0)
        self.assertEqual(len(telemetry), len(CHENNAI_CML_TOPOLOGY))
        for link_id, data in telemetry.items():
            self.assertEqual(data['status'], 'ACTIVE')
            self.assertIn('retrieved_rain_rate_mm_hr', data)
            self.assertGreaterEqual(data['retrieved_rain_rate_mm_hr'], 0.0)
            self.assertIn(data['zone'], ['Central', 'South', 'North', 'West'])

    def test_stochastic_nowcaster_1min_substepping(self):
        """Test 1-minute continuous interpolation from keyframe horizons."""
        keyframes = {
            15: self.test_grid_1km * 0.9,
            30: self.test_grid_1km * 0.8,
            60: self.test_grid_1km * 0.6,
            90: self.test_grid_1km * 0.4,
            120: self.test_grid_1km * 0.2,
            180: self.test_grid_1km * 0.05
        }
        sub_stepped = self.stochastic_engine.sub_step_1min(keyframes, max_horizon_min=60)
        self.assertEqual(len(sub_stepped), 60)
        for m in range(1, 61):
            self.assertIn(m, sub_stepped)
            grid_m = sub_stepped[m]
            self.assertEqual(grid_m.shape, (20, 20))
            self.assertFalse(np.isnan(grid_m).any())
            self.assertTrue(np.all(grid_m >= 0.0))

    def test_stochastic_ensemble_spread(self):
        """Test probabilistic ensemble quantiles P10 <= P50 <= P90."""
        keyframes = {
            15: self.test_grid_1km,
            30: self.test_grid_1km * 0.85
        }
        sub_stepped = self.stochastic_engine.sub_step_1min(keyframes, max_horizon_min=30)
        result = self.stochastic_engine.run_stochastic_ensemble(sub_stepped, seed=42)

        self.assertIsInstance(result, StochasticForecastResult)
        self.assertEqual(len(result.lead_minutes), 30)
        self.assertTrue(np.all(result.p10_low <= result.p50_median + 1e-4))
        self.assertTrue(np.all(result.p50_median <= result.p90_high + 1e-4))
        self.assertTrue(np.all(result.poe_extreme >= 0.0))
        self.assertTrue(np.all(result.poe_extreme <= 1.0))
        self.assertLess(result.execution_time_ms, 500.0, "Ensemble execution must run in < 500 ms")

    def test_super_resolution_downscaling_10x(self):
        """Test 1 km -> 100m downscaling and strict mass conservation."""
        res = self.sr_engine.downscale(self.test_grid_1km, apply_mass_conservation=True)
        self.assertIsInstance(res, SuperResolutionResult)
        self.assertEqual(res.shape_100m, (200, 200))
        self.assertLessEqual(res.mass_conservation_error_pct, 0.001,
                             f"Mass conservation error {res.mass_conservation_error_pct}% exceeds 0.001% tolerance")
        self.assertTrue(np.all(res.grid_100m >= 0.0))

    def test_multisensor_kalman_fusion(self):
        """Test 2D Optimal Interpolation Kalman fusion of radar, gauges, and CML links."""
        gauges = {
            'G1': {'latitude': 13.0674, 'longitude': 80.2443, 'rainfall_rate_mm_hr': 60.0},
            'G2': {'latitude': 12.9900, 'longitude': 80.1693, 'rainfall_rate_mm_hr': 45.0}
        }
        cml_data = {
            'C1': {'midpoint_lat': 13.0418, 'midpoint_lon': 80.2335, 'retrieved_rain_rate_mm_hr': 55.0}
        }
        fused_grid, diag = self.fusion_engine.fuse(self.test_grid_1km, gauges, cml_data)
        self.assertEqual(fused_grid.shape, (20, 20))
        self.assertFalse(np.isnan(fused_grid).any())
        self.assertTrue(np.all(fused_grid >= 0.0))
        self.assertEqual(diag['status'], 'converged')
        self.assertEqual(diag['observation_count'], 3)


if __name__ == '__main__':
    unittest.main(verbosity=2)
