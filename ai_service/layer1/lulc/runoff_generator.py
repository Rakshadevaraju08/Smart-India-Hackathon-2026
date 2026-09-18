"""Layer 1: Surface Runoff Generator Engine.

Couples rainfall forcing I(t) from Layer 0 with LULC imperviousness, dynamic soil
infiltration capacity, surface depression storage, and micro-catchment geometry to
compute physical Surface Runoff Rates R_excess(t) [mm/hr] and Tributary Inflow
Discharge Q_surf(t) [m³/s] for all 7,894 Greater Chennai Corporation road segments.
"""

from dataclasses import dataclass, field
import logging
from pathlib import Path
import time
from typing import Any, Dict, Optional, Union
import numpy as np
import pandas as pd

from .impervious_extractor import ImperviousExtractor
from .soil_hydrology import SoilHydrologyModel

logger = logging.getLogger(__name__)


@dataclass
class RunoffResult:
    """Encapsulates the Layer 1 Surface Runoff Generation execution outputs."""
    dataframe: pd.DataFrame
    runoff_rates_mm_hr: np.ndarray
    discharge_m3_s: np.ndarray
    total_rain_volume_m3: float
    total_runoff_volume_m3: float
    total_infiltrated_volume_m3: float
    diagnostics: Dict[str, Any] = field(default_factory=dict)

    @property
    def streets_df(self) -> pd.DataFrame:
        return self.dataframe

    def __getitem__(self, item: str) -> Any:
        if item in ("dataframe", "df", "streets_df"):
            return self.dataframe
        if hasattr(self, item):
            return getattr(self, item)
        return self.diagnostics[item]


