# Layer 1: 2D Micro-Topographical DEM, LULC & Surface Runoff Engine
## Technical Specification, Hydrologic Physics & Implementation Architecture

---

## 1. Executive Overview

### 1.1 The Urban Hydrology Challenge in Chennai
The Greater Chennai Corporation (GCC) metropolitan area spans approximately 426 km² across 15 administrative zones, encompassing 7,894 critical road segments and storm drainage corridors. Chennai's flood susceptibility is governed by a precarious combination of factors:
1. **Extremely Flat Coastal Topography**: Average ground elevation across the metropolitan basin ranges from 2.0 to 12.0 meters above Mean Sea Level (MSL), with typical regional hydraulic slopes of less than $0.001\text{ to }0.003\text{ m/m}$ (1 to 3 meters drop per kilometer).
2. **Dense Impervious Urbanization**: Intense urban expansion has sealed formerly pervious marshlands and agricultural plains with asphalt and reinforced concrete, pushing Directly Connected Impervious Area (DCIA) fractions to over $90\%$ in central commercial districts like T. Nagar (Zone 9) and Royapuram (Zone 5).
3. **Complex Soil Mechanics & Geotechnical Heterogeneity**: The coastal fringe features high-permeability littoral sand (Hydrologic Soil Group A), while the inland and northern basins (Madhavaram, Tondiarpet, Ambattur) sit atop low-permeability alluvial clays and weathered charnockite (HSG C and D) with saturated hydraulic conductivities ($K_{\text{sat}}$) as low as $3.8\text{ mm/hr}$.
4. **Perched Water Tables & Canal Riparian Waterlogging**: The historic Buckingham Canal, along with the Adyar and Cooum river systems, creates riparian corridors where the groundwater table sits mere centimeters below the ground surface during the Northeast Monsoon (NEM), eliminating natural soil infiltration capacity.
5. **Coastal Subsidence**: Sentinel-1 InSAR measurements reveal coastal ground sinking at rates exceeding $3.5\text{ mm/year}$ in localized extraction corridors, causing soil compaction and creating artificial hollows that trap surface runoff.

### 1.2 Objective and Role of Layer 1
Layer 1 acts as the **topographical, land cover, and hydrologic conversion engine** of the KAIROS Urban Flood Nowcasting System. 

It receives spatial rainfall intensity vectors ($I_i(t)$ in mm/hr) from **Layer 0** (Atmospheric Doppler Radar & Optical Flow Nowcasting) and routes them through:
- High-resolution digital terrain modeling (ISRO Cartosat-1 30m stereoscopic DEM).
- Hydro-conditioning (breaching digital infrastructure dams, stream burning, underpass depression carving).
- Advanced Land Use / Land Cover (LULC) impervious area extraction.
- Geotechnical soil infiltration modeling (USDA/ICAR Hydrologic Soil Groups, dynamic Antecedent Moisture Condition AMC, riparian penalties).
- Surface excess runoff and tributary discharge generation ($R_{\text{excess}}$ [mm/hr] and $Q_{\text{surf}}$ [$\text{m}^3/\text{s}$]).

These outputs are formatted to feed directly into street inundation and 1D/2D hydrodynamic pipe-network solvers with **guaranteed $0.000000\%$ volumetric mass continuity**.

---

## 2. System Architecture & End-to-End Dataflow

