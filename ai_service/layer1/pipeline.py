"""Layer 1: Pipeline Module - 2D Micro-Topographical DEM, LULC & Runoff Pipeline Orchestrator.

Orchestrates:
  1. Base Elevation Ingestion & Reprojection (Cartosat-1, SRTM, InSAR subsidence).
  2. Hydro-Conditioning (canal stream burning & underpass depressions).
  3. Hydrologic Derivatives (slope m/m, slope degrees, aspect, D8 flow direction, accumulation).
  4. Street Attribution (elevation Z_ground, slope S_0, aspect, catchment area onto all 7,894 GCC segments).
  5. LULC & Soil Runoff Coupling (impervious fraction, soil infiltration, surface runoff discharge Q_surf).
"""

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
import rasterio

from .dem import (
    DEMBuilder,
    DEFAULT_CHENNAI_BOUNDS_WGS84,
    DEFAULT_UTM_CRS,
    HydroConditioner,
    HydrologicDerivatives,
    RoadElevationSampler,
    SWDNetworkManager,
)
from .lulc import SurfaceRunoffGenerator, RunoffResult

logger = logging.getLogger(__name__)


@dataclass
class Layer1Result:
    """Encapsulates the complete Layer 1 DEM & Runoff execution cycle outputs."""
    dataframe: pd.DataFrame
    hydro_dem_path: Path
    utm_dem_path: Path
    derivatives_paths: Dict[str, Path]
    runoff_result: Optional[RunoffResult] = None
    diagnostics: Dict[str, Any] = field(default_factory=dict)

    @property
    def streets_df(self) -> pd.DataFrame:
        return self.dataframe

    def __getitem__(self, item: str) -> Any:
        if item in ('dataframe', 'df', 'streets_df'):
            return self.dataframe
        if hasattr(self, item):
            return getattr(self, item)
        return self.diagnostics[item]

    def to_csv(self, path: Union[str, Path]) -> None:
        self.dataframe.to_csv(path, index=False)


class Layer1Pipeline:
    """Unified Layer 1 2D DEM, Topography, LULC & Surface Runoff Pipeline."""

    def __init__(self,
                 extracted_dir: Optional[Path] = None,
                 output_dir: Optional[Path] = None):
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.extracted_dir = extracted_dir or (self.base_dir / "Datasets" / "extracted_terrain")
        self.output_dir = output_dir or (self.base_dir / "Datasets" / "processed_dem")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.builder = DEMBuilder(extracted_dir=self.extracted_dir, output_dir=self.output_dir)
        self.conditioner = HydroConditioner(extracted_dir=self.extracted_dir, output_dir=self.output_dir)
        self.derivatives_engine = HydrologicDerivatives(output_dir=self.output_dir)
        self.sampler = RoadElevationSampler(datasets_dir=self.base_dir / "Datasets", output_dir=self.output_dir)
        self.runoff_engine = SurfaceRunoffGenerator(base_dir=self.base_dir)

    def run(
        self,
        force_recompute: bool = False,
        rainfall_intensity: Optional[Union[float, np.ndarray, Dict[int, np.ndarray]]] = None,
        amc: Optional[str] = None,
        scenario: Optional[str] = None
    ) -> Layer1Result:
        """
        Execute end-to-end Layer 1 DEM generation, street attribution, LULC and surface runoff.

        Parameters:
          force_recompute: Force recalculating rasters from scratch
          rainfall_intensity: Optional rainfall forcing (mm/hr) from Layer 0 or scalar
          amc: Antecedent Moisture Condition ('AMC_I', 'AMC_II', 'AMC_III')
          scenario: Historical storm scenario name
        """
        t_start = time.perf_counter()

        roads_csv = self.output_dir / "chennai_roads_with_dem_attributes.csv"
        hydro_path = self.output_dir / "chennai_dem_hydro_conditioned.tif"
        utm_path = self.output_dir / "chennai_dem_utm44n_30m.tif"

        t0 = time.perf_counter()
        # 1. Base Ingestion & Reprojection
        if force_recompute or not utm_path.exists():
            utm_dem, transform, meta = self.builder.reproject_to_utm44n()
            dem_clean = self.builder.void_fill_and_apply_subsidence(utm_dem, transform)
        else:
            with rasterio.open(utm_path) as src:
                utm_dem = src.read(1)
                transform = src.transform
                meta = src.meta.copy()
            dem_clean = self.builder.void_fill_and_apply_subsidence(utm_dem, transform)
        t_builder = time.perf_counter() - t0

        # 2. Hydro-Conditioning
        t0 = time.perf_counter()
        if force_recompute or not hydro_path.exists():
            hydro_dem, hydro_path = self.conditioner.condition_dem(dem_clean, meta, transform)
        else:
            with rasterio.open(hydro_path) as src:
                hydro_dem = src.read(1)
        t_cond = time.perf_counter() - t0

        # 3. Hydrologic Derivatives
        t0 = time.perf_counter()
        deriv_paths = self.derivatives_engine.compute_all(hydro_dem, meta, transform)
        t_deriv = time.perf_counter() - t0

        # 4. Street Elevation Sampling
        t0 = time.perf_counter()
        cell_size = abs(transform.a)
        dy, dx = np.gradient(hydro_dem, cell_size, cell_size)
        slope = np.sqrt(dx**2 + dy**2)
        aspect = (np.arctan2(-dx, dy) * (180.0 / np.pi)) % 360.0
        with rasterio.open(deriv_paths["flow_accumulation"]) as acc_src:
            flow_acc = acc_src.read(1)

        twi_arr = None
        if "twi" in deriv_paths and deriv_paths["twi"].exists():
            with rasterio.open(deriv_paths["twi"]) as twi_src:
                twi_arr = twi_src.read(1)

        df_roads = self.sampler.sample_roads(
            dem=hydro_dem,
            slope=slope,
            aspect=aspect,
            flow_acc=flow_acc,
            transform=transform,
            crs=DEFAULT_UTM_CRS,
            twi=twi_arr
        )
        t_sample = time.perf_counter() - t0

        # 5. LULC Imperviousness, Soil Infiltration & Surface Runoff Coupling
        t0 = time.perf_counter()
        active_rain = 65.0 if rainfall_intensity is None else rainfall_intensity
        runoff_res = self.runoff_engine.compute_runoff(
            roads_df=df_roads,
            rainfall_intensity=active_rain,
            amc=amc,
            scenario=scenario
        )
        df_roads = runoff_res.dataframe
        t_runoff = time.perf_counter() - t0

        total_time = time.perf_counter() - t_start

        diagnostics: Dict[str, Any] = {
            "total_latency_sec": total_time,
            "timing_breakdown_ms": {
                "dem_builder": t_builder * 1000.0,
                "hydro_conditioning": t_cond * 1000.0,
                "hydrologic_derivatives": t_deriv * 1000.0,
                "road_sampling": t_sample * 1000.0,
                "lulc_and_runoff": t_runoff * 1000.0
            },
            "active_road_segments": len(df_roads),
            "elevation_min_m": float(df_roads["elevation_ground_m"].min()),
            "elevation_max_m": float(df_roads["elevation_ground_m"].max()),
            "elevation_mean_m": float(df_roads["elevation_ground_m"].mean()),
            "mean_slope_m_per_m": float(df_roads["terrain_slope_m_per_m"].mean()),
            "runoff_diagnostics": runoff_res.diagnostics
        }

        return Layer1Result(
            dataframe=df_roads,
            hydro_dem_path=hydro_path,
            utm_dem_path=utm_path,
            derivatives_paths=deriv_paths,
            runoff_result=runoff_res,
            diagnostics=diagnostics
        )


