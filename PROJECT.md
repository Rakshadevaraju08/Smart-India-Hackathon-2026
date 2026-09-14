# Project: Urban Flood Nowcasting System Web GIS Command Twin (SIH 2026 PS 26085)

## Architecture
The Urban Flood Nowcasting System Web GIS Command Twin is an ultra-responsive, zero-dependency, standalone Web GIS application calibrated for Greater Chennai Corporation. It integrates hydro-conditioned elevation models, live-recalculated street inundation, dynamic solid waste clogging simulations, Saint-Venant orifice backflow hydraulics, and first responder emergency evacuation routing.

### High-Level Components
1. **Presentation & GIS Shell (`frontend/index.html`)**:
   - Dark tactical CartoDB Dark Matter / MapLibre tile basemap centered on Chennai metropolitan core (`[13.04, 80.24]`, zoom 12-13).
   - Telemetry Header: Live IMD Dual-Pol Radar telemetry badge (Meenambakkam 10-min scan), Storm scenario selector (Michaung 95 mm/h, Monsoon 40 mm/h, Convective 20 mm/h), center-view reset.
   - Executive KPI Strip: Inundated Road Count, Surcharging Manhole Nodes ($HGL > Z_{ground}$), Critical Substations at Plinth Risk, Peak Rain Rate, Max Inundation Depth.
   - GIS Map Viewport: Leaflet/MapLibre canvas/SVG rendering 500+ authentic Chennai road vectors, 25 animated pulsing red fountain backflow manhole hotspots, 20 TANGEDCO 230kV/110kV substations, and dual evacuation polylines.
   - Nowcast Dock: 0–180 min time slider, 1.5–2s auto-advance playback loop, dynamic SVG hyetograph mini-sparkline, and real-time depth re-evaluator.
   - Surcharge & Evacuation Sidebar:
     - Tab 1: First Responder A* Evacuation Routing Simulator with 4 vehicle clearance profiles, scenario selector, dual polylines (submerged bottleneck vs glowing green safe corridor), and turn-by-turn navigation cues.
     - Tab 2: Surcharge Diagnostic Inspector with Saint-Venant orifice hydraulics ($D, n, Q_0, Q_{eff}, \Delta h, Q_{backflow}$) and Solid Waste Dynamic Clogging Slider ($\mu_{clog} \in [0\%, 80\%]$).
     - Tab 3: Cloud Export Modal with 1-click React/Vite/Tailwind export prompt for Bolt.new.
2. **Geospatial & Hydraulic Data Layer (`frontend/data/chennai_flood_data.js`)**:
   - Bundled globally as `window.CHENNAI_FLOOD_DATA` to ensure 100% offline, zero-npm, zero-server standalone execution without `file:///` CORS errors.
   - Contains 521 authentic Chennai road segments derived from Greater Chennai Corporation 7,894 OSM vector geometries (`00_master_flooded_street_segments.csv`).
   - 25 field-audited chronic surcharge blockage hotspots from civic grievance logs.
   - 20 TANGEDCO 230kV/110kV substations with authentic plinth heights and coordinates.
   - 2 full routing scenarios (Velachery $\rightarrow$ Guindy Trauma Hospital, Kilpauk KMC $\rightarrow$ Chennai Central).
3. **Execution & Launcher Layer (`launch_dashboard.bat`)**:
   - 1-click Windows batch launcher invoking default web browser with `file:///` URI, running with zero dependencies.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Dark Tactical Basemap | CartoDB Dark Matter / MapLibre basemap centered on Chennai core | M1 | ORIGINAL_REQUEST §R1 |
