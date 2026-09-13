# 🚀 Team Kairos: SIH 2026 Master Sprint Tracker & Kanban Board

**Problem Statement ID:** 26085 | **Ministry:** Ministry of Earth Sciences (MoES) / NCMRWF  
**Project:** Urban Flood Nowcasting System (Drainage and Rainfall Coupling)  
**Target Domain:** Greater Chennai Corporation (GCC) & CMA (Scalable to Mumbai, Delhi, Bengaluru)

---

## 👥 Core Team Roles & Domain Ownership

| Name | Role / Subsystem | Primary Tech Stack |
|---|---|---|
| **Gagan K S** *(Lead)* | System Architecture, 1D Surcharge Engine, FastAPI & React GIS Twin | `FastAPI`, `pyswmm`, `React.js`, `MapLibre GL` |
| **Yashwanth** | Radar Optical Flow & Quantitative Precipitation Nowcasting (0–3h) | `OpenCV`, `scipy.ndimage`, `netCDF4`, `IMD Radar` |
| **Rithesh** | Synthetic Subsurface Drainage Multigraph & Hydraulic Conductance | `osmnx`, `networkx`, `geopandas`, Manning''s Eq. |
| **Vijay** | Cartosat DEM Hydrologic Conditioning & Depression Pooling | `pysheds`, `rasterio`, Wang & Liu Pit-Filling |
| **Raksha** | Ground-Truth Validation, GCC 1913 Grievances & Michaung Calibration | `pandas`, `scikit-learn`, `HEC-RAS` comparison |
| **Vaishnavi** | Sentinel-1 SAR Flood Inundation & Impervious Surface Mapping | `Sentinel-1 GEE`, `Rasterio`, LULC Runoff $C$ |

---

## 📋 Kanban Board Tasks (For GitHub Project)

### 📌 Column 1: 📋 Backlog (To Do)
* **Task 1.1:** Doppler Radar Optical Flow Semi-Lagrangian Advection (`@Yashwanth-N17`)
* **Task 1.2:** Road-Following Subsurface Drainage Multigraph Generator (`@Rithesh`)
* **Task 1.3:** Cartosat 10m/30m Hydro-Conditioning & Depression Pooling (`@Vijay`)
* **Task 1.4:** Empirical Clogging Factor ($\mu_{clog}$) Dynamic Calculation (`@Gagan` & `@Rithesh`)
* **Task 1.5:** 1D Fast Hydraulic Surcharge & Backwater Engine (<350ms) (`@Gagan`)
* **Task 1.6:** Dynamic A* Emergency Evacuation Routing API (`@Gagan`)
* **Task 1.7:** Interactive Web GIS Twin Dashboard (`@Gagan` & Team)

### 📌 Column 2: ⏳ In Progress
* **Task 2.1:** Master Dataset Feature Cross-Correlation & Validation (`@Raksha`)
* **Task 2.2:** Slide 3 Architecture Flowchart & Slide 4 Feasibility Matrix Polish (`@Gagan` & `@Yashwanth`)

### 📌 Column 3: 🔍 In Review / Testing
* **Task 3.1:** Python 3.13 Virtual Environment & 21 Package Dependencies Integrity

### 📌 Column 4: ✅ Completed (Done)
* [x] **Project Repository & Organization Setup:** Migrated codebase to `Team-Kairos-SIH/Smart-India-Hackathon-2026`.
* [x] **Master Guide & Defense Playbook:** Comprehensive 300-line strategy document (`SIH2026_Urban_Flood_Master_Guide.md`).
* [x] **Domain Maintenance Datasets:** 25 blockage grievance hotspots, 1,671 km SWD desilting, 20 TANGEDCO substations assembled in `maintenance_data/`.
* [x] **Official 6-Slide Template Alignment:** Formatted as per MoES / NCMRWF guidelines.
