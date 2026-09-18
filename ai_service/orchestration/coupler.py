"""
KAIROS Urban Flood Nowcasting System: Layer 0 -> Layer 1 Hydrologic Coupler.

Dedicated in-memory coupling between:
  - Layer 0 (Flat-Plane Doppler Radar Ingestion, Calibration & Optical Flow Nowcasting)
  - Layer 1 (Cartosat-1 DEM, LULC Impervious Area, Soil Hydrology & Surface Runoff)

Maintains complete layer decoupling: Layer 0 and Layer 1 remain 100% independent
modules with zero cross-dependencies. The Coupler acts as the orchestration link.
"""

from dataclasses import dataclass
import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

from ..layer0.pipeline import Layer0Pipeline, Layer0Result
from ..layer1.lulc import SurfaceRunoffGenerator, RunoffResult


@dataclass
class CoupledResult:
    """Encapsulates the end-to-end coupled telemetry and diagnostics from Layer 0 and Layer 1."""
    dataframe: pd.DataFrame
    layer0_result: Layer0Result
    runoff_result: RunoffResult
    diagnostics: Dict[str, Any]

    @property
    def streets_df(self) -> pd.DataFrame:
        """Alias for standard road segment dataframe."""
        return self.dataframe

    def to_csv(self, output_path: Union[str, Path]) -> Path:
        """Export coupled road segment hydrologic telemetry to CSV."""
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        self.dataframe.to_csv(p, index=False)
        return p

    def to_telemetry_dict(self, sample_zones: bool = True) -> Dict[str, Any]:
        """Format as lightweight JSON-serializable telemetry payload for Web API/WebSocket."""
        diag = self.diagnostics
        r_diag = diag.get("layer1_runoff_diagnostics", {})
        l0_diag = diag.get("layer0_diagnostics", {})

        payload: Dict[str, Any] = {
            "status": "success",
            "mode": diag.get("mode", "auto"),
            "scenario": diag.get("scenario", "michaung"),
            "horizon_min": diag.get("horizon_min", 60),
            "amc": diag.get("amc", "AMC_III"),
            "timestamp": str(self.layer0_result.calibrated_sweep.timestamp),
            "total_latency_ms": diag.get("total_latency_ms", 0.0),
            "active_segments": len(self.dataframe),
            "kpis": {
                "mean_rain_mm_hr": r_diag.get("mean_rainfall_mm_hr", 0.0),
                "mean_runoff_mm_hr": r_diag.get("mean_runoff_rate_mm_hr", 0.0),
                "mean_discharge_m3_s": r_diag.get("mean_discharge_m3_s", 0.0),
                "max_discharge_m3_s": r_diag.get("max_discharge_m3_s", 0.0),
                "mean_impervious_fraction": r_diag.get("mean_impervious_fraction", 0.806),
                "mean_soil_infiltration_mm_hr": r_diag.get("mean_effective_infiltration_mm_hr", 3.69),
                "catchment_runoff_volume_m3": r_diag.get("catchment_runoff_volume_m3", 0.0),
                "mass_balance_error_pct": r_diag.get("mass_balance_error_pct", 0.0),
                "radar_bias_ratio": round(float(self.layer0_result.g_r_ratio), 3),
            }
        }

        if sample_zones and len(self.dataframe) > 0:
            key_zones = [
                {"name": "T. Nagar (Commercial CBD)", "zone": 9, "filter_road": "street"},
                {"name": "Royapuram (Dense North)", "zone": 5, "filter_road": "street"},
                {"name": "Velachery (Clay Basin)", "zone": 13, "filter_road": "street"},
                {"name": "Alandur (Mixed Urban)", "zone": 12, "filter_road": "residential"},
            ]
            z_telemetry = []
            for kz in key_zones:
                sub = self.dataframe[
                    (self.dataframe["zone_no"] == kz["zone"]) &
                    (self.dataframe["road_class"].astype(str).str.contains(kz["filter_road"], case=False, na=False))
                ]
                if len(sub) > 0:
                    r = sub.iloc[0]
                    z_telemetry.append({
                        "locality": kz["name"],
                        "zone_no": kz["zone"],
                        "rainfall_mm_hr": float(r.get("rainfall_intensity_mm_hr", 0.0)),
                        "impervious_fraction": float(r.get("impervious_fraction", 0.0)),
                        "hydrologic_soil_group": str(r.get("hydrologic_soil_group", "C")),
                        "infiltration_mm_hr": float(r.get("effective_infiltration_mm_hr", 0.0)),
                        "runoff_mm_hr": float(r.get("surface_runoff_rate_mm_hr", 0.0)),
                        "discharge_m3_s": float(r.get("surface_runoff_inflow_m3_s", 0.0)),
                    })
            payload["zonal_telemetry"] = z_telemetry

        return payload