| 2 | IMD Radar Telemetry Header | Live Doppler status badge (Meenambakkam 10-min scan, reflectivity/rain rate) | M1 | ORIGINAL_REQUEST §R1 |
| 3 | Storm Scenario Selector | Cyclone Michaung (95 mm/h), Monsoon (40 mm/h), Convective (20 mm/h) | M1 | ORIGINAL_REQUEST §R1 |
| 4 | Executive KPI Strip | Inundated roads, surcharging nodes, plinth hazards, peak rain rate, max depth | M1 | ORIGINAL_REQUEST §R1 |
| 5 | Authentic Chennai Road Vectors | 500+ genuine Chennai road vectors color-coded by NDMA thresholds | M2 | ORIGINAL_REQUEST §R2 |
| 6 | NDMA 4-Tier Inundation Styling | <10cm Green, 10-25cm Amber, 25-50cm Orange, >50cm Critical Red | M2 | ORIGINAL_REQUEST §R2 |
| 7 | Pulsing Fountain Surcharge Markers | Animated pulsing red markers on surcharging manholes with fountain ripple | M2 | ORIGINAL_REQUEST §R2 |
| 8 | TANGEDCO Substation Risk Pins | 230kV / 110kV substations with plinth flood risk alert badges and popups | M2 | ORIGINAL_REQUEST §R2 |
| 9 | Interactive Layer Switcher | Toggle controls for Roads, Surcharging Nodes, Substations, Evacuation Routes | M2 | ORIGINAL_REQUEST §R2 |
| 10 | 0–180m Nowcast Time Slider | 6 discrete intervals: T+0, T+30, T+60, T+90 (Peak), T+120, T+180m | M3 | ORIGINAL_REQUEST §R3 |
| 11 | Auto-Advance Playback Controller | Play/pause button auto-cycling time steps every 1.5–2.0 seconds | M3 | ORIGINAL_REQUEST §R3 |
| 12 | Dynamic Hyetograph SVG Sparkline | Visual SVG/canvas mini-hyetograph showing precipitation progression | M3 | ORIGINAL_REQUEST §R3 |
| 13 | 60 FPS Polyline Update Engine | High-performance cached geometry updates on slider scrub without DOM re-alloc | M3 | ORIGINAL_REQUEST Acceptance |
| 14 | Vehicle Clearance Threshold Selector | Ambulance (30cm), NDRF Truck (45cm), Sedan (18cm), 2-Wheeler (10cm) | M4 | ORIGINAL_REQUEST §R4 |
| 15 | Dynamic Vehicle Clearance Warnings | Real-time alerts when road inundation exceeds selected vehicle limit | M4 | ORIGINAL_REQUEST §R4 |
| 16 | Scenario Route Selector | Velachery $\rightarrow$ Guindy and Kilpauk KMC $\rightarrow$ Chennai Central | M4 | ORIGINAL_REQUEST §R4 |
| 17 | Dual Polyline Route Display | Direct standard route (dashed red) vs Kairos A* safe bypass (glowing green) | M4 | ORIGINAL_REQUEST §R4 |
| 18 | Bottleneck & Hydrolock Diagnostics | Identification of submerged underpass bottlenecks and engine failure risk | M4 | ORIGINAL_REQUEST §R4 |
| 19 | Turn-by-Turn Safe Navigation Cues | Turn-by-turn guidance, distance, ETA, and detour metrics for both scenarios | M4 | ORIGINAL_REQUEST §R4 |
| 20 | Asset Diagnostic Card | Clicking road or manhole populates full hydraulic parameters | M5 | ORIGINAL_REQUEST §R5 |
| 21 | Authentic Hydraulic Equations | Manning capacity $Q_0$, effective capacity $Q_{eff}$, surcharge head $\Delta h$ | M5 | ORIGINAL_REQUEST §R5 |
| 22 | Saint-Venant Orifice Backflow | $Q_{backflow} = C_d A \sqrt{2g \Delta h}$ with $C_d=0.62$, $A=\pi D^2/4$ | M5 | ORIGINAL_REQUEST §R5 |
| 23 | Solid Waste Clogging Slider | Dynamic $\mu_{clog}$ slider from 0% to 80% scaling city flood depths | M5 | ORIGINAL_REQUEST §R5 |
| 24 | Live Clogging-Asset Synchronization | Clogging slider adjustments dynamically update active asset diagnostic values | M5 | ORIGINAL_REQUEST §R5 |
| 25 | Surcharging Manhole Inspection | Clicking surcharging manhole markers populates diagnostic card | M5 | ORIGINAL_REQUEST §R5 |
| 26 | Standalone Browser Execution | Zero npm, zero server dependencies, clean execution via `launch_dashboard.bat` | M6 | ORIGINAL_REQUEST §R6 |
| 27 | Clean Component Architecture | Well-organized, modular HTML/CSS/JS frontend structure | M6 | ORIGINAL_REQUEST §R6 |
| 28 | Bolt.new 1-Click Export Prompt | Copy-paste React/Vite/Tailwind export prompt for 1-click cloud deployment | M6 | ORIGINAL_REQUEST §R6 |
| 29 | Comprehensive E2E Verification | 4-Tier requirement-driven opaque-box test suite passing 100% | M7 | Dual-Track Acceptance |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Geospatial & Hydraulic Asset Pipeline | Extract 500+ authentic Chennai road WKT geometries, 20 TANGEDCO substations with plinths, and 25 verified surcharge hotspots into `chennai_flood_data.js` | none | DONE |
| M2 | Tactical GIS Command Shell & Telemetry | Full-viewport dark tactical interface, IMD radar telemetry header, storm selector, dynamic KPI strip, 4-tier NDMA styling, pulsing fountain markers, layer toggles | M1 | DONE |
| M3 | Dynamic Nowcast Time Engine & 60 FPS Optimization | 0-180m time slider, auto-advance play/pause loop, dynamic SVG hyetograph sparkline, cached polyline updates for 60 FPS | M1 | DONE |
| M4 | A* Emergency Evacuation Routing Simulator | Vehicle clearance selectors (4 types) with dynamic warning badges, scenario route selector, dual polylines (submerged bottleneck vs safe green corridor), and turn-by-turn guidance sync | M1 | DONE |
| M5 | Surcharge Hydraulics, Diagnostic Inspector & Clogging | Interactive asset card for roads and manholes, Manning capacity, Saint-Venant orifice backflow equation ($Q_{backflow} = C_d A \sqrt{2g \Delta h}$), dynamic clogging slider (0-80%) live-syncing asset card | M1 | DONE |
| M6 | Standalone Packaging, Launcher & Bolt.new Export | Clean zero-npm execution, verified `launch_dashboard.bat`, and interactive copy-paste modal for 1-click Bolt.new React/Vite/Tailwind export | M2, M3, M4, M5 | DONE |
| M7 | E2E Testing Suite Track | Independent requirement-driven 4-tier test runner (Tiers 1-4: 5xN Feature, 5xN Boundary, Pairwise, Real-world) publishing `TEST_READY.md` | none | DONE |
| M8 | Final Integration, Adversarial Hardening & Forensic Audit | Pass 100% E2E test suite, execute Tier 5 adversarial testing, Forensic Integrity Audit, and deliver final verified project | M6, M7 | DONE |