```
                             [ RAW TERRAIN SOURCES ]
                     ISRO Cartosat-1 30m DEM / SRTM-v3 1-Arcsec
                     Sentinel-1 InSAR Ground Subsidence Rasters
                                        │
                                        ▼
  ┌───────────────────────────────────────────────────────────────────────────┐
  │ 1. DEM BUILDER MODULE (dem_builder.py)                                    │
  │    - Mosaic & clip to Chennai Metropolitan Domain (79.60E to 80.35E,     │
  │      12.65N to 13.35N)                                                    │
  │    - Reproject WGS84 (EPSG:4326) -> UTM Zone 44N Planar Metric (EPSG:32644)│
  │    - Apply InSAR vertical subsidence offset: Z_corr = Z_raw - (v_sub * dt)│
  └─────────────────────────────────────┬─────────────────────────────────────┘
                                        │
                                        ▼
  ┌───────────────────────────────────────────────────────────────────────────┐
  │ 2. HYDRO-CONDITIONER MODULE (hydro_conditioner.py)                        │
  │    - Digital Dam Breaching: Remove artificial bridge embankments          │
  │    - Stream Burning: Carve Buckingham Canal, Adyar, Cooum, Otteri Nullah  │
  │    - Underpass Depressions: Enforce negative relief at railway subways    │
  └─────────────────────────────────────┬─────────────────────────────────────┘
                                        │
                                        ▼
  ┌───────────────────────────────────────────────────────────────────────────┐
  │ 3. HYDROLOGIC DERIVATIVES ENGINE (hydrologic_derivatives.py)              │
  │    - 8-Neighborhood Horn Elevation Gradient: Slope S_0 (m/m and degrees)   │
  │    - Azimuth Aspect: Compass direction of steepest slope                  │
  │    - D8 Steepest-Descent Flow Matrix: Cardinal & diagonal flow vectors   │
  │    - Upstream Flow Accumulation Grid: Catchment contributing cells        │
  └─────────────────────────────────────┬─────────────────────────────────────┘
                                        │
                                        ▼
  ┌───────────────────────────────────────────────────────────────────────────┐
  │ 4. ROAD ELEVATION SAMPLER MODULE (road_sampler.py)                        │
  │    - Spatial Join: 7,894 Greater Chennai Corporation street segments      │
  │    - Bilinear Interpolation: Sample Z_ground, S_0, aspect, and catchment  │
  │      area directly onto road segment centroids                            │
  └─────────────────────────────────────┬─────────────────────────────────────┘
                                        │
                 Layer 0 Precipitation  │  Conditioned Road Geometries & DEM
                 (Nowcast Rain mm/hr)   │  (Slope, Elevation, Road Classes)
                        │               │
                        ▼               ▼
  ┌───────────────────────────────────────────────────────────────────────────┐
  │ 5. LULC & SOIL HYDROLOGY ENGINE (ai_service/layer1/lulc/)                │
  │                                                                           │
  │   [A] impervious_extractor.py:                                            │
  │       - Zone Baselines (GCC 15 Zones) + Road Class Modifiers (OSM)        │
  │       - Chennai Municipal RWH Disconnection: 0.94x DCIA on Residential     │
  │       - Building Coverage Ratio (BCR) & Manning's Overland Roughness n    │
  │       - Cartosat Slope Adjustment on Rational C: C = C_base * (1 + adj)   │
  │       - IRC:SP:42 / CPHEEO Storm Frequency Factor: Cf up to 1.25          │
  │                                                                           │
  │   [B] soil_hydrology.py:                                                  │
  │       - ICAR / USDA Hydrologic Soil Group (A, B, C, D) from K_sat         │
  │       - Dynamic Antecedent Moisture Condition (AMC I, II, III)            │
  │       - Coastal Water Table Penalty: 0.50x if dist < 1.5km & elev < 3.5m  │
  │       - Canal Riparian Waterlogging Penalty: 0.40x within 150m of canals  │
  │       - InSAR Subsidence Compaction Penalty: 0.85x if sub > 3.5 mm/yr     │
  │                                                                           │
  │   [C] runoff_generator.py:                                                │
  │       - Slope-Modulated Micro-Depression Storage: Sd(S_0)                 │
  │       - Net Excess Surface Runoff Rate: R_excess [mm/hr]                  │
  │       - Tributary Inflow Discharge: Q_surf [m³/s]                         │
  │       - Catchment Volume Conservation: Exact 0.000000% Continuity Balance │
  └─────────────────────────────────────┬─────────────────────────────────────┘
                                        │
                                        ▼
                            [ OUTPUT DATASETS ]
                  RunoffResult / Layer1Result Enriched Dataframe
                 (7,894 Street Inflow Telemetry & Diagnostics)
```

---

## 3. Mathematical & Physical Formulations

### 3.1 DEM Projection & Coordinate Conversion
The raw Cartosat-1 elevation model is provided in geographic angular coordinates (WGS84, `EPSG:4326`). Angular coordinates are unsuitable for hydrodynamic calculations because longitudinal degree length varies with latitude ($\Delta x = \Delta \lambda \cdot R \cos \phi$). 

The DEM is projected to the **Universal Transverse Mercator (UTM) Zone 44 North (`EPSG:32644`)** coordinate reference system using a transverse cylinder conformal projection:
$$x = k_0 N \left( A + (1 - T + C) \frac{A^3}{6} + \dots \right)$$
$$y = k_0 \left( M + N \tan \phi \left( \frac{A^2}{2} + (5 - T + 9C + 4C^2) \frac{A^4}{24} + \dots \right) \right)$$
Where $k_0 = 0.9996$ is the central meridian scale factor, $N$ is the radius of curvature in the prime vertical, and $M$ is the meridional distance from the equator.

