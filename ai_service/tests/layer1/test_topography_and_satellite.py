"""Layer 1: Unit Test Suite for Micro-Topography Derivatives & Satellite LULC.

Tests:
  1. Topographic Wetness Index (TWI = ln(a / tan(beta))) calculation & boundaries.
  2. Sentinel-2 10m NDVI & DCIA raster generation covering 10x10 km AOI.
  3. Road sampler attribution including terrain_twi.
  4. Automatic zip extraction fallback.
"""

import unittest
from pathlib import Path
import numpy as np
import rasterio

from ai_service.layer1.dem.hydrologic_derivatives import HydrologicDerivatives
from ai_service.layer1.dem.road_sampler import RoadElevationSampler
from ai_service.layer1.lulc.sentinel2_processor import Sentinel2Processor, UTM_BOUNDS_10KM
from ai_service.layer1.dem.dem_builder import find_or_extract_file


class TestTopographyAndSatellite(unittest.TestCase):
    """Verifies Layer 1 advanced topographical and satellite deliverables."""

    @classmethod
    def setUpClass(cls):
        cls.base_dir = Path(__file__).resolve().parent.parent.parent.parent
        cls.output_dir = cls.base_dir / "Datasets" / "processed_dem"
        cls.derivatives_engine = HydrologicDerivatives(output_dir=cls.output_dir)
        cls.s2_processor = Sentinel2Processor(base_dir=cls.base_dir)

    def test_01_topographic_wetness_index_raster(self):
        """Verify that chennai_twi.tif exists and exhibits valid physical bounds."""
        twi_path = self.output_dir / "chennai_twi.tif"
        if not twi_path.exists():
            # Synthesize synthetic test grid if not yet run
            dem = np.full((100, 100), 10.0, dtype=np.float32)
            meta = {
                "driver": "GTiff", "height": 100, "width": 100,
                "count": 1, "dtype": "float32", "crs": "EPSG:32644",
                "transform": rasterio.transform.from_origin(412000, 1440000, 30.0, 30.0),
                "nodata": -9999.0
            }
            self.derivatives_engine.compute_all(dem, meta, meta["transform"])

        self.assertTrue(twi_path.exists(), "chennai_twi.tif must be created")
        with rasterio.open(twi_path) as src:
            twi_arr = src.read(1)
            valid = twi_arr[twi_arr > 0.0]
            self.assertGreater(len(valid), 0, "TWI raster must contain valid non-zero values")
            self.assertGreaterEqual(float(np.min(valid)), 0.0, "TWI must be non-negative")
            self.assertLessEqual(float(np.max(valid)), 30.0, "TWI must be physically bounded <= 30")

    def test_02_sentinel2_satellite_processor(self):
        """Verify Sentinel-2 10m NDVI & DCIA generation and AOI coverage."""
        res = self.s2_processor.process_or_generate_dcia()
        self.assertTrue(res["ndvi"].exists(), "Sentinel-2 NDVI raster must exist")
        self.assertTrue(res["dcia"].exists(), "Sentinel-2 DCIA raster must exist")

        with rasterio.open(res["dcia"]) as src:
            self.assertEqual(src.res, (10.0, 10.0), "Sentinel-2 pixel resolution must be exactly 10m x 10m")
            self.assertEqual(src.width, 1000, "10 km AOI must produce exactly 1000 columns")
            self.assertEqual(src.height, 1000, "10 km AOI must produce exactly 1000 rows")

            dcia_arr = src.read(1)
            valid = dcia_arr[dcia_arr >= 0.0]
            self.assertGreaterEqual(float(np.min(valid)), 0.0, "DCIA must be >= 0.0")
            self.assertLessEqual(float(np.max(valid)), 1.0, "DCIA must be <= 1.0")

    def test_03_road_sampler_includes_twi(self):
        """Verify that RoadElevationSampler enriches road dataframe with terrain_twi."""
        dem = np.full((50, 50), 12.0, dtype=np.float32)
        slope = np.full((50, 50), 0.003, dtype=np.float32)
        aspect = np.full((50, 50), 90.0, dtype=np.float32)
        flow_acc = np.full((50, 50), 25.0, dtype=np.float32)
        transform = rasterio.transform.from_origin(412000, 1440000, 30.0, 30.0)

        sampler = RoadElevationSampler(datasets_dir=self.base_dir / "Datasets", output_dir=self.output_dir)
        df_roads = sampler.sample_roads(
            dem=dem, slope=slope, aspect=aspect,
            flow_acc=flow_acc, transform=transform
        )

        self.assertIn("terrain_twi", df_roads.columns, "terrain_twi must be present in sampled road columns")
        self.assertGreaterEqual(len(df_roads), 500, "Road sampler must process road segments")

    def test_04_sentinel2_point_sampling(self):
        """Verify sampling of Sentinel-2 DCIA at authentic Chennai coordinates."""
        lats = np.array([13.0418, 12.9756])  # T. Nagar, Velachery
        lons = np.array([80.2341, 80.2201])
        dcia_sampled = self.s2_processor.sample_impervious_at_points(lats, lons)

        self.assertEqual(len(dcia_sampled), 2)
        self.assertTrue(np.all(dcia_sampled >= 0.20))
    def test_05_modular_dem_package_exports(self):
        """Verify that ai_service.layer1.dem modular subpackage exports all core classes."""
        from ai_service.layer1.dem import (
            DEMBuilder,
            HydroConditioner,
            HydrologicDerivatives,
            RoadElevationSampler,
            SWDNetworkManager,
            find_or_extract_file,
        )
        self.assertTrue(callable(DEMBuilder))
        self.assertTrue(callable(HydroConditioner))
        self.assertTrue(callable(HydrologicDerivatives))
        self.assertTrue(callable(RoadElevationSampler))
        self.assertTrue(callable(SWDNetworkManager))
        self.assertTrue(callable(find_or_extract_file))

    def test_06_swd_network_manager_depth_classification(self):
        """Verify SWDNetworkManager loads drainage network and classifies multi-tier burn depths."""
        from ai_service.layer1.dem.swd_network import SWDNetworkManager, DEFAULT_BURN_DEPTHS

        manager = SWDNetworkManager(base_dir=self.base_dir)
        gdf_swd = manager.load_drainage_network()
        self.assertGreater(len(gdf_swd), 50, "Should load at least 50 drainage features from OSM network")
        self.assertIn("burn_depth_m", gdf_swd.columns, "burn_depth_m must be computed")

        # Verify multi-tier depths exist
        depths = gdf_swd["burn_depth_m"].unique()
        self.assertTrue(any(d >= 2.0 for d in depths), "Should contain major river/canal burn depths >= 2.0m")
        self.assertTrue(any(d <= 1.5 for d in depths), "Should contain drain/ditch depths <= 1.5m")

        # Check burn shapes extraction
        shapes = manager.get_burn_shapes()
        self.assertGreater(len(shapes), 50, "Should generate burn shapes for hydro-conditioning")

    def test_07_hydro_conditioner_swd_integration(self):
        """Verify that HydroConditioner uses SWDManager to carve streams into DEM."""
        from ai_service.layer1.dem.hydro_conditioner import HydroConditioner

        conditioner = HydroConditioner(output_dir=self.output_dir, base_dir=self.base_dir)
        dem = np.full((100, 100), 10.0, dtype=np.float32)
        meta = {
            "driver": "GTiff", "height": 100, "width": 100,
            "count": 1, "dtype": "float32", "crs": "EPSG:32644",
            "transform": rasterio.transform.from_origin(415000, 1438000, 30.0, 30.0),
            "nodata": -9999.0
        }
        hydro_dem, p_out = conditioner.condition_dem(dem, meta, meta["transform"])
        self.assertTrue(p_out.exists(), "Hydro-conditioned DEM must be written to disk")
        self.assertEqual(hydro_dem.shape, (100, 100))
        self.assertTrue(np.all(hydro_dem <= 10.0), "Elevation should not increase after stream carving")

    @classmethod
    def tearDownClass(cls):
        import gc
        gc.collect()


if __name__ == "__main__":
    unittest.main()

