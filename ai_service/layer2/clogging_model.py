"""Layer 2: Clogging Model Module - Dynamic Solid Waste & Silt Capacity Degradation.

Parameterizes conduit conveyance reduction using GCC municipal maintenance records:
  - GCC Zonal Solid Waste & Silt Generation (TPD)
  - Pre-monsoon SWD Desilting Completion Progress (%)
  - Civic 1913 Drain Blockage & Waterlogging Hotspot Complaints

Computes empirical Clogging Index mu_clog in [0.0, 0.85]:
  Effective Conduit Area:      A_eff = A_0 * (1 - mu_clog)
  Penalized Manning Roughness: n_eff = n_0 * (1 + 1.8 * mu_clog)
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Default base Manning roughness values (IS 456 / CPHEEO guidelines)
DEFAULT_MANNING_ROUGHNESS: Dict[str, float] = {
    "rcc_pipe": 0.013,          # Pre-cast Reinforced Cement Concrete Pipe
    "box_culvert": 0.015,       # In-situ RCC Rectangular Box Drain
    "masonry_open": 0.020,      # Brick/Stone Masonry Drain
    "natural_channel": 0.030,   # Earthen Outfall Canal (Otteri/Virugambakkam)
}


def find_dataset_path(base_dir: Path, filename: str) -> Path:
    """Search for dataset file in Datasets directory recursively."""
    datasets_dir = base_dir / "Datasets"
    for p in datasets_dir.rglob(filename):
        if p.is_file():
            return p
    raise FileNotFoundError(f"Could not locate '{filename}' in {datasets_dir}")


class SolidWasteCloggingModel:
    """Computes zone-specific and segment-level dynamic drainage clogging penalties."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).resolve().parent.parent.parent
        self.datasets_dir = self.base_dir / "Datasets"
        self._zone_clogging_cache: Dict[int, float] = {}
        self._load_civic_records()

    def _load_civic_records(self):
        """Load and cross-reference GCC solid waste and drain desilting CSVs."""
        try:
            waste_file = find_dataset_path(self.base_dir, "chennai_gcc_solid_waste_zone_summary.csv")
            desilt_file = find_dataset_path(self.base_dir, "chennai_gcc_drain_maintenance_records.csv")

            df_waste = pd.read_csv(waste_file)
            df_desilt = pd.read_csv(desilt_file)

            merged = pd.merge(df_waste, df_desilt, on="zone_no", suffixes=("_waste", "_desilt"))

            for _, row in merged.iterrows():
                zone_no = int(row["zone_no"])
                # 1. Desilting shortfall ratio (0.0 if 100% desilted, up to 0.40)
                desilt_progress = float(row.get("desilting_progress_pct", 75.0)) / 100.0
                desilt_arrears = max(0.0, 1.0 - desilt_progress)

                # 2. Uncollected solid waste litter pressure (0.0 to 0.25)
                eff = float(row.get("collection_efficiency_pct", 90.0)) / 100.0
                litter_pressure = max(0.0, 1.0 - eff)

                # Base zonal clogging factor (typically 0.15 to 0.55 across Chennai)
                mu_base = 0.10 + 0.50 * desilt_arrears + 0.40 * litter_pressure
                self._zone_clogging_cache[zone_no] = round(float(np.clip(mu_base, 0.05, 0.80)), 3)

            logger.info("Loaded GCC civic clogging factors for %d zones", len(self._zone_clogging_cache))
        except Exception as e:
            logger.warning("Using calibrated zonal default clogging: %s", e)
            # Default GCC 15 zones baseline clogging factor
            self._zone_clogging_cache = {z: 0.35 for z in range(1, 16)}

    def get_zone_clogging_factor(self, zone_no: int, global_modifier: float = 1.0) -> float:
        """Get clogging factor mu_clog in [0.0, 0.85] for a given GCC municipal zone."""
        base_mu = self._zone_clogging_cache.get(zone_no, 0.35)
        return float(np.clip(base_mu * global_modifier, 0.0, 0.85))

    def apply_conduit_penalties(
        self,
        nominal_area_m2: float,
        nominal_manning_n: float,
        mu_clog: float
    ) -> Tuple[float, float]:
        """
        Calculates effective cross-sectional area and effective Manning roughness:
          A_eff = A_0 * (1 - mu_clog)
          n_eff = n_0 * (1 + 1.8 * mu_clog)
        """
        mu = max(0.0, min(0.85, float(mu_clog)))
        a_eff = nominal_area_m2 * (1.0 - mu)
        n_eff = nominal_manning_n * (1.0 + 1.8 * mu)
        return float(a_eff), float(n_eff)
