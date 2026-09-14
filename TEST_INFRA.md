# E2E Test Infra: Urban Flood Nowcasting System Web GIS Command Twin

## Test Philosophy
- Opaque-box, requirement-driven. Derived strictly from `ORIGINAL_REQUEST.md` and user specifications, independent of internal implementation artifacts.
- Methodology: Category-Partition + Boundary Value Analysis (BVA) + Pairwise Combinatorial Testing + Real-World Workload Testing.
- Verification mechanism: Direct headless / DOM inspection & JS evaluation executing in Python (`tests/e2e/test_runner.py`) without requiring node modules or external servers.

## Feature Inventory & Test Mapping
| # | Feature | Source | Tier 1 (Coverage) | Tier 2 (Boundaries) | Tier 3 (Pairwise) | Tier 4 (Workload) |
|---|---------|--------|:-----------------:|:-------------------:|:-----------------:|:-----------------:|
| 1 | Dark Tactical Basemap & Shell | ORIGINAL_REQUEST §R1 | 5 tests | 5 tests | ✓ | ✓ |
| 2 | IMD Radar Telemetry Header | ORIGINAL_REQUEST §R1 | 5 tests | 5 tests | ✓ | ✓ |
| 3 | Storm Scenario Selector (3 storms) | ORIGINAL_REQUEST §R1 | 5 tests | 5 tests | ✓ | ✓ |
| 4 | Executive KPI Strip (5 metrics) | ORIGINAL_REQUEST §R1 | 5 tests | 5 tests | ✓ | ✓ |
| 5 | Authentic Chennai Road Vectors (500+) | ORIGINAL_REQUEST §R2 | 5 tests | 5 tests | ✓ | ✓ |
| 6 | NDMA 4-Tier Depth Styling | ORIGINAL_REQUEST §R2 | 5 tests | 5 tests | ✓ | ✓ |
| 7 | Pulsing Fountain Surcharge Markers | ORIGINAL_REQUEST §R2 | 5 tests | 5 tests | ✓ | ✓ |
| 8 | TANGEDCO Substation Risk Alerts | ORIGINAL_REQUEST §R2 | 5 tests | 5 tests | ✓ | ✓ |
| 9 | Interactive Layer Switcher | ORIGINAL_REQUEST §R2 | 5 tests | 5 tests | ✓ | ✓ |
| 10 | 0–180m Nowcast Time Slider (6 steps)| ORIGINAL_REQUEST §R3 | 5 tests | 5 tests | ✓ | ✓ |
| 11 | Auto-Advance Playback Controller | ORIGINAL_REQUEST §R3 | 5 tests | 5 tests | ✓ | ✓ |
| 12 | Dynamic Hyetograph SVG Sparkline | ORIGINAL_REQUEST §R3 | 5 tests | 5 tests | ✓ | ✓ |
| 13 | 60 FPS Polyline Scrub Performance | Acceptance Criteria | 5 tests | 5 tests | ✓ | ✓ |
| 14 | Vehicle Clearance Threshold Selector| ORIGINAL_REQUEST §R4 | 5 tests | 5 tests | ✓ | ✓ |
| 15 | Dynamic Vehicle Warning Evaluation | Acceptance Criteria | 5 tests | 5 tests | ✓ | ✓ |
| 16 | Scenario Route Selector (2 routes) | ORIGINAL_REQUEST §R4 | 5 tests | 5 tests | ✓ | ✓ |
| 17 | Dual Polyline Route Display | ORIGINAL_REQUEST §R4 | 5 tests | 5 tests | ✓ | ✓ |
| 18 | Bottleneck & Hydrolock Diagnostics | ORIGINAL_REQUEST §R4 | 5 tests | 5 tests | ✓ | ✓ |
| 19 | Turn-by-Turn Safe Navigation Cues | ORIGINAL_REQUEST §R4 | 5 tests | 5 tests | ✓ | ✓ |
| 20 | Asset Diagnostic Card (Road/Manhole)| ORIGINAL_REQUEST §R5 | 5 tests | 5 tests | ✓ | ✓ |
| 21 | Authentic Hydraulic Calculations | ORIGINAL_REQUEST §R5 | 5 tests | 5 tests | ✓ | ✓ |
| 22 | Saint-Venant Orifice Backflow Eq | ORIGINAL_REQUEST §R5 | 5 tests | 5 tests | ✓ | ✓ |
| 23 | Solid Waste Clogging Slider (0–80%) | ORIGINAL_REQUEST §R5 | 5 tests | 5 tests | ✓ | ✓ |
| 24 | Live Clogging-Asset Live Sync | ORIGINAL_REQUEST §R5 | 5 tests | 5 tests | ✓ | ✓ |
| 25 | Surcharging Manhole Click Handling | Acceptance Criteria | 5 tests | 5 tests | ✓ | ✓ |
| 26 | Standalone Local File Execution | ORIGINAL_REQUEST §R6 | 5 tests | 5 tests | ✓ | ✓ |
| 27 | Clean Architecture & 0 Console Errors| Acceptance Criteria | 5 tests | 5 tests | ✓ | ✓ |
| 28 | Bolt.new 1-Click Export Prompt | ORIGINAL_REQUEST §R6 | 5 tests | 5 tests | ✓ | ✓ |
| 29 | Windows 1-Click Batch Launcher | ORIGINAL_REQUEST §R6 | 5 tests | 5 tests | ✓ | ✓ |

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Target |
|---|----------|--------------------|--------|
| 1 | Cyclone Michaung Emergency Ambulance Dispatch | F3, F4, F6, F10, F14, F15, F16, F17, F18, F19 | 108 Ambulance safely navigates Velachery to Guindy Trauma Hospital avoiding 52cm underpass flood |
| 2 | Heavy NDRF Rescue Truck Monsoon Operations | F3, F5, F7, F8, F14, F15, F16, F17, F19 | NDRF Truck navigates Kilpauk to Chennai Central traversing up to 45cm clearance |
| 3 | Solid Waste Drain Blockage Impact Demonstration | F10, F20, F21, F22, F23, F24, F25 | Raising clogging slider to 80% causes surge in manhole backflow and turns amber roads to red |
| 4 | Grid Resiliency & Substation Hazard Evacuation | F4, F7, F8, F9, F10, F20 | Monitoring Velachery & Perungudi 230kV substations as plinth flood risks escalate at T+90 peak |
| 5 | Command Center Full Offline Drill & Cloud Export | F1, F2, F11, F12, F26, F27, F28, F29 | 1-click batch launcher start, continuous 1.5s playback, hyetograph visual check, copy Bolt.new prompt |

## Coverage Thresholds
- Tier 1: ≥ 5 tests per feature (29 × 5 = 145 tests)
- Tier 2: ≥ 5 boundary tests per feature (29 × 5 = 145 tests)
- Tier 3: ≥ 29 pairwise cross-feature tests
- Tier 4: ≥ 5 end-to-end realistic operational scenarios
- Total test target: ≥ 324 automated test checks in `tests/e2e/test_runner.py`
