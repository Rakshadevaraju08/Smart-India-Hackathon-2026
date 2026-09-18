"""Layer 4: Safe Emergency Navigation & Critical Asset Safeguarding.

Exports:
  - RiskCostEvaluator: Vehicle hydrodynamic impedance evaluator
  - VEHICLE_PROFILES: Dictionary of vehicle characteristics
  - DynamicRoutingEngine: Flood-aware route solver
  - CriticalAssetsMonitor: Electrical substation plinth monitor
  - Layer4Pipeline: Master orchestration pipeline
"""

import sys
from typing import Any

__all__ = [
    "RiskCostEvaluator",
    "VEHICLE_PROFILES",
    "DynamicRoutingEngine",
    "CriticalAssetsMonitor",
    "Layer4Pipeline",
]


def __getattr__(name: str) -> Any:
    if name == "RiskCostEvaluator" or name == "VEHICLE_PROFILES":
        from .risk_cost_evaluator import RiskCostEvaluator, VEHICLE_PROFILES
        return globals()[name]
    elif name == "DynamicRoutingEngine":
        from .routing_engine import DynamicRoutingEngine
        return DynamicRoutingEngine
    elif name == "CriticalAssetsMonitor":
        from .critical_assets_monitor import CriticalAssetsMonitor
        return CriticalAssetsMonitor
    elif name == "Layer4Pipeline":
        from .pipeline import Layer4Pipeline
        return Layer4Pipeline
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
