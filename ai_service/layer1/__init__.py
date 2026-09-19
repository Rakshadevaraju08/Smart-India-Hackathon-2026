"""Layer 1: 2D Micro-Topographical DEM, LULC & Runoff Engine (GCC / MoES 26085).

Authoritative public API for ISRO Cartosat-1 ingestion, UTM Zone 44N reprojection,
InSAR coastal subsidence calibration, hydro-conditioning (canal stream burning & underpasses),
hydraulic derivative calculation (slope, aspect, D8 flow), street-level elevation sampling,
and LULC / soil infiltration surface runoff generation.
"""

from typing import TYPE_CHECKING, Any

from .dem import (
    DEFAULT_CHENNAI_BOUNDS_WGS84,
    DEFAULT_PIXEL_RES_M,
    DEFAULT_UTM_CRS,
    DEMBuilder,
    HydroConditioner,
    HydrologicDerivatives,
    RoadElevationSampler,
    SWDNetworkManager,
    find_or_extract_file,
)
from .lulc import (
    ImperviousExtractor,
    SoilHydrologyModel,
    SurfaceRunoffGenerator,
    RunoffResult,
    Sentinel2Processor,
)
from . import dem
from . import lulc

if TYPE_CHECKING:
    from .pipeline import Layer1Pipeline, Layer1Result

__all__ = [
    "dem",
    "lulc",
    "DEMBuilder",
    "HydroConditioner",
    "HydrologicDerivatives",
    "RoadElevationSampler",
    "SWDNetworkManager",
    "ImperviousExtractor",
    "SoilHydrologyModel",
    "SurfaceRunoffGenerator",
    "RunoffResult",
    "Sentinel2Processor",
    "Layer1Pipeline",
    "Layer1Result",
    "DEFAULT_CHENNAI_BOUNDS_WGS84",
    "DEFAULT_UTM_CRS",
    "DEFAULT_PIXEL_RES_M",
    "find_or_extract_file",
]


def __getattr__(name: str) -> Any:
    if name in ("Layer1Pipeline", "Layer1Result"):
        from .pipeline import Layer1Pipeline, Layer1Result
        if name == "Layer1Pipeline":
            return Layer1Pipeline
        return Layer1Result
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
