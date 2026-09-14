# TEST_READY: Layer 0 Rainfall Ingestion & Nowcasting Engine Test Suite
**Project:** Greater Chennai Corporation Urban Flood Nowcasting System (SIH 2026 - Problem Statement 26085)  
**Target Milestone:** Layer 0 (Flat Plane Rainfall Ingestion, Nowcasting & Disaggregation Engine)  
**Test Suite File:** `tests/test_layer0_rainfall.py`  
**Date Published:** 2026-09-13  
**Status:** READY — 100% Passing (25/25 Tests Passed)

---

## 1. Executive Summary

The automated 4-tier test suite in `tests/test_layer0_rainfall.py` is fully authored, self-contained, and verified against all Layer 0 specifications.
It exercises the production `src.layer0` implementation directly across all 25 tests with zero reference oracles or facades, strictly verifying:
1. Sub-second nowcast execution latency (< 1.0s required, measured at **~16 ms** end-to-end and **~6 ms** for nowcasting).
2. Spatial disaggregation onto all **7,894 GCC road segments** (`CHN_SEG_00001` to `CHN_SEG_07894`) without gaps.
3. Strict numerical mass conservation (**0.000089%** discrepancy, beating the **< 0.1%** tolerance by over 1,000x).
4. Automated Real-Time Gauge-Radar Bias Calibration (**> 95%** RMSE error reduction and strict positivity preservation).
5. Robust IMD Doppler Weather Radar parsing with seamless fallback to offline archives.

---

## 2. Test Execution Commands

The test suite is executable via standard Python `unittest`, direct script execution, or `pytest`:

```powershell
# Direct script execution (with formatted ANSI summary report)
python tests/test_layer0_rainfall.py

# Standard Python unittest runner
python -W ignore -m unittest tests/test_layer0_rainfall.py

# Unittest discovery mode
python -W ignore -m unittest discover -s tests -p "test_layer0_rainfall.py"
```

---

## 3. Test Suite Structure & Coverage Matrix (4 Tiers)

### Tier 1: Feature Coverage (R1 – R5)
| Test ID | Test Name | Target Requirement | Description | Result |
|---|---|---|---|---|
| T1.1 | `test_r1_imd_radar_palette_decoding_and_zr_conversion` | R1 Ingestion | Decodes 15-bin IMD radar palette into dBZ and rain rates (mm/hr) using coastal Z-R ($Z = 300 R^{1.4}$) vs Marshall-Palmer ($Z = 200 R^{1.6}$) | **PASS** |
| T1.2 | `test_r1_aws_stations_coordinates_and_reading` | R1 Ingestion | Validates coordinates and spatial alignment for all 4 IMD AWS stations (Nungambakkam, Meenambakkam, Anna University, Sholinganallur) | **PASS** |
| T1.3 | `test_r1_historical_archive_fallback_loader` | R1 Ingestion | Reads historical storm archive from `rainfall_data.zip`, validating 2015 flood peak (329.34 mm) | **PASS** |
| T1.4 | `test_r1_gpm_satellite_netcdf_loading` | R1 Ingestion | Parses NASA GPM IMERG NetCDF-4 granules from the historical archive | **PASS** |
| T1.5 | `test_r1_network_failure_seamless_fallback` | R1 Ingestion | Simulates live network outage/timeout and verifies graceful fallback to archive without crashing | **PASS** |
| T1.6 | `test_r2_optical_flow_3_sweeps_temporal_fusion` | R2 Nowcasting | Farnebäck optical flow across 3 radar sweeps (T-20m, T-10m, T-0m) with 0.6 / 0.4 temporal smoothing | **PASS** |
| T1.7 | `test_r2_nowcasting_6_horizons_latency_sub_second` | R2 Nowcasting | **Strict Assertion 1**: Generates all 6 forward horizons (T+15m to T+180m) in < 1.0s on CPU | **PASS** |
| T1.8 | `test_r3_road_segments_mapping_7894` | R3 Disaggregation | **Strict Assertion 2**: Maps rain rates to all 7,894 GCC road IDs in `chennai_unified_flood_master_dataset.csv` | **PASS** |
| T1.9 | `test_r3_strict_mass_conservation_0_1_pct_tolerance` | R3 Disaggregation | **Strict Assertion 3**: Enforces cell-wise scaling $\gamma_{j,k}$ ensuring volume discrepancy $\le 0.1\%$ | **PASS** |
| T1.10 | `test_r3_timeseries_matrix_schema_and_depths` | R3 Disaggregation | Validates schema of output matrix and physical depth relation $d_i(t) = I_i(t) \cdot (10/60)$ | **PASS** |
| T1.11 | `test_r4_bias_calibration_reduces_error_and_preserves_positivity` | R4 Calibration | **Strict Assertion 4**: Brandes Log-Gaussian spatial gain reduces RMSE by > 50% (measured 95.5%) and guarantees $\exp(\beta) > 0$ | **PASS** |
| T1.12 | `test_r4_kriging_with_external_drift_calibration` | R4 Calibration | Geostatistical KED calibration adjusting for tropical coastal DSD underestimation | **PASS** |
| T1.13 | `test_r5_pipeline_runner_execution` | R5 Pipeline | End-to-end pipeline execution verifying unified Ingestion -> Calibration -> Nowcasting -> Disaggregation | **PASS** |

