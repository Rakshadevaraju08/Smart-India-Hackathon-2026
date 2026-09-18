"""
Unit & Integration Tests for ai_service.orchestration Subpackage.
"""

import unittest
import numpy as np

from ai_service.orchestration import (
    Layer0Layer1Coupler,
    CoupledResult,
    run_coupled_layer0_layer1,
)


class TestOrchestrationSubpackage(unittest.TestCase):
    """Test suite for Layer 0 -> Layer 1 in-memory orchestration."""

    def setUp(self):
        self.coupler = Layer0Layer1Coupler()

    def test_01_coupler_instantiation(self):
        """Verify coupler components are loaded lazily and cleanly."""
        self.assertIsNotNone(self.coupler.l0_pipeline)
        self.assertIsNotNone(self.coupler.runoff_generator)

    def test_02_michaung_storm_coupling(self):
        """Verify in-memory coupling on historical Michaung cloudburst."""
        res = self.coupler.couple(mode="archive", scenario="michaung", horizon_min=60, amc="AMC_III")
        self.assertIsInstance(res, CoupledResult)
        self.assertEqual(len(res.dataframe), 7894)

        # Check required hydrologic columns exist
        for col in [
            "rainfall_intensity_mm_hr",
            "impervious_fraction",
            "hydrologic_soil_group",
            "effective_infiltration_mm_hr",
            "surface_runoff_rate_mm_hr",
            "surface_runoff_inflow_m3_s",
        ]:
            self.assertIn(col, res.dataframe.columns)

        # Verify storm rainfall and runoff are strictly positive
        mean_rain = np.mean(res.dataframe["rainfall_intensity_mm_hr"].values)
        mean_runoff = np.mean(res.dataframe["surface_runoff_rate_mm_hr"].values)
        self.assertGreater(mean_rain, 50.0)
        self.assertGreater(mean_runoff, 40.0)

        # Verify mass balance error is 0.000000%
        r_diag = res.diagnostics["layer1_runoff_diagnostics"]
        self.assertLess(r_diag["mass_balance_error_pct"], 0.01)

    def test_03_telemetry_dict_serialization(self):
        """Verify lightweight JSON telemetry serialization for API gateway."""
        res = self.coupler.couple(mode="archive", scenario="michaung", horizon_min=60, amc="AMC_III")
        telemetry = res.to_telemetry_dict(sample_zones=True)

        self.assertEqual(telemetry["status"], "success")
        self.assertEqual(telemetry["active_segments"], 7894)
        self.assertIn("kpis", telemetry)
        self.assertIn("zonal_telemetry", telemetry)
        self.assertGreater(len(telemetry["zonal_telemetry"]), 0)

    def test_04_functional_api_and_backward_compatibility(self):
        """Verify run_coupled_layer0_layer1 functional wrapper works."""
        res = run_coupled_layer0_layer1(scenario="michaung", horizon_min=60, amc="AMC_III", mode="archive")
        self.assertIsInstance(res, CoupledResult)
        self.assertEqual(len(res.streets_df), 7894)


if __name__ == "__main__":
    unittest.main()
