# Chennai Metropolitan Economy - Flood Exposure & Micro-Economic Damage Formulation

## 1. Executive Summary & Economic Significance
- **Metropolitan Economic Output:** Greater Chennai Corporation (GCC) generates over **₹1,146 Crore per day** in economic output across retail, wholesale, IT/software exports, automotive manufacturing, and port logistics.
- **Total Commercial Units:** Over **147,190 commercial establishments** registered under GCC trade licenses and spatial OpenStreetMap business nodes.
- **Direct Flood Exposure:** An estimated **36.7% of all commercial establishments** operate at ground floor or semi-basement levels without plinth protection against flash flooding $> 15\text{ cm}$.

---

## 2. Micro-Economic Vulnerability Zones
1. **The T. Nagar Retail Complex (Zone 9 - Teynampet):**
   - *Density:* 1,236 commercial units/sq km.
   - *Vulnerability:* Highest retail turnover concentration in South India. During street inundation $> 20\text{ cm}$, water ingress causes direct stock spoilage of expensive handloom fabrics, silk sarees, consumer electronics, and paper records.
   - *Hourly Business Interruption Loss:* ~₹2.4 Crore/hr.
2. **George Town / Parrys (Zone 5 - Royapuram):**
   - *Density:* 1,559 commercial units/sq km (highest physical density in Chennai).
   - *Vulnerability:* Century-old basement godowns stocking wholesale chemicals, paper, surgical supplies, and hardware. Surcharging drains flood basements rapidly, resulting in total inventory loss.
   - *Hourly Business Interruption Loss:* ~₹1.85 Crore/hr.
3. **Guindy Industrial Estate (Zone 12 - Alandur):**
   - *Vulnerability:* Precision CNC lathes, electronic circuit testing rigs, and automated manufacturing lines cannot tolerate water depths $> 10\text{ cm}$. In the 2015 floods, Guindy MSMEs suffered over ₹1,500 Crore in direct plant damage.
4. **OMR IT Corridor (Zones 13, 14, 15):**
   - *Vulnerability:* While server rooms are often placed on upper floors, underground diesel generator backup systems, chiller plants, and fiber conduit trenches sit in basements. Water depth $> 30\text{ cm}$ disables backup power and blocks commuter transport.

---

## 3. Depth-Damage Functions for Urban Flood Modeling
In hydraulic flood damage estimation, economic loss is calculated using depth-damage percentage curves $f(d)$:
$$\text{Direct Damage (INR)} = \sum_{i \in \text{Assets}} V_i \cdot f_k(d_i)$$
Where:
- $V_i$ = Insured replacement asset value of establishment $i$.
- $d_i$ = Water depth at establishment $i$ in centimeters.
- $f_k(d)$ = Damage curve for sector category $k$:

| Water Depth ($d$) | Retail Textiles/Jewellery | Industrial / MSME | IT/ITES Offices | Agro Wholesale / Food |
|---|---|---|---|---|
| **0 - 5 cm** | 2% (Minor cleanup) | 1% | 0% | 5% (Moisture loss) |
| **5 - 15 cm** | 15% (Ground shelf damage) | 10% (Motor damage) | 2% (Wiring) | 25% (Perishables) |
| **15 - 30 cm** | 45% (Inventory ruin) | 35% (Machinery loss) | 15% (Basement power) | 70% (Total rot) |
| **30 - 60 cm** | 80% (Severe structural/stock) | 65% (Heavy machinery) | 40% (Chiller outage) | 95% (Evacuated) |
| **> 60 cm** | 100% (Total inventory loss) | 90% (Catastrophic loss)| 75% (Facility shutdown)| 100% (Complete loss)|

By coupling the 0–3 hour nowcasted water depth to these economic curves, the decision-support system can quantify projected rupee damages and trigger targeted proactive mitigation (e.g., portable sandbag deployment, inventory elevation).