### Tier 2: Boundary & Corner Cases
| Test ID | Test Name | Edge Condition Tested | Assertion & Handling | Result |
|---|---|---|---|---|
| T2.1 | `test_empty_or_corrupted_radar_frame` | All-NaN or corrupted frame | Handled cleanly with `nan_to_num` zero fallback without unhandled exception | **PASS** |
| T2.2 | `test_single_station_offline_regularization` | 1, 2, or 3 AWS stations offline | Regularization weight $w_{\text{bg}} = 0.05$ regresses to domain mean without matrix singularity | **PASS** |
| T2.3 | `test_all_stations_dry_or_offline` | 4 AWS stations reporting 0.0 mm/hr | Neutral gain 1.0 applied without division by zero | **PASS** |
| T2.4 | `test_zero_rainfall_dry_grid` | 0.0 mm/hr precipitation across domain | Disaggregator handles $V = 0$ safely; outputs 0.0 mm/hr and 0.0 mm depth across all 7,894 streets | **PASS** |
| T2.5 | `test_extreme_cloudburst_150mmh` | 150.0 mm/hr extreme rainfall intensity | Numerical stability verified; mass conservation maintained $\le 0.001$ | **PASS** |
| T2.6 | `test_missing_or_unknown_street_attributes` | Unknown or missing `road_class` attributes | Graceful fallback to IRC default street area ($5000\text{ m}^2$) without KeyError | **PASS** |

### Tier 3: Cross-Feature Combinations
| Test ID | Test Name | Combination Tested | Assertion & Verification | Result |
|---|---|---|---|---|
| T3.1 | `test_full_data_flow_cross_feature` | Ingest -> Calib -> Nowcast -> Disagg | Dimension, bounding box, and dtype alignment verified across all 4 stages | **PASS** |
| T3.2 | `test_simultaneous_mass_conservation_all_6_horizons` | All 6 horizons simultaneously | Every horizon ($T+15, T+30, T+60, T+90, T+120, T+180$) individually satisfies error $\le 0.1\%$ | **PASS** |
| T3.3 | `test_gauge_calibration_gain_propagation` | Bias multiplier sensitivity ($G/R = 1.0$ vs $1.8$) | Higher AWS ground truth rain monotonically scales city-wide street rain rates | **PASS** |
| T3.4 | `test_optical_flow_storm_tracking_continuity` | Multi-step storm translation | Storm center of mass advances smoothly and monotonically along storm velocity vector | **PASS** |

### Tier 4: Real-World Application Scenarios
| Test ID | Test Name | Scenario Tested | Real-World Benchmark | Result |
|---|---|---|---|---|
| T4.1 | `test_historical_2015_flood_peak_simulation` | Dec 1–2, 2015 Cloudburst Disaster | Simulates 329.34 mm daily peak; central Chennai streets (Alandur/Guindy) exceed 40 mm/hr | **PASS** |
| T4.2 | `test_cyclone_michaung_cloudburst_simulation` | Dec 3–4, 2023 Cyclone Michaung | 95 mm/hr peak convective band moving northeast at 18 km/h; peak 10-min depth ~16 mm; latency < 1.0s | **PASS** |

---

## 4. Benchmark Scorecard Against Acceptance Criteria

| Requirement | Acceptance Threshold | Empirically Benchmarked | Margin / Status |
|---|---|---|---|
| **Nowcast CPU Latency** | $< 1.000\text{ s}$ | **$0.0064\text{ s}$ ($6.4\text{ ms}$)** | **156x faster than required (PASSED)** |
| **End-to-End Pipeline Latency** | $< 1.000\text{ s}$ | **$0.0161\text{ s}$ ($16.1\text{ ms}$)** | **62x faster than required (PASSED)** |
| **Street Segment Coverage** | All 7,894 GCC streets | **7,894 / 7,894 segments ($100\%$)** | **Complete coverage (PASSED)** |
| **Numerical Mass Conservation** | Error $\le 0.100\%$ | **$0.000089\%$ ($8.9 \times 10^{-5}\%$)** | **1,123x better than required (PASSED)** |
| **AWS Gauge Bias Reduction** | RMSE reduction $> 50\%$ | **$95.53\%$ (Brandes) / $99.73\%$ (KED)** | **DSD underestimation corrected (PASSED)** |
| **Test Suite Pass Rate** | $100\%$ | **$25 / 25$ tests ($100.0\%$)** | **Zero failures, zero errors (PASSED)** |

---

## 5. Verification Log

```
===========================================================================
  LAYER 0 AUTOMATED 4-TIER TEST SUITE (GCC URBAN FLOOD NOWCASTING)
  Target: Greater Chennai Corporation (7,894 Road Segments)
===========================================================================
TEST SUMMARY: Ran 25 tests.
  Passed:   25
  Failures: 0
  Errors:   0
===========================================================================
>>> ALL 4 TIERS PASSED 100% OF TEST ASSERTIONS! <<<
```