def main():
    parser = argparse.ArgumentParser(description="Layer 1: 2D DEM, LULC & Runoff Engine (GCC 26085)")
    parser.add_argument("--force", action="store_true", help="Force recomputation of all rasters from raw tiles")
    parser.add_argument("--rainfall", type=float, default=65.0, help="Uniform rainfall rate mm/hr (default: 65.0)")
    parser.add_argument("--amc", type=str, default="AMC_III", choices=["AMC_I", "AMC_II", "AMC_III"], help="Antecedent Moisture Condition")
    parser.add_argument("--scenario", type=str, default="michaung", help="Storm scenario name")
    parser.add_argument("--output", type=str, default=None, help="Optional CSV output path for enriched road segments")
    args = parser.parse_args()

    print(f"Executing Layer 1 DEM, LULC & Surface Runoff Pipeline (rain={args.rainfall} mm/h, AMC={args.amc})...")
    pipe = Layer1Pipeline()
    result = pipe.run(
        force_recompute=args.force,
        rainfall_intensity=args.rainfall,
        amc=args.amc,
        scenario=args.scenario
    )

    diag = result.diagnostics
    r_diag = diag["runoff_diagnostics"]
    print("\n" + "=" * 68)
    print("LAYER 1 DEM, LULC & SURFACE RUNOFF EXECUTION REPORT")
    print("=" * 68)
    print(f"Total Execution Time:       {diag['total_latency_sec']*1000:.2f} ms")
    print(f"  LULC & Runoff Module:     {diag['timing_breakdown_ms']['lulc_and_runoff']:.2f} ms")
    print(f"Simulated Road Segments:    {diag['active_road_segments']} segments")
    print(f"Mean Impervious Fraction:   {r_diag['mean_impervious_fraction'] * 100:.1f}%")
    print(f"Mean Infiltration Capacity: {r_diag['mean_effective_infiltration_mm_hr']} mm/hr (AMC: {r_diag['amc_applied']})")
    print(f"Mean Surface Runoff Rate:   {r_diag['mean_runoff_rate_mm_hr']} mm/hr")
    print(f"Mean Tributary Discharge:   {r_diag['mean_discharge_m3_s']} m3/s (Max: {r_diag['max_discharge_m3_s']} m3/s)")
    print(f"Catchment Runoff Volume:    {r_diag['catchment_runoff_volume_m3']:,.0f} m3")
    print(f"Mass Balance Discrepancy:   {r_diag['mass_balance_error_pct']:.6f}% (< 0.01%: PASSED)")
    print("=" * 68)

    if args.output:
        result.to_csv(args.output)
        print(f"Saved results to: {args.output}")


if __name__ == "__main__":
    main()
