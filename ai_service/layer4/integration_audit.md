# Layer 4 Final Integration Audit

This document outlines the actual public interfaces and architecture of the KAIROS Layer 4 system prior to final API integration. No business logic or algorithmic design changes have been made in this step.

## 1. Existing Files and Responsibilities
- `road_graph.py`: Loads and parses the road network from `.pkl` into a NetworkX `MultiDiGraph`.
- `layer3_mock.py`: Defines the strictly typed `Layer3Result` contract and the `MockLayer3Provider`.
- `temporal_flood.py`: Owns `TemporalFloodDepthService` which interpolates depths across the 6 forecast horizons and applies safety uncertainty margins.
- `vehicle_risk.py`: (`risk_cost_evaluator`) Evaluates Water Hazard Penalty Function (WHPF) costs for specific vehicles based on flood depths.
- `routing_engine.py`: Owns `DynamicRoutingEngine`, handling KDTree spatial snapping and time-dependent A* safe routing.
- `critical_assets_monitor.py`: Owns `CriticalAssetsMonitor`, evaluating plinth vulnerability for TANGEDCO substations loaded from CSV.
- `pipeline.py`: The master orchestration class (`Layer4Pipeline`) tying the above components together via independent CLI methods.
- `api.py`: A FastAPI server that currently serves Layer 0 (`/api/nowcast`) but is completely isolated from Layer 4.

## 2. Exact Public Interfaces
**A. What function/class initializes Layer 4?**
The `Layer4Pipeline(graph_path: str)` class in `pipeline.py` initializes the routing graph and instantiates the `DynamicRoutingEngine` and `CriticalAssetsMonitor`.

**B. What function/class performs routing?**
`DynamicRoutingEngine.solve_route(request: RouteRequest)`

**C. What exact arguments does routing currently require?**
It strictly requires a `RouteRequest` dataclass containing:
- `origin_lon` (float)
- `origin_lat` (float)
- `dest_lon` (float)
- `dest_lat` (float)
- `vehicle_type` (str)
- `departure_time_minutes` (float)
- `temporal_service` (`TemporalFloodDepthService`)

**D. What exact object/result does routing return?**
It returns a `RoutingResult` dataclass containing properties like `success` (bool), `nodes_explored` (int), `total_physical_travel_time_seconds` (float), `total_hazard_cost_seconds` (float), `total_distance_m` (float), `arrival_time` (float), `blocked_edges` (int), `path` (List[str]), and `failure_reason` (str).

**H. What exact function/class exposes critical asset monitoring?**
`CriticalAssetsMonitor.evaluate_substations(temporal_service: TemporalFloodDepthService)`

**I. What exact object/result does the substation monitor return?**
A `List[SubstationMonitoringResult]`. Each dataclass contains precise metrics like `substation_id`, `flood_status` (SAFE/AT_RISK/CRITICAL/UNKNOWN), `maximum_effective_depth`, `uncertainty_flag`, and `explanation`.

## 3. Existing API / Server Structure
**K. Is there already a FastAPI/Flask application?**
Yes. `ai_service/api.py` contains an active FastAPI application configured with CORS, static file mounts, and existing endpoints (`/api/health`, `/api/nowcast`). We must absolutely reuse this existing FastAPI server.

**L. Where should API schemas live?**
Based on the existing project structure (where Layer 0 schemas are inline in `api.py` or abstracted natively), the Pydantic request/response models for Layer 4 (e.g., `/route` and `/assets/status`) should be added directly to `ai_service/api.py` to maintain the microservice pattern, or abstracted to a new `ai_service/schemas.py` if they become too verbose.

## 4. Current Layer 3 Dependency Flow
**E. How does routing obtain Layer 3 predictions?**
Inside the A* search loop, for every candidate edge, the engine calls `temporal_service.get_effective_depth(segment_id, arrival_time)`. This returns a dictionary containing the time-interpolated `effective_depth_cm`.

**F. How is the Layer3Result interface injected?**
1. A provider yields a `Layer3Result`.
2. The `Layer3Result` is passed into the constructor of `TemporalFloodDepthService`.
3. The `TemporalFloodDepthService` is embedded directly into the `RouteRequest` dataclass.
4. The `RouteRequest` is passed to the routing engine.

**G. How is the mock provider selected?**
Currently, `MockLayer3Provider` is strictly hardcoded inside the `Layer4Pipeline.run_routing()` and `run_asset_monitor()` orchestration methods.

## 5. Integration Problems to Fix Before Implementation
1. **Hardcoded Mock Provider:** The `MockLayer3Provider` is tightly coupled and instantiated *twice* directly inside the `pipeline.py` execution methods (once for routing, once for assets). `Layer4Pipeline` should accept a `Layer3ProviderInterface` via dependency injection during initialization or execution, so we can swap it for a real provider without touching the orchestration code.
2. **Duplicate Graph Loading:** The mock provider accepts `self.graph` to generate its predictions. This is acceptable for the mock, but the real provider will likely not need the routing graph. The injection pattern must be decoupled.
3. **API Instantiation:** Instantiating `Layer4Pipeline` inside the FastAPI endpoint will reload the massive 35MB routing graph on every single HTTP request. `Layer4Pipeline` must be instantiated *once* globally on API startup (similar to the existing `_pipeline` singleton for Layer 0) and reused.

## 6. Recommended Files to Modify in the Next Step
1. **`ai_service/pipeline.py`**: Refactor `Layer4Pipeline` to accept `Layer3ProviderInterface` as an injected dependency rather than hardcoding the mock provider. Consolidate so Layer 3 fetching happens once per API request, shared between routing and monitoring if needed.
2. **`ai_service/api.py`**: Add the Layer 4 global singleton, define Pydantic models (e.g., `RouteRequestSchema`, `AssetStatusResponse`), and expose the strictly orchestrating `/api/v1/route` and `/api/v1/assets/status` endpoints.
