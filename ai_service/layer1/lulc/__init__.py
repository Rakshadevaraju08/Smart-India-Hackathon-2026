"""Layer 1: LULC & Hydrologic Soil Runoff Subpackage.

Exposes:
  - ImperviousExtractor: Land cover impervious surface fraction and roughness
  - SoilHydrologyModel: USDA/ICAR HSG classification and dynamic AMC infiltration
  - SurfaceRunoffGenerator: Coupled physical surface runoff and discharge generator
  - RunoffResult: Structured execution output dataclass
"""

from .impervious_extractor import ImperviousExtractor
from .soil_hydrology import SoilHydrologyModel
from .runoff_generator import SurfaceRunoffGenerator, RunoffResult
from .sentinel2_processor import Sentinel2Processor

__all__ = [
    "ImperviousExtractor",
    "SoilHydrologyModel",
    "SurfaceRunoffGenerator",
    "RunoffResult",
    "Sentinel2Processor",
]
