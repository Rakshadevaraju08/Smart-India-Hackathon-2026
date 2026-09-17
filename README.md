# Urban Flood Nowcasting System (Drainage and Rainfall Coupling)

**Smart India Hackathon 2026** | **Problem Statement ID**: 26085  
**Ministry / Organization**: Ministry of Earth Sciences (MoES) / NCMRWF  
**Target Domain**: Greater Chennai Corporation (GCC) & Chennai Metropolitan Area  

---

## 📁 Repository & Project Architecture

This workspace is strictly structured into modular components:

```
SIH/
│
├── Datasets/                                            # Single ML-ready training dataset
│   └── chennai_unified_flood_master_dataset.csv         # 7,894 segments × 27 coupled features (1.62 MB)
│
├── Google_Drive_Datasets/                               # Cloud vault staging folder for heavy raw data
│   ├── 01_Rainfall_Yashwanth/                           # 4,416 NASA GPM satellite .nc4 rasters & ERA5
│   ├── 02_Drainage_Rithesh/                             # CMWSSB pipe attributes & OSM vector network
│   ├── 03_Terrain_and_DEM_Vijay/                        # ISRO Cartosat-1 30m DEM & soil maps
│   ├── 04_Historical_Floods_Raksha/                     # 7,895 flooded streets & HEC-RAS models
│   ├── 05_Satellite_Vaishnavi/                          # Sentinel-1 SAR & 10m LULC land cover
│   ├── 06_Civic_Maintenance_Gagan/                      # Silt, solid waste, and blockage records
│   ├── chennai_unified_flood_master_dataset.csv         # Consolidated ML table copy
│   ├── inventory.xlsx                                   # Grand Master Inventory
│   └── README.md                                        # Google Drive upload instructions
│
├── maintenance_data/                                    # Day 1 Civic Maintenance & Domain Datasets
│   ├── blockage_complaints/                             # 25 chronic drain blockage coordinates
│   ├── drain_maintenance/                               # 1,671 km SWD desilting & 44 outfall canals
│   ├── economic_data/                                   # 12 commercial clusters & rupee loss curves
│   ├── electrical/                                      # 20 TANGEDCO substations & plinth heights
│   ├── solid_waste/                                     # Zonal MSW generation & litter risk index
│   └── traffic/                                         # Peak PCU counts & evacuation routing profile
│
├── research_reports/                                    # Publication-grade technical documentation
│   ├── Urban_Flood_Nowcasting_Comprehensive_Research_Report.pdf # 5-Page formal PDF architecture report
│   ├── research_report_urban_flood_nowcasting.md        # Comprehensive technical markdown report
│   └── urban_flood_nowcasting_proposal_v2.docx          # Project proposal document
│
├── scripts/                                             # Essential project scripts
│   ├── download_drive_data.py                           # Downloads raw archives from Google Drive
│   └── verify_env.py                                    # Verifies all 21 Python dependencies
│
├── inventory.xlsx                                       # Grand Master Team Data Catalog
├── requirements.txt                                     # Pinned dependencies (Python 3.13 tested)
└── .gitignore                                           # Excludes heavy binaries (>25MB) from Git
```

---

## ⚡ Quick Start

### 1. Environment Setup
```powershell
pip install -r requirements.txt
python scripts/verify_env.py
```

### 2. Inspect the Master ML Dataset
```python
import pandas as pd
df = pd.read_csv("Datasets/chennai_unified_flood_master_dataset.csv")
print(df.shape)  # (7894, 27)
```

### 3. Download Raw Archives from Google Drive (Optional)
```powershell
python scripts/download_drive_data.py
```

---

## 🧪 How to Verify & Test After Cloning to a PC

If anyone clones this repository onto their machine, here is how they can immediately test and run everything:

### Step 1: Run the Automated Layer 0 Test Suite (25 Tests)
Run pytest to verify radar scraping, PySteps optical flow nowcasting, Kriging bias calibration, and 100% mass conservation across all 7,894 streets:
```powershell
pytest tests/test_layer0_rainfall.py -v
```
*(All 25 tests pass in ~8 seconds with zero failures).*

### Step 2: Run the Layer 0 Rainfall Ingestion & Nowcasting Pipeline
Execute the full Python pipeline directly in the terminal:
```powershell
python -m src.layer0.pipeline
```
This will:
- Poll live IMD Meenambakkam/Chennai Port radar feeds (`sr_chn.gif`).
- Fetch real-time AWS rain gauges across Chennai.
- Run Farnebäck optical flow nowcasting for 6 forward time steps ($T+15\text{m}$ to $T+180\text{m}$).
- Remap continuous rainfall onto all 7,894 road segments with exact volume conservation.

### Step 3: Launch the Full Command Twin Dashboard (1-Click)
Double-click [`launch_dashboard.bat`](file:///c:/Users/Gagan%20K%20S/Documents/SIH/launch_dashboard.bat) or run in terminal:
```powershell
.\launch_dashboard.bat
```
This automatically boots the backend API bridge on port 8000 and opens the Web GIS tactical dashboard in your default browser.