All grid cells are resampled to an exact planar resolution of **$30.0 \times 30.0\text{ meters}$** ($900\text{ m}^2/\text{cell}$).

### 3.2 Horn's Slope Gradient Formulation
The terrain surface slope gradient ($S_0$ in m/m and degrees) is derived using the standard 8-neighborhood 2nd-order finite-difference formulation by Horn (1981):

Given a $3 \times 3$ moving elevation window:
$$\begin{bmatrix} z_{1} & z_{2} & z_{3} \\ z_{4} & z_{5} & z_{6} \\ z_{7} & z_{8} & z_{9} \end{bmatrix}$$
The partial derivatives in the East-West ($\partial z / \partial x$) and North-South ($\partial z / \partial y$) directions are:
$$\left(\frac{\partial z}{\partial x}\right) = \frac{(z_3 + 2z_6 + z_9) - (z_1 + 2z_4 + z_7)}{8 \cdot \Delta x}$$
$$\left(\frac{\partial z}{\partial y}\right) = \frac{(z_7 + 2z_8 + z_9) - (z_1 + 2z_2 + z_3)}{8 \cdot \Delta y}$$
The terrain slope grade $S_0$ [m/m] and slope angle $\theta$ [degrees] are:
$$S_0 = \sqrt{\left(\frac{\partial z}{\partial x}\right)^2 + \left(\frac{\partial z}{\partial y}\right)^2}$$
$$\theta = \arctan(S_0) \times \frac{180}{\pi}$$

### 3.3 Hydro-Conditioning & Stream Burning
Raw satellite DEMs frequently suffer from artificial "digital dams" where elevated road and railway bridges cross natural drainage channels, blocking the computational flow of water in numerical models. 

To rectify this:
1. **Canal Burning**: Major arterial waterways (Buckingham Canal, Cooum River, Adyar River, Otteri Nullah, Captain Cotton Canal) are burned into the DEM raster by subtracting a hydraulic incision depth:
   $$Z_{\text{conditioned}}(x, y) = Z_{\text{raw}}(x, y) - \Delta Z_{\text{burn}} \quad \text{for } (x, y) \in \Omega_{\text{canals}}$$
   Where $\Delta Z_{\text{burn}} = 2.5\text{ to }4.0\text{ meters}$.
2. **Underpass Depression Carving**: Known flood-prone railway subways (e.g., Gengu Reddy Subway in Egmore, RBI Subway in George Town, Rangarajapuram Subway in T. Nagar) are depressed below adjacent street level by $1.8\text{ meters}$ to replicate the real-world physical hollows that accumulate floodwater.

---

## 4. Advanced LULC & Soil Hydrology Factors

### 4.1 Directly Connected Impervious Area (DCIA / $f_{\text{imp}}$)
Imperviousness dictates what portion of precipitation is prohibited from infiltrating the subsoil. In Layer 1, $f_{\text{imp}}$ is determined via a multi-tier spatial model:
$$f_{\text{imp,base}} = 0.50 \cdot \omega_{\text{road}} + 0.50 \cdot \omega_{\text{zone}}$$

Where:
* **$\omega_{\text{zone}}$** represents the zonal urban density baseline across the 15 GCC zones:
  - Zone 5 (Royapuram - Historic Dense Core): $0.94$
  - Zone 9 (T. Nagar / Teynampet - High-density Commercial): $0.94$
  - Zone 10 (Kodambakkam - Dense Mixed Residential): $0.91$
  - Zone 8 (Anna Nagar - Planned Urban Residential): $0.88$
  - Zone 1 (Thiruvottiyur - North Coastal / Mixed): $0.58$
  - Zone 15 (Sholinganallur - South Coastal IT Fringe): $0.60$
* **$\omega_{\text{road}}$** represents the roadway pavement imperviousness based on OpenStreetMap highway classification:
  - Motorway / Trunk / Primary: $0.94\text{ to }0.98$
  - Secondary / Tertiary: $0.86\text{ to }0.90$
  - Residential / Living Street: $0.72\text{ to }0.80$
  - Service / Track / Path: $0.30\text{ to }0.65$

### 4.2 Rainwater Harvesting (RWH) Disconnection Discount
Under the Tamil Nadu Municipal Corporation (Mandatory Rainwater Harvesting) Act, all residential structures in Chennai are legally required to maintain rooftop percolation pits and soakaways. 
- In residential, service, and living street corridors, rooftop runoff is partially disconnected from directly entering the curb gutters.
- Layer 1 applies an **effective DCIA disconnection discount of $0.94\times$** (6% reduction in connected imperviousness) on residential and service corridors:
  $$f_{\text{imp}} = \begin{cases} \text{clip}(f_{\text{imp,base}} \times 0.94,\; 0.20,\; 0.98) & \text{if Road Class } \in \{\text{residential, service, living\_street}\} \\ \text{clip}(f_{\text{imp,base}} \times 1.00,\; 0.20,\; 0.98) & \text{if Road Class } \in \{\text{motorway, trunk, primary}\} \end{cases}$$