class SurfaceRunoffGenerator:
    """Coupled LULC and soil-informed surface runoff generator for urban road corridors."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).resolve().parent.parent.parent.parent
        self.impervious_extractor = ImperviousExtractor(base_dir=self.base_dir)
        self.soil_model = SoilHydrologyModel(base_dir=self.base_dir)

    def compute_runoff(
        self,
        roads_df: Optional[pd.DataFrame] = None,
        rainfall_intensity: Union[float, np.ndarray, Dict[int, np.ndarray]] = 65.0,
        horizon_min: int = 60,
        amc: Optional[str] = None,
        scenario: Optional[str] = None,
        depression_storage_imp_mm: float = 1.5,
        depression_storage_perv_mm: float = 4.0,
        default_subcatchment_area_m2: float = 3500.0
    ) -> RunoffResult:
        """
        Generate physically-grounded surface runoff rates and discharge vectors.

        Parameters:
          roads_df: Base DataFrame of 7,894 road segments
          rainfall_intensity: Scalar float (mm/hr), 1D numpy array, or dict of horizons
          horizon_min: Forecast horizon to select if a dictionary is provided
          amc: Antecedent Moisture Condition ('AMC_I', 'AMC_II', 'AMC_III')
          scenario: Storm event name to infer default AMC
          depression_storage_imp_mm: Initial retention on asphalt/concrete (default: 1.5 mm)
          depression_storage_perv_mm: Initial retention on pervious soil/turf (default: 4.0 mm)
          default_subcatchment_area_m2: Default catchment contributing area per segment

        Returns:
          RunoffResult instance with discharge vectors, volume budgets, and diagnostics.
        """
        t_start = time.perf_counter()

        # 1. Enrich road data with LULC Imperviousness
        df = self.impervious_extractor.extract_impervious_attributes(roads_df)

        # 2. Enrich road data with Soil Infiltration & AMC
        df = self.soil_model.compute_soil_attributes(
            roads_df=df,
            amc=amc,
            scenario=scenario
        )

        n_segments = len(df)

        # 3. Resolve Rainfall Intensity Array I_i(t) in mm/hr
        if isinstance(rainfall_intensity, dict):
            rain_arr = rainfall_intensity.get(horizon_min, next(iter(rainfall_intensity.values())))
        elif isinstance(rainfall_intensity, np.ndarray):
            rain_arr = rainfall_intensity
        else:
            rain_arr = np.full(n_segments, float(rainfall_intensity), dtype=np.float32)

        if len(rain_arr) != n_segments:
            rain_arr = np.resize(rain_arr, n_segments).astype(np.float32)

        # Subcatchment area A_c in m²
        if "catchment_area_m2" in df.columns:
            areas = df["catchment_area_m2"].values.astype(np.float64)
        else:
            areas = np.full(n_segments, default_subcatchment_area_m2, dtype=np.float64)

        f_imp = df["impervious_fraction"].values.astype(np.float32)
        f_soil = df["effective_infiltration_mm_hr"].values.astype(np.float32)

        # 4. Slope-Modulated Depression Storage Abstraction (Hollow Trapping)
        if "terrain_slope_m_per_m" in df.columns:
            slopes = df["terrain_slope_m_per_m"].values.astype(np.float32)
            # Flatter slopes retain more puddle hollow storage; steep slopes drain faster
            sd_imp_base = np.clip(depression_storage_imp_mm * (1.0 - (slopes - 0.01) * 8.0), 0.8, 2.5)
            sd_perv_base = np.clip(depression_storage_perv_mm * (1.0 - (slopes - 0.01) * 6.0), 2.0, 6.0)
        else:
            sd_imp_base = np.full(n_segments, depression_storage_imp_mm, dtype=np.float32)
            sd_perv_base = np.full(n_segments, depression_storage_perv_mm, dtype=np.float32)

        # 5. Dynamic Storm Intensity Factor C_f (IRC:SP:42 / CPHEEO standard)
        # High recurrence cloudbursts saturate micro-depressions and accelerate surface crusting
        cf = self.impervious_extractor.compute_frequency_factor(rain_arr).astype(np.float32)
        sd_imp = sd_imp_base / cf
        sd_perv = sd_perv_base / cf
        f_soil_eff = f_soil / cf

        # 6. Physical Runoff & Abstraction with Strict Mass Conservation
        # Impervious component:
        r_imp = np.maximum(0.0, rain_arr - sd_imp)
        l_imp = rain_arr - r_imp  # actual depression abstraction on impervious

        # Pervious component:
        f_loss = np.minimum(rain_arr, f_soil_eff)
        r_perv = np.maximum(0.0, rain_arr - f_loss - sd_perv)
        l_perv = np.maximum(0.0, rain_arr - f_loss - r_perv)  # actual depression abstraction on pervious

        # Composite Net Surface Runoff Rate R_excess in mm/hr
        r_excess = ((f_imp * r_imp) + ((1.0 - f_imp) * r_perv)).astype(np.float32)
        actual_infil_rate = ((1.0 - f_imp) * f_loss).astype(np.float32)
        actual_dep_rate = ((f_imp * l_imp) + ((1.0 - f_imp) * l_perv)).astype(np.float32)

        # 7. Tributary Discharge Rate Q_surf in m³/s
        # Q = (R_excess [mm/hr] / 1000 [m/mm] / 3600 [s/hr]) * Area [m²]
        q_surf = (r_excess / 3.6e6) * areas
        q_surf = np.round(q_surf, 4).astype(np.float32)

        # 8. Global Catchment Volume Budget (for dt = 1 hr)
        dt_hr = 1.0
        v_rain = float(np.sum((rain_arr / 1000.0) * areas * dt_hr))
        v_runoff = float(np.sum((r_excess / 1000.0) * areas * dt_hr))
        v_infil = float(np.sum((actual_infil_rate / 1000.0) * areas * dt_hr))
        v_dep = float(np.sum((actual_dep_rate / 1000.0) * areas * dt_hr))

        # Enforce strict volumetric consistency
        vol_discrepancy_pct = (abs(v_rain - (v_runoff + v_infil + v_dep)) / max(1e-3, v_rain)) * 100.0

        # Enriched outputs
        df.loc[:, "rainfall_intensity_mm_hr"] = np.round(rain_arr, 2)
        df.loc[:, "surface_runoff_rate_mm_hr"] = np.round(r_excess, 2)
        df.loc[:, "surface_runoff_inflow_m3_s"] = q_surf

        elapsed_ms = (time.perf_counter() - t_start) * 1000.0

        diagnostics = {
            "execution_time_ms": round(elapsed_ms, 2),
            "total_segments": n_segments,
            "amc_applied": df["amc_condition"].iloc[0] if "amc_condition" in df.columns else "AMC_II",
            "mean_rainfall_mm_hr": round(float(np.mean(rain_arr)), 2),
            "mean_runoff_rate_mm_hr": round(float(np.mean(r_excess)), 2),
            "mean_discharge_m3_s": round(float(np.mean(q_surf)), 4),
            "max_discharge_m3_s": round(float(np.max(q_surf)), 4),
            "mean_impervious_fraction": round(float(np.mean(f_imp)), 3),
            "mean_effective_infiltration_mm_hr": round(float(np.mean(f_soil)), 2),
            "catchment_rain_volume_m3": round(v_rain, 1),
            "catchment_runoff_volume_m3": round(v_runoff, 1),
            "catchment_infiltrated_volume_m3": round(v_infil, 1),
            "catchment_depression_volume_m3": round(v_dep, 1),
            "mass_balance_error_pct": round(vol_discrepancy_pct, 6),
            "mass_balance_passed": vol_discrepancy_pct < 0.01,
        }

        return RunoffResult(
            dataframe=df,
            runoff_rates_mm_hr=r_excess,
            discharge_m3_s=q_surf,
            total_rain_volume_m3=v_rain,
            total_runoff_volume_m3=v_runoff,
            total_infiltrated_volume_m3=v_infil,
            diagnostics=diagnostics
        )
