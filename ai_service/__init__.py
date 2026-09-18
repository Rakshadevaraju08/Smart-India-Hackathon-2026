"""AI Service Core Package for Urban Flood Nowcasting System."""

__all__ = [
    "run_coupled_layer0_layer1",
    "CoupledResult",
    "Layer0Layer1Coupler",
]


def __getattr__(name: str):
    if name in ("run_coupled_layer0_layer1", "CoupledResult", "Layer0Layer1Coupler"):
        from .orchestration import run_coupled_layer0_layer1, CoupledResult, Layer0Layer1Coupler
        if name == "run_coupled_layer0_layer1":
            return run_coupled_layer0_layer1
        elif name == "CoupledResult":
            return CoupledResult
        return Layer0Layer1Coupler
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
