"""Layer 1: Soil Hydrology & Infiltration Model.

Classifies USDA/ICAR Hydrologic Soil Groups (HSG A/B/C/D) and dynamically calculates
effective infiltration capacity f_soil(t) modulated by Antecedent Moisture Conditions
(AMC I: Dry, AMC II: Normal, AMC III: Saturated) and shallow coastal water tables.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Antecedent Moisture Condition (AMC) Infiltration Adjustment Multipliers
AMC_INFILTRATION_MULTIPLIERS: Dict[str, float] = {
    "AMC_I": 1.35,    # Dry soil: high capillary suction head
    "AMC_II": 1.00,   # Baseline / average moisture condition
    "AMC_III": 0.40,  # Saturated condition: waterlogged pore space
}


class SoilHydrologyModel:
    """Evaluates soil classification and dynamic infiltration capacity across GCC."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).resolve().parent.parent.parent.parent
        self.datasets_dir = self.base_dir / "Datasets"
        self._cached_master_df: Optional[pd.DataFrame] = None

    @staticmethod
    def classify_hsg(ksat_mm_hr: float) -> str:
        """Classify soil into USDA/ICAR Hydrologic Soil Group based on K_sat."""
        if ksat_mm_hr >= 12.0:
            return "A"  # Sand, loamy sand (High infiltration)
        elif ksat_mm_hr >= 8.0:
            return "B"  # Sandy loam, loam (Moderate infiltration)
        elif ksat_mm_hr >= 4.5:
            return "C"  # Clay loam, shallow sandy clay (Slow infiltration)
        else:
            return "D"  # Clay, black cotton, marine alluvium (Very slow infiltration)

    @staticmethod
    def determine_amc(antecedent_rainfall_5day_mm: Optional[float] = None,
                      scenario: Optional[str] = None) -> str:
        """Determine Antecedent Moisture Condition from 5-day rain or scenario name."""
        if antecedent_rainfall_5day_mm is not None:
            if antecedent_rainfall_5day_mm < 35.0:
                return "AMC_I"
            elif antecedent_rainfall_5day_mm <= 53.0:
                return "AMC_II"
            else:
                return "AMC_III"

        scen_lower = (scenario or "").lower()
        if any(w in scen_lower for w in ["michaung", "2015", "deluge", "cyclone", "extreme"]):
            return "AMC_III"
        elif any(w in scen_lower for w in ["dry", "pre_monsoon"]):
            return "AMC_I"
        return "AMC_II"

    def _get_base_df(self, roads_df: Optional[pd.DataFrame]) -> pd.DataFrame:
        if roads_df is not None:
            return roads_df.copy()
        if self._cached_master_df is not None:
            return self._cached_master_df.copy()

        master_csv = self.datasets_dir / "chennai_unified_flood_master_dataset.csv"
        if not master_csv.exists():
            raise FileNotFoundError(f"Missing master road dataset: {master_csv}")
        self._cached_master_df = pd.read_csv(master_csv)
        return self._cached_master_df.copy()

    def compute_soil_attributes(
        self,
        roads_df: Optional[pd.DataFrame] = None,
        amc: Optional[str] = None,
        antecedent_5day_mm: Optional[float] = None,
        scenario: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Compute HSG classification and effective infiltration rate for all road segments.
        Vectorized numpy operations for sub-millisecond execution.
        """
        df = self._get_base_df(roads_df)
        n_segments = len(df)
        active_amc = amc or self.determine_amc(antecedent_5day_mm, scenario)
        amc_mult = AMC_INFILTRATION_MULTIPLIERS.get(active_amc, 1.0)

        # Ingestion of baseline infiltration rate K_sat
        if "soil_infiltration_rate_mm_hr" in df.columns:
            ksat = df["soil_infiltration_rate_mm_hr"].values.astype(np.float32)
        else:
            ksat = np.full(n_segments, 8.5, dtype=np.float32)

        # Vectorized HSG categorization
        conds = [ksat >= 12.0, ksat >= 8.0, ksat >= 4.5]
        choices = ["A", "B", "C"]
        hsg_arr = np.select(conds, choices, default="D")

        # Dynamic infiltration capacity: f_soil = K_sat * AMC_mult
        f_soil = ksat * amc_mult

        # Coastal water table shallow depth penalty:
        if "distance_to_coast_km" in df.columns and "elevation_m" in df.columns:
            dist_coast = df["distance_to_coast_km"].values
            elev = df["elevation_m"].values
            shallow_mask = (dist_coast < 1.5) & (elev < 3.5)
            f_soil = np.where(shallow_mask, f_soil * 0.50, f_soil)

        # Riparian canal / wetland waterlogging penalty (< 150m from major canal):
        if "distance_to_major_canal_m" in df.columns:
            dist_canal = df["distance_to_major_canal_m"].values
            canal_mask = dist_canal < 150.0
            f_soil = np.where(canal_mask, f_soil * 0.40, f_soil)

        # InSAR coastal ground subsidence compaction penalty (> 3.5 mm/yr):
        if "subsidence_rate_mm_yr" in df.columns:
            subsidence = df["subsidence_rate_mm_yr"].values
            sub_mask = subsidence > 3.5
            f_soil = np.where(sub_mask, f_soil * 0.85, f_soil)

        df.loc[:, "hydrologic_soil_group"] = hsg_arr
        df.loc[:, "baseline_ksat_mm_hr"] = np.round(ksat, 2)
        df.loc[:, "effective_infiltration_mm_hr"] = np.round(f_soil, 2)
        df.loc[:, "amc_condition"] = active_amc

        return df
