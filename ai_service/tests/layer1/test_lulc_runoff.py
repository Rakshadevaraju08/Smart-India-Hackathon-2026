"""Automated Verification Test Suite for Layer 1 LULC, Soil Hydrology & Surface Runoff Engine."""

import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_service.layer1.lulc.impervious_extractor import ImperviousExtractor
from ai_service.layer1.lulc.soil_hydrology import SoilHydrologyModel
from ai_service.layer1.lulc.runoff_generator import SurfaceRunoffGenerator, RunoffResult
from ai_service.layer1.pipeline import Layer1Pipeline, Layer1Result


class TestLayer1LULCRunoff(unittest.TestCase):
    """Test suite for Layer 1 LULC and Soil Runoff Engine."""

    @classmethod
    def setUpClass(cls):
        cls.base_dir = Path(__file__).resolve().parents[3]
        cls.extractor = ImperviousExtractor(base_dir=cls.base_dir)
        cls.soil_model = SoilHydrologyModel(base_dir=cls.base_dir)
        cls.runoff_gen = SurfaceRunoffGenerator(base_dir=cls.base_dir)

    def test_01_impervious_extractor_bounds(self):
        """Verify impervious fraction, BCR, and composite C remain within physical bounds."""
        df = self.extractor.extract_impervious_attributes()
        self.assertEqual(len(df), 7894, "Must cover all 7,894 GCC road segments")

        f_imp = df["impervious_fraction"].values
        self.assertTrue(np.all(f_imp >= 0.20), "Impervious fraction must be >= 0.20")
        self.assertTrue(np.all(f_imp <= 0.98), "Impervious fraction must be <= 0.98")

        c_comp = df["runoff_coefficient_c"].values
        self.assertTrue(np.all(c_comp >= 0.20), "Composite C must be >= 0.20")
        self.assertTrue(np.all(c_comp <= 0.96), "Composite C must be <= 0.96")

        manning_n = df["manning_overland_n"].values
        self.assertTrue(np.all(manning_n >= 0.014), "Manning's n must be >= 0.014")
        self.assertTrue(np.all(manning_n <= 0.180), "Manning's n must be <= 0.180")

    def test_02_zonal_differentiation(self):
        """Verify that commercial core (Zone 9 T. Nagar) has higher imperviousness than outskirts."""
        df = self.extractor.extract_impervious_attributes()
        z9_mean = df[df["zone_no"] == 9]["impervious_fraction"].mean()
        z15_mean = df[df["zone_no"] == 15]["impervious_fraction"].mean()

        self.assertGreater(z9_mean, z15_mean, "Zone 9 (T. Nagar CBD) must be more impervious than Zone 15 (Sholinganallur)")
        self.assertGreaterEqual(z9_mean, 0.85, "Zone 9 mean imperviousness should be >= 85%")

    def test_03_soil_hsg_classification(self):
        """Verify USDA/ICAR Hydrologic Soil Group classification logic."""
        self.assertEqual(SoilHydrologyModel.classify_hsg(16.0), "A")
        self.assertEqual(SoilHydrologyModel.classify_hsg(9.5), "B")
        self.assertEqual(SoilHydrologyModel.classify_hsg(6.2), "C")
        self.assertEqual(SoilHydrologyModel.classify_hsg(3.8), "D")

    def test_04_amc_transitions(self):
        """Verify that Antecedent Moisture Condition III significantly reduces soil infiltration."""
        df_amc1 = self.soil_model.compute_soil_attributes(amc="AMC_I")
        df_amc2 = self.soil_model.compute_soil_attributes(amc="AMC_II")
        df_amc3 = self.soil_model.compute_soil_attributes(amc="AMC_III")

        mean_amc1 = df_amc1["effective_infiltration_mm_hr"].mean()
        mean_amc2 = df_amc2["effective_infiltration_mm_hr"].mean()
        mean_amc3 = df_amc3["effective_infiltration_mm_hr"].mean()

        self.assertGreater(mean_amc1, mean_amc2, "AMC I (Dry) should have higher infiltration than AMC II")
        self.assertGreater(mean_amc2, mean_amc3, "AMC II (Normal) should have higher infiltration than AMC III")
        self.assertAlmostEqual(mean_amc3 / mean_amc2, 0.40, delta=0.05,
                               msg="AMC III should throttle baseline infiltration by ~60%")

    def test_05_zero_rainfall_zero_runoff(self):
        """Verify that zero rainfall produces zero surface runoff."""
        res = self.runoff_gen.compute_runoff(rainfall_intensity=0.0)
        self.assertEqual(float(np.max(res.runoff_rates_mm_hr)), 0.0)
        self.assertEqual(float(np.max(res.discharge_m3_s)), 0.0)
        self.assertEqual(res.total_runoff_volume_m3, 0.0)

    def test_06_monsoon_runoff_and_mass_conservation(self):
        """Verify physical runoff generation and strict mass continuity under 65 mm/hr rain."""
        res = self.runoff_gen.compute_runoff(
            rainfall_intensity=65.0,
            amc="AMC_III",
            scenario="michaung"
        )
        diag = res.diagnostics
        self.assertGreater(diag["mean_runoff_rate_mm_hr"], 35.0, "Runoff rate under 65mm/h should exceed 35 mm/h")
        self.assertGreater(diag["mean_discharge_m3_s"], 0.03, "Mean tributary discharge should exceed 0.03 m3/s")
        self.assertLess(diag["mass_balance_error_pct"], 0.01, "Global mass balance error must be < 0.01%")
        self.assertTrue(diag["mass_balance_passed"])

    def test_07_subsecond_execution_performance(self):
        """Verify that LULC and surface runoff computation finishes in under 50 ms."""
        res = self.runoff_gen.compute_runoff(rainfall_intensity=75.0)
        elapsed_ms = res.diagnostics["execution_time_ms"]
        self.assertLess(elapsed_ms, 50.0, f"Execution latency ({elapsed_ms} ms) must be < 50 ms SLA")

    def test_08_frequency_factor_scaling(self):
        """Verify IRC:SP:42 / CPHEEO frequency scaling multiplier Cf."""
        # Low intensity (< 25 mm/hr) should have Cf = 1.00
        cf_low = float(ImperviousExtractor.compute_frequency_factor(15.0))
        self.assertAlmostEqual(cf_low, 1.00, places=2)

        # Moderate intensity (37.5 mm/hr) should be ~1.05
        cf_mod = float(ImperviousExtractor.compute_frequency_factor(37.5))
        self.assertAlmostEqual(cf_mod, 1.05, places=2)

        # Heavy cloudburst (> 50 mm/hr) scales up to 1.25
        cf_heavy = float(ImperviousExtractor.compute_frequency_factor(75.0))
        self.assertAlmostEqual(cf_heavy, 1.175, places=2)

        cf_extreme = float(ImperviousExtractor.compute_frequency_factor(100.0))
        self.assertAlmostEqual(cf_extreme, 1.25, places=2)

    def test_09_rwh_disconnection_factor(self):
        """Verify that Chennai RWH discount disconnects DCIA by 6% on residential corridors."""
        df = self.extractor.extract_impervious_attributes()
        # Create synthetic test rows to compare residential vs motorway under identical zone
        synth_df = pd.DataFrame([
            {"segment_id": 1, "zone_no": 9, "road_class": "motorway", "catchment_area_m2": 1000.0},
            {"segment_id": 2, "zone_no": 9, "road_class": "residential", "catchment_area_m2": 1000.0}
        ])
        res_synth = self.extractor.extract_impervious_attributes(synth_df)
        f_imp_motor = res_synth.loc[res_synth["road_class"] == "motorway", "impervious_fraction"].iloc[0]
        f_imp_resid = res_synth.loc[res_synth["road_class"] == "residential", "impervious_fraction"].iloc[0]

        # Residential must be lower due to 0.94 RWH discount and lower road class modifier
        self.assertLess(f_imp_resid, f_imp_motor)

    def test_10_slope_adjustment(self):
        """Verify Cartosat DEM slope increases composite C and reduces depression storage."""
        synth_df = pd.DataFrame([
            {"segment_id": 1, "zone_no": 8, "road_class": "secondary", "terrain_slope_m_per_m": 0.001, "catchment_area_m2": 1000.0},
            {"segment_id": 2, "zone_no": 8, "road_class": "secondary", "terrain_slope_m_per_m": 0.040, "catchment_area_m2": 1000.0}
        ])
        res_synth = self.extractor.extract_impervious_attributes(synth_df)
        c_flat = res_synth.loc[res_synth["terrain_slope_m_per_m"] == 0.001, "runoff_coefficient_c"].iloc[0]
        c_steep = res_synth.loc[res_synth["terrain_slope_m_per_m"] == 0.040, "runoff_coefficient_c"].iloc[0]

        self.assertGreater(c_steep, c_flat, "Steeper slope must yield higher composite runoff coefficient C")

    def test_11_riparian_and_subsidence_penalties(self):
        """Verify canal riparian proximity (<150m) and InSAR subsidence (>3.5mm/yr) reduce infiltration."""
        synth_soil = pd.DataFrame([
            {"segment_id": 1, "soil_infiltration_rate_mm_hr": 10.0, "distance_to_major_canal_m": 500.0, "subsidence_rate_mm_yr": 1.0},
            {"segment_id": 2, "soil_infiltration_rate_mm_hr": 10.0, "distance_to_major_canal_m": 50.0, "subsidence_rate_mm_yr": 1.0},
            {"segment_id": 3, "soil_infiltration_rate_mm_hr": 10.0, "distance_to_major_canal_m": 500.0, "subsidence_rate_mm_yr": 5.0}
        ])
        res = self.soil_model.compute_soil_attributes(synth_soil, amc="AMC_II")
        f_norm = res.loc[res["segment_id"] == 1, "effective_infiltration_mm_hr"].iloc[0]
        f_canal = res.loc[res["segment_id"] == 2, "effective_infiltration_mm_hr"].iloc[0]
        f_sub = res.loc[res["segment_id"] == 3, "effective_infiltration_mm_hr"].iloc[0]

        self.assertAlmostEqual(f_canal, f_norm * 0.40, places=1, msg="Canal riparian zone must receive 60% infiltration penalty")
        self.assertAlmostEqual(f_sub, f_norm * 0.85, places=1, msg="Compacted subsidence zone must receive 15% infiltration penalty")

    def test_12_multi_intensity_mass_conservation(self):
        """Verify global hydrologic mass conservation across light, moderate, severe, and cloudburst events."""
        for intensity in [12.0, 35.0, 65.0, 110.0]:
            res = self.runoff_gen.compute_runoff(
                rainfall_intensity=intensity,
                amc="AMC_II"
            )
            err = res.diagnostics["mass_balance_error_pct"]
            self.assertLess(err, 0.001, f"Mass balance error ({err}%) at {intensity} mm/hr must be < 0.001%")
            self.assertTrue(res.diagnostics["mass_balance_passed"])


if __name__ == "__main__":
    unittest.main()
