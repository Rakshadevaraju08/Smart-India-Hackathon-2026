#!/usr/bin/env python3
"""Exhaustive Robustness Audit and Adversarial Stress Test Suite for Layer 0 (ai_service/layer0).

Target: Greater Chennai Corporation (7,894 Road Segments) — Problem Statement #26085.

Tests:
1. Complete IMD Radar outage / Blackout (Network disconnection, HTTP 500, corrupt bytes, fallback)
2. Extreme Cloudburst (150 mm/hr up to 300 mm/hr, Cyclone Michaung / 2015 deluge stress)
3. Partial and Complete AWS gauge outage (0 gauges responding, None/NaN/corrupt values, single station)
4. Dry condition / zero rain (Guarantees zero ghost rain across all modules)
5. Corrupted, NaN, Inf, and negative radar reflectivity inputs
6. Strict mass conservation on Chennai's 7,894 streets within 0.1% tolerance
7. Opportunistic CML microwave link inversion under extreme fading, link drops, and dry baselines
8. Physics-informed 100m Super-Resolution downscaling mass conservation and numerical stability
9. Multi-Sensor Optimal Interpolation & Kalman Fusion under sparse, noisy, and missing observations
"""

import os
import sys
import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_service.layer0 import (
    IMDRadarIngestion,
    IMDAWSIngestion,
    HistoricalArchiveLoader,
    StormMotionNowcaster,
    StreetDisaggregator,
    GaugeRadarCalibrator,
    Layer0Pipeline,
    dbz_to_rain_rate,
    rain_rate_to_dbz,
    DEFAULT_CHENNAI_BOUNDS,
    DEFAULT_GRID_SHAPE,
    DEFAULT_HORIZONS,
    CHENNAI_AWS_STATIONS,
    RadarSweep,
)
from ai_service.layer0.cml_ingestor import CMLLink, CMLPrecipitationEngine, CHENNAI_CML_TOPOLOGY
from ai_service.layer0.stochastic_nowcaster import StochasticCascadeNowcaster, StochasticForecastResult
from ai_service.layer0.super_resolution import TopographicSuperResolutionEngine, SuperResolutionResult
from ai_service.layer0.fusion import MultiSensorKalmanFusion

ROADS_DATASET_PATH = PROJECT_ROOT / "Google_Drive_Datasets" / "chennai_unified_flood_master_dataset.csv"


