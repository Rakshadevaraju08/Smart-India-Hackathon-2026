"""Layer 0: Multi-Sensor Optimal Interpolation (OI) & 2D Spatial Kalman Fusion.

Fuses IMD Doppler Weather Radar, 35 GCC Ward Telemetry Gauges, Telecom CML Links,
and INSAT-3DS Satellite Hydro-Estimator into a minimum-variance analysis grid.
"""

from dataclasses import dataclass
import numpy as np
from scipy.spatial.distance import cdist
from scipy.sparse import csr_matrix, lil_matrix
from typing import Dict, List, Tuple, Optional, Any


class MultiSensorKalmanFusion:
    """Optimal Interpolation (2D-Var) engine with Gaspari-Cohn spatial localization."""

    def __init__(self,
                 bounds: Tuple[float, float, float, float] = (79.60, 12.65, 80.35, 13.35),
                 shape: Tuple[int, int] = (79, 83),
                 corr_length_km: float = 12.0,
                 loc_cutoff_km: float = 25.0,
                 sigma_background: float = 0.45):
        self.min_lon, self.min_lat, self.max_lon, self.max_lat = bounds
        self.n_lat, self.n_lon = shape
        self.n_cells = self.n_lat * self.n_lon
        self.L_b = corr_length_km
        self.c0 = loc_cutoff_km
        self.sigma_b = sigma_background

        # Precompute coordinate grid
        lats = np.linspace(self.min_lat, self.max_lat, self.n_lat)
        lons = np.linspace(self.min_lon, self.max_lon, self.n_lon)
        grid_lon, grid_lat = np.meshgrid(lons, lats)
        self.grid_coords = np.column_stack([grid_lat.ravel(), grid_lon.ravel()])

    def _gaspari_cohn(self, r: np.ndarray) -> np.ndarray:
        """Evaluate Gaspari-Cohn 5th-order compact polynomial correlation taper."""
        z = r / self.c0
        taper = np.zeros_like(z)
        m1 = (z >= 0.0) & (z <= 1.0)
        m2 = (z > 1.0) & (z <= 2.0)

        # 0 <= z <= 1
        taper[m1] = 1.0 - (5.0/3.0)*z[m1]**2 + (5.0/8.0)*z[m1]**3 + 0.5*z[m1]**4 - 0.25*z[m1]**5
        # 1 < z <= 2
        taper[m2] = 4.0 - 5.0*z[m2] + (5.0/3.0)*z[m2]**2 + (5.0/8.0)*z[m2]**3 - 0.5*z[m2]**4 + (1.0/12.0)*z[m2]**5 - (2.0 / (3.0 * z[m2]))
        return np.maximum(0.0, taper)

    def _build_gauge_operator(self, gauge_coords: np.ndarray) -> csr_matrix:
        """Construct sparse bilinear observation operator H_gauge."""
        P = len(gauge_coords)
        H = lil_matrix((P, self.n_cells), dtype=np.float32)

        dlat = (self.max_lat - self.min_lat) / (self.n_lat - 1)
        dlon = (self.max_lon - self.min_lon) / (self.n_lon - 1)

        for p in range(P):
            g_lat, g_lon = gauge_coords[p]
            r = np.clip((g_lat - self.min_lat) / dlat, 0, self.n_lat - 2)
            c = np.clip((g_lon - self.min_lon) / dlon, 0, self.n_lon - 2)
            r0, c0 = int(np.floor(r)), int(np.floor(c))
            r1, c1 = r0 + 1, c0 + 1
            dr, dc = r - r0, c - c0

            # Bilinear weights
            H[p, r0 * self.n_lon + c0] = (1 - dr) * (1 - dc)
            H[p, r0 * self.n_lon + c1] = (1 - dr) * dc
            H[p, r1 * self.n_lon + c0] = dr * (1 - dc)
            H[p, r1 * self.n_lon + c1] = dr * dc

        return H.tocsr()

    def fuse(self,
             radar_grid: np.ndarray,
             gauges_data: Dict[str, Dict[str, Any]],
             cml_telemetry: Optional[Dict[str, Dict[str, Any]]] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Perform 2D Optimal Interpolation multi-sensor fusion."""
        c = 0.1
        clean_radar = np.nan_to_num(radar_grid, nan=0.0, posinf=500.0, neginf=0.0).astype(np.float64)
        x_b = np.log(np.maximum(0.0, clean_radar.ravel()) + c).astype(np.float64)

        # Extract gauge and CML observations
        obs_coords, obs_vals, obs_vars = [], [], []

        # 1. Gauges
        if gauges_data:
            for g_id, g in gauges_data.items():
                if not isinstance(g, dict):
                    continue
                lat = g.get('latitude', g.get('lat'))
                lon = g.get('longitude', g.get('lon'))
                raw_rate = g.get('rainfall_rate_mm_hr', g.get('rate', 0.0))
                if lat is not None and lon is not None:
                    try:
                        f_lat = float(lat)
                        f_lon = float(lon)
                        f_rate = float(raw_rate) if raw_rate is not None else 0.0
                        if not (np.isfinite(f_lat) and np.isfinite(f_lon)):
                            continue
                        f_rate = max(0.0, f_rate) if np.isfinite(f_rate) else 0.0
                        obs_coords.append([f_lat, f_lon])
                        obs_vals.append(np.log(f_rate + c))
                        obs_vars.append(0.08 + 0.02 * np.sqrt(f_rate))
                    except (ValueError, TypeError):
                        continue

        # 2. CML Midpoints (if provided)
        if cml_telemetry:
            for c_id, c_link in cml_telemetry.items():
                if not isinstance(c_link, dict):
                    continue
                lat = c_link.get('midpoint_lat')
                lon = c_link.get('midpoint_lon')
                raw_rate = c_link.get('retrieved_rain_rate_mm_hr', 0.0)
                if lat is not None and lon is not None:
                    try:
                        f_lat = float(lat)
                        f_lon = float(lon)
                        f_rate = float(raw_rate) if raw_rate is not None else 0.0
                        if not (np.isfinite(f_lat) and np.isfinite(f_lon)):
                            continue
                        f_rate = max(0.0, f_rate) if np.isfinite(f_rate) else 0.0
                        obs_coords.append([f_lat, f_lon])
                        obs_vals.append(np.log(f_rate + c))
                        obs_vars.append(0.12 + 0.03 * np.sqrt(f_rate))
                    except (ValueError, TypeError):
                        continue

        P_obs = len(obs_vals)
        if P_obs == 0:
            return clean_radar.astype(np.float32), {'status': 'no_observations_used'}

        obs_coords = np.array(obs_coords, dtype=np.float64)
        y_obs = np.array(obs_vals, dtype=np.float64)
        R_obs_diag = np.array(obs_vars, dtype=np.float64)
        H_obs = self._build_gauge_operator(obs_coords)

        # Innovation at observation sites
        innov = y_obs - H_obs.dot(x_b)

        # Compute cross-covariance B * H_obs^T (n_cells x P_obs)
        dist_grid_obs = cdist(self.grid_coords, obs_coords) * 111.0
        soar_corr = (1.0 + dist_grid_obs / self.L_b) * np.exp(-dist_grid_obs / self.L_b)
        taper = self._gaspari_cohn(dist_grid_obs)
        BHt = (self.sigma_b ** 2) * (soar_corr * taper)  # Shape: (n_cells, P_obs)

        # Observation-to-observation covariance H_obs * B * H_obs^T
        dist_obs_obs = cdist(obs_coords, obs_coords) * 111.0
        HBHt = (self.sigma_b ** 2) * (
            (1.0 + dist_obs_obs / self.L_b) * np.exp(-dist_obs_obs / self.L_b) * self._gaspari_cohn(dist_obs_obs)
        )

        # Solve system: (H B H^T + R) w = innov
        A_mat = HBHt + np.diag(R_obs_diag)
        try:
            weights = np.linalg.solve(A_mat, innov)
        except np.linalg.LinAlgError:
            weights, _, _, _ = np.linalg.lstsq(A_mat, innov, rcond=1e-4)

        # State analysis update: x_a = x_b + B H^T w
        dx = BHt.dot(weights)
        x_a = x_b + dx

        # Invert log transform: R = exp(x_a) - c
        R_fused = np.maximum(0.0, np.exp(x_a) - c).reshape(self.n_lat, self.n_lon)

        diagnostics = {
            'mean_innovation': float(np.mean(innov)),
            'max_dx': float(np.max(np.abs(dx))),
            'observation_count': P_obs,
            'status': 'converged'
        }
        return R_fused.astype(np.float32), diagnostics