class Layer0Layer1Coupler:
    """
    Dedicated in-memory coordinator coupling Layer 0 rainfall with Layer 1 surface runoff.
    """

    def __init__(self, base_dir: Optional[Union[str, Path]] = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parents[2]
        self._l0_pipeline: Optional[Layer0Pipeline] = None
        self._runoff_generator: Optional[SurfaceRunoffGenerator] = None

    @property
    def l0_pipeline(self) -> Layer0Pipeline:
        if self._l0_pipeline is None:
            self._l0_pipeline = Layer0Pipeline()
        return self._l0_pipeline

    @property
    def runoff_generator(self) -> SurfaceRunoffGenerator:
        if self._runoff_generator is None:
            self._runoff_generator = SurfaceRunoffGenerator(base_dir=self.base_dir)
        return self._runoff_generator

    def couple(
        self,
        mode: str = "auto",
        scenario: str = "michaung",
        horizon_min: int = 60,
        amc: str = "AMC_III",
        custom_roads_df: Optional[pd.DataFrame] = None
    ) -> CoupledResult:
        """
        Execute in-memory coupling:
          1. Layer 0 nowcasts rainfall field to lead time horizon.
          2. Disaggregates to 7,894 road segments.
          3. Feeds rainfall array directly into Layer 1 LULC & runoff engine.
          4. Returns enriched telemetry with strict mass balance.
        """
        t_start = time.perf_counter()

        # Step 1: Run Layer 0
        l0_res = self.l0_pipeline.run(mode=mode, scenario=scenario)

        df_l0 = l0_res.dataframe
        col_name = f"I_T+{horizon_min}m_mm_hr"
        if col_name not in df_l0.columns:
            # Fallback to T+60m or first available rain column
            rain_cols = [c for c in df_l0.columns if c.startswith("I_T+")]
            col_name = rain_cols[0] if rain_cols else "I_T+60m_mm_hr"

        rain_vector = df_l0[col_name].values.astype(np.float32)

        # Step 2: Run Layer 1 Runoff Generator
        runoff_res = self.runoff_generator.compute_runoff(
            roads_df=custom_roads_df,
            rainfall_intensity=rain_vector,
            amc=amc,
            scenario=scenario
        )

        total_latency_ms = (time.perf_counter() - t_start) * 1000.0

        diagnostics = {
            "mode": mode,
            "scenario": scenario,
            "horizon_min": horizon_min,
            "amc": amc,
            "total_latency_ms": round(total_latency_ms, 2),
            "layer0_latency_ms": round(l0_res.diagnostics.get("total_latency_sec", 0.0) * 1000.0, 2),
            "layer1_latency_ms": round(runoff_res.diagnostics.get("execution_time_ms", 0.0), 2),
            "layer0_diagnostics": l0_res.diagnostics,
            "layer1_runoff_diagnostics": runoff_res.diagnostics,
        }

        return CoupledResult(
            dataframe=runoff_res.dataframe,
            layer0_result=l0_res,
            runoff_result=runoff_res,
            diagnostics=diagnostics
        )


def run_coupled_layer0_layer1(
    scenario: str = "michaung",
    horizon_min: int = 60,
    amc: str = "AMC_III",
    mode: str = "auto"
) -> CoupledResult:
    """Convenience function executing the in-memory coupling."""
    coupler = Layer0Layer1Coupler()
    return coupler.couple(mode=mode, scenario=scenario, horizon_min=horizon_min, amc=amc)