class TestLayer0AdversarialStress(unittest.TestCase):
    """Exhaustive adversarial test cases for Layer 0."""

    @classmethod
    def setUpClass(cls):
        cls.disaggregator = StreetDisaggregator(str(ROADS_DATASET_PATH))
        cls.calibrator = GaugeRadarCalibrator()
        cls.nowcaster = StormMotionNowcaster()
        cls.stochastic_nowcaster = StochasticCascadeNowcaster(n_ensemble_members=10)
        cls.cml_engine = CMLPrecipitationEngine()
        cls.sr_engine = TopographicSuperResolutionEngine(scale_factor=10)
        cls.fusion_engine = MultiSensorKalmanFusion(shape=DEFAULT_GRID_SHAPE)
        cls.archive_loader = HistoricalArchiveLoader()

    # =========================================================================
    # 1. IMD RADAR OUTAGE & BLACKOUT RESILIENCE
    # =========================================================================

    def test_radar_blackout_network_disconnection(self):
        """Test complete network blackout when polling IMD Mausam server."""
        ingestor = IMDRadarIngestion(request_timeout=0.1)
        with patch('requests.get', side_effect=ConnectionError("IMD Mausam unreachable / Network down")):
            gif = ingestor.fetch_live_gif(product='sri')
            self.assertIsNone(gif, "Should return None on network connection error")

            # High-level fetch_latest_radar must fall back cleanly without raising exception
            sweep = ingestor.fetch_latest_radar(product='sri', fallback_scenario='michaung')
            self.assertIsInstance(sweep, RadarSweep)
            self.assertEqual(sweep.grid.shape, DEFAULT_GRID_SHAPE)
            self.assertGreater(float(np.max(sweep.grid)), 50.0, "Archive fallback should yield valid storm data")
            self.assertEqual(len(sweep.gauges), 4)

    def test_radar_blackout_corrupted_truncated_bytes(self):
        """Test receiving corrupted or truncated image bytes from radar gateway."""
        ingestor = IMDRadarIngestion(request_timeout=0.1)
        corrupt_bytes = b"GIF89a\x00\x01\x00\x00corrupted_payload_garbage_data"
        with patch.object(ingestor, 'fetch_live_gif', return_value=corrupt_bytes):
            sweep = ingestor.fetch_latest_radar(fallback_scenario='2015_flood')
            self.assertIsInstance(sweep, RadarSweep)
            self.assertEqual(sweep.grid.shape, DEFAULT_GRID_SHAPE)
            self.assertFalse(np.isnan(sweep.grid).any())

    def test_radar_blackout_maintenance_photo_rejection(self):
        """Test rejection of non-radar maintenance photos or 1x1 error pixels."""
        ingestor = IMDRadarIngestion()
        # 1x1 pixel image
        tiny_img = Image.new('RGB', (1, 1), color=(255, 0, 0))
        self.assertFalse(ingestor.is_valid_radar_sweep(tiny_img))

        # Photographic test pattern (uniform grey 800x800)
        grey_img = Image.new('RGB', (800, 800), color=(128, 128, 128))
        self.assertFalse(ingestor.is_valid_radar_sweep(grey_img))

    # =========================================================================
    # 2. EXTREME CLOUDBURST (150 mm/hr - 300 mm/hr)
    # =========================================================================

    def test_extreme_cloudburst_150mmh_pipeline_stability(self):
        """Simulate severe 150 mm/hr cloudburst (Cyclone Michaung / 2015 deluge)."""
        H, W = DEFAULT_GRID_SHAPE
        y_idx, x_idx = np.mgrid[0:H, 0:W]
        dist_sq = (x_idx - W // 2)**2 + (y_idx - H // 2)**2
        cloudburst_grid = (150.0 * np.exp(-dist_sq / 36.0)).astype(np.float32)

        # 1. Calibration under extreme cloudburst
        aws_worker = IMDAWSIngestion()
        gauges = aws_worker.synthesize_gauges_from_radar(cloudburst_grid, dsd_gain=1.45)
        calibrated_radar, gr_ratio, diag = self.calibrator.calibrate(cloudburst_grid, gauges, method='brandes')
        self.assertFalse(np.isnan(calibrated_radar).any())
        self.assertTrue(np.all(calibrated_radar >= 0.0))
        self.assertGreaterEqual(float(np.max(calibrated_radar)), 140.0)

        # 2. Deterministic nowcasting
        sweeps = [cloudburst_grid * 0.85, cloudburst_grid * 0.92, calibrated_radar]
        nowcasts = self.nowcaster.nowcast(sweeps, horizons_min=[15, 30, 60, 90, 120, 180])
        for h in [15, 30, 60, 90, 120, 180]:
            self.assertIn(h, nowcasts)
            self.assertFalse(np.isnan(nowcasts[h]).any())
            self.assertTrue(np.all(nowcasts[h] >= 0.0))

        # 3. Disaggregation onto 7,894 streets with strict mass conservation
        df_streets = self.disaggregator.disaggregate(nowcasts)
        self.assertEqual(len(df_streets), 7894)
        vol_errors = self.disaggregator.verify_mass_conservation(df_streets, nowcasts)
        for h, err_pct in vol_errors.items():
            self.assertLessEqual(err_pct, 0.001, f"Horizon {h}m volume error {err_pct}% exceeds 0.001%")

        # 4. Stochastic nowcasting PoE for extreme cloudburst
        one_min = self.stochastic_nowcaster.sub_step_1min(nowcasts, max_horizon_min=30)
        stoch_res = self.stochastic_nowcaster.run_stochastic_ensemble(one_min, seed=42)
        self.assertTrue(np.all(stoch_res.p90_high >= stoch_res.p50_median - 1e-4))
        self.assertGreater(float(np.max(stoch_res.poe_extreme)), 0.50,
                           "PoE for 50 mm/hr threshold should detect the 150 mm/hr cloudburst core")

    # =========================================================================
    # 3. AWS GAUGE OUTAGE (0 GAUGES, NULL/CORRUPT TELEMETRY)
    # =========================================================================

    def test_complete_aws_gauge_blackout_zero_gauges(self):
        """Test system behavior when 0 AWS stations respond (complete gauge outage)."""
        test_radar = np.full(DEFAULT_GRID_SHAPE, 45.0, dtype=np.float32)
        calibrated, gr_ratio, diag = self.calibrator.calibrate(test_radar, gauges={}, method='brandes')
        self.assertEqual(gr_ratio, 1.0, "Should default to 1.0 gain on total gauge outage")
        np.testing.assert_allclose(calibrated, test_radar, atol=1e-5)

        # Test KED with zero gauges
        calibrated_ked, gr_ked, diag_ked = self.calibrator.calibrate(test_radar, gauges={}, method='ked')
        self.assertEqual(gr_ked, 1.0)
        np.testing.assert_allclose(calibrated_ked, test_radar, atol=1e-5)

    def test_corrupted_gauge_telemetry_null_and_nan_values(self):
        """Test telemetry containing None, NaN, Inf, and negative values."""
        test_radar = np.full(DEFAULT_GRID_SHAPE, 30.0, dtype=np.float32)
        corrupt_gauges = {
            '43278': {'lat': 13.0674, 'lon': 80.2443, 'rainfall_rate_mm_hr': None},           # None value
            '43279': {'lat': 12.9900, 'lon': 80.1693, 'rainfall_rate_mm_hr': float('nan')},    # NaN value
            'AWS-AU': {'lat': 13.0110, 'lon': 80.2355, 'rainfall_rate_mm_hr': float('inf')},   # Inf value
            'AWS-SH': {'lat': 12.9010, 'lon': 80.2279, 'rainfall_rate_mm_hr': -15.0},          # Negative value
            'CORRUPT': {'lat': None, 'lon': None, 'rainfall_rate_mm_hr': 50.0},                 # Missing coords
        }
        calibrated, gr_ratio, diag = self.calibrator.calibrate(test_radar, corrupt_gauges, method='brandes')
        self.assertFalse(np.isnan(calibrated).any())
        self.assertFalse(np.isinf(calibrated).any())
        self.assertTrue(np.all(calibrated >= 0.0))

        # Kalman fusion with corrupted gauge dictionary
        fused, f_diag = self.fusion_engine.fuse(test_radar, corrupt_gauges)
        self.assertFalse(np.isnan(fused).any())
        self.assertTrue(np.all(fused >= 0.0))

    def test_single_surviving_gauge(self):
        """Test when 3 of 4 gauges are destroyed, and only 1 remains operational."""
        test_radar = np.full(DEFAULT_GRID_SHAPE, 20.0, dtype=np.float32)
        single_gauge = {
            '43278': {'lat': 13.0674, 'lon': 80.2443, 'rainfall_rate_mm_hr': 30.0, 'name': 'Nungambakkam'}
        }
        calibrated, gr_ratio, diag = self.calibrator.calibrate(test_radar, single_gauge, method='brandes')
        self.assertGreater(gr_ratio, 1.0)
        self.assertFalse(np.isnan(calibrated).any())
        self.assertTrue(np.all(calibrated >= 0.0))

    # =========================================================================
    # 4. DRY CONDITION / ZERO RAIN (ZERO GHOST RAIN GUARANTEE)
    # =========================================================================

    def test_zero_rain_dry_grid_introduces_zero_ghost_rain(self):
        """Verify that absolutely zero ghost rain is generated during dry weather."""
        zero_grid = np.zeros(DEFAULT_GRID_SHAPE, dtype=np.float32)

        # 1. Calibration on dry grid
        calibrated, gr_ratio, diag = self.calibrator.calibrate(zero_grid, gauges={}, method='brandes')
        self.assertEqual(float(np.max(calibrated)), 0.0, "Calibrator must not create ghost rain on dry grid")

        # 2. Optical flow and advection
        sweeps = [zero_grid, zero_grid, zero_grid]
        nowcasts = self.nowcaster.nowcast(sweeps)
        for h, forecast in nowcasts.items():
            self.assertEqual(float(np.max(forecast)), 0.0, f"Nowcast horizon {h} introduced ghost rain")

        # 3. Disaggregation onto 7,894 streets
        df_streets = self.disaggregator.disaggregate(nowcasts)
        for col in [c for c in df_streets.columns if c.startswith('I_') or c.startswith('d_')]:
            self.assertEqual(float(df_streets[col].max()), 0.0, f"Disaggregation column {col} has ghost rain")

        # 4. Stochastic 1-minute ensemble
        one_min = self.stochastic_nowcaster.sub_step_1min(nowcasts, max_horizon_min=30)
        stoch_res = self.stochastic_nowcaster.run_stochastic_ensemble(one_min, seed=42)
        self.assertEqual(float(np.max(stoch_res.p90_high)), 0.0, "Stochastic P90 introduced ghost rain")
        self.assertEqual(float(np.max(stoch_res.poe_extreme)), 0.0, "Stochastic PoE must be 0.0 everywhere")

        # 5. Topographic Super-Resolution (100m)
        sr_res = self.sr_engine.downscale(zero_grid)
        self.assertEqual(float(np.max(sr_res.grid_100m)), 0.0, "Super-resolution introduced ghost rain")

        # 6. Multi-Sensor Kalman Fusion
        fused, f_diag = self.fusion_engine.fuse(zero_grid, gauges_data={})
        self.assertEqual(float(np.max(fused)), 0.0, "Kalman fusion introduced ghost rain")

    # =========================================================================
    # 5. CORRUPTED & NAN RADAR REFLECTIVITY INPUTS
    # =========================================================================

    def test_nan_and_inf_radar_inputs(self):
        """Test radar grid with adversarial NaN, +Inf, -Inf, and negative values."""
        corrupt_grid = np.zeros(DEFAULT_GRID_SHAPE, dtype=np.float32)
        corrupt_grid[10:20, 10:20] = np.nan
        corrupt_grid[25:35, 25:35] = np.inf
        corrupt_grid[40:50, 40:50] = -np.inf
        corrupt_grid[55:65, 55:65] = -999.0
        corrupt_grid[0:10, 0:10] = 50.0  # Real rain in corner

        # Calibrator sanitization
        calibrated, _, _ = self.calibrator.calibrate(corrupt_grid, gauges={})
        self.assertFalse(np.isnan(calibrated).any())
        self.assertFalse(np.isinf(calibrated).any())
        self.assertTrue(np.all(calibrated >= 0.0))

        # Nowcaster sanitization
        u_flow, v_flow = self.nowcaster.compute_storm_motion(corrupt_grid, corrupt_grid, corrupt_grid)
        self.assertFalse(np.isnan(u_flow).any())
        self.assertFalse(np.isnan(v_flow).any())
        forecasts = self.nowcaster.extrapolate(corrupt_grid, u_flow, v_flow, horizons_min=[15, 30])
        self.assertFalse(np.isnan(forecasts[15]).any())
        self.assertTrue(np.all(forecasts[15] >= 0.0))

        # Disaggregator sanitization
        df_out = self.disaggregator.disaggregate(forecasts)
        self.assertFalse(df_out.isna().any().any())

        # Super-Resolution sanitization
        sr_res = self.sr_engine.downscale(corrupt_grid)
        self.assertFalse(np.isnan(sr_res.grid_100m).any())
        self.assertTrue(np.all(sr_res.grid_100m >= 0.0))

    def test_dbz_conversion_with_nan_and_sub_threshold(self):
        """Test dBZ to rain rate power law with NaN, negative dBZ, and extreme dBZ."""
        dbz_adversarial = np.array([np.nan, -100.0, 0.0, 14.9, 15.0, 50.0, 65.0, np.inf], dtype=np.float32)
        rates = dbz_to_rain_rate(dbz_adversarial)
        self.assertFalse(np.isnan(rates).any())
        self.assertEqual(rates[0], 0.0, "NaN should be zeroed")
        self.assertEqual(rates[1], 0.0, "-100 dBZ should be masked")
        self.assertEqual(rates[3], 0.0, "< 15 dBZ should be masked")
        self.assertGreater(rates[4], 0.0, ">= 15 dBZ should produce rain")
        self.assertGreater(rates[6], 100.0, "65 dBZ should be extreme convective rain")
        self.assertLessEqual(rates[7], 500.0, "Inf dBZ should be safely capped")

        # Invertibility check on valid rates
        dbz_reconstructed = rain_rate_to_dbz(rates)
        self.assertFalse(np.isnan(dbz_reconstructed).any())

    # =========================================================================
    # 6. MASS CONSERVATION ACROSS 7,894 CHENNAI STREETS (0.1% TOLERANCE)
    # =========================================================================

    def test_strict_mass_conservation_diverse_spatial_patterns(self):
        """Verify strict mass conservation across 7,894 streets for 3 distinct rainfall patterns."""
        H, W = DEFAULT_GRID_SHAPE
        y_idx, x_idx = np.mgrid[0:H, 0:W]

        patterns = {
            'uniform_25mmh': np.full((H, W), 25.0, dtype=np.float32),
            'steep_michaung_cell': (120.0 * np.exp(-((x_idx - 40)**2 + (y_idx - 40)**2) / 18.0)).astype(np.float32),
            'bimodal_squall_line': (
                80.0 * np.exp(-((x_idx - 20)**2 + (y_idx - 30)**2) / 25.0) +
                70.0 * np.exp(-((x_idx - 60)**2 + (y_idx - 50)**2) / 25.0)
            ).astype(np.float32),
        }

        for name, grid in patterns.items():
            df_streets = self.disaggregator.disaggregate({15: grid})
            vol_errors = self.disaggregator.verify_mass_conservation(df_streets, {15: grid})
            err_pct = vol_errors[15]
            self.assertLessEqual(
                err_pct, 0.001,
                f"Pattern '{name}' mass conservation error {err_pct:.7f}% exceeds strict 0.001% limit!"
            )

    # =========================================================================
    # 7. TELECOM CML MICROWAVE INGESTION ADVERSARIAL STRESS
    # =========================================================================

    def test_cml_deep_fade_and_outage_capping(self):
        """Test CML behavior when microwave link drops completely (deep fade / tower outage)."""
        link = CMLLink(
            link_id='TEST-OUTAGE',
            tx_lat=13.0827, tx_lon=80.2755,
            rx_lat=13.0674, rx_lon=80.2443,
            frequency_ghz=18.0, polarization='H',
            tsl_dbm=15.0,
            rsl_dbm=-120.0,       # Complete link drop / outage (-75 dB attenuation)
            baseline_dbm=-45.0
        )
        rain_rate = self.cml_engine.invert_link(link)
        self.assertLessEqual(rain_rate, 300.0, "Outage fade must be capped at physical 300 mm/hr limit")

    def test_cml_anomalous_propagation_positive_rsl(self):
        """Test anomalous propagation where RSL > baseline (negative attenuation)."""
        link = CMLLink(
            link_id='TEST-ANOPROP',
            tx_lat=13.0827, tx_lon=80.2755,
            rx_lat=13.0674, rx_lon=80.2443,
            tsl_dbm=15.0,
            rsl_dbm=-40.0,        # Higher than baseline (-45.0)
            baseline_dbm=-45.0
        )
        rain_rate = self.cml_engine.invert_link(link)
        self.assertEqual(rain_rate, 0.0, "Negative attenuation must return 0.0 mm/hr")

    # =========================================================================
    # 8. SUPER RESOLUTION (1km -> 100m) MASS CONSERVATION
    # =========================================================================

    def test_super_resolution_mass_conservation_under_steep_topography(self):
        """Verify 100m super-resolution preserves exact water volume on steep gradient."""
        test_1km = np.zeros((15, 15), dtype=np.float32)
        test_1km[7, 7] = 120.0
        test_1km[6:9, 6:9] += 40.0

        res = self.sr_engine.downscale(test_1km, apply_mass_conservation=True)
        self.assertEqual(res.shape_100m, (150, 150))
        self.assertLessEqual(res.mass_conservation_error_pct, 0.001)

    # =========================================================================
    # 9. END-TO-END PIPELINE UNDER ADVERSARIAL COMBINATIONS
    # =========================================================================

    def test_end_to_end_pipeline_blackout_and_extreme_deluge(self):
        """Execute full Layer0Pipeline in offline mode with Cyclone Michaung deluge."""
        pipeline = Layer0Pipeline()
        result = pipeline.run(mode='archive', scenario='michaung', calib_method='brandes')

        self.assertEqual(len(result.dataframe), 7894)
        self.assertEqual(len(result.forecasts), 6)
        self.assertLessEqual(result.diagnostics['max_mass_error_pct'], 0.001)
        self.assertLess(result.diagnostics['total_latency_sec'], 1.0,
                        "Full pipeline execution must complete in < 1.0 second on CPU")


if __name__ == '__main__':
    unittest.main(verbosity=2)
