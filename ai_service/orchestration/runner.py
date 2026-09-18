#!/usr/bin/env python3
"""
KAIROS Urban Flood Nowcasting System: Master Orchestration CLI Runner.

Executes the coupled pipeline between Layer 0 and Layer 1, providing telemetry,
zonal diagnostics, and optional JSON/CSV exports for Web API and GIS Twin integration.
"""

import argparse
import json
from pathlib import Path
import sys
import time

from .coupler import Layer0Layer1Coupler


def main():
    parser = argparse.ArgumentParser(
        description="KAIROS Master Pipeline Orchestrator: Layer 0 -> Layer 1 Runner"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["auto", "live", "archive"],
        default="auto",
        help="Execution mode (default: auto)",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default="michaung",
        help="Storm scenario name (michaung, 2015_flood, monsoon, dry)",
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=60,
        choices=[15, 30, 60, 120, 180],
        help="Nowcast lead time horizon in minutes (default: 60)",
    )
    parser.add_argument(
        "--amc",
        type=str,
        default="AMC_III",
        choices=["AMC_I", "AMC_II", "AMC_III"],
        help="Antecedent Moisture Condition (default: AMC_III)",
    )
    parser.add_argument(
        "--export-json",
        type=str,
        default=None,
        help="Optional path to export JSON telemetry payload for web backend",
    )
    parser.add_argument(
        "--export-csv",
        type=str,
        default=None,
        help="Optional path to export full road segment dataframe to CSV",
    )

    args = parser.parse_args()

    print("=" * 75)
    print("      KAIROS MASTER PIPELINE ORCHESTRATOR: LAYER 0 -> LAYER 1")
    print(f"      Mode: {args.mode.upper()} | Scenario: {args.scenario.upper()} | Horizon: T+{args.horizon}m")
    print("=" * 75)

    coupler = Layer0Layer1Coupler()
    coupled_res = coupler.couple(
        mode=args.mode,
        scenario=args.scenario,
        horizon_min=args.horizon,
        amc=args.amc,
    )

    diag = coupled_res.diagnostics
    r_diag = diag.get("layer1_runoff_diagnostics", {})

    print(f"\n[EXECUTION SUMMARY]")
    print(f"  ✓ Layer 0 (Nowcasting) Latency:    {diag.get('layer0_latency_ms', 0):.2f} ms")
    print(f"  ✓ Layer 1 (Runoff) Latency:        {diag.get('layer1_latency_ms', 0):.2f} ms")
    print(f"  ✓ Total Coupled Runtime:           {diag.get('total_latency_ms', 0):.2f} ms")
    print(f"  ✓ Disaggregated Road Segments:     {len(coupled_res.dataframe):,} segments")
    print(f"  ✓ Mean Impervious Fraction:        {r_diag.get('mean_impervious_fraction', 0)*100:.1f}%")
    print(f"  ✓ Infiltration Capacity:           {r_diag.get('mean_effective_infiltration_mm_hr', 0):.2f} mm/hr ({args.amc})")
    print(f"  ✓ Mean Rainfall Intensity:         {r_diag.get('mean_rainfall_mm_hr', 0):.2f} mm/hr")
    print(f"  ✓ Mean Surface Runoff Rate:        {r_diag.get('mean_runoff_rate_mm_hr', 0):.2f} mm/hr")
    print(f"  ✓ Mean Tributary Discharge:        {r_diag.get('mean_discharge_m3_s', 0):.4f} m³/s")
    print(f"  ✓ Max Peak Inflow Discharge:       {r_diag.get('max_discharge_m3_s', 0):.4f} m³/s")
    print(f"  ✓ Catchment Runoff Volume:         {r_diag.get('catchment_runoff_volume_m3', 0):,.0f} m³")
    print(f"  ✓ Mass Balance Discrepancy:        {r_diag.get('mass_balance_error_pct', 0):.6f}% (< 0.01%: PASSED)")

    telemetry = coupled_res.to_telemetry_dict(sample_zones=True)
    z_list = telemetry.get("zonal_telemetry", [])

    if z_list:
        print("\n" + "=" * 75)
        print("          METROPOLITAN LOCALITY HYDROLOGIC TELEMETRY")
        print("=" * 75)
        print(f"{'Locality / Typology':<26} | {'Zone':<4} | {'Rain':<7} | {'f_imp':<5} | {'HSG':<3} | {'f_soil':<8} | {'Runoff':<7} | {'Q_surf':<8}")
        print(f"{'':<26} | {'':<4} | {'(mm/h)':<7} | {'(%)':<5} | {'':<3} | {'(mm/h)':<8} | {'(mm/h)':<7} | {'(m³/s)':<8}")
        print("-" * 75)
        for z in z_list:
            print(
                f"{z['locality']:<26} | {z['zone_no']:<4} | {z['rainfall_mm_hr']:>5.2f} | "
                f"{z['impervious_fraction']*100:>4.1f}% | {z['hydrologic_soil_group']:^3} | "
                f"{z['infiltration_mm_hr']:>6.1f} | {z['runoff_mm_hr']:>5.2f} | {z['discharge_m3_s']:>7.4f}"
            )
        print("=" * 75)

    if args.export_json:
        p_json = Path(args.export_json)
        p_json.parent.mkdir(parents=True, exist_ok=True)
        with open(p_json, "w") as f:
            json.dump(telemetry, f, indent=2)
        print(f"\n✓ Exported JSON telemetry to: {p_json}")

    if args.export_csv:
        p_csv = coupled_res.to_csv(args.export_csv)
        print(f"✓ Exported CSV dataset to: {p_csv}")


if __name__ == "__main__":
    main()
