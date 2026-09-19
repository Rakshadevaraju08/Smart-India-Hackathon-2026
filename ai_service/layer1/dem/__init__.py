"""Layer 1: Digital Elevation Model (DEM) & Hydro-Topography Sub-Package.

Modular sub-package responsible for:
  1. ISRO Cartosat-1 30m DEM mosaicking, EGM96 geoid calibration, and UTM Zone 44N reprojection.
  2. InSAR coastal land subsidence vertical displacement adjustment.
  3. Stormwater Drainage (SWD) Network, canal, and railway underpass hydro-conditioning.
  4. 8-neighborhood Horn slope gradient (S_0), aspect, D8 flow accumulation, and Topographic Wetness Index (TWI).
  5. Street-level elevation and topographic sampling across all 7,894 GCC road segments.
"""

from .dem_builder import (
    DEFAULT_CHENNAI_BOUNDS_WGS84,
    DEFAULT_PIXEL_RES_M,
    DEFAULT_UTM_CRS,
    DEMBuilder,
    find_or_extract_file,
)
from .swd_network import (
    DEFAULT_BURN_DEPTHS,
    SWDNetworkManager,
)
from .hydro_conditioner import HydroConditioner
from .hydrologic_derivatives import HydrologicDerivatives
from .road_sampler import RoadElevationSampler

__all__ = [
    "DEMBuilder",
    "HydroConditioner",
    "HydrologicDerivatives",
    "RoadElevationSampler",
    "SWDNetworkManager",
    "find_or_extract_file",
    "DEFAULT_CHENNAI_BOUNDS_WGS84",
    "DEFAULT_UTM_CRS",
    "DEFAULT_PIXEL_RES_M",
    "DEFAULT_BURN_DEPTHS",
]
