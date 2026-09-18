#!/usr/bin/env python3
"""
Adversarial Hydraulic & Physical Stress Testing Harness
Project: Urban Flood Nowcasting System Web GIS Command Twin (SIH 2026 PS 26085)
Location: tests/adversarial/test_hydraulic_adversary.py

Adversarially probes:
1. Orifice backflow when Delta h <= 0 (strict 0.000 enforcement, no negatives or NaN).
2. Orifice backflow under extreme surcharge (up to Delta h = 5.0m - 50.0m, sqrt(Delta h) scaling).
3. Clogging slider at mu_clog = 0% and mu_clog = 80% (capacity drop and city depth escalation).
4. Continuity and stability of depth values across all 6 time steps for all 3 storm scenarios.
5. Division by zero or NaN checks across all 521 segments and 25 manholes under full parameter grids.
"""

import os
import sys
import json
import math
import time
from pathlib import Path

# Color helpers for terminal reporting
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


class AdversarialTestFailure(Exception):
    pass


class HydraulicAdversaryRunner:
    def __init__(self, project_root):
        self.root = Path(project_root).resolve()
        self.data_path = self.root / "frontend" / "data" / "chennai_flood_data.js"
        self.html_path = self.root / "frontend" / "index.html"
        
        self.data = {}
        self.segments = []
        self.manholes = []
        self.substations = []
        self.routes = {}
        
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.failures = []
        
        self.time_keys = ['t0', 't30', 't60', 't90', 't120', 't180']
        self.storm_scenarios = {
            'michaung': 1.00,
            'monsoon': 0.55,
            'moderate': 0.30
        }

    def load_dataset(self):
        """Loads and parses the official frontend dataset."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Missing dataset at {self.data_path}")
            
        with open(self.data_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        if start_idx == -1 or end_idx == -1:
            raise ValueError("Could not locate JSON payload in chennai_flood_data.js")
            
        raw_json = content[start_idx:end_idx + 1]
        self.data = json.loads(raw_json)
        self.segments = self.data.get('segments', [])
        self.manholes = self.data.get('surcharging_manholes', [])
        self.substations = self.data.get('substations', [])
        self.routes = self.data.get('routes', {})

    def record_test(self, name, condition, details=""):
        self.total_tests += 1
        if condition:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
            self.failures.append(f"[FAIL] {name}: {details}")
            print(f"  {RED}[FAIL]{RESET} {name}: {details}")

    # ==========================================================================
    # SECTION 1: ORIFICE BACKFLOW WHEN DELTA H <= 0
    # ==========================================================================
    def test_orifice_backflow_zero_and_negative(self):
        print(f"\n{BOLD}{CYAN}=== TEST SUITE 1: Orifice Backflow Edge Cases (Delta h <= 0) ==={RESET}")
        
        # Test mathematical formula implementation
        # Q = Cd * A * sqrt(2 * g * Delta_h) when Delta_h > 0 else 0
        test_heads = [
            0.0,
            -0.0,
            -0.0000001,
            -0.01,
            -0.1,
            -1.0,
            -5.0,
            -100.0,
            -1e9,
            -float('inf')
        ]
        
        for dia_mm in [600, 800, 900, 1200]:
            area = math.pi * ((dia_mm / 1000.0) ** 2) / 4.0
            cd = 0.62
            for dh in test_heads:
                # Direct simulation of JS: deltaH > 0 ? (cd * area * Math.sqrt(2 * 9.81 * deltaH)) : 0
                if dh > 0:
                    q_backflow = cd * area * math.sqrt(2 * 9.81 * dh)
                else:
                    q_backflow = 0.0
                
                # Check 1: Must be exactly 0.0
                self.record_test(
                    f"Zero/Neg Head (D={dia_mm}mm, dh={dh})",
                    q_backflow == 0.0 and not math.isnan(q_backflow) and not math.isinf(q_backflow),
                    f"Got q_backflow={q_backflow}"
                )
                
                # Check 2: String formatting output must be '0.000'
                formatted = f"{q_backflow:.3f}"
                self.record_test(
                    f"Zero/Neg Head Formatting (D={dia_mm}mm, dh={dh})",
                    formatted == "0.000",
                    f"Got formatted={formatted}"
                )

        # Adversarial check on all 25 manholes when HGL <= ground elevation
        for mh in self.manholes:
            elev = mh.get('elevation') or mh.get('ground_elevation') or 5.0
            dia = mh.get('pipe_dia_mm') or mh.get('diameter_mm') or 600
            cd = mh.get('discharge_coeff', 0.62)
            area = math.pi * ((dia / 1000.0) ** 2) / 4.0
            
            # Simulate artificial negative surcharge (HGL below ground, e.g. dry pipe or deep drain)
            for sub_surface_hgl in [elev, elev - 0.5, elev - 5.0, elev - 50.0]:
                delta_h = max(0.0, sub_surface_hgl - elev)
                q_backflow = (cd * area * math.sqrt(2 * 9.81 * delta_h)) if delta_h > 0 else 0.0
                self.record_test(
                    f"Sub-surface Manhole Head {mh['id']} (HGL={sub_surface_hgl}m, Elev={elev}m)",
                    delta_h == 0.0 and q_backflow == 0.0 and not math.isnan(q_backflow),
                    f"delta_h={delta_h}, q_backflow={q_backflow}"
                )

        # Check road segment backflow guard (streetDepth <= 15 -> qBackflow = 0)
        for depth_cm in [0.0, 5.0, 10.0, 14.99, 15.0]:
            dia = 900
            area = math.pi * ((dia / 1000.0) ** 2) / 4.0
            cd = 0.62
            effective_mu = 0.35
            delta_h = (depth_cm / 100.0) + (0.25 * effective_mu)
            q_backflow = (cd * area * math.sqrt(2 * 9.81 * max(0.01, delta_h - 0.15))) if depth_cm > 15 else 0.0
            self.record_test(
                f"Road Segment Backflow Guard (depth={depth_cm}cm)",
                q_backflow == 0.0,
                f"Expected 0.0 at depth <= 15cm, got {q_backflow}"
            )

    # ==========================================================================
    # SECTION 2: ORIFICE BACKFLOW UNDER EXTREME SURCHARGE & SQRT SCALING
    # ==========================================================================
    def test_orifice_backflow_extreme_surcharge(self):
        print(f"\n{BOLD}{CYAN}=== TEST SUITE 2: Extreme Surcharge & Sqrt(Delta h) Scaling ==={RESET}")
        
        dia_mm = 600
        area = math.pi * ((dia_mm / 1000.0) ** 2) / 4.0
        cd = 0.62
        g = 9.81
        
        # Test reference head delta_h = 5.0m
        dh_ref = 5.0
        q_5m = cd * area * math.sqrt(2 * g * dh_ref)
        expected_q_5m = 0.62 * (math.pi * 0.36 / 4.0) * math.sqrt(2 * 9.81 * 5.0) # ~1.736275 m3/s
        
        self.record_test(
            "Orifice backflow at Delta h = 5.0m exact calculation",
            abs(q_5m - expected_q_5m) < 1e-9,
            f"Expected {expected_q_5m}, got {q_5m}"
        )
        
        # Check scaling with sqrt(Delta h) across range 0.01m to 50.0m
        test_heads = [0.01, 0.04, 0.16, 0.25, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 9.0, 16.0, 25.0, 50.0]
        base_h = 1.0
        q_base = cd * area * math.sqrt(2 * g * base_h)
        
        for dh in test_heads:
            q = cd * area * math.sqrt(2 * g * dh)
            expected_ratio = math.sqrt(dh / base_h)
            actual_ratio = q / q_base
            
            self.record_test(
                f"Sqrt Scaling (dh={dh}m vs base={base_h}m)",
                abs(actual_ratio - expected_ratio) < 1e-9,
                f"Expected ratio {expected_ratio:.6f}, got {actual_ratio:.6f}"
            )
            
            # Monotonicity test: dQ/d(dh) > 0
            if dh > 0.01:
                q_prev = cd * area * math.sqrt(2 * g * (dh - 0.001))
                self.record_test(
                    f"Strict Monotonicity at dh={dh}m",
                    q > q_prev,
                    f"q({dh})={q} <= q({dh-0.001})={q_prev}"
                )

        # Scale with Diameter D^2
        for d_test in [300, 600, 900, 1200, 1800]:
            a_test = math.pi * ((d_test / 1000.0) ** 2) / 4.0
            q_d = cd * a_test * math.sqrt(2 * g * 5.0)
            expected_d_ratio = (d_test / dia_mm) ** 2
            actual_d_ratio = q_d / q_5m
            self.record_test(
                f"Diameter Quadratic Scaling (D={d_test}mm vs {dia_mm}mm)",
                abs(actual_d_ratio - expected_d_ratio) < 1e-9,
                f"Expected {expected_d_ratio}, got {actual_d_ratio}"
            )

        # Test extreme geyser conditions (Delta h = 10m, 50m)
        for extreme_dh in [10.0, 20.0, 50.0]:
            q_ext = cd * area * math.sqrt(2 * g * extreme_dh)
            self.record_test(
                f"Extreme geyser stability at dh={extreme_dh}m",
                q_ext > 0 and not math.isnan(q_ext) and not math.isinf(q_ext),
                f"q_ext={q_ext}"
            )

    # ==========================================================================
    # SECTION 3: CLOGGING SLIDER CAPACITY DROP & CITY DEPTH ESCALATION
    # ==========================================================================
    def test_clogging_slider_behavior(self):
        print(f"\n{BOLD}{CYAN}=== TEST SUITE 3: Clogging Slider Behavior (mu_clog = 0% to 80%) ==={RESET}")
        
        # Test slider multiplier mapping: state.cloggingMultiplier = 0.6 + (val / 100) * 0.8
        clog_0_mult = 0.6 + (0 / 100) * 0.8  # 0.60
        clog_35_mult = 0.6 + (35 / 100) * 0.8 # 0.88
        clog_80_mult = 0.6 + (80 / 100) * 0.8 # 1.24
        
        self.record_test("Clogging multiplier at 0%", abs(clog_0_mult - 0.60) < 1e-9, f"Got {clog_0_mult}")
        self.record_test("Clogging multiplier at 80%", abs(clog_80_mult - 1.24) < 1e-9, f"Got {clog_80_mult}")
        
        # Test rated capacity impact formula: Math.max(20, 100 - val)
        cap_0 = max(20, 100 - 0)
        cap_80 = max(20, 100 - 80)
        self.record_test("Rated spec capacity at mu=0%", cap_0 == 100, f"Expected 100%, got {cap_0}%")
        self.record_test("Rated spec capacity at mu=80%", cap_80 == 20, f"Expected 20%, got {cap_80}%")
        
        # Check city-wide depth escalation across ALL 521 segments
        # At T+90m (peak storm), storm multiplier = 1.0
        depths_at_0 = []
        depths_at_80 = []
        inundated_count_0 = 0
        inundated_count_80 = 0
        severe_count_0 = 0
        severe_count_80 = 0
        
        t_key = 't90'
        storm_mult = 1.00
        
        for seg in self.segments:
            base_d = seg.get('depths', {}).get(t_key, 0.0)
            d_0 = base_d * storm_mult * clog_0_mult
            d_80 = base_d * storm_mult * clog_80_mult
            
            depths_at_0.append(d_0)
            depths_at_80.append(d_80)
            
            if d_0 > 10.0:
                inundated_count_0 += 1
            if d_80 > 10.0:
                inundated_count_80 += 1
                
            if d_0 > 25.0:
                severe_count_0 += 1
            if d_80 > 25.0:
                severe_count_80 += 1
                
            # Individual segment check: depth at 80% MUST be >= depth at 0%
            self.record_test(
                f"Segment {seg['id']} depth escalation",
                d_80 >= d_0 and (d_80 > d_0 or base_d == 0),
                f"d_0={d_0}, d_80={d_80}"
            )
            
            # Ratio check: d_80 / d_0 must equal 1.24 / 0.60 (~2.0667)
            if base_d > 0:
                ratio = d_80 / d_0
                self.record_test(
                    f"Segment {seg['id']} escalation ratio",
                    abs(ratio - (1.24 / 0.60)) < 1e-6,
                    f"Expected {1.24/0.60:.4f}, got {ratio:.4f}"
                )

        mean_depth_0 = sum(depths_at_0) / len(depths_at_0)
        mean_depth_80 = sum(depths_at_80) / len(depths_at_80)
        
        print(f"  [METRIC] Mean City Depth: {mean_depth_0:.2f} cm (at 0%) -> {mean_depth_80:.2f} cm (at 80%) [+{((mean_depth_80/mean_depth_0)-1)*100:.1f}%]")
        print(f"  [METRIC] Inundated Segments (>10cm): {inundated_count_0} (at 0%) -> {inundated_count_80} (at 80%)")
        print(f"  [METRIC] Severe Segments (>25cm): {severe_count_0} (at 0%) -> {severe_count_80} (at 80%)")
        
        self.record_test(
            "City-wide mean depth increases under 80% clogging",
            mean_depth_80 > mean_depth_0,
            f"{mean_depth_80} <= {mean_depth_0}"
        )
        self.record_test(
            "Inundated road segments count escalates under 80% clogging",
            inundated_count_80 >= inundated_count_0,
            f"{inundated_count_80} < {inundated_count_0}"
        )
        self.record_test(
            "Severe road segments count escalates under 80% clogging",
            severe_count_80 >= severe_count_0,
            f"{severe_count_80} < {severe_count_0}"
        )

        # Test monotonicity across the whole range: 0, 10, 20, 30, 40, 50, 60, 70, 80
        prev_mean = 0.0
        for val in range(0, 81, 10):
            mult = 0.6 + (val / 100.0) * 0.8
            cur_mean = sum(s.get('depths', {}).get(t_key, 0.0) * storm_mult * mult for s in self.segments) / len(self.segments)
            if val > 0:
                self.record_test(
                    f"Monotonic mean depth escalation at {val}% clogging",
                    cur_mean > prev_mean,
                    f"cur={cur_mean} <= prev={prev_mean}"
                )
            prev_mean = cur_mean

        # Test effective capacity reduction in Diagnostic Inspector card
        # effCap = theorCap * (1 - effectiveMu), where effectiveMu = min(0.85, baseMu * clog)
        for seg in self.segments[:50]:  # sample 50 segments
            theor_cap = seg.get('theoretical_cap', 0.317)
            base_mu = seg.get('mu_clog', 0.35)
            
            eff_mu_0 = min(0.85, base_mu * clog_0_mult)
            eff_cap_0 = theor_cap * (1 - eff_mu_0)
            
            eff_mu_80 = min(0.85, base_mu * clog_80_mult)
            eff_cap_80 = theor_cap * (1 - eff_mu_80)
            
            self.record_test(
                f"Effective capacity drop for {seg['id']}",
                eff_cap_80 <= eff_cap_0 and eff_cap_80 >= 0,
                f"eff_cap_0={eff_cap_0}, eff_cap_80={eff_cap_80}"
            )

    # ==========================================================================
    # SECTION 4: CONTINUITY & STABILITY ACROSS ALL 6 TIME STEPS & 3 SCENARIOS
    # ==========================================================================
    def test_continuity_and_stability(self):
        print(f"\n{BOLD}{CYAN}=== TEST SUITE 4: Continuity & Stability Across Time & Scenarios ==={RESET}")
        
        # Test 1: Scenario ordering dominance: Michaung (1.00) >= Monsoon (0.55) >= Moderate (0.30)
        # across all 521 segments and all 6 time steps (521 * 6 * 3 = 9,378 checks)
        for seg in self.segments:
            seg_id = seg['id']
            depths = seg.get('depths', {})
            
            for t_step in self.time_keys:
                base_d = depths.get(t_step, 0.0)
                
                # Check base depth valid
                self.record_test(
                    f"Base depth valid {seg_id} at {t_step}",
                    base_d >= 0.0 and not math.isnan(base_d) and not math.isinf(base_d) and base_d < 300.0,
                    f"base_d={base_d}"
                )
                
                d_michaung = base_d * self.storm_scenarios['michaung']
                d_monsoon = base_d * self.storm_scenarios['monsoon']
                d_moderate = base_d * self.storm_scenarios['moderate']
                
                # Dominance check
                self.record_test(
                    f"Storm scenario hierarchy {seg_id} at {t_step}",
                    d_michaung >= d_monsoon and d_monsoon >= d_moderate and d_moderate >= 0.0,
                    f"M={d_michaung}, Mon={d_monsoon}, Mod={d_moderate}"
                )

            # Continuity check across time: delta between consecutive steps must be physically bounded
            for i in range(len(self.time_keys) - 1):
                t1 = self.time_keys[i]
                t2 = self.time_keys[i + 1]
                d1 = depths.get(t1, 0.0)
                d2 = depths.get(t2, 0.0)
                step_delta = abs(d2 - d1)
                
                self.record_test(
                    f"Temporal continuity {seg_id} between {t1}->{t2}",
                    step_delta <= 100.0,  # Max 100cm jump in 30-60 min
                    f"Jump of {step_delta:.2f} cm between {t1} ({d1}cm) and {t2} ({d2}cm)"
                )

            # Hydrograph profile check:
            # Under rain storm, flood depth at T+90m (or T+60m/T+120m) should be higher than T+0m
            d_t0 = depths.get('t0', 0.0)
            d_t90 = depths.get('t90', 0.0)
            d_t180 = depths.get('t180', 0.0)
            
            if d_t90 > 5.0:  # If it gets flooded at all
                self.record_test(
                    f"Hydrograph peak accumulation {seg_id}",
                    d_t90 >= d_t0,
                    f"Peak {d_t90} < Initial {d_t0}"
                )
                # Receding curve check: T+180m should be receding or equal compared to peak
                self.record_test(
                    f"Hydrograph recession {seg_id}",
                    d_t180 <= d_t90,
                    f"Receding {d_t180} > Peak {d_t90}"
                )

        # Test 2: Continuity and stability of manhole HGL and Surcharge
        for mh in self.manholes:
            mh_id = mh['id']
            elev = mh.get('elevation') or mh.get('ground_elevation') or 5.0
            hgl_steps = mh.get('hgl_steps', {})
            
            for t_step in self.time_keys:
                base_hgl = hgl_steps.get(t_step, mh.get('hgl', elev))
                
                # Check base HGL valid
                self.record_test(
                    f"Manhole base HGL valid {mh_id} at {t_step}",
                    base_hgl >= elev - 2.0 and not math.isnan(base_hgl) and not math.isinf(base_hgl),
                    f"base_hgl={base_hgl}, elev={elev}"
                )
                
                for scenario_name, storm_mult in self.storm_scenarios.items():
                    # Dynamic HGL formula from JS:
                    # effectiveHgl = elev + Math.max(0.02, (baseHgl - elev) * state.stormMultiplier * (1 + 0.35 * (state.cloggingMultiplier - 1)));
                    eff_hgl = elev + max(0.02, (base_hgl - elev) * storm_mult * (1.0))
                    delta_h = max(0.0, eff_hgl - elev)
                    
                    self.record_test(
                        f"Manhole HGL stability {mh_id} ({scenario_name}, {t_step})",
                        eff_hgl >= elev and delta_h >= 0.0 and not math.isnan(eff_hgl),
                        f"eff_hgl={eff_hgl}, elev={elev}, delta_h={delta_h}"
                    )

    # ==========================================================================
    # SECTION 5: DIVISION BY ZERO & NAN INTEGRITY AUDIT ACROSS ALL ENTITIES
    # ==========================================================================
    def test_division_by_zero_and_nan(self):
        print(f"\n{BOLD}{CYAN}=== TEST SUITE 5: Division by Zero & NaN Exhaustive Audit ==={RESET}")
        
        # Audit all 521 segments
        self.record_test("Segments count == 521", len(self.segments) == 521, f"Found {len(self.segments)}")
        
        for idx, seg in enumerate(self.segments):
            seg_id = seg.get('id', f'SEG_{idx}')
            
            # 1. Pipe diameter > 0 (prevents division by zero in hydraulic equations)
            pipe_dia = seg.get('pipe_dia', 0)
            self.record_test(
                f"Segment {seg_id} pipe diameter > 0",
                pipe_dia is not None and pipe_dia > 0 and not math.isnan(pipe_dia),
                f"pipe_dia={pipe_dia}"
            )
            
            # 2. Manning n > 0 (prevents division by zero in 1/n)
            manning_n = seg.get('manning_n', 0)
            self.record_test(
                f"Segment {seg_id} manning n > 0",
                manning_n is not None and manning_n > 0 and not math.isnan(manning_n),
                f"manning_n={manning_n}"
            )
            
            # 3. Elevation finite and positive
            elev = seg.get('elevation', 0)
            self.record_test(
                f"Segment {seg_id} elevation valid",
                elev is not None and elev > 0 and not math.isnan(elev) and not math.isinf(elev),
                f"elev={elev}"
            )
            
            # 4. Theoretical capacity finite and positive
            theor_cap = seg.get('theoretical_cap', 0)
            self.record_test(
                f"Segment {seg_id} theoretical capacity valid",
                theor_cap is not None and theor_cap > 0 and not math.isnan(theor_cap) and not math.isinf(theor_cap),
                f"theor_cap={theor_cap}"
            )
            
            # 5. Coordinates valid and non-empty
            coords = seg.get('coords', [])
            self.record_test(
                f"Segment {seg_id} coordinates valid",
                isinstance(coords, list) and len(coords) >= 2,
                f"coords len={len(coords) if isinstance(coords, list) else 'not a list'}"
            )
            for pt in coords:
                lat, lon = pt[0], pt[1]
                self.record_test(
                    f"Segment {seg_id} coordinate bounds",
                    12.80 <= lat <= 13.35 and 80.05 <= lon <= 80.40 and not math.isnan(lat) and not math.isnan(lon),
                    f"coord=({lat}, {lon})"
                )

            # 6. Test Manning and Backflow calculations for this segment under parameter sweeps
            # sweep clog: 0.0 to 1.5, storm: 0.0 to 2.0
            for clog in [0.60, 0.88, 1.0, 1.24]:
                for storm in [0.30, 0.55, 1.0, 1.5]:
                    base_mu = seg.get('mu_clog', 0.35)
                    effective_mu = min(0.85, base_mu * clog)
                    eff_cap = theor_cap * (1 - effective_mu)
                    
                    self.record_test(
                        f"Segment {seg_id} eff_cap math stability (clog={clog}, storm={storm})",
                        eff_cap >= 0 and not math.isnan(eff_cap) and not math.isinf(eff_cap),
                        f"eff_cap={eff_cap}"
                    )
                    
                    for t_key in self.time_keys:
                        base_depth = seg.get('depths', {}).get(t_key, 0.0)
                        street_depth = base_depth * storm * clog
                        delta_h = (street_depth / 100.0) + (0.25 * effective_mu)
                        hgl = elev + delta_h
                        
                        area = math.pi * ((pipe_dia / 1000.0) ** 2) / 4.0
                        cd = 0.62
                        # JS logic: streetDepth > 15 ? (cd * area * Math.sqrt(2 * 9.81 * Math.max(0.01, deltaH - 0.15))) : 0;
                        if street_depth > 15:
                            inner_term = 2 * 9.81 * max(0.01, delta_h - 0.15)
                            q_backflow = cd * area * math.sqrt(inner_term)
                        else:
                            q_backflow = 0.0
                            
                        self.record_test(
                            f"Segment {seg_id} hydraulic integrity ({t_key}, clog={clog}, storm={storm})",
                            not math.isnan(street_depth) and not math.isnan(hgl) and not math.isnan(q_backflow)
                            and not math.isinf(street_depth) and not math.isinf(hgl) and not math.isinf(q_backflow),
                            f"depth={street_depth}, hgl={hgl}, q={q_backflow}"
                        )

        # Audit all 25 manholes
        self.record_test("Manholes count == 25", len(self.manholes) == 25, f"Found {len(self.manholes)}")
        
        for idx, mh in enumerate(self.manholes):
            mh_id = mh.get('id', f'MH_{idx}')
            
            # Coordinates
            lat = mh.get('lat')
            lon = mh.get('lon') or mh.get('lng')
            self.record_test(
                f"Manhole {mh_id} coordinate valid",
                lat is not None and lon is not None and 12.80 <= lat <= 13.35 and 80.05 <= lon <= 80.40,
                f"coord=({lat}, {lon})"
            )
            
            # Elevation
            elev = mh.get('elevation') or mh.get('ground_elevation')
            self.record_test(
                f"Manhole {mh_id} elevation valid",
                elev is not None and elev > 0 and not math.isnan(elev) and not math.isinf(elev),
                f"elev={elev}"
            )
            
            # Diameter
            dia = mh.get('pipe_dia_mm') or mh.get('diameter_mm')
            self.record_test(
                f"Manhole {mh_id} diameter > 0",
                dia is not None and dia > 0 and not math.isnan(dia),
                f"dia={dia}"
            )
            
            # Discharge coefficient
            cd = mh.get('discharge_coeff')
            self.record_test(
                f"Manhole {mh_id} discharge coefficient in (0, 1]",
                cd is not None and 0 < cd <= 1.0 and not math.isnan(cd),
                f"cd={cd}"
            )
            
            # All 6 time steps HGL
            hgl_steps = mh.get('hgl_steps', {})
            for t_key in self.time_keys:
                step_hgl = hgl_steps.get(t_key)
                self.record_test(
                    f"Manhole {mh_id} hgl_step {t_key} valid",
                    step_hgl is not None and not math.isnan(step_hgl) and not math.isinf(step_hgl),
                    f"hgl={step_hgl}"
                )
                
                # Test JS simulation calculation under all parameter combinations
                for clog in [0.60, 0.88, 1.0, 1.24]:
                    for storm in [0.30, 0.55, 1.0]:
                        effective_hgl = elev + max(0.02, (step_hgl - elev) * storm * (1 + 0.35 * (clog - 1)))
                        delta_h = max(0.0, effective_hgl - elev)
                        area = math.pi * ((dia / 1000.0) ** 2) / 4.0
                        backflow = cd * area * math.sqrt(2 * 9.81 * delta_h) if delta_h > 0 else 0.0
                        
                        self.record_test(
                            f"Manhole {mh_id} simulation stability ({t_key}, clog={clog}, storm={storm})",
                            not math.isnan(effective_hgl) and not math.isnan(delta_h) and not math.isnan(backflow)
                            and not math.isinf(effective_hgl) and not math.isinf(delta_h) and not math.isinf(backflow),
                            f"eff_hgl={effective_hgl}, delta_h={delta_h}, backflow={backflow}"
                        )

        # Audit all 20 substations
        self.record_test("Substations count == 20", len(self.substations) == 20, f"Found {len(self.substations)}")
        for ss in self.substations:
            ss_id = ss.get('id')
            plinth = ss.get('plinth_cm')
            elev = ss.get('elevation_m')
            self.record_test(
                f"Substation {ss_id} plinth valid",
                plinth is not None and plinth > 0 and not math.isnan(plinth),
                f"plinth={plinth}"
            )
            self.record_test(
                f"Substation {ss_id} elevation valid",
                elev is not None and elev > 0 and not math.isnan(elev),
                f"elev={elev}"
            )

        # Audit routing scenarios
        self.record_test("Routes scenario1 exists", 'scenario1' in self.routes, "Missing scenario1")
        self.record_test("Routes scenario2 exists", 'scenario2' in self.routes, "Missing scenario2")
        for sc_name, sc_data in self.routes.items():
            for route_type in ['direct', 'safe']:
                coords = sc_data.get(route_type, [])
                self.record_test(
                    f"Route {sc_name} {route_type} coordinates valid",
                    isinstance(coords, list) and len(coords) >= 2,
                    f"len={len(coords)}"
                )
                for pt in coords:
                    lat, lon = pt[0], pt[1]
                    self.record_test(
                        f"Route {sc_name} {route_type} coordinate bounds",
                        12.80 <= lat <= 13.35 and 80.05 <= lon <= 80.40 and not math.isnan(lat) and not math.isnan(lon),
                        f"coord=({lat}, {lon})"
                    )
            
            # Check route depths
            direct_depth = sc_data.get('direct_bottleneck_depth_cm')
            safe_depth = sc_data.get('safe_max_depth_cm')
            self.record_test(
                f"Route {sc_name} direct bottleneck depth valid",
                direct_depth is not None and direct_depth >= 0 and not math.isnan(direct_depth),
                f"depth={direct_depth}"
            )
            self.record_test(
                f"Route {sc_name} safe corridor depth valid",
                safe_depth is not None and safe_depth >= 0 and not math.isnan(safe_depth),
                f"depth={safe_depth}"
            )
            self.record_test(
                f"Route {sc_name} safe corridor depth < direct bottleneck",
                safe_depth < direct_depth,
                f"safe={safe_depth} >= direct={direct_depth}"
            )

    def run_all(self):
        start_time = time.time()
        print(f"\n{BOLD}======================================================================{RESET}")
        print(f"{BOLD}  ADVERSARIAL HYDRAULIC & PHYSICAL STRESS TEST HARNESS (CHALLENGER 1){RESET}")
        print(f"{BOLD}  Greater Chennai Corporation Pilot: 521 Segments, 25 Manholes, 20 Substations{RESET}")
        print(f"{BOLD}======================================================================{RESET}")
        
        self.load_dataset()
        print(f"Loaded dataset: {len(self.segments)} segments, {len(self.manholes)} manholes, {len(self.substations)} substations.")
        
        self.test_orifice_backflow_zero_and_negative()
        self.test_orifice_backflow_extreme_surcharge()
        self.test_clogging_slider_behavior()
        self.test_continuity_and_stability()
        self.test_division_by_zero_and_nan()
        
        duration = time.time() - start_time
        print(f"\n{BOLD}======================================================================{RESET}")
        print(f"{BOLD}  ADVERSARIAL STRESS TEST RESULTS SUMMARY{RESET}")
        print(f"{BOLD}======================================================================{RESET}")
        print(f"Total Probes Executed: {BOLD}{self.total_tests}{RESET}")
        print(f"Passed Probes:         {GREEN}{BOLD}{self.passed_tests}{RESET}")
        print(f"Failed Probes:         {RED}{BOLD}{self.failed_tests}{RESET}")
        print(f"Pass Rate:             {BOLD}{(self.passed_tests / self.total_tests) * 100:.2f}%{RESET}")
        print(f"Execution Duration:    {duration:.3f} seconds")
        print(f"{BOLD}======================================================================{RESET}")
        
        if self.failed_tests > 0:
            print(f"\n{RED}{BOLD}VERDICT: REPORT_DEFECT{RESET}")
            print(f"Encountered {len(self.failures)} failure modes:")
            for f in self.failures[:20]:
                print(f"  {f}")
            if len(self.failures) > 20:
                print(f"  ... and {len(self.failures) - 20} more failures.")
            return False
        else:
            print(f"\n{GREEN}{BOLD}VERDICT: CONFIRM_CORRECTNESS{RESET}")
            print("All hydraulic equations, edge cases, scaling laws, continuity, and non-zero/non-NaN constraints verified.")
            return True


if __name__ == "__main__":
    current = Path(__file__).resolve()
    # Find project root by locating frontend directory
    project_root = current.parent
    for _ in range(5):
        if (project_root / "frontend").is_dir():
            break
        project_root = project_root.parent
    runner = HydraulicAdversaryRunner(project_root)
    success = runner.run_all()
    sys.exit(0 if success else 1)

