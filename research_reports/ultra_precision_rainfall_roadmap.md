# Ultra-Precision Precipitation Nowcasting & Super-Resolution Roadmap
## Physics-Informed Deep Learning, Opportunistic Sensing & Microphysics Downscaling
**Document ID:** MoES-NCMRWF-SIH2026-PRECISION-L0  
**Target:** 100m Spatial Grid | 1-Minute Temporal Cadence | Probabilistic Stochastic Ensembles  
**Basin:** Greater Chennai Corporation (GCC) & Adyar/Cooum/Kosasthalaiyar Catchments  

---

## 1. Global Frontier Deep Learning & Physics-Informed Models (2024–2026)

### 1.1 Comparative Benchmark Matrix of Frontier AI Precipitation Models

| Model | Lab / Release | Core Architecture | Input -> Output Resolution | Lead Time / Cadence | Extreme Rain Skill (CSI @ 30+ mm/hr) | Code & Weight Availability |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **NowcastNet** | Tsinghua Univ & UC Berkeley (*Nature* 2023) | Physics-Informed Generative (Advective Continuity + Two-Path UNet) | 1 km -> 1 km (2048 x 2048 km domain) | 0–3 hr / 10 min | **CSI = 0.385** (Outperforms DGMR by 42%) | Code Ocean DOI: 10.24433/CO.0832447.v1<br>HuggingFace: OneScience-Group/NowcastNet_Earth |
| **DiffCast** | Tsinghua / CVPR 2024 | Residual Diffusion (Deterministic Global Motion + Stochastic Residual) | 1 km -> 1 km | 0–3 hr / 6–10 min | **CSI = 0.362** (Eliminates perceptual blur) | GitHub: DeminYu98/DiffCast (PyTorch) |
| **PreDiff** | HKUST / NeurIPS 2023 | Latent Diffusion Model (LDM) with Physical Knowledge Alignment | 1 km -> 1 km | 0–2 hr / 10 min | **CSI = 0.348** (Constrained mass balance) | GitHub: gaozhihan/PreDiff (PyTorch) |
| **NVIDIA CorrDiff** | NVIDIA Earth-2 (2024) | Score-Based Corrector Diffusion (EDM formulation) | 25 km / 9 km NWP -> 2 km / 500m | 0–24 hr / Hourly to sub-hourly | **High-Frequency PSD Preservation** | GitHub: NVIDIA/earth2studio & NVIDIA/physicsnemo |
| **MetNet-3** | Google DeepMind (2023–2024) | Spatiotemporal Axial Attention UNet + Sensor Densification | 1 km MRMS + Sat + GFS -> 1 km | 0–24 hr / **2 min** | Highest 24-hr CRPS across CONUS | Proprietary Google checkpoints (Operational in Google Search Weather) |
| **PySteps 1.4+** | International Open Source Community (2024) | Multi-Scale FFT Cascade Decomposition + AR(p) Stochastic Advection | 1 km -> 1 km (Extensible to 100m) | 0–3 hr / **1–5 min** | Standard Operational Benchmark in DWD/BoM/MeteoSwiss | GitHub: pySTEPS/pysteps (Conda/Pip, MIT License) |

---

## 2. Opportunistic Urban Sensors for Chennai: Engineering Feasibility

While IMD operates Doppler Weather Radars (Chennai Port S-band, Sriharikota C-band) and ~25 Automated Weather Stations (AWS) in Chennai, opportunistic sensing provides 100x–1000x denser surface telemetry.

### 2.1 Commercial Microwave Links (CML) via Telecom Cell Towers
Mobile operators (Reliance Jio, Bharti Airtel, BSNL) interconnect urban cell towers via point-to-point microwave backhaul links operating at frequencies 13 to 38 GHz (and 70-80 GHz E-band for 5G).
Liquid water induces severe attenuation due to Mie scattering and dielectric absorption.
The specific path attenuation k (dB/km) is linked to path-averaged rain rate R (mm/hr) by the ITU-R P.838-3 Power Law:
    k = a * R^b <=> R = (k / a)^(1/b)
Chennai has over 12,000+ cellular backhaul links traversing GCC wards. Microwave beams travel 15-45m above ground, right beneath the radar beam (which overshoots at >800m altitude), perfectly catching localized ground cloudbursts.

### 2.2 Moving Vehicular Rain Sensing (Dashcams & Dynamic Wiper Rates)
Chennai features >80,000 auto-rickshaws, 45,000 cabs (Ola/Uber), and 3,500 MTC buses.
- Wiper frequency correlates with rain impact flux: R = alpha * (f_wipe)^beta + gamma * v_vehicle.
- Forward dashcams extract high-frequency rain streaks and contrast reduction via edge CV.

### 2.3 Crowdsourced Citizen Smartphone Barometric Pressure Networks
Modern smartphones contain MEMS barometers (0.01 hPa precision).
Severe tropical downbursts produce cold pool downdrafts that slam the surface, creating localized meso-high pressure bubbles (+1.0 to +3.5 hPa) 10-25 minutes before rain arrives.
When >5 phones detect Delta_p > +1.2 hPa within 500m, Layer 0 triggers a Convective Initiation Alert before radar reflectivity even descends to the ground.

---

## 3. Coastal & Topographical Microphysics Downscaling for Chennai

1. **Sea-Breeze Front (SBF) & Urban Heat Island (UHI) Convergence:**
   Moist easterlies from Bay of Bengal collide with Chennai's +2.5K urban thermal dome, forming stationary 2km-wide cloudburst corridors along Buckingham Canal / OMR.
2. **Warm-Rain Collision-Coalescence:**
   Rain formation is concentrated below 2.5 km with small-to-medium drop diameters (D0 < 1.4mm). Standard Marshall-Palmer (Z = 200 R^1.6) underestimates tropical rain by 30-50%. Must calibrate to maritime convective Z = 130 R^1.4 or dual-pol K_dp: R(K_dp) = 44.0 * |K_dp|^0.822.
3. **Beam Overshoot Geometry:**
   At 40-60 km range (South Chennai / Tambaram), the radar beam center is at ~583m AGL with beam top at 1.0-1.2 km. Radar misses shallow rain formation beneath 600m without ground calibration.

---

## 4. Top 3 Actionable Innovations for Layer 0 Pipeline

### Rank 1: PySteps 1.4+ Stochastic Cascade Decomposition & 1-Minute Sub-Stepping
- Decomposes rain field into spatial octave cascades via FFT; advects with AR(2) stochastic perturbations.
- Sub-steps advection vectors by 10x to interpolate 10-minute radar frames down to 1-minute intervals with mass conservation.
- Delivers P10, P50, P90, and Probability of Exceedance (>50 mm/hr) for emergency routing.

### Rank 2: Physics-Guided Topographical Swin-UNet Super-Resolution (1 km -> 100m)
- Conditions on 1 km radar, 30m Cartosat/Copernicus DEM elevation, slope gradient, surface imperviousness, and coastal distance.
- Enforces strict mass conservation layer: mean of 10x10 sub-pixels mathematically matches 1 km parent cell.

### Rank 3: Opportunistic CML & Personal Weather Station Kalman Bias Calibrator
- Inverts microwave attenuation via ITU-R P.838-3 power law.
- Interpolates ground-to-radar log-bias ratio using Kriging with External Drift (KED) with coastal distance and beam height covariates.