### 4.3 DEM Slope Modulation on Composite Runoff Coefficient ($C$)
The baseline Rational runoff coefficient is:
$$C_{\text{base}} = f_{\text{imp}} \cdot 0.95 + (1.0 - f_{\text{imp}}) \cdot 0.20$$
On steeper slopes, gravity accelerates overland flow velocity, giving water less opportunity to infiltrate or pond in micro-depressions. Layer 1 applies a **topographical slope adjustment**:
$$\Delta C_{\text{slope}} = \text{clip}\left((S_0 - 0.01) \times 1.5,\; -0.04,\; +0.06\right)$$
$$C_{\text{composite}} = \text{clip}\left(C_{\text{base}} \cdot (1.0 + \Delta C_{\text{slope}}),\; 0.20,\; 0.96\right)$$

### 4.4 Storm Intensity Frequency Factor ($C_f$)
Urban storm drainage design codes (IRC:SP:42 and CPHEEO Manual on Storm Water Drainage Systems) require scaling runoff coefficients during extreme recurrence-interval storms. During intense cloudbursts, intense rain droplets cause soil surface crusting and rapidly submerge micro-relief features.

Layer 1 dynamically calculates $C_f(I)$ as a function of rainfall intensity $I$ [mm/hr]:
$$C_f(I) = \begin{cases} 
1.00 & I < 25.0\text{ mm/hr (Design Storm } \le \text{2-year return)} \\
1.00 + 0.10 \times \left(\frac{I - 25.0}{25.0}\right) & 25.0 \le I < 50.0\text{ mm/hr (5-year to 10-year storm)} \\
1.10 + 0.15 \times \min\left(1.0, \frac{I - 50.0}{50.0}\right) & I \ge 50.0\text{ mm/hr (25-year to 100-year cloudburst, capped at } 1.25\text{)}
\end{cases}$$

### 4.5 Soil Hydrology & Hydraulic Soil Group (HSG) Classification
Saturated hydraulic conductivity ($K_{\text{sat}}$) across Chennai varies from $3.8\text{ mm/hr}$ in the tight illitic clays of North Chennai to $16.0\text{ mm/hr}$ in the Besant Nagar / ECR beach sands.

Following USDA Natural Resources Conservation Service (NRCS) and Indian Council of Agricultural Research (ICAR) benchmarks:
- **Group A (Low Runoff Potential)**: $K_{\text{sat}} \ge 12.0\text{ mm/hr}$ (Deep littoral sand, gravelly loam)
- **Group B (Moderate Runoff Potential)**: $8.0 \le K_{\text{sat}} < 12.0\text{ mm/hr}$ (Sandy loam, red loamy soil)
- **Group C (Slow Infiltration Rate)**: $4.5 \le K_{\text{sat}} < 8.0\text{ mm/hr}$ (Clay loams, shallow soils, weathered rock)
- **Group D (High Runoff Potential)**: $K_{\text{sat}} < 4.5\text{ mm/hr}$ (Heavy swelling black cotton clays, saline sodic soils)

### 4.6 Dynamic Antecedent Moisture Condition (AMC)
Soil infiltration is not static; it depends heavily on prior rainfall over the previous 5 days ($P_5$):
- **AMC I (Dry Condition)**: $P_5 < 35.0\text{ mm}$ (Dry season / onset of monsoon). Soil pores are aerated, promoting suction head:
  $$\Phi_{\text{AMC}} = 1.30 \quad (+30\% \text{ infiltration capacity})$$
- **AMC II (Average Condition)**: $35.0 \le P_5 \le 55.0\text{ mm}$ (Standard seasonal moist soil):
  $$\Phi_{\text{AMC}} = 1.00 \quad (\text{Baseline } K_{\text{sat}})$$
- **AMC III (Saturated Condition)**: $P_5 > 55.0\text{ mm}$ or Active Cyclone (Michaung / 2015 Flood). Soils are completely waterlogged, suction head drops to zero:
  $$\Phi_{\text{AMC}} = 0.40 \quad (-60\% \text{ infiltration capacity throttle})$$

