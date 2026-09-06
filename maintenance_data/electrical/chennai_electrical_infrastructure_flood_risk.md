# TANGEDCO Electrical Infrastructure - Urban Flood Risk Assessment

## 1. Context & Operational Vulnerability
- **Governing Agency:** Tamil Nadu Generation and Distribution Corporation (TANGEDCO) & Tamil Nadu Transmission Corporation (TANTRANSCO).
- **Urban Asset Hierarchy:**
  1. *400 kV / 230 kV Major Transmission Substations:* Bulk feeding city intake nodes (Ennore, Alandur, Mylapore, Koyambedu).
  2. *110 kV / 33 kV Distribution Substations:* Located directly in dense residential and commercial neighborhoods.
  3. *Distribution Transformers (DTs) & Ring Main Units (RMUs):* Mounted on dual-pole structures or ground plinths.
  4. *Low-Tension (LT) Pillar Boxes:* Street-corner junction boxes feeding domestic service connections (typically elevated 30–45 cm above road level).

---

## 2. Electrocution Hazard & Preemptive Power Shutdown Protocols
- **Failure Trigger Mechanism:**
  - Standard street-corner pillar boxes and ground-mounted DT plinths are positioned between **20 cm and 45 cm** above road grade.
  - When localized street water depth exceeds **25 cm**, water enters unsealed feeder pillar boxes, leading to phase-to-ground flashovers, underground cable insulation breakdown, and lethal electrocution risks for pedestrians wading through floodwaters.
- **The Blind Grid Shutdown Problem:**
  - Currently, because TANGEDCO lacks real-time, street-level flood depth nowcasting, engineers are forced to pull the master circuit breaker on an entire **11 kV feeder** or even an entire **33 kV substation** when waterlogging is reported by phone or social media.
  - *Consequence:* Life-saving medical facilities, water pumping booster stations, and communications towers in adjacent dry streets lose power unnecessarily for 12–36 hours.

---

## 3. How Flood Nowcasting Empowers TANGEDCO Grid Operations
1. **Targeted Micro-Feeder Tripping:**
   - By forecasting water depth $d > 25\text{ cm}$ at a 1-hour lead time, the SCADA system can de-energize only the specific downstream DT spur lines or RMU switches before water reaches the live busbars.
2. **Prioritizing Pumping Station & Hospital Feeder Lines:**
   - Critical infrastructure (e.g., GCC stormwater pumping stations at Vyasarpadi, Stanley Hospital, Rajiv Gandhi Government General Hospital) can be dynamically routed to alternate elevated 33 kV feeders.
3. **Post-Flood Rapid Restoration:**
   - Instead of manually inspecting thousands of submerged transformers after rains subside, utility crews receive a spatial GeoJSON map indicating exactly which asset pins remained above water and can be immediately re-energized.
