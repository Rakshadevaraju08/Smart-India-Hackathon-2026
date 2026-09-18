"""Layer 2: 1D Subsurface Stormwater Conduit & Surcharge Hydraulics Engine (GCC / MoES 26085).

Authoritative public API for Manning pipe flow, municipal solid waste clogging degradation,
drop-inlet weir/orifice capture, manhole HGL pressurization, and geyser surcharge backflow.
"""

from typing import TYPE_CHECKING, Any

from .clogging_model import DEFAULT_MANNING_ROUGHNESS, SolidWasteCloggingModel
from .conduit_flow import ConduitFlowEngine
from .drainage_graph import DrainageGraphNetwork
from .inlet_capture import InletCaptureEngine
from .manhole_surcharge import ManholeSurchargeEngine

if TYPE_CHECKING:
    from .pipeline import Layer2Pipeline, Layer2Result

__all__ = [
    "SolidWasteCloggingModel",
    "ConduitFlowEngine",
    "InletCaptureEngine",
    "ManholeSurchargeEngine",
    "DrainageGraphNetwork",
    "Layer2Pipeline",
    "Layer2Result",
    "DEFAULT_MANNING_ROUGHNESS",
]


def __getattr__(name: str) -> Any:
    if name in ("Layer2Pipeline", "Layer2Result"):
        from .pipeline import Layer2Pipeline, Layer2Result
        if name == "Layer2Pipeline":
            return Layer2Pipeline
        return Layer2Result
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