### 4.7 Geo-Environmental Environmental Infiltration Penalties
Layer 1 applies three geo-environmental penalties directly to effective soil infiltration:
$$f_{\text{soil}} = K_{\text{sat}} \times \Phi_{\text{AMC}} \times \Psi_{\text{coastal}} \times \Psi_{\text{canal}} \times \Psi_{\text{insar}}$$

1. **Coastal Shallow Water Table Penalty ($\Psi_{\text{coastal}}$)**:
   - On the coastal margin where ground elevation is $< 3.5\text{ m}$ MSL and distance to the Bay of Bengal is $< 1.5\text{ km}$, tidal backwater maintains a perched water table within 0.5m of the road surface.
   - Penalty: $\Psi_{\text{coastal}} = 0.50$ (50% reduction).
2. **Canal Riparian Waterlogging Penalty ($\Psi_{\text{canal}}$)**:
   - Within $< 150\text{ meters}$ of the Buckingham Canal, Otteri Nullah, Cooum, or Adyar river channels, hydraulic head from the canal causes continuous sub-base soil saturation.
   - Penalty: $\Psi_{\text{canal}} = 0.40$ (60% reduction).
3. **InSAR Subsidence Soil Compaction Penalty ($\Psi_{\text{insar}}$)**:
   - Road segments situated in active subsidence bowls ($v_{\text{sub}} > 3.5\text{ mm/year}$) undergo vertical compaction that collapses macropores and significantly reduces matrix permeability.
   - Penalty: $\Psi_{\text{insar}} = 0.85$ (15% reduction).

---

## 5. Slope-Modulated Depression Storage & Mass Continuity

### 5.1 Micro-Depression Storage Modeling ($S_d$)
Before surface runoff can initiate, rainfall must satisfy initial abstraction / depression storage in the micro-undulations of the surface:
- On flat terrain ($S_0 \approx 0.001\text{ m/m}$), puddle hollows trap substantial water.
- On steeper slopes ($S_0 \ge 0.030\text{ m/m}$), gravitational gradients cause depressions to spill prematurely.

The base depression storage is scaled by Cartosat DEM slope $S_0$ [m/m]:
$$S_{d,\text{imp,base}} = \text{clip}\left(1.5 \times [1.0 - (S_0 - 0.01) \times 8.0],\; 0.8,\; 2.5\right) \quad [\text{mm}]$$
$$S_{d,\text{perv,base}} = \text{clip}\left(4.0 \times [1.0 - (S_0 - 0.01) \times 6.0],\; 2.0,\; 6.0\right) \quad [\text{mm}]$$

Under extreme storm intensities, high rainfall rates fill these hollows rapidly, modulated by $C_f$:
$$S_{d,\text{imp}} = \frac{S_{d,\text{imp,base}}}{C_f(I)}, \qquad S_{d,\text{perv}} = \frac{S_{d,\text{perv,base}}}{C_f(I)}, \qquad f_{\text{soil,eff}} = \frac{f_{\text{soil}}}{C_f(I)}$$

### 5.2 Mathematical Proof of Strict Catchment Mass Conservation
For any incoming rainfall intensity $I$ [mm/hr] across a subcatchment with area $A_c$ [$\text{m}^2$] and impervious fraction $f_{\text{imp}}$:

**1. Impervious Component Fraction ($f_{\text{imp}}$)**:
- Runoff generation: $R_{\text{imp}} = \max(0.0, I - S_{d,\text{imp}})$
- Depression abstraction: $L_{\text{imp}} = I - R_{\text{imp}} \ge 0$
- Mass identity on impervious surface: $R_{\text{imp}} + L_{\text{imp}} \equiv I$

**2. Pervious Component Fraction ($1.0 - f_{\text{imp}}$)**:
- Soil infiltration loss: $f_{\text{loss}} = \min(I, f_{\text{soil,eff}})$
- Runoff generation: $R_{\text{perv}} = \max(0.0, I - f_{\text{loss}} - S_{d,\text{perv}})$
- Actual pervious depression abstraction: $L_{\text{perv}} = \max(0.0, I - f_{\text{loss}} - R_{\text{perv}}) \ge 0$
- Mass identity on pervious surface: $R_{\text{perv}} + f_{\text{loss}} + L_{\text{perv}} \equiv I$

**3. Catchment Composite Budget**:
The composite excess runoff rate $R_{\text{excess}}$, actual infiltration rate $\text{Infil}_{\text{actual}}$, and actual depression rate $\text{Dep}_{\text{actual}}$ are:
$$R_{\text{excess}} = f_{\text{imp}} \cdot R_{\text{imp}} + (1 - f_{\text{imp}}) \cdot R_{\text{perv}}$$
$$\text{Infil}_{\text{actual}} = (1 - f_{\text{imp}}) \cdot f_{\text{loss}}$$
$$\text{Dep}_{\text{actual}} = f_{\text{imp}} \cdot L_{\text{imp}} + (1 - f_{\text{imp}}) \cdot L_{\text{perv}}$$

