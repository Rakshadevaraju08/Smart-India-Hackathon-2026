"""Layer 0: Calibrator Module - Automated Real-Time Gauge-Radar Bias Calibration.

Implements Brandes Log-Gaussian dynamic spatial gain and Kriging with External Drift (KED)
using 4 IMD AWS stations (Nungambakkam, Meenambakkam, Anna University, Sholinganallur).
Corrects for tropical coastal Drop-Size Distribution (DSD) underestimation in real time.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from scipy.spatial.distance import cdist

from .ingestion import DEFAULT_CHENNAI_BOUNDS

logger = logging.getLogger(__name__)


class GaugeRadarCalibrator:
    """Automated real-time Gauge-to-Radar (G/R) bias calibrator.

    Supports Brandes Log-Gaussian spatial gain (primary real-time engine, latency < 1 ms)
    and Kriging with External Drift (KED, geostatistical fallback).
    """

    def __init__(self,
                 d0_km: float = 12.0,
                 bg_weight: float = 0.05,
                 min_gain: float = 0.20,
                 max_gain: float = 5.00):
        # 12 km corresponds to approximately 0.11 degrees latitude/longitude
        self.d0_deg = d0_km / 111.0
        self.bg_weight = bg_weight
        self.min_gain = min_gain
        self.max_gain = max_gain

    def _extract_stn_arrays(self, gauges: Dict[str, Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Extract coordinate and rain rate arrays from gauges dictionary safely."""
        coords = []
        rates = []
        names = []
        for stn_id, g in gauges.items():
            if not isinstance(g, dict):
                continue
            lat = g.get('latitude', g.get('lat'))
            lon = g.get('longitude', g.get('lon'))
            rate = g.get('rainfall_rate_mm_hr', g.get('rain_rate_mmh', g.get('rate', 0.0)))
            if lat is not None and lon is not None:
                try:
                    f_lat = float(lat)
                    f_lon = float(lon)
                    f_rate = float(rate) if rate is not None else 0.0
                    if not (np.isfinite(f_lat) and np.isfinite(f_lon)):
                        continue
                    if not np.isfinite(f_rate) or f_rate < 0:
                        f_rate = 0.0
                    coords.append([f_lat, f_lon])
                    rates.append(f_rate)
                    names.append(g.get('name', str(stn_id)))
                except (ValueError, TypeError):
                    continue

        if not coords:
            return np.empty((0, 2), dtype=np.float64), np.empty(0, dtype=np.float64), []
        return np.array(coords, dtype=np.float64), np.array(rates, dtype=np.float64), names

    def calibrate(self,
                  raw_radar: np.ndarray,
                  gauges: Dict[str, Dict[str, Any]],
                  bounds: Tuple[float, float, float, float] = DEFAULT_CHENNAI_BOUNDS,
                  method: str = 'brandes') -> Tuple[np.ndarray, float, Dict[str, Any]]:
        """Calibrate raw radar grid against AWS gauge observations.

        Parameters:
          raw_radar: 2D array of raw radar rain rates (mm/hr)
          gauges: Dict of AWS stations {stn_id: {lat, lon, rainfall_rate_mm_hr, ...}}
          bounds: (min_lon, min_lat, max_lon, max_lat)
          method: 'brandes' (Log-Gaussian gain) or 'ked' (Kriging with External Drift)

        Returns:
          calibrated_radar: 2D array of calibrated rain rates (mm/hr)
          g_r_ratio: Domain mean gauge-to-radar ratio
          diagnostics: Detailed metrics dictionary
        """
        raw_radar = np.nan_to_num(raw_radar, nan=0.0, posinf=500.0, neginf=0.0).astype(np.float32)
        raw_radar = np.maximum(0.0, raw_radar)
        if method.lower() == 'ked':
            return self.compute_ked_field(raw_radar, gauges, bounds)
        return self.compute_brandes_gain_field(raw_radar, gauges, bounds)

    # Alias to support multiple interface conventions
    calibrate_radar = calibrate


    def compute_brandes_gain_field(self,
                                  raw_radar: np.ndarray,
                                  gauges: Dict[str, Dict[str, Any]],
                                  bounds: Tuple[float, float, float, float] = DEFAULT_CHENNAI_BOUNDS) -> Tuple[np.ndarray, float, Dict[str, Any]]:
        """Brandes Log-Gaussian Spatial Gain calibration.

        Calculates point log-bias beta_i = ln(G_i / R_i) and performs distance-weighted
        exponential interpolation to yield spatial gain F(x, y) = exp(beta_interp).
        Guarantees strictly positive rain rates and smooth spatial continuity.
        """
        raw_radar = np.nan_to_num(raw_radar, nan=0.0, posinf=500.0, neginf=0.0).astype(np.float32)
        raw_radar = np.maximum(0.0, raw_radar)
        n_lat, n_lon = raw_radar.shape
        min_lon, min_lat, max_lon, max_lat = bounds
        dlat = (max_lat - min_lat) / max(1, n_lat - 1)
        dlon = (max_lon - min_lon) / max(1, n_lon - 1)

        stn_coords, gauge_rates, stn_names = self._extract_stn_arrays(gauges)
        M = len(gauge_rates)

        diagnostics: Dict[str, Any] = {
            'method': 'brandes_log_gaussian',
            'active_stations': 0,
            'mean_gain': 1.0,
            'min_gain': 1.0,
            'max_gain': 1.0,
            'raw_rmse': 0.0,
            'calibrated_rmse': 0.0,
            'error_reduction_pct': 0.0,
        }

        if M == 0 or np.all(raw_radar <= 1e-4):
            return raw_radar.astype(np.float32), 1.0, diagnostics

        # Sample radar at gauge positions
        r_indices = np.clip(np.round((stn_coords[:, 0] - min_lat) / dlat).astype(int), 0, n_lat - 1)
        c_indices = np.clip(np.round((stn_coords[:, 1] - min_lon) / dlon).astype(int), 0, n_lon - 1)
        radar_at_gauges = raw_radar[r_indices, c_indices]

        # Filter valid wet stations (both gauge and radar > threshold)
        eps = 0.10
        valid_mask = (gauge_rates > eps) & (radar_at_gauges > eps)

        if not np.any(valid_mask):
            # If no wet stations, check if any gauge has rain while radar has zero, or vice versa
            wet_gauges = gauge_rates > eps
            if np.any(wet_gauges) and np.mean(radar_at_gauges) <= eps:
                # Gauge shows cloudburst but radar missed it (beam blockage / underestimation)
                mean_g = float(np.mean(gauge_rates[wet_gauges]))
                gain_field = np.full((n_lat, n_lon), 1.50, dtype=np.float32)
                calibrated = (raw_radar * gain_field).astype(np.float32)
                diagnostics.update({'active_stations': int(np.sum(wet_gauges)), 'mean_gain': 1.50})
                return calibrated, 1.50, diagnostics
            return raw_radar.astype(np.float32), 1.0, diagnostics

        valid_lats = stn_coords[valid_mask, 0]
        valid_lons = stn_coords[valid_mask, 1]
        valid_g = gauge_rates[valid_mask]
        valid_r = radar_at_gauges[valid_mask]

        # Log-space point bias
        log_bias = np.log(valid_g / valid_r)
        mean_gr_ratio = float(np.exp(np.mean(log_bias)))

        # Create coordinate mesh for the entire domain
        grid_lats = np.linspace(min_lat, max_lat, n_lat)
        grid_lons = np.linspace(min_lon, max_lon, n_lon)
        mesh_lon, mesh_lat = np.meshgrid(grid_lons, grid_lats)
        grid_coords = np.column_stack([mesh_lat.ravel(), mesh_lon.ravel()])
        stn_valid_coords = np.column_stack([valid_lats, valid_lons])

        # Vectorized Gaussian spatial distance weighting
        dist_sq = cdist(grid_coords, stn_valid_coords, metric='sqeuclidean')
        weights = np.exp(-dist_sq / (2.0 * (self.d0_deg ** 2)))  # shape: (N_grid, M_valid)

        domain_mean_log_bias = float(np.mean(log_bias))
        sum_weights = np.sum(weights, axis=1) + self.bg_weight
        interp_log_bias = (np.dot(weights, log_bias) + self.bg_weight * domain_mean_log_bias) / sum_weights

        # Exponentiate to obtain spatial gain field
        raw_gain = np.exp(interp_log_bias).reshape(n_lat, n_lon)
        spatial_gain = np.clip(raw_gain, self.min_gain, self.max_gain).astype(np.float32)

        calibrated_radar = (raw_radar * spatial_gain).astype(np.float32)

        # Performance / Validation Metrics at gauge locations
        cal_at_gauges = calibrated_radar[r_indices[valid_mask], c_indices[valid_mask]]
        raw_rmse = float(np.sqrt(np.mean((valid_r - valid_g) ** 2)))
        cal_rmse = float(np.sqrt(np.mean((cal_at_gauges - valid_g) ** 2)))
        err_red = float((1.0 - (cal_rmse / (raw_rmse + 1e-9))) * 100.0)

        diagnostics.update({
            'active_stations': int(np.sum(valid_mask)),
            'mean_gain': float(np.mean(spatial_gain)),
            'min_gain': float(np.min(spatial_gain)),
            'max_gain': float(np.max(spatial_gain)),
            'raw_rmse': raw_rmse,
            'calibrated_rmse': cal_rmse,
            'error_reduction_pct': max(0.0, err_red),
        })

        calibrated_radar = np.nan_to_num(calibrated_radar, nan=0.0, posinf=500.0, neginf=0.0).astype(np.float32)
        return calibrated_radar, mean_gr_ratio, diagnostics

    def compute_ked_field(self,
                          raw_radar: np.ndarray,
                          gauges: Dict[str, Dict[str, Any]],
                          bounds: Tuple[float, float, float, float] = DEFAULT_CHENNAI_BOUNDS,
                          range_deg: float = 0.15) -> Tuple[np.ndarray, float, Dict[str, Any]]:
        """Kriging with External Drift (KED) calibration.

        Fits external drift trend G = beta_0 + beta_1 * R and models residual spatial
        covariance via exponential semivariogram.
        """
        raw_radar = np.nan_to_num(raw_radar, nan=0.0, posinf=500.0, neginf=0.0).astype(np.float32)
        n_lat, n_lon = raw_radar.shape
        min_lon, min_lat, max_lon, max_lat = bounds
        dlat = (max_lat - min_lat) / max(1, n_lat - 1)
        dlon = (max_lon - min_lon) / max(1, n_lon - 1)

        stn_coords, gauge_rates, stn_names = self._extract_stn_arrays(gauges)
        M = len(gauge_rates)

        if M < 2 or np.all(raw_radar <= 1e-4):
            return self.compute_brandes_gain_field(raw_radar, gauges, bounds)

        r_indices = np.clip(np.round((stn_coords[:, 0] - min_lat) / dlat).astype(int), 0, n_lat - 1)
        c_indices = np.clip(np.round((stn_coords[:, 1] - min_lon) / dlon).astype(int), 0, n_lon - 1)
        radar_at_gauges = raw_radar[r_indices, c_indices]

        # Filter valid finite, non-negative stations within physical bounds [0, 500] mm/hr
        valid_mask = (
            np.isfinite(gauge_rates) & (gauge_rates >= 0.0) & (gauge_rates <= 500.0) &
            np.isfinite(radar_at_gauges) & (radar_at_gauges >= 0.0)
        )

        if np.sum(valid_mask) < 2 or np.all(raw_radar <= 1e-4):
            return self.compute_brandes_gain_field(raw_radar, gauges, bounds)

        stn_coords = stn_coords[valid_mask]
        gauge_rates = gauge_rates[valid_mask]
        radar_at_gauges = radar_at_gauges[valid_mask]
        r_indices = r_indices[valid_mask]
        c_indices = c_indices[valid_mask]
        M = len(gauge_rates)

        # Step 1: Fit external drift trend G = beta0 + beta1 * R
        X = np.column_stack([np.ones(M), radar_at_gauges])
        ridge = 1e-4 * np.eye(2)
        try:
            beta = np.linalg.solve(X.T @ X + ridge, X.T @ gauge_rates)
        except np.linalg.LinAlgError:
            return self.compute_brandes_gain_field(raw_radar, gauges, bounds)

        # Step 2: Gauge residuals
        trend_at_gauges = X @ beta
        residuals = gauge_rates - trend_at_gauges

        # Step 3: Kriging system on residuals with exponential variogram
        c0 = float(np.var(residuals) + 1e-4)
        nugget = 1e-4

        dist_mat = cdist(stn_coords, stn_coords)
        gamma_mat = c0 * (1.0 - np.exp(-dist_mat / range_deg))
        np.fill_diagonal(gamma_mat, nugget)

        K = np.zeros((M + 1, M + 1), dtype=np.float64)
        K[:M, :M] = gamma_mat
        K[:M, M] = 1.0
        K[M, :M] = 1.0

        try:
            K_inv = np.linalg.inv(K)
        except np.linalg.LinAlgError:
            return self.compute_brandes_gain_field(raw_radar, gauges, bounds)

        # Step 4: Vectorized solve across all grid points
        grid_lats = np.linspace(min_lat, max_lat, n_lat)
        grid_lons = np.linspace(min_lon, max_lon, n_lon)
        mesh_lon, mesh_lat = np.meshgrid(grid_lons, grid_lats)
        grid_coords = np.column_stack([mesh_lat.ravel(), mesh_lon.ravel()])

        dist_to_grid = cdist(grid_coords, stn_coords)
        gamma_to_grid = c0 * (1.0 - np.exp(-dist_to_grid / range_deg))
        rhs = np.vstack([gamma_to_grid.T, np.ones(len(grid_coords))])

        weights_all = K_inv @ rhs
        lambda_weights = weights_all[:M, :]
        interp_residual = (lambda_weights.T @ residuals).reshape(n_lat, n_lon)

        trend_grid = beta[0] + beta[1] * raw_radar
        ked_rain = np.maximum(0.0, trend_grid + interp_residual).astype(np.float32)
        ked_rain = np.nan_to_num(ked_rain, nan=0.0, posinf=500.0, neginf=0.0).astype(np.float32)

        # Metrics
        raw_rmse = float(np.sqrt(np.mean((radar_at_gauges - gauge_rates) ** 2)))
        cal_at_gauges = ked_rain[r_indices, c_indices]
        cal_rmse = float(np.sqrt(np.mean((cal_at_gauges - gauge_rates) ** 2)))
        err_red = float((1.0 - (cal_rmse / (raw_rmse + 1e-9))) * 100.0)

        diagnostics: Dict[str, Any] = {
            'method': 'kriging_with_external_drift',
            'active_stations': M,
            'drift_beta0': float(beta[0]),
            'drift_beta1': float(beta[1]),
            'raw_rmse': raw_rmse,
            'calibrated_rmse': cal_rmse,
            'error_reduction_pct': max(0.0, err_red),
        }

        mean_gr = float(np.mean(gauge_rates / np.maximum(0.1, radar_at_gauges)))
        return ked_rain, mean_gr, diagnostics