## Interface Contracts

### Data Contract (`chennai_flood_data.js` $\rightarrow$ `index.html`)
- `window.CHENNAI_FLOOD_DATA.segments`: Array of objects:
  ```js
  {
    id: "STR_...",
    name: "Road Name",
    coordinates: [[lat, lon], [lat, lon], ...], // Genuine WKT LineString coordinates
    base_elevation: Float, // Meters above MSL
    base_depths: [d0, d30, d60, d90, d120, d180], // cm at default scenario
    diameter_mm: Integer, // Drainage conduit diameter in mm (e.g. 900)
    manning_n: 0.015,
    q0_capacity: Float // m^3/s theoretical capacity
  }
  ```
- `window.CHENNAI_FLOOD_DATA.surcharging_manholes`: Array of objects:
  ```js
  {
    id: "MH_...",
    name: "Location / Landmark",
    lat: Float,
    lng: Float,
    ground_elevation: Float, // Z_ground in meters
    base_hgl: [h0, h30, h60, h90, h120, h180], // HGL elevation in meters
    diameter_mm: Integer, // Manhole cover diameter (e.g. 600 mm)
    discharge_coeff: 0.62
  }
  ```
- `window.CHENNAI_FLOOD_DATA.substations`: Array of 20 objects:
  ```js
  {
    id: "SS_...",
    name: "Substation Name",
    lat: Float,
    lng: Float,
    voltage_kv: Integer, // 230 or 110
    elevation_m: Float,
    plinth_height_cm: Float,
    risk_level: "Safe" | "Warning" | "Critical"
  }
  ```
- `window.CHENNAI_FLOOD_DATA.routing_scenarios`: Map of scenario keys (`velachery_guindy`, `kilpauk_central`):
  ```js
  {
    name: String,
    origin: { name: String, coords: [lat, lng] },
    destination: { name: String, coords: [lat, lng] },
    direct_route: {
      distance_km: Float,
      max_depth_cm: Float,
      bottleneck_location: String,
      warning: String,
      coordinates: [[lat, lng], ...]
    },
    safe_route: {
      distance_km: Float,
      max_depth_cm: Float,
      detour_minutes: Float,
      eta_minutes: Float,
      coordinates: [[lat, lng], ...],
      turn_by_turn: [String, ...]
    }
  }
  ```

### Hydraulic Engine Contract (`index.html`)
- `calculateEffectiveDepth(baseDepth, clogMultiplier, scenarioMultiplier)`: Returns dynamically adjusted flood depth in cm.
- `calculateManholeSurcharge(manhole, tStep, clogMultiplier, scenarioMultiplier)`:
  - $\text{HGL} = \text{base\_hgl}[tStep] \cdot (1 + 0.3 \cdot \mu_{clog}) \cdot \text{scenarioMultiplier}$
  - $\Delta h = \max(0, \text{HGL} - Z_{ground})$
  - $Q_{backflow} = C_d \cdot (\pi D^2 / 4) \cdot \sqrt{2 \cdot 9.81 \cdot \Delta h}$ in $\text{m}^3/\text{s}$.
- `evaluateVehicleClearance(depthCm, vehicleType)`:
  - Vehicle limits: ambulance = 30cm, heavy = 45cm, car = 18cm, twowheeler = 10cm.
  - Returns `{ safe: Boolean, clearanceCm: Float, marginCm: Float, warning: String }`.

## Code Layout
- `frontend/index.html`: Tactical Web GIS command interface, Leaflet/MapLibre map instance, telemetry panels, diagnostic card, A* routing simulator, and Bolt.new modal.
- `frontend/data/chennai_flood_data.js`: Unified authentic geospatial and hydraulic datasets for Greater Chennai Corporation.
- `launch_dashboard.bat`: 1-click Windows launcher.
- `tests/e2e/`: Automated E2E test runner and test case definitions.
- `tests/e2e/test_runner.py`: Python-based opaque-box requirement and DOM validation test runner.