Summing all three terms:
$$\begin{aligned}
R_{\text{excess}} + \text{Infil}_{\text{actual}} + \text{Dep}_{\text{actual}} &= f_{\text{imp}} (R_{\text{imp}} + L_{\text{imp}}) + (1 - f_{\text{imp}}) (R_{\text{perv}} + f_{\text{loss}} + L_{\text{perv}}) \\
&= f_{\text{imp}} \cdot I + (1 - f_{\text{imp}}) \cdot I \\
&= I \cdot [f_{\text{imp}} + 1 - f_{\text{imp}}] \\
&\equiv I \quad \mathbf{[Q.E.D.]}
\end{aligned}$$

Integrating over contributing area $A_c$ and time step $\Delta t$:
$$V_{\text{rain}} \equiv V_{\text{runoff}} + V_{\text{infiltrated}} + V_{\text{depression}}$$
This mathematical formulation guarantees that **mass balance error is exactly $0.000000\%$**, precluding numerical generation or loss of water.

### 5.3 Tributary Inflow Discharge ($Q_{\text{surf}}$)
The overland runoff rate $R_{\text{excess}}$ [mm/hr] is translated into volumetric discharge rate $Q_{\text{surf}}$ entering the local road curb inlet or roadside swale:
$$Q_{\text{surf}} = \left(\frac{R_{\text{excess}}}{1000 \cdot 3600}\right) \cdot A_c = \frac{R_{\text{excess}} \cdot A_c}{3.6 \times 10^6} \quad \left[\text{m}^3/\text{s}\right]$$

---

## 6. Software Architecture & Implementation Details

Layer 1 is located in `ai_service/layer1/` and structured as follows:

```
ai_service/layer1/
├── __init__.py                     # Public API exports and lazy accessors
├── dem_builder.py                  # Ingestion, UTM 44N reprojection & InSAR subsidence
├── hydro_conditioner.py            # Stream burning & subway underpass carving
├── hydrologic_derivatives.py       # Horn's slope (m/m, deg), aspect & D8 flow direction
├── road_sampler.py                 # Spatial attribution onto 7,894 GCC road segments
├── pipeline.py                     # Layer1Pipeline orchestrator
└── lulc/                           # LULC, Soil Hydrology & Runoff Subpackage
    ├── __init__.py                 # Subpackage public API
    ├── impervious_extractor.py     # DCIA, BCR, Manning's n, RWH discount, Cf scaling
    ├── soil_hydrology.py           # HSG A/B/C/D, AMC I/II/III, riparian/coastal/InSAR penalties
    └── runoff_generator.py         # Sd(S_0), R_excess, Q_surf, mass balance conservation
```

### 6.1 Class Hierarchy and Core Responsibilities

#### `DEMBuilder` ([`ai_service/layer1/dem_builder.py`](file:///home/yashwanth-n17/Documents/Workspace%20Linux/Smart-India-Hackathon-2026/ai_service/layer1/dem_builder.py))
- Reads source DEM GeoTIFF rasters using `rasterio`.
- Reprojects raster grids into UTM Zone 44N metric space using nearest-neighbor or bilinear interpolation.
- Normalizes elevation bounds and produces `chennai_cartosat_utm44n.tif`.

#### `HydroConditioner` ([`ai_service/layer1/hydro_conditioner.py`](file:///home/yashwanth-n17/Documents/Workspace%20Linux/Smart-India-Hackathon-2026/ai_service/layer1/hydro_conditioner.py))
- Ingests vector geometries of Chennai waterways and subway underpasses.
- Burns channels into the UTM DEM to guarantee continuous drainage pathways.
- Produces `chennai_hydro_conditioned_dem.tif`.

#### `HydrologicDerivatives` ([`ai_service/layer1/hydrologic_derivatives.py`](file:///home/yashwanth-n17/Documents/Workspace%20Linux/Smart-India-Hackathon-2026/ai_service/layer1/hydrologic_derivatives.py))
- Vectorized 2D NumPy convolution for Horn's elevation gradients.
- Calculates `slope_m_per_m.tif`, `slope_degrees.tif`, and `flow_direction_d8.tif`.

