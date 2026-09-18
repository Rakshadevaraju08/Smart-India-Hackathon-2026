"""
KAIROS Orchestration Subpackage.

Coordinates decoupled execution and high-performance in-memory coupling between
the independent layers of the KAIROS Urban Flood Nowcasting System:
  - Layer 0: Flat-Plane Atmospheric Nowcasting Engine
  - Layer 1: Cartosat-1 DEM, LULC Imperviousness & Soil Hydrology
  - Layer 2: Stormwater Drainage & Manhole Hydraulics
  - Layer 3: 2D Dynamic Inundation Solver
  - Layer 4: Tactical Evacuation Routing Engine
"""

from .coupler import (
    Layer0Layer1Coupler,
    CoupledResult,
    run_coupled_layer0_layer1,
)

__all__ = [
    "Layer0Layer1Coupler",
    "CoupledResult",
    "run_coupled_layer0_layer1",
]
