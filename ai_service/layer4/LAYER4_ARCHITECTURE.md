# KAIROS Layer 4 Architecture

Layer 4 is the **Dynamic Safe Emergency Navigation & Critical Assets Safeguarding** module. It decouples street-level routing and flood-risk evaluation from the hydrodynamic forecasting engines (Layer 0–3) through a strict contract.

## System Components

### 1. Road Graph
The foundation is a NetworkX `MultiDiGraph` generated from OpenStreetMap. It maps the physical topology of the Greater Chennai Corporation (GCC). Node snapping is accelerated using a `scipy.spatial.cKDTree`.

### 2. Layer3Result Contract
Layer 4 does not compute raw hydrodynamic flood levels. It consumes a strongly-typed `Layer3Result` contract providing time-indexed depth predictions (`depth_T+15m_cm`, etc.) and binary impassability flags for each `segment_id`.

### 3. Layer3 Provider
A provider pattern supplies the `Layer3Result` to Layer 4. Currently, this relies on a `MockLayer3Provider` for development. Because of this decoupled dependency injection, the routing algorithms do not know or care where the data comes from. **The routing algorithm does not need to change when the provider is replaced.**

### 4. Temporal Depth Calculation
The `TemporalFloodDepthService` interpolates the discrete Layer 3 forecast horizons (e.g., T+15, T+30) into continuous `effective_depth_cm` at any arbitrary arrival time. It also adds an uncertainty safety margin (e.g., +10%).

### 5. Risk / WHPF (Water Hazard Penalty Function)
The `FloodHazardEvaluator` determines the dynamic cost of traversing a flooded segment. It applies non-linear penalties as the effective depth approaches a specific vehicle's wading limit (e.g., 30cm for passenger cars, 45cm for ambulances), acting as the heuristic weight for routing.

### 6. Time-Dependent A*
The `DynamicRoutingEngine` implements a modified A* search. Crucially, edge costs are evaluated *at the vehicle's calculated arrival time* rather than statically at departure, ensuring the route avoids flash floods that happen while the vehicle is en route.

### 7. Underpass Handling
Underpasses (`is_underpass=True`) evaluate a configurable lookahead window (e.g., 30 minutes) beyond the arrival time. If the underpass is forecasted to exceed safe wading limits at any point during this window, it is aggressively penalized/blocked to prevent trapping vehicles in rapid inundation zones.

### 8. Route Metrics
The routing engine tracks overarching safety KPIs per route: total hazard cost, physical travel time, maximum effective depth encountered, and underpasses safely avoided.

### 9. Critical Asset Monitoring
The `CriticalAssetsMonitor` tracks 20 critical TANGEDCO substations. It projects the surrounding `segment_id`'s flood forecast against the substation's ground elevation and plinth height, categorizing risk into `SAFE`, `AT_RISK`, `CRITICAL`, or `UNKNOWN`. 

### 10. Pipeline / Service Orchestration
`Layer4Service` ties together the dependency-injected Provider, Graph, Monitor, and Routing Engine into unified operations: `route()` and `get_asset_status()`.

### 11. API 
FastAPI exposes the orchestration service to the web via standard HTTP REST endpoints (`POST /route`, `GET /assets/status`), handling validation and serialization.

### 12. Frontend Integration Boundary
The API forms the strict boundary for the frontend. The frontend sends coordinate/vehicle requests and renders the returned geometry and safety KPIs on map interfaces.

---

## Architecture Flow

### CURRENT FLOW (Development)
```
Layer 3 Mock Provider
         ↓
    Layer3Result
         ↓
  Layer 4 Service (A* / Assets)
```

### FUTURE FLOW (Production)
```
 Real Layer 3 (Manning-Saint-Venant)
         ↓
    Layer3Result
         ↓
  Layer 4 Service (A* / Assets)
```