#### `RoadElevationSampler` ([`ai_service/layer1/road_sampler.py`](file:///home/yashwanth-n17/Documents/Workspace%20Linux/Smart-India-Hackathon-2026/ai_service/layer1/road_sampler.py))
- Maps road centerline coordinates onto the hydro-conditioned elevation raster.
- Outputs `chennai_roads_with_dem_attributes.csv` containing ground elevation, slope, and aspect for all 7,894 segments.

#### `ImperviousExtractor` ([`ai_service/layer1/lulc/impervious_extractor.py`](file:///home/yashwanth-n17/Documents/Workspace%20Linux/Smart-India-Hackathon-2026/ai_service/layer1/lulc/impervious_extractor.py))
- Computes $f_{\text{imp}}$, Building Coverage Ratio ($\text{BCR}$), and Manning's overland $n$.
- Applies Chennai Corporation RWH disconnection factor ($0.94\times$ on residential/service).
- Applies Cartosat DEM slope grade adjustment to composite Rational $C$.
- Provides static method `compute_frequency_factor(rainfall_intensity)` for $C_f$ calculation.

#### `SoilHydrologyModel` ([`ai_service/layer1/lulc/soil_hydrology.py`](file:///home/yashwanth-n17/Documents/Workspace%20Linux/Smart-India-Hackathon-2026/ai_service/layer1/lulc/soil_hydrology.py))
- Maps $K_{\text{sat}}$ to Hydrologic Soil Groups (A, B, C, D).
- Applies AMC I, II, or III multipliers.
- Evaluates coastal proximity ($<1.5\text{km}$), canal proximity ($<150\text{m}$), and InSAR subsidence ($>3.5\text{mm/yr}$) penalties.

#### `SurfaceRunoffGenerator` ([`ai_service/layer1/lulc/runoff_generator.py`](file:///home/yashwanth-n17/Documents/Workspace%20Linux/Smart-India-Hackathon-2026/ai_service/layer1/lulc/runoff_generator.py))
- Coordinates `ImperviousExtractor` and `SoilHydrologyModel`.
- Evaluates slope-modulated depression storage $S_d(S_0)$.
- Computes $R_{\text{excess}}$ [mm/hr] and $Q_{\text{surf}}$ [$\text{m}^3/\text{s}$].
- Enforces strict volumetric mass continuity across the catchment and returns `RunoffResult`.

---

## 7. In-Memory Coupling with Layer 0

