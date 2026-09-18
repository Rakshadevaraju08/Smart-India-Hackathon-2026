"""Layer 3: Physics-Informed AI Surrogate Engine (GCC / MoES 26085).

Authoritative public API for sub-second hydrodynamic nowcasting,
Relational Graph Convolutional Message-Passing (R-GCN), physical mass conservation enforcement,
and historical ground truth flood depth validation.
"""

from typing import TYPE_CHECKING, Any

from .benchmark_validator import BenchmarkValidator
from .graph_builder import StreetDrainageGraph
from .mass_conservation_loss import MassConservationConstraint
from .surrogate_model import HORIZONS_MIN, PIGNNSurrogateEngine

if TYPE_CHECKING:
    from .pipeline import Layer3Pipeline, Layer3Result

__all__ = [
    "StreetDrainageGraph",
    "PIGNNSurrogateEngine",
    "MassConservationConstraint",
    "BenchmarkValidator",
    "Layer3Pipeline",
    "Layer3Result",
    "HORIZONS_MIN",
]


def __getattr__(name: str) -> Any:
    if name in ("Layer3Pipeline", "Layer3Result"):
        from .pipeline import Layer3Pipeline, Layer3Result
        if name == "Layer3Pipeline":
            return Layer3Pipeline
        return Layer3Result
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
