"""Layer 0: CML Ingestor Module - Opportunistic Cellular Microwave Link Rainfall Ingestion.

Implements ITU-R P.838-3 specific attenuation power-law inversion:
    k = a * R^b  =>  R = (k / a)**(1/b)
where k is specific path attenuation in dB/km, and R is path-averaged rain rate in mm/hr.

Leverages existing cellular microwave backhaul links (Jio, Airtel, BSNL) across
Greater Chennai Corporation (GCC) wards to provide dense, near-surface (15-45m AGL)
precipitation telemetry directly beneath the Doppler radar beam.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

logger = logging.getLogger(__name__)

# ITU-R P.838-3 Coefficients for standard microwave backhaul frequencies (Horizontal & Vertical)
# Frequency (GHz): (a_H, b_H, a_V, b_V)
ITU_R_P838_COEFFICIENTS: Dict[int, Tuple[float, float, float, float]] = {
    13: (0.0240, 1.1516, 0.0210, 1.1200),
    15: (0.0367, 1.1190, 0.0335, 1.0890),
    18: (0.0707, 1.0818, 0.0604, 1.0515),
    23: (0.1287, 1.0230, 0.1128, 1.0001),
    26: (0.1747, 0.9930, 0.1538, 0.9754),
    38: (0.3844, 0.8552, 0.3524, 0.8410),
    73: (0.9500, 0.7200, 0.9100, 0.7100), # E-Band 5G backhaul
}

@dataclass
class CMLLink:
    """Represents a point-to-point commercial microwave backhaul link."""
    link_id: str
    tx_lat: float
    tx_lon: float
    rx_lat: float
    rx_lon: float
    frequency_ghz: float = 18.0
    polarization: str = 'H'  # 'H' or 'V'
    tsl_dbm: float = 15.0    # Transmit Signal Level
    rsl_dbm: float = -45.0   # Received Signal Level
    baseline_dbm: float = -45.0 # Dry weather baseline RSL
    length_km: float = 0.0

    def __post_init__(self):
        if self.length_km <= 0.0:
            dlat = (self.rx_lat - self.tx_lat) * 111.0
            dlon = (self.rx_lon - self.tx_lon) * 111.0 * np.cos(np.radians(self.tx_lat))
            self.length_km = max(0.2, float(np.sqrt(dlat**2 + dlon**2)))

    @property
    def midpoint(self) -> Tuple[float, float]:
        """Return (lat, lon) midpoint of link path."""
        return ((self.tx_lat + self.rx_lat) / 2.0, (self.tx_lon + self.rx_lon) / 2.0)


# Representative GCC ward microwave backhaul topology (15 key links across Chennai)
CHENNAI_CML_TOPOLOGY: List[Dict[str, Any]] = [
    {'id': 'CML-CHN-01', 'tx': (13.0827, 80.2755), 'rx': (13.0674, 80.2443), 'freq': 18.0, 'pol': 'H', 'zone': 'Central'}, # Ripon -> Nungambakkam
    {'id': 'CML-CHN-02', 'tx': (13.0674, 80.2443), 'rx': (13.0418, 80.2335), 'freq': 23.0, 'pol': 'H', 'zone': 'Central'}, # Nungambakkam -> T. Nagar
    {'id': 'CML-CHN-03', 'tx': (13.0418, 80.2335), 'rx': (13.0062, 80.2570), 'freq': 18.0, 'pol': 'V', 'zone': 'South'},   # T. Nagar -> Adyar
    {'id': 'CML-CHN-04', 'tx': (13.0062, 80.2570), 'rx': (12.9792, 80.2195), 'freq': 23.0, 'pol': 'H', 'zone': 'South'},   # Adyar -> Velachery
    {'id': 'CML-CHN-05', 'tx': (12.9792, 80.2195), 'rx': (12.9010, 80.2279), 'freq': 18.0, 'pol': 'H', 'zone': 'South'},   # Velachery -> Sholinganallur
    {'id': 'CML-CHN-06', 'tx': (13.0418, 80.2335), 'rx': (13.0035, 80.2015), 'freq': 18.0, 'pol': 'H', 'zone': 'South'},   # T. Nagar -> Alandur
    {'id': 'CML-CHN-07', 'tx': (13.0035, 80.2015), 'rx': (12.9900, 80.1693), 'freq': 23.0, 'pol': 'V', 'zone': 'South'},   # Alandur -> Meenambakkam
    {'id': 'CML-CHN-08', 'tx': (13.0827, 80.2755), 'rx': (13.1118, 80.2436), 'freq': 18.0, 'pol': 'H', 'zone': 'North'},   # Ripon -> Perambur
    {'id': 'CML-CHN-09', 'tx': (13.1118, 80.2436), 'rx': (13.1481, 80.2315), 'freq': 18.0, 'pol': 'H', 'zone': 'North'},   # Perambur -> Madhavaram
    {'id': 'CML-CHN-10', 'tx': (13.1481, 80.2315), 'rx': (13.1672, 80.2581), 'freq': 23.0, 'pol': 'H', 'zone': 'North'},   # Madhavaram -> Manali
    {'id': 'CML-CHN-11', 'tx': (13.1672, 80.2581), 'rx': (13.2185, 80.3214), 'freq': 18.0, 'pol': 'V', 'zone': 'North'},   # Manali -> Kathivakkam
    {'id': 'CML-CHN-12', 'tx': (13.0890, 80.1990), 'rx': (13.1143, 80.1552), 'freq': 23.0, 'pol': 'H', 'zone': 'West'},    # Anna Nagar -> Ambattur
    {'id': 'CML-CHN-13', 'tx': (13.0512, 80.2120), 'rx': (13.0405, 80.1742), 'freq': 18.0, 'pol': 'H', 'zone': 'West'},    # Vadapalani -> Valasaravakkam
    {'id': 'CML-CHN-14', 'tx': (13.0827, 80.2755), 'rx': (13.0982, 80.2741), 'freq': 38.0, 'pol': 'H', 'zone': 'North'},   # Ripon -> Basin Bridge
    {'id': 'CML-CHN-15', 'tx': (13.0982, 80.2741), 'rx': (13.1250, 80.2885), 'freq': 23.0, 'pol': 'V', 'zone': 'North'},   # Basin Bridge -> Tondiarpet
]


class CMLPrecipitationEngine:
    """Inverts commercial microwave link signal attenuation to rain rate."""

    def __init__(self, wet_antenna_attenuation_db: float = 1.8):
        self.waa_db = wet_antenna_attenuation_db

    @staticmethod
    def get_itu_parameters(frequency_ghz: float, polarization: str = 'H') -> Tuple[float, float]:
        """Retrieve ITU-R P.838-3 (a, b) coefficients via nearest available frequency."""
        known_freqs = np.array(list(ITU_R_P838_COEFFICIENTS.keys()))
        nearest_freq = known_freqs[np.argmin(np.abs(known_freqs - frequency_ghz))]
        a_H, b_H, a_V, b_V = ITU_R_P838_COEFFICIENTS[int(nearest_freq)]
        return (a_H, b_H) if polarization.upper() == 'H' else (a_V, b_V)

    def invert_link(self, link: CMLLink) -> float:
        """Invert single link attenuation to path-averaged rain rate (mm/hr)."""
        if not np.isfinite(link.rsl_dbm) or not np.isfinite(link.baseline_dbm):
            return 0.0

        total_attenuation = link.baseline_dbm - link.rsl_dbm
        if total_attenuation <= 0.2:
            return 0.0

        # Physical ceiling on microwave rain attenuation (link drop/outage safety cap)
        rain_attenuation = max(0.0, total_attenuation - self.waa_db)
        if rain_attenuation <= 0.05 or link.length_km <= 0.05:
            return 0.0

        specific_k = rain_attenuation / link.length_km  # dB/km
        a, b = self.get_itu_parameters(link.frequency_ghz, link.polarization)
        
        # Inversion formula: R = (k / a)**(1 / b)
        rain_rate = float((specific_k / a) ** (1.0 / b))
        # Cap at realistic physical maximum cloudburst rate (300 mm/hr) to avoid outage artifact spikes
        return round(min(300.0, max(0.0, rain_rate)), 2)

    def harvest_mesh_telemetry(
        self,
        simulated_storm_intensity: Optional[float] = None,
        epicenter_lat: float = 12.98,
        epicenter_lon: float = 80.22
    ) -> Dict[str, Dict[str, Any]]:
        """Harvest or simulate real-time CML readings across Chennai telecom mesh."""
        results = {}
        now_iso = datetime.now(timezone.utc).isoformat()

        for topo in CHENNAI_CML_TOPOLOGY:
            tx_lat, tx_lon = topo['tx']
            rx_lat, rx_lon = topo['rx']
            mid_lat = (tx_lat + rx_lat) / 2.0
            mid_lon = (tx_lon + rx_lon) / 2.0

            if simulated_storm_intensity is not None:
                dist_sq = (mid_lat - epicenter_lat)**2 + (mid_lon - epicenter_lon)**2
                decay = float(np.exp(-dist_sq / 0.04))
                true_rain_rate = simulated_storm_intensity * decay
            else:
                true_rain_rate = 0.0

            a, b = self.get_itu_parameters(topo['freq'], topo['pol'])
            length_km = max(0.5, float(np.sqrt(((rx_lat - tx_lat)*111.0)**2 + ((rx_lon - tx_lon)*111.0)**2)))
            
            if true_rain_rate > 0.1:
                k_true = a * (true_rain_rate ** b)
                rain_attenuation = k_true * length_km
                total_att = rain_attenuation + self.waa_db
            else:
                total_att = 0.0

            baseline = -45.0
            rsl = baseline - total_att

            link = CMLLink(
                link_id=topo['id'],
                tx_lat=tx_lat,
                tx_lon=tx_lon,
                rx_lat=rx_lat,
                rx_lon=rx_lon,
                frequency_ghz=topo['freq'],
                polarization=topo['pol'],
                tsl_dbm=15.0,
                rsl_dbm=round(rsl, 2),
                baseline_dbm=baseline,
                length_km=round(length_km, 2)
            )

            retrieved_rain = self.invert_link(link)

            results[topo['id']] = {
                'link_id': topo['id'],
                'midpoint_lat': round(mid_lat, 4),
                'midpoint_lon': round(mid_lon, 4),
                'length_km': round(length_km, 2),
                'frequency_ghz': topo['freq'],
                'polarization': topo['pol'],
                'attenuation_db': round(total_att, 2),
                'retrieved_rain_rate_mm_hr': retrieved_rain,
                'zone': topo['zone'],
                'timestamp': now_iso,
                'status': 'ACTIVE'
            }

        return results