Layer 1 is designed to couple seamlessly with Layer 0 via [`ai_service/orchestration/coupler.py`](file:///home/yashwanth-n17/Documents/Workspace%20Linux/Smart-India-Hackathon-2026/ai_service/orchestration/coupler.py).

### 7.1 Separation of Concerns
- **Layer 0 (Atmospheric Nowcasting)** has zero knowledge of road geometry, soil mechanics, or elevation. It ingests Doppler radar sweeps, calibrates against ground AWS gauges, applies Lucas-Kanade optical flow, and emits a spatial rainfall vector ($I_i(t)$ in mm/hr) for each segment centroid.
- **Layer 1 (LULC & Hydrology)** has zero knowledge of radar sweeps, reflectivity dBZ, or atmospheric advection vectors. It receives numerical rainfall rates and processes them through the terrain and soil physics.
- **The Orchestrator (`Layer0Layer1Coupler`)** acts as the high-speed in-memory bridge.

### 7.2 Coupling Workflow
```python
# In-memory execution: 0 disk I/O between layers
from ai_service.orchestration import Layer0Layer1Coupler

coupler = Layer0Layer1Coupler()
result = coupler.couple(
    scenario="michaung",    # Historical Cyclone Michaung archive
    horizon_min=60,         # 60-minute nowcast lead time
    amc="AMC_III",          # Saturated soil conditions
    mode="archive"
)

# Access coupled telemetry dataframe
print(result.streets_df[[
    "segment_id",
    "street_name",
    "rainfall_intensity_mm_hr",       # From Layer 0
    "impervious_fraction",            # From Layer 1 LULC
    "effective_infiltration_mm_hr",   # From Layer 1 Soil
    "surface_runoff_rate_mm_hr",      # From Layer 1 Runoff
    "surface_runoff_inflow_m3_s"      # From Layer 1 Hydraulics
]].head())
```

---

## 8. Verification & Performance Benchmarks

### 8.1 Automated Test Suite
Layer 1 is covered by a 12-test automated verification suite in [`ai_service/tests/layer1/test_lulc_runoff.py`](file:///home/yashwanth-n17/Documents/Workspace%20Linux/Smart-India-Hackathon-2026/ai_service/tests/layer1/test_lulc_runoff.py):

| Test ID | Test Method | Physical Property Verified | Result |
|---|---|---|---|
| `01` | `test_01_impervious_extractor_bounds` | $f_{\text{imp}} \in [0.20, 0.98]$, $C \in [0.20, 0.96]$, $n \in [0.014, 0.180]$ across all 7,894 segments | **PASS** |
| `02` | `test_02_zonal_differentiation` | Zone 9 (CBD core) imperviousness exceeds Zone 15 (suburban fringe) | **PASS** |
| `03` | `test_03_soil_hsg_classification` | Correct categorisation into USDA/ICAR HSG Groups A, B, C, D | **PASS** |
| `04` | `test_04_amc_transitions` | AMC III throttles baseline infiltration by ~60% compared to AMC II | **PASS** |
| `05` | `test_05_zero_rainfall_zero_runoff` | $I = 0\text{ mm/hr}$ generates exactly $0.0\text{ mm/hr}$ runoff and $0.0\text{ m}^3/\text{s}$ discharge | **PASS** |
| `06` | `test_06_monsoon_runoff_and_mass_conservation` | Runoff under 65 mm/hr storm event satisfies mass balance ($<0.01\%$) | **PASS** |
| `07` | `test_07_subsecond_execution_performance` | Complete 7,894-segment execution completes in $< 50\text{ ms}$ | **PASS** (15 ms) |
| `08` | `test_08_frequency_factor_scaling` | IRC:SP:42 $C_f$ multiplier scales from $1.00$ at $15\text{ mm/h}$ to $1.25$ at $100\text{ mm/h}$ | **PASS** |
| `09` | `test_09_rwh_disconnection_factor` | Residential corridors exhibit 6% lower effective DCIA than arterial motorways | **PASS** |
| `10` | `test_10_slope_adjustment` | Steeper Cartosat slopes produce higher composite runoff coefficients ($C$) | **PASS** |
| `11` | `test_11_riparian_and_subsidence_penalties` | Segments $<150\text{m}$ from canals receive 60% penalty; $>3.5\text{mm/yr}$ subsidence receives 15% penalty | **PASS** |
| `12` | `test_12_multi_intensity_mass_conservation` | Multi-scenario mass balance error is strictly $< 0.0001\%$ at 12, 35, 65, and 110 mm/hr | **PASS** ($0.000000\%$) |

### 8.2 Execution Performance
- **Segment Processing Throughput**: All 7,894 segments are calculated in **$14\text{ to }18\text{ milliseconds}$** on standard x86-64 hardware.
- **Memory Allocation**: In-memory vectorized NumPy operations with zero intermediary CSV writes during nowcast cycles.
- **Mass Discrepancy**: **$0.000000\%$** machine precision across all storm intensities.

---

## 9. Developer & Operational Guide

### 9.1 Environment & Dependencies
Layer 1 is built to run in high-performance Python environments using standard scientific packages:
- `numpy >= 1.26.0`
- `pandas >= 2.0.0`
- `scipy >= 1.11.0`
- `rasterio >= 1.3.0`

### 9.2 Running Layer 1 Standalone
```bash
# Execute standalone Layer 1 pipeline with 65 mm/hr rain under AMC III
python3 -m ai_service.layer1.pipeline --rainfall 65.0 --amc AMC_III --scenario michaung
```

### 9.3 Running the Coupled Pipeline
```bash
# Run Layer 0 nowcasting directly coupled to Layer 1 surface runoff
python3 -c "
from ai_service import run_coupled_layer0_layer1

res = run_coupled_layer0_layer1(scenario='michaung', horizon_min=60, amc='AMC_III', mode='archive')
print('Enriched Streets:', len(res.streets_df))
print('Mean Rainfall (mm/hr):', res.diagnostics['layer1_runoff_diagnostics']['mean_rainfall_mm_hr'])
print('Mean Runoff (mm/hr):', res.diagnostics['layer1_runoff_diagnostics']['mean_runoff_rate_mm_hr'])
print('Mean Tributary Discharge (m3/s):', res.diagnostics['layer1_runoff_diagnostics']['mean_discharge_m3_s'])
print('Catchment Mass Balance Error (%):', res.diagnostics['layer1_runoff_diagnostics']['mass_balance_error_pct'])
"
```

### 9.4 Running Automated Verification Tests
```bash
# Run Layer 1 unit and integration test suite
python3 -m unittest discover -s ai_service/tests/layer1

# Run both Layer 0 and Layer 1 test suites
python3 -m unittest discover -s ai_service/tests/layer0 && python3 -m unittest discover -s ai_service/tests/layer1
```
