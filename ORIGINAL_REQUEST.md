# Original User Request

## 2026-09-12T13:53:21Z

Build and polish a high-performance, full-viewport Web GIS Command Twin frontend for the Urban Flood Nowcasting System (SIH 2026 - Problem Statement 26085) calibrated for Greater Chennai Corporation (7,894 road segments).

Working directory: c:\Users\Gagan K S\Documents\SIH
Integrity mode: development

## Requirements

### R1. Tactical Emergency Web GIS Command Interface
- Full-viewport dark tactical theme (CartoDB Dark Matter / MapLibre GL tiles) centered on Chennai metropolitan core.
- Dynamic telemetry header featuring IMD Dual-Pol Radar status (10-min scan at Meenambakkam), storm scenario selector (Cyclone Michaung 95 mm/h peak, Monsoon 40 mm/h, Convective 20 mm/h), and center-view controls.
- Real-time Executive KPI strip tracking: Inundated Road Count, Surcharging Manhole Nodes (HGL > Z_ground), Critical Substations at Plinth Risk, Peak Rain Rate, and Max Flood Depth.

### R2. Spatial Inundation & Surcharge Diagnostic Map Layers
- 500+ authentic Chennai road vectors color-coded by water depth according to NDMA thresholds (<10cm green safe, 10-25cm amber caution, 25-50cm orange severe, >50cm critical red).
- Animated pulsing red markers on surcharging manholes with fountain backflow ripple animation.
- TANGEDCO 230kV / 110kV electrical substations with plinth flood risk alert pins.
- Interactive Layer Switcher allowing toggle of Roads, Surcharging Nodes, Substations, and Evacuation Routes.

### R3. Dynamic 0–180 Minute Nowcast Time Slider & Playback
- Interactive time-slider with tick marks at T+0 (Now), T+30m, T+60m, T+90m (Peak), T+120m, and T+180m.
- Play/Pause auto-advance animation button cycling through time steps every 1.5–2 seconds.
- Embedded storm rainfall hyetograph mini sparkline display showing precipitation intensity progression.
- Immediate recalculation and re-coloring of street inundation depths and surcharging nodes upon scrubbing.

### R4. First Responder A* Emergency Evacuation Routing Simulator
- Vehicle clearance threshold selector:
  - 🚑 108 Emergency Ambulance (Clearance limit: 30 cm)
  - 🚒 NDRF Heavy Rescue Truck / Bus (Clearance limit: 45 cm)
  - 🚗 Passenger Car / Sedan (Clearance limit: 18 cm)
  - 🛵 Two-Wheeler / Auto-Rickshaw (Clearance limit: 10 cm)
- Scenario route selector (e.g. Velachery Lake Colony to Guindy Trauma Hospital / Kilpauk KMC to Chennai Central).
- Dual polyline visualization:
  - Direct Standard Route: Red dashed line warning of submerged underpass bottlenecks (e.g. 52 cm depth) and engine hydrolock failure.
  - Kairos A* Safe Bypass: Solid glowing green polyline routing via elevated ridge corridors (max depth < 10 cm) with ETA, detour time (+3.2 min), and turn-by-turn navigation cues.

### R5. Surcharge Diagnostic Inspector & Dynamic Solid Waste Clogging Simulator
- Asset Diagnostic Card: Clicking any road segment or manhole marker populates nominal diameter (D), Manning roughness (n), theoretical capacity (Q_0), effective capacity (Q_eff = Q_0(1 - mu)), HGL surcharge head (Delta h), and backflow rate (Q_backflow = C_d A sqrt(2g Delta h)).
- Interactive Solid Waste Dynamic Clogging Slider (mu_clog from 0% to 80%): Real-time scaling that demonstrates how plastic debris and uncleaned drains directly increase city-wide flood depth.

### R6. Standalone Local Execution & Cloud-Ready Export
- Self-contained execution via local file (frontend/index.html) and 1-click Windows launcher (launch_dashboard.bat) requiring zero npm install or server dependencies.
- Clean component architecture and copy-paste prompt for 1-click React/Vite/Tailwind export to Bolt.new.

## Acceptance Criteria

### Visual Polish & Responsiveness
- [ ] Dashboard opens cleanly in any modern browser with zero console errors.
- [ ] Map renders at 60 FPS without lag when dragging the time slider or dynamic clogging slider.
- [ ] All typography, KPI cards, and telemetry badges have high contrast and zero overlapping text.

### Interactive Functionality
- [ ] Time slider correctly updates flood depths across all 500+ road segments for each time-step.
- [ ] Clicking any road segment or pulsing manhole accurately updates the Diagnostic Inspector card.
- [ ] Changing the vehicle clearance filter dynamically triggers warnings if the road depth exceeds clearance.
- [ ] One-click launch_dashboard.bat successfully launches the interface in the default browser.
