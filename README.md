# Urban Flood Nowcasting System (Drainage and Rainfall Coupling)

[![Smart India Hackathon 2026](https://img.shields.io/badge/SIH-2026-blue.svg)](https://www.sih.gov.in/)
[![Problem Statement](https://img.shields.io/badge/MoES%20%2F%20NCMRWF-PS%2026085-orange.svg)](https://www.sih.gov.in/)
[![Python 3.13+](https://img.shields.io/badge/Python-3.13%2B-green.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Web GIS](https://img.shields.io/badge/Frontend-Leaflet%20Web%20GIS-199900.svg)](https://leafletjs.com/)
[![Tests](https://img.shields.io/badge/Tests-25%2F25%20Passing-brightgreen.svg)](tests/test_layer0_rainfall.py)

A physics-coupled 1D-2D hydro-meteorological nowcasting engine that predicts street-level urban inundation (0–3 hour lead time) for Greater Chennai Corporation (GCC - 7,894 road segments, 15 zones) by coupling Doppler Weather Radar nowcasts, 2D micro-topography, and 1D subsurface stormwater drainage graph hydraulics.

---

## ??? System Architecture

`
                               STAGE 1: DATA INGESTION & NOWCASTING (LAYER 0)
        +-----------------------------------------------------------------------+
        ¦   IMD Doppler Weather Radar       ¦   Real-Time Automatic Rain Gauges ¦
        ¦   (Meenambakkam / Chennai Port)   ¦   (Nungambakkam, Guindy, etc.)    ¦
        ¦   10-min SRI & PAC Grids          ¦   15-min Telemetry                ¦
        +-----------------------------------------------------------------------+
                          ¦                                   ¦
                          ?                                   ?
        +-----------------------------------------------------------------------+
        ¦       Dynamic Gauge-to-Radar Bias Calibration Engine (KED)            ¦
        ¦       Corrects tropical cyclonic Drop Size Distribution (DSD) bias    ¦
        +-----------------------------------------------------------------------+
                                            ¦
                                            ?
        +-----------------------------------------------------------------------+
        ¦       Farnebäck Semi-Lagrangian Optical Flow Nowcaster (PySteps)      ¦
        ¦       Projects rain field motion to T+15m, T+30m, T+60m ... T+180m    ¦
        ¦       (Execution Latency: 2.8 ms)                                     ¦
        +-----------------------------------------------------------------------+
                                            ¦
                                            ?
        +-----------------------------------------------------------------------+
        ¦       Mass-Conservative Street Disaggregator                          ¦
        ¦       Downscales 1 km radar nowcast onto 7,894 road segments          ¦
        ¦       (Strict mass conservation: <= 0.000089% volume error)           ¦
        +-----------------------------------------------------------------------+
                                            ¦
                                            ?
                            STAGES 2 - 5: 1D-2D HYDRAULIC TWIN
        +-----------------------------------------------------------------------+
        ¦  • 2D Overland Runoff Accumulation (Modified Rational / Shallow Water)¦
        ¦  • 1D Subsurface Conduit Capacity (Manning's Pipe Flow)               ¦
        ¦  • Dynamic Solid Waste Clogging Penalty (mu_clog in [0.0, 0.8])      ¦
        ¦  • Manhole Hydraulic Grade Line Surcharge & Street Backflow Rate      ¦
        ¦  • First Responder Emergency A* Evacuation Routing Engine             ¦
        +-----------------------------------------------------------------------+
`

---

## ?? Repository Directory Structure

`
SIH/
+-- src/                                  # Production source code
¦   +-- layer0/                           # Layer 0: Rainfall Ingestion & Nowcasting Engine
¦   ¦   +-- __init__.py
¦   ¦   +-- ingestion.py                  # Live IMD radar scraper, AWS poller & fallback
¦   ¦   +-- calibrator.py                 # Brandes & Kriging (KED) gauge-radar calibration
¦   ¦   +-- nowcaster.py                  # Farnebäck optical flow advection (PySteps)
¦   ¦   +-- disaggregator.py              # Area-weighted mass-conservative street mapper
¦   ¦   +-- pipeline.py                   # Master Layer 0 pipeline orchestrator
¦   +-- api.py                            # FastAPI hydrodynamic nowcasting backend bridge
¦
+-- frontend/                             # Tactical Web GIS Command Twin
¦   +-- index.html                        # Full-screen dark tactical emergency interface
¦   +-- data/
¦       +-- chennai_flood_data.js         # Calibrated spatial dataset for 7,894 road segments
¦
+-- tests/                                # Automated verification test suite
¦   +-- test_layer0_rainfall.py           # 25-test comprehensive suite (100% passing)
¦   +-- test_adversarial_m8_2.py          # Hydraulic stress and boundary test suite
¦   +-- adversarial/                      # Hydraulic adversarial scenarios
¦   +-- e2e/                              # End-to-end integration tests
¦
+-- research_reports/                     # System design documentation
¦   +-- research_report_urban_flood_nowcasting.md # Architectural specification report
¦
+-- scripts/                              # Utility scripts
¦   +-- deploy_to_vercel.py               # Vercel deployment helper
¦   +-- download_drive_data.py            # Drive dataset staging script
¦   +-- prepare_frontend_data.py          # GeoJSON data builder
¦   +-- verify_env.py                     # Environment package verifier
¦
+-- launch_dashboard.bat                  # 1-click Windows launcher (starts API & browser)
+-- requirements.txt                      # Pinned Python 3.13 dependencies
+-- vercel.json                           # Vercel web routing configuration
+-- README.md                             # Project documentation
`

---

## ? Quick Start & Verification

### 1. Environment Installation
Clone the repository and install dependencies:
`powershell
git clone https://github.com/Team-Kairos-SIH/Smart-India-Hackathon-2026.git
cd Smart-India-Hackathon-2026
pip install -r requirements.txt
`

### 2. Run the Layer 0 Test Suite (25 Tests)
Run pytest to verify radar scraping, PySteps optical flow nowcasting, Kriging bias calibration, and mass conservation:
`powershell
pytest tests/test_layer0_rainfall.py -v
`
*Expected result: 25 passed in ~8 seconds (100% pass rate).*

### 3. Run the Standalone Layer 0 Pipeline
Execute the complete rainfall ingestion and nowcasting engine:
`powershell
python -m src.layer0.pipeline
`
This fetches live IMD radar grids, runs the optical flow cloud nowcast, calibrates with ground rain gauges, and generates model-ready rain vectors for all 7,894 streets in Chennai.

### 4. Launch the Tactical Command Twin (1-Click)
Double-click launch_dashboard.bat or run:
`powershell
.\launch_dashboard.bat
`
This starts the backend API on port 8000 and opens the Web GIS Command Twin in your browser:
- **0–180 Min Nowcast Slider**: Scrub forward in time to watch inundation develop street-by-street.
- **Surcharge Diagnostic Inspector**: Click any road or manhole to inspect nominal diameter ($), hydraulic head, and backflow rate.
- **Dynamic Clogging Simulator**: Slide solid waste blockage ($\mu_{\text{clog}}$) from 0% to 80% to observe the real-world impact of uncleaned drains.
- **A\* Emergency Routing**: Switch vehicle types (108 Ambulance, NDRF truck, passenger car, two-wheeler) to calculate safe flood-avoidance routes.

---

## ?? Team Kairos — SIH 2026
- **Gagan K S** (Lead Contributor)
- **Yashwanth N**
- **Rithesh**
- **Vijay**
- **Raksha**
- **Vaishnavi**
