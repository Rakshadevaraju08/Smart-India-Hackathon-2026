# Chennai Metropolitan Area (CMA) - Traffic & Transportation Flood Vulnerability Profile

## 1. Context & Data Sources
- **Sources Consulted:** Chennai Metropolitan Development Authority (CMDA) Comprehensive Mobility Plan (CMP 2019 / CTTS Update), Ministry of Road Transport and Highways (MoRTH), Chennai City Traffic Police (CCTP) annual data, and Tamil Nadu Road Development Company (TNRDC).
- **Urban Extent:** The Chennai Metropolitan Area spans over 1,189 sq km (expanded to 5,904 sq km under Chennai Master Plan III).
- **Vehicular Population:** Exceeds 6.2 Million registered vehicles, with a two-wheeler dominance of ~52-56% and personal cars comprising ~25-28%.

---

## 2. Key Arterial Corridors & Bottleneck Vulnerabilities
During cyclonic downpours and high-intensity rainfall events, specific critical road corridors experience catastrophic failure:
1. **GST Road (NH 32 - Airport Corridor):**
   - *Daily Volume:* ~194,200 PCU.
   - *Failure Mechanism:* The subway beneath the Chennai International Airport runway and the Chromepet/Pallavaram railway crossings receive heavy overland runoff from the Pallavaram hillocks. Water depths frequently reach 40–80 cm, severing the southern gateway of Chennai.
2. **Anna Salai (Mount Road - Central Spine):**
   - *Daily Volume:* ~178,500 PCU.
   - *Failure Mechanism:* Saidapet Maraimalai Adigal Bridge approaches and Gemini Flyover underpass experience backwater surcharging from Adyar river and Buckingham Canal tributaries.
3. **Rajiv Gandhi Salai (OMR IT Expressway):**
   - *Daily Volume:* ~128,400 PCU.
   - *Failure Mechanism:* Flanked by the Pallikaranai marshland on the west and Buckingham Canal on the east. Service lanes between SRP Tools, Perungudi, and Karapakkam experience chronic sheet flow flooding exceeding 30 cm.
4. **Poonamallee High Road (EVR Periyar Salai):**
   - *Daily Volume:* ~138,600 PCU.
   - *Failure Mechanism:* Serves key tertiary hospitals (Kilpauk Medical College, Rajiv Gandhi Government General Hospital). Waterlogging near KMC Hospital and Nehru Park blocks ambulance movements.
5. **Velachery Bypass & 100 Feet Road:**
   - *Daily Volume:* ~86,400 PCU.
   - *Failure Mechanism:* Built on the floodplains of Velachery Lake and Pallikaranai marsh. When Velachery Lake surplus spills, water depths routinely exceed 50–100 cm, trapping thousands of vehicles.

---

## 3. Integration with Flood-Aware Safe Routing API (Problem Statement Core)
- Standard navigation maps (e.g., Google Maps) route ambulances and emergency dispatchers through the fastest theoretical paths, often steering them into deeply inundated underpasses.
- **Dynamic Routing Formulation:**
  - An edge $e$ in the navigation graph represents a road segment with length $L_e$, dry traversal time $T_{0,e}$, and predicted water depth $d(e, t)$ in centimeters at forecast lead time $t \in [0, 180\text{ min}]$.
  - The dynamic traversal cost function:
    $$C(e, t) = \begin{cases}
    T_{0, e} \cdot \left(1 + \gamma \cdot \left(\frac{d(e, t)}{d_{\text{caution}}}\right)^2\right) & \text{if } d(e, t) \le d_{\text{impassable}} \\
    \infty & \text{if } d(e, t) > d_{\text{impassable}}
    \end{cases}$$
  - **Threshold Parameters by Vehicle Category:**
    | Vehicle Type | Caution Depth $d_{\text{caution}}$ | Impassable Depth $d_{\text{impassable}}$ | Speed Penalty Factor $\gamma$ |
    |---|---|---|---|
    | **Emergency Ambulance** | 15 cm | 30 cm | 2.5 |
    | **City Bus / Heavy Transport** | 25 cm | 45 cm | 1.8 |
    | **Standard Passenger Car** | 10 cm | 20 cm | 3.5 |
    | **Two-Wheeler (Motorcycle/Scooter)** | 5 cm | 15 cm | 5.0 |
