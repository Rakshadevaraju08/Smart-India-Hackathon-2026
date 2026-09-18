# Urban Flood Nowcasting System (Drainage and Rainfall Coupling)

[![Smart India Hackathon 2026](https://img.shields.io/badge/SIH-2026-blue.svg)](https://www.sih.gov.in/)
[![Problem Statement](https://img.shields.io/badge/MoES%20%2F%20NCMRWF-PS%2026085-orange.svg)](https://www.sih.gov.in/)
[![Python 3.13+](https://img.shields.io/badge/Python-3.13%2B-green.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Web GIS](https://img.shields.io/badge/Frontend-Leaflet%20Web%20GIS-199900.svg)](https://leafletjs.com/)
[![Tests](https://img.shields.io/badge/Tests-31%2F31%20Passing-brightgreen.svg)](ai_service/tests/test_layer0_rainfall.py)

A physics-coupled 1D-2D hydro-meteorological nowcasting engine that predicts street-level urban inundation (0-3 hour lead time) for Greater Chennai Corporation (GCC - 7,894 road segments, 15 zones) by coupling Doppler Weather Radar nowcasts, 2D micro-topography, and 1D subsurface stormwater drainage graph hydraulics.

---

## Technical Architecture

`
                       STAGE 1: DATA INGESTION & NOWCASTING (LAYER 0)
        +-----------------------------------+-----------------------------------+
        |   IMD Doppler Weather Radar       |   Real-Time Automatic Rain Gauges |
        |   (Meenambakkam / Chennai Port)   |   (Nungambakkam, Guindy, etc.)    |
        |   10-min SRI & PAC Grids          |   15-min Telemetry                |
        +-----------------+-----------------+-----------------+-----------------+
                          |                                   |
                          v                                   v
        +-----------------------------------------------------------------------+
        |       Dynamic Gauge-to-Radar Bias Calibration Engine (KED)            |
        |       Corrects tropical cyclonic Drop Size Distribution (DSD) bias    |
        +-----------------------------------+-----------------------------------+
                                            |
                                            v
        +-----------------------------------------------------------------------+
        |       Farneback Semi-Lagrangian Optical Flow Nowcaster (PySteps)      |
        |       Projects rain field motion to T+15m, T+30m, T+60m ... T+180m    |
        |       (Execution Latency: 2.8 ms)                                     |
        +-----------------------------------+-----------------------------------+
                                            |
                                            v
        +-----------------------------------------------------------------------+
        |       Mass-Conservative Street Disaggregator                          |
        |       Downscales 1 km radar nowcast onto 7,894 road segments          |
        |       (Strict mass conservation: <= 0.000089% volume error)           |
        +-----------------------------------+-----------------------------------+
                                            |
                                            v
                            STAGES 2 - 5: 1D-2D HYDRAULIC TWIN
        +-----------------------------------------------------------------------+
        |  * 2D Overland Runoff Accumulation (Modified Rational / Shallow Water)|
        |  * 1D Subsurface Conduit Capacity (Manning's Pipe Flow)               |
        |  * Dynamic Solid Waste Clogging Penalty (mu_clog in [0.0, 0.8])       |
        |  * Manhole Hydraulic Grade Line Surcharge & Street Backflow Rate      |
        |  * First Responder Emergency A* Evacuation Routing Engine             |
        +-----------------------------------------------------------------------+
`

---

## Repository Directory Structure

`
SIH/
|-- src/                                  # Production source code
|   |-- layer0/                           # Layer 0: Rainfall Ingestion & Nowcasting Engine
|   |   |-- __init__.py
|   |   |-- ingestion.py                  # Live IMD radar scraper, AWS poller & fallback
|   |   |-- calibrator.py                 # Brandes & Kriging (KED) gauge-radar calibration
|   |   |-- nowcaster.py                  # Farneback optical flow advection (PySteps)
|   |   |-- disaggregator.py              # Area-weighted mass-conservative street mapper
|   |   +-- pipeline.py                   # Master Layer 0 pipeline orchestrator
|   +-- api.py                            # FastAPI hydrodynamic nowcasting backend bridge
|
|-- frontend/                             # Tactical Web GIS Command Twin
|   |-- index.html                        # Full-screen dark tactical emergency interface
|   +-- data/
|       +-- chennai_flood_data.js         # Calibrated spatial dataset for 7,894 road segments
|
|-- tests/                                # Automated verification test suite
|   |-- test_layer0_rainfall.py           # 25-test comprehensive suite (100% passing)
|   |-- test_adversarial_m8_2.py          # Hydraulic stress and boundary test suite
|   |-- adversarial/                      # Hydraulic adversarial scenarios
|   +-- e2e/                              # End-to-end integration tests
|
|-- research_reports/                     # System design documentation
|   +-- research_report_urban_flood_nowcasting.md # Architectural specification report
|
|-- scripts/                              # Utility scripts
|   |-- deploy_to_vercel.py               # Vercel deployment helper
|   |-- download_drive_data.py            # Drive dataset staging script
|   |-- prepare_frontend_data.py          # GeoJSON data builder
|   +-- verify_env.py                     # Environment package verifier
|
|-- launch_dashboard.bat                  # 1-click Windows launcher (starts API & browser)
|-- requirements.txt                      # Pinned Python 3.13 dependencies
|-- vercel.json                           # Vercel web routing configuration
+-- README.md                             # Project documentation
`

---

## Quick Start & Verification

### 1. 1-Click Dependency Installation (All-in-One)
On Windows:
```cmd
install_dependencies.bat
```
On Linux / macOS / WSL:
```bash
bash install_dependencies.sh
```
*This automatically installs Python requirements (`pip install -r requirements.txt`), Node.js backend modules (`backend/`), and React/Vite Frontend packages (`Frontend/`).*

#### Manual Installation (Alternative):
```bash
# 1. Python Environment
python -m pip install -r requirements.txt

# 2. Node.js API Gateway Backend
cd backend && npm install && cd ..

# 3. React / Vite Frontend
cd Frontend && npm install && cd ..
```

### 2. Run the Full Test Suite
Run pytest to verify radar scraping, optical flow nowcasting, Kriging calibration, CML attenuation inversion, 1-min stochastic sub-stepping, 100m super-resolution, and 2D-Var Kalman fusion:
```bash
pytest ai_service/tests/ -v
```
*Expected result: 31 passed in ~2.5 seconds (100% pass rate).*

Run the physical hydraulic stress & adversarial routing test harnesses:
```bash
python ai_service/tests/adversarial/test_hydraulic_adversary.py
python ai_service/tests/test_adversarial_m8_2.py
node backend/tests/test_api.js
```

### 3. Run the Layer 0 Ingestion & Nowcasting Pipeline
Execute the complete rainfall ingestion and nowcasting engine:
```bash
python -m ai_service.layer0.pipeline
```
This fetches live IMD radar grids, fuses 35 GCC municipal ward gauges and cellular microwave links (CML), runs optical flow cloud nowcasting, and generates mass-conserved rainfall vectors for all 7,894 streets in Chennai.

### 4. Launch the System
- **1-Click System Launcher (Node API + Dashboard)**:
  ```bash
  bash launch_system.sh
  ```
- **Windows 1-Click Standalone Viewer**:
  Double-click `launch_dashboard.bat` to instantly launch the Tactical Command Twin in your default browser.
- **Vite Interactive React Dashboard (Dev Mode)**:
  ```bash
  cd Frontend
  npm run dev
  ```

---

## Team Kairos - SIH 2026
- **Yashwanth N** (Team Lead)
- **Gagan K S**
- **Rithesh**
- **Vijay**
- **Raksha**
- **Vaishnavi**
