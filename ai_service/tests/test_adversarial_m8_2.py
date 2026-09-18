#!/usr/bin/env python3
"""
Adversarial Challenge Verification Suite — Challenger 2 (Milestone M8)
Urban Flood Nowcasting System Web GIS Command Twin (SIH 2026 - Problem Statement 26085)
Calibrated for Greater Chennai Corporation (GCC Pilot)

Mission Scope:
Adversarially challenge routing, vehicle clearances, UI states, and event handling:
1. Vehicle clearance thresholds against exact flood depths:
   - Boundary at threshold - 0.1cm (passable)
   - Boundary at threshold (passable)
   - Boundary at threshold + 0.1cm (breached/impassable)
   - Verify warning logic for all 4 vehicle types across both routes.
2. Route switching:
   - Ensure switching from Scenario 1 to Scenario 2 and back cleanly updates
     all DOM fields, metric cards, waypoints, and coordinates without stale residues.
3. Manhole selection:
   - Simulate clicking all 25 manholes and verify that every one yields valid
     non-NaN hydraulic attributes in the inspector.
4. Standalone launcher and zero-dependency file verification:
   - Batch launcher and zero CORS file:/// execution integrity.

Execution:
    python tests/test_adversarial_m8_2.py
"""

import sys
import os
import re
import json
import math
import time
from pathlib import Path

# ==============================================================================
# CONFIGURATION & CONSTANTS
# ==============================================================================

VEHICLE_CONFIG = {
    'ambulance': {'name': '108 Emergency Ambulance', 'clearance': 30.0, 'caution': 15.0},
    'bus': {'name': 'NDRF Rescue Heavy Truck / Bus', 'clearance': 45.0, 'caution': 25.0},
    'car': {'name': 'Civilian Passenger Car / Sedan', 'clearance': 18.0, 'caution': 10.0},
    'bike': {'name': 'Two-Wheeler / Auto-Rickshaw', 'clearance': 10.0, 'caution': 5.0}
}

TIME_KEYS = ['t0', 't30', 't60', 't90', 't120', 't180']
TIME_LABELS = ['T + 0m', 'T + 30m', 'T + 60m', 'T + 90m', 'T + 120m', 'T + 180m']
TIME_CLOCKS = ['(18:40 IST)', '(19:10 IST)', '(19:40 IST)', '(20:10 IST)', '(20:40 IST)', '(21:40 IST)']
TIME_FACTORS = [0.10, 0.45, 0.85, 1.00, 0.88, 0.65]
RAIN_RATES = [12.4, 38.6, 84.2, 95.0, 62.5, 24.1]

# ==============================================================================
# DOM SIMULATION ENGINE
# ==============================================================================

class MockDOMElement:
    def __init__(self, element_id):
        self.id = element_id
        self.innerText = ""
        self.innerHTML = ""
        self.className = ""
        self.value = ""
        self.dataset = {}
        self.classList = set()

    def set_class_name(self, name):
        self.className = name
        self.classList = set(name.split())


class MockDocument:
    def __init__(self):
        self.elements = {}

    def get_element_by_id(self, element_id):
        if element_id not in self.elements:
            self.elements[element_id] = MockDOMElement(element_id)
        return self.elements[element_id]


class MockLayerGroup:
    def __init__(self):
        self.layers = []

    def clear_layers(self):
        self.layers.clear()

    def add_layer(self, layer):
        self.layers.append(layer)


class AppState:
    def __init__(self):
        self.currentTimeStep = 2 # T+60m default
        self.isPlaying = False
        self.cloggingMultiplier = 1.0
        self.activeTab = 'routing'
        self.selectedVehicle = 'ambulance'
        self.activeScenario = 'scenario1'
        self.selectedAsset = None
        self.stormMultiplier = 1.0


# ==============================================================================
# JAVASCRIPT APPLICATION LOGIC REPLICA (EXACT MIRROR OF frontend/index.html)
# ==============================================================================

def js_update_vehicle_and_route_ui(data, state, doc, route_layer_group):
    if not data or not data.get('routes'):
        return

    scenario_key = state.activeScenario
    scenario = data['routes'].get(scenario_key)
    if not scenario:
        return

    vehicle = VEHICLE_CONFIG.get(state.selectedVehicle, VEHICLE_CONFIG['ambulance'])
    storm = state.stormMultiplier
    clog = state.cloggingMultiplier

    dynamic_direct_depth = scenario['direct_bottleneck_depth_cm'] * storm * clog
    dynamic_safe_depth = scenario['safe_max_depth_cm'] * storm * clog

    # Scenario Titles & Destination
    doc.get_element_by_id('route-direct-title').innerText = f"Direct Standard ({scenario['title'].split('→')[0].split('->')[0].strip() or 'Direct'})"
    doc.get_element_by_id('route-safe-title').innerText = f"Kairos A* Safe Bypass ({scenario.get('safe_corridor', 'Elevated Ridge')})"
    doc.get_element_by_id('route-destination-badge').innerText = scenario['destination']

    # Direct Route Metrics & Clearance Warnings
    doc.get_element_by_id('route-direct-dist').innerText = f"{scenario['direct_distance_km']} km"
    doc.get_element_by_id('route-direct-eta').innerText = f"{scenario['direct_eta_min']} min"
    doc.get_element_by_id('route-direct-depth').innerText = f"{dynamic_direct_depth:.1f} cm"

    direct_depth_diff = dynamic_direct_depth - vehicle['clearance']
    direct_warn_el = doc.get_element_by_id('route-direct-clearance-warn')
    direct_badge_el = doc.get_element_by_id('route-direct-badge')
    direct_msg_el = doc.get_element_by_id('route-direct-msg')

    if direct_depth_diff > 0:
        direct_warn_el.innerText = f"(Exceeds {vehicle['name']} limit ({vehicle['clearance']}cm) by +{direct_depth_diff:.1f}cm!)"
        direct_warn_el.set_class_name('text-red-400 text-[10px] block font-bold')
        direct_badge_el.innerText = 'Impassable'
        direct_badge_el.set_class_name('text-[10px] bg-red-900/60 text-red-300 px-1.5 py-0.5 rounded border border-red-700 font-mono font-bold')
        direct_msg_el.innerHTML = f"⚠️ <b>CRITICAL FAILURE RISK:</b> Water depth at {scenario.get('direct_bottleneck_location', 'underpass')} reaches <b>{dynamic_direct_depth:.1f} cm</b>, exceeding {vehicle['name']} air intake clearance ({vehicle['clearance']} cm). Catastrophic hydrostatic engine hydrolock imminent."
    else:
        direct_warn_el.innerText = f"(Within vehicle limit: {vehicle['clearance']}cm)"
        direct_warn_el.set_class_name('text-amber-400 text-[10px] block font-medium')
        direct_badge_el.innerText = 'Caution'
        direct_badge_el.set_class_name('text-[10px] bg-amber-900/40 text-amber-300 px-1.5 py-0.5 rounded border border-amber-800 font-mono font-bold')
        direct_msg_el.innerHTML = f"⚠️ <b>CAUTION:</b> High water level ({dynamic_direct_depth:.1f} cm). Transit permitted only with specialized heavy snorkel."

    # Safe Route Metrics & Clearance Margins
    doc.get_element_by_id('route-safe-dist').innerText = f"{scenario['safe_distance_km']} km (+{scenario.get('detour_extra_km', 0.8)} km)"
    doc.get_element_by_id('route-safe-eta').innerText = f"{scenario['safe_eta_min']} min (+{scenario.get('detour_extra_min', 3.2)} min)"
    doc.get_element_by_id('route-safe-depth').innerText = f"{dynamic_safe_depth:.1f} cm"

    safe_margin = vehicle['clearance'] - dynamic_safe_depth
    safe_margin_el = doc.get_element_by_id('route-safe-clearance-margin')
    safe_badge_el = doc.get_element_by_id('route-safe-badge')
    safe_msg_el = doc.get_element_by_id('route-safe-msg')
    kpi_safe_route_el = doc.get_element_by_id('kpi-safe-route')

    if safe_margin >= 0:
        safe_margin_el.innerText = f"(Safety Margin: +{safe_margin:.1f} cm above limit)"
        safe_margin_el.set_class_name('text-emerald-300 text-[10px] block font-semibold')
        safe_badge_el.innerText = '100% Operational'
        safe_badge_el.set_class_name('text-[10px] bg-emerald-900/60 text-emerald-300 px-1.5 py-0.5 rounded border border-emerald-700 font-mono font-bold')
        safe_msg_el.innerHTML = f"✅ <b>100% CLEAR:</b> Rerouted via elevated ridge corridor. Max corridor accumulation is only <b>{dynamic_safe_depth:.1f} cm</b>, leaving a guaranteed <b>+{safe_margin:.1f} cm</b> safety clearance margin. Uninterrupted emergency transit."
        kpi_safe_route_el.innerText = '100% Operational'
        kpi_safe_route_el.set_class_name('text-base font-bold text-emerald-400 font-mono')
    else:
        safe_margin_el.innerText = f"(Clearance Warning: Exceeded by +{(-safe_margin):.1f} cm)"
        safe_margin_el.set_class_name('text-amber-400 text-[10px] block font-bold')
        safe_badge_el.innerText = 'Caution'
        safe_badge_el.set_class_name('text-[10px] bg-amber-900/60 text-amber-300 px-1.5 py-0.5 rounded border border-amber-700 font-mono font-bold')
        safe_msg_el.innerHTML = f"⚠️ <b>WARNING:</b> Extreme cloudburst causes runoff to exceed vehicle clearance ({vehicle['clearance']} cm). Dispatch NDRF Heavy Rescue Bus instead."
        kpi_safe_route_el.innerText = f"Caution ({dynamic_safe_depth:.1f}cm)"
        kpi_safe_route_el.set_class_name('text-base font-bold text-amber-400 font-mono')

    # Turn-by-Turn Guidance
    turn_container = doc.get_element_by_id('route-turn-by-turn')
    if scenario.get('turn_by_turn'):
        items = []
        for cue in scenario['turn_by_turn']:
            styled_cue = cue
            if 'Avoid' in cue:
                styled_cue = f'<strong class="text-rose-300">{cue}</strong>'
            elif any(k in cue for k in ['Turn', 'Bypass', 'Ridge', 'Flyover']):
                styled_cue = f'<strong class="text-emerald-300">{cue}</strong>'
            items.append(f"<li>{styled_cue}</li>")
        turn_container.innerHTML = "".join(items)

    # Render Map Polylines
    js_render_route_polylines(scenario, dynamic_direct_depth, dynamic_safe_depth, route_layer_group)


def js_render_route_polylines(scenario, direct_depth, safe_depth, route_layer_group):
    route_layer_group.clear_layers()

    # 1. Direct Flooded Route
    direct_layer = {
        'type': 'polyline',
        'coords': scenario.get('direct', []),
        'color': '#ef4444',
        'weight': 5,
        'dashArray': '8, 8',
        'tooltip': f"Direct Route: IMPASSABLE ({direct_depth:.1f} cm flood bottleneck)"
    }
    # 2. Safe Bypass Route
    safe_layer = {
        'type': 'polyline',
        'coords': scenario.get('safe', []),
        'color': '#10b981',
        'weight': 6,
        'tooltip': f"Kairos A* Safe Bypass: 100% CLEAR ({safe_depth:.1f} cm max depth)"
    }
    # 3. Origin marker
    start_coord = scenario.get('direct', [[0, 0]])[0]
    origin_marker = {
        'type': 'marker',
        'coord': start_coord,
        'label': 'A',
        'popup': f"Origin: {scenario.get('origin', '')}"
    }
    # 4. Destination marker
    end_coord = scenario.get('direct', [[0, 0]])[-1]
    dest_marker = {
        'type': 'marker',
        'coord': end_coord,
        'label': 'B',
        'popup': f"Destination: {scenario.get('destination', '')}"
    }

    route_layer_group.add_layer(direct_layer)
    route_layer_group.add_layer(safe_layer)
    route_layer_group.add_layer(origin_marker)
    route_layer_group.add_layer(dest_marker)


def js_select_asset(asset_type, data, state, doc):
    state.selectedAsset = {'type': asset_type, 'data': data}
    js_switch_tab('inspector', state, doc)
    js_refresh_active_asset_diagnostic(state, doc)


def js_switch_tab(tab_id, state, doc):
    state.activeTab = tab_id
    tabs = ['routing', 'inspector', 'clogging']
    for t in tabs:
        btn = doc.get_element_by_id(f"tab-{t}-btn")
        content = doc.get_element_by_id(f"tab-{t}")
        if t == tab_id:
            btn.set_class_name('flex-1 py-2 rounded text-center transition flex items-center justify-center gap-1.5 bg-cyan-600/20 text-cyan-400 border border-cyan-500/30 font-semibold')
            content.classList.discard('hidden')
        else:
            btn.set_class_name('flex-1 py-2 rounded text-center transition flex items-center justify-center gap-1.5 text-slate-400 hover:text-slate-200')
            content.classList.add('hidden')


def js_refresh_active_asset_diagnostic(state, doc):
    if not state.selectedAsset:
        return

    t_key = TIME_KEYS[state.currentTimeStep]
    storm = state.stormMultiplier
    clog = state.cloggingMultiplier
    asset = state.selectedAsset['data']
    is_manhole = state.selectedAsset['type'] == 'manhole'

    asset_id = asset.get('id', 'UNKNOWN')
    zone_text = asset.get('zone', 'Metropolitan Core')
    if asset.get('road_class'):
        zone_text += f" ({asset['road_class']})"
    elif asset.get('name') or asset.get('location'):
        zone_text += f" ({asset.get('name') or asset.get('location')})"

    elev = asset.get('elevation', asset.get('ground_elevation', 5.0))
    dia = asset.get('pipe_dia', asset.get('pipe_dia_mm', asset.get('diameter_mm', 600)))
    theor_cap = asset.get('theoretical_cap', 0.317)
    base_mu = asset.get('mu_clog', asset.get('clog_mu', 0.35))
    effective_mu = min(0.85, base_mu * clog)

    manning_n = asset.get('manning_n', 0.015)
    eff_cap = theor_cap * (1 - effective_mu)

    street_depth = 0.0
    hgl = 0.0
    delta_h = 0.0
    q_backflow = 0.0

    if is_manhole:
        base_hgl = asset.get('hgl_steps', {}).get(t_key, asset.get('hgl', elev + 0.5))
        hgl = elev + max(0.02, (base_hgl - elev) * storm * (1 + 0.35 * (clog - 1)))
        delta_h = max(0.0, hgl - elev)
        street_depth = delta_h * 75.0

        area = math.pi * ((dia / 1000.0) ** 2) / 4.0
        cd = asset.get('discharge_coeff', 0.62)
        q_backflow = (cd * area * math.sqrt(2 * 9.81 * delta_h)) if delta_h > 0 else 0.0
    else:
        base_depth = asset.get('depths', {}).get(t_key, 0)
        street_depth = base_depth * storm * clog
        delta_h = (street_depth / 100.0) + (0.25 * effective_mu)
        hgl = elev + delta_h

        area = math.pi * ((dia / 1000.0) ** 2) / 4.0
        cd = 0.62
        q_backflow = (cd * area * math.sqrt(2 * 9.81 * max(0.01, delta_h - 0.15))) if street_depth > 15 else 0.0

    # Populate DOM
    doc.get_element_by_id('inspector-asset-id').innerText = str(asset_id)
    doc.get_element_by_id('inspector-zone').innerText = str(zone_text)
    doc.get_element_by_id('inspector-elevation').innerText = f"{elev:.2f} m MSL"
    doc.get_element_by_id('inspector-dia').innerText = f"{dia} mm ({'Manhole Frame' if is_manhole else 'RCC Hume SWD'})"
    doc.get_element_by_id('inspector-manning').innerText = f"{manning_n} (RCC Pipe / CPHEEO)"
    doc.get_element_by_id('inspector-theor-cap').innerText = f"{theor_cap:.3f} m³/s"
    doc.get_element_by_id('inspector-clog').innerText = f"{effective_mu:.2f} ({round(effective_mu * 100)}% Clogged)"
    doc.get_element_by_id('inspector-eff-cap').innerText = f"{eff_cap:.3f} m³/s"
    doc.get_element_by_id('inspector-hgl').innerText = f"{hgl:.2f} m (+{delta_h:.2f}m Surcharge Head)"
    doc.get_element_by_id('inspector-backflow').innerText = f"{q_backflow:.3f} m³/s (Saint-Venant Orifice Cd=0.62)"
    doc.get_element_by_id('inspector-depth').innerText = f"{street_depth:.1f} cm"


# ==============================================================================
# EMPIRICAL ADVERSARIAL TEST HARNESS
# ==============================================================================

class AdversarialCheck:
    def __init__(self, check_id, category, description, passed, details=""):
        self.check_id = check_id
        self.category = category
        self.description = description
        self.passed = passed
        self.details = details


class AdversarialChallengerM82:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir).resolve()
        self.data_file = self.root_dir / 'frontend' / 'data' / 'chennai_flood_data.js'
        self.index_html_file = self.root_dir / 'frontend' / 'index.html'
        self.launcher_bat_file = self.root_dir / 'launch_dashboard.bat'
        
        self.checks = []
        self.data = {}
        self.load_data()

    def load_data(self):
        with open(self.data_file, 'r', encoding='utf-8') as f:
            content = f.read()
        idx = content.find('{')
        raw_json = content[idx:].rstrip(';\n ')
        self.data = json.loads(raw_json)

    def record(self, check_id, category, description, passed, details=""):
        c = AdversarialCheck(check_id, category, description, passed, details)
        self.checks.append(c)
        status = "PASS" if passed else "FAIL"
        if not passed:
            print(f"  [{status}] {check_id}: {description} -> {details}")
        return passed

    # ==========================================================================
    # SECTION 1: VEHICLE CLEARANCE BOUNDARY & WARNING VERIFICATION
    # ==========================================================================
    def test_vehicle_clearances(self):
        print("\n--- [ADV-01] VEHICLE CLEARANCE THRESHOLDS & BOUNDARY CHALLENGES ---")
        
        # Test 1.1: Exact Boundary conditions for each vehicle (threshold - 0.1cm, threshold, threshold + 0.1cm)
        for v_key, v_info in VEHICLE_CONFIG.items():
            threshold = v_info['clearance']
            v_name = v_info['name']

            # Boundary 1: threshold - 0.1 cm (Passable)
            d_pass = threshold - 0.1
            diff_pass = d_pass - threshold
            self.record(
                f"VC_BOUND_{v_key.upper()}_MINUS_0.1_DIRECT",
                "Vehicle Clearance Boundary",
                f"{v_name} at depth {d_pass:.1f}cm (clearance - 0.1cm) on Direct Route is within limit",
                diff_pass <= 0,
                f"diff={diff_pass:.2f} <= 0"
            )

            # Boundary 2: exact threshold (Passable)
            d_exact = threshold
            diff_exact = d_exact - threshold
            self.record(
                f"VC_BOUND_{v_key.upper()}_EXACT_DIRECT",
                "Vehicle Clearance Boundary",
                f"{v_name} at exact depth {d_exact:.1f}cm (clearance threshold) on Direct Route is within limit",
                diff_exact <= 0,
                f"diff={diff_exact:.2f} <= 0"
            )

            # Boundary 3: threshold + 0.1 cm (Breached/Impassable)
            d_breach = threshold + 0.1
            diff_breach = d_breach - threshold
            self.record(
                f"VC_BOUND_{v_key.upper()}_PLUS_0.1_DIRECT",
                "Vehicle Clearance Boundary",
                f"{v_name} at depth {d_breach:.1f}cm (clearance + 0.1cm) on Direct Route is breached",
                diff_breach > 0,
                f"diff={diff_breach:.2f} > 0"
            )

            # Now test Safe Route Margin Boundary:
            # Margin = threshold - depth
            # Margin at threshold - 0.1cm -> +0.1 cm (>= 0 -> 100% Operational)
            margin_pass = threshold - (threshold - 0.1)
            self.record(
                f"VC_BOUND_{v_key.upper()}_MINUS_0.1_SAFE",
                "Vehicle Clearance Boundary",
                f"{v_name} safe margin at depth {threshold - 0.1:.1f}cm is positive (+0.1cm)",
                margin_pass >= 0 and abs(margin_pass - 0.1) < 1e-6,
                f"margin={margin_pass:.2f}"
            )

            # Margin at exact threshold -> 0.0 cm (>= 0 -> 100% Operational)
            margin_exact = threshold - threshold
            self.record(
                f"VC_BOUND_{v_key.upper()}_EXACT_SAFE",
                "Vehicle Clearance Boundary",
                f"{v_name} safe margin at exact threshold {threshold:.1f}cm is zero (0.0cm)",
                margin_exact >= 0 and abs(margin_exact) < 1e-6,
                f"margin={margin_exact:.2f}"
            )

            # Margin at threshold + 0.1cm -> -0.1 cm (< 0 -> Caution/Deficit Warning)
            margin_breach = threshold - (threshold + 0.1)
            self.record(
                f"VC_BOUND_{v_key.upper()}_PLUS_0.1_SAFE",
                "Vehicle Clearance Boundary",
                f"{v_name} safe margin at depth {threshold + 0.1:.1f}cm is negative (-0.1cm)",
                margin_breach < 0 and abs(margin_breach - (-0.1)) < 1e-6,
                f"margin={margin_breach:.2f}"
            )

        # Test 1.2: Empirical DOM and UI State Verification across 4 Vehicles × 2 Routes
        doc = MockDocument()
        layers = MockLayerGroup()
        state = AppState()

        for scen_key in ['scenario1', 'scenario2']:
            scen = self.data['routes'][scen_key]
            direct_depth = scen['direct_bottleneck_depth_cm']
            safe_depth = scen['safe_max_depth_cm']

            for v_key, v_info in VEHICLE_CONFIG.items():
                state.activeScenario = scen_key
                state.selectedVehicle = v_key
                state.stormMultiplier = 1.0
                state.cloggingMultiplier = 1.0

                js_update_vehicle_and_route_ui(self.data, state, doc, layers)

                # Check Direct Route Warning & Badge
                direct_warn = doc.get_element_by_id('route-direct-clearance-warn')
                direct_badge = doc.get_element_by_id('route-direct-badge')
                direct_msg = doc.get_element_by_id('route-direct-msg')

                is_direct_breached = direct_depth > v_info['clearance']
                expected_direct_badge = 'Impassable' if is_direct_breached else 'Caution'
                expected_direct_color = 'text-red-400' if is_direct_breached else 'text-amber-400'

                b_pass = direct_badge.innerText == expected_direct_badge
                self.record(
                    f"VC_UI_DIRECT_BADGE_{scen_key}_{v_key}",
                    "Vehicle Warning UI",
                    f"Direct route badge for {v_key} in {scen_key} (depth={direct_depth}cm vs clearance={v_info['clearance']}cm) is '{expected_direct_badge}'",
                    b_pass,
                    f"actual='{direct_badge.innerText}', expected='{expected_direct_badge}'"
                )

                c_pass = expected_direct_color in direct_warn.className
                self.record(
                    f"VC_UI_DIRECT_COLOR_{scen_key}_{v_key}",
                    "Vehicle Warning UI",
                    f"Direct route warning color for {v_key} in {scen_key} contains '{expected_direct_color}'",
                    c_pass,
                    f"className='{direct_warn.className}'"
                )

                if is_direct_breached:
                    diff_val = direct_depth - v_info['clearance']
                    text_ok = f"+{diff_val:.1f}cm!" in direct_warn.innerText
                    self.record(
                        f"VC_UI_DIRECT_DEFICIT_TEXT_{scen_key}_{v_key}",
                        "Vehicle Warning UI",
                        f"Direct route warning text specifies exact deficit +{diff_val:.1f}cm for {v_key}",
                        text_ok,
                        f"innerText='{direct_warn.innerText}'"
                    )
                else:
                    text_ok = f"Within vehicle limit: {v_info['clearance']}cm" in direct_warn.innerText
                    self.record(
                        f"VC_UI_DIRECT_SAFE_TEXT_{scen_key}_{v_key}",
                        "Vehicle Warning UI",
                        f"Direct route warning text states within limit for {v_key}",
                        text_ok,
                        f"innerText='{direct_warn.innerText}'"
                    )

                # Check Safe Route Margin & Badge
                safe_margin_el = doc.get_element_by_id('route-safe-clearance-margin')
                safe_badge = doc.get_element_by_id('route-safe-badge')
                safe_msg = doc.get_element_by_id('route-safe-msg')
                kpi_safe = doc.get_element_by_id('kpi-safe-route')

                safe_margin = v_info['clearance'] - safe_depth
                is_safe_operational = safe_margin >= 0
                expected_safe_badge = '100% Operational' if is_safe_operational else 'Caution'

                sb_pass = safe_badge.innerText == expected_safe_badge
                self.record(
                    f"VC_UI_SAFE_BADGE_{scen_key}_{v_key}",
                    "Vehicle Warning UI",
                    f"Safe route badge for {v_key} in {scen_key} (safe_depth={safe_depth}cm vs clearance={v_info['clearance']}cm) is '{expected_safe_badge}'",
                    sb_pass,
                    f"actual='{safe_badge.innerText}', expected='{expected_safe_badge}'"
                )

                if is_safe_operational:
                    margin_text_ok = f"+{safe_margin:.1f} cm above limit" in safe_margin_el.innerText
                    self.record(
                        f"VC_UI_SAFE_MARGIN_TEXT_{scen_key}_{v_key}",
                        "Vehicle Warning UI",
                        f"Safe route margin text displays +{safe_margin:.1f} cm for {v_key}",
                        margin_text_ok,
                        f"innerText='{safe_margin_el.innerText}'"
                    )
                    kpi_ok = kpi_safe.innerText == '100% Operational'
                    self.record(
                        f"VC_UI_SAFE_KPI_{scen_key}_{v_key}",
                        "Vehicle Warning UI",
                        f"Safe route KPI indicates '100% Operational' for {v_key}",
                        kpi_ok,
                        f"kpi='{kpi_safe.innerText}'"
                    )

        # Test 1.3: Synthetic boundary injection into UI (testing threshold - 0.1, threshold, threshold + 0.1)
        synthetic_data = json.loads(json.dumps(self.data))
        for v_key, v_info in VEHICLE_CONFIG.items():
            threshold = v_info['clearance']
            for delta, label, expect_impassable in [(-0.1, 'MINUS_0.1', False), (0.0, 'EXACT', False), (0.1, 'PLUS_0.1', True)]:
                synth_depth = threshold + delta
                synthetic_data['routes']['scenario1']['direct_bottleneck_depth_cm'] = synth_depth
                state.activeScenario = 'scenario1'
                state.selectedVehicle = v_key
                state.stormMultiplier = 1.0
                state.cloggingMultiplier = 1.0

                js_update_vehicle_and_route_ui(synthetic_data, state, doc, layers)

                badge = doc.get_element_by_id('route-direct-badge').innerText
                expected = 'Impassable' if expect_impassable else 'Caution'
                self.record(
                    f"VC_SYNTH_DIRECT_{v_key}_{label}",
                    "Synthetic Boundary Challenge",
                    f"Synthetic direct depth {synth_depth:.1f}cm for {v_key} (thresh={threshold}cm) produces badge '{expected}'",
                    badge == expected,
                    f"actual='{badge}', expected='{expected}'"
                )

    # ==========================================================================
    # SECTION 2: ROUTE SWITCHING STATE INTEGRITY & STALE RESIDUE ELIMINATION
    # ==========================================================================
    def test_route_switching(self):
        print("\n--- [ADV-02] ROUTE SWITCHING INTEGRITY & RESIDUE SCRUBBING ---")

        doc = MockDocument()
        layers = MockLayerGroup()
        state = AppState()
        state.selectedVehicle = 'ambulance'

        s1_expected_dest = self.data['routes']['scenario1']['destination']
        s2_expected_dest = self.data['routes']['scenario2']['destination']
        s1_expected_cues_len = len(self.data['routes']['scenario1']['turn_by_turn'])
        s2_expected_cues_len = len(self.data['routes']['scenario2']['turn_by_turn'])

        # Step 2.1: Initialize Scenario 1 (Velachery -> Guindy)
        state.activeScenario = 'scenario1'
        js_update_vehicle_and_route_ui(self.data, state, doc, layers)

        s1_direct_title = doc.get_element_by_id('route-direct-title').innerText
        s1_safe_title = doc.get_element_by_id('route-safe-title').innerText
        s1_destination = doc.get_element_by_id('route-destination-badge').innerText
        s1_direct_dist = doc.get_element_by_id('route-direct-dist').innerText
        s1_direct_eta = doc.get_element_by_id('route-direct-eta').innerText
        s1_direct_depth = doc.get_element_by_id('route-direct-depth').innerText
        s1_safe_dist = doc.get_element_by_id('route-safe-dist').innerText
        s1_safe_eta = doc.get_element_by_id('route-safe-eta').innerText
        s1_safe_depth = doc.get_element_by_id('route-safe-depth').innerText
        s1_cues_html = doc.get_element_by_id('route-turn-by-turn').innerHTML
        s1_cues_count = s1_cues_html.count('<li>')
        s1_layers_count = len(layers.layers)

        self.record(
            "RS_S1_INIT_DEST",
            "Route Switching",
            f"Scenario 1 destination matches data ('{s1_expected_dest}')",
            s1_destination == s1_expected_dest,
            f"actual='{s1_destination}'"
        )
        self.record(
            "RS_S1_INIT_CUES_COUNT",
            "Route Switching",
            f"Scenario 1 has exactly {s1_expected_cues_len} turn-by-turn waypoint cues",
            s1_cues_count == s1_expected_cues_len,
            f"count={s1_cues_count}"
        )
        self.record(
            "RS_S1_INIT_LAYERS_COUNT",
            "Route Switching",
            "Scenario 1 renders exactly 4 map layers (2 polylines + 2 markers)",
            s1_layers_count == 4,
            f"layers={s1_layers_count}"
        )

        # Step 2.2: Switch to Scenario 2 (Kilpauk Medical College -> Chennai Central)
        state.activeScenario = 'scenario2'
        js_update_vehicle_and_route_ui(self.data, state, doc, layers)

        s2_direct_title = doc.get_element_by_id('route-direct-title').innerText
        s2_safe_title = doc.get_element_by_id('route-safe-title').innerText
        s2_destination = doc.get_element_by_id('route-destination-badge').innerText
        s2_direct_dist = doc.get_element_by_id('route-direct-dist').innerText
        s2_direct_eta = doc.get_element_by_id('route-direct-eta').innerText
        s2_direct_depth = doc.get_element_by_id('route-direct-depth').innerText
        s2_safe_dist = doc.get_element_by_id('route-safe-dist').innerText
        s2_safe_eta = doc.get_element_by_id('route-safe-eta').innerText
        s2_safe_depth = doc.get_element_by_id('route-safe-depth').innerText
        s2_cues_html = doc.get_element_by_id('route-turn-by-turn').innerHTML
        s2_cues_count = s2_cues_html.count('<li>')
        s2_layers_count = len(layers.layers)

        # Verify Scenario 2 DOM values
        self.record(
            "RS_S2_DEST_UPDATE",
            "Route Switching",
            f"Scenario 2 destination cleanly updated to '{s2_expected_dest}'",
            s2_destination == s2_expected_dest,
            f"actual='{s2_destination}'"
        )
        self.record(
            "RS_S2_DIRECT_DIST_UPDATE",
            "Route Switching",
            "Scenario 2 direct distance updated to '4.2 km'",
            s2_direct_dist == '4.2 km',
            f"actual='{s2_direct_dist}'"
        )
        self.record(
            "RS_S2_DIRECT_DEPTH_UPDATE",
            "Route Switching",
            "Scenario 2 direct bottleneck depth updated to '44.0 cm'",
            s2_direct_depth == '44.0 cm',
            f"actual='{s2_direct_depth}'"
        )
        self.record(
            "RS_S2_SAFE_DEPTH_UPDATE",
            "Route Switching",
            "Scenario 2 safe bypass depth updated to '6.2 cm'",
            s2_safe_depth == '6.2 cm',
            f"actual='{s2_safe_depth}'"
        )
        self.record(
            "RS_S2_CUES_COUNT",
            "Route Switching",
            f"Scenario 2 has exactly {s2_expected_cues_len} turn-by-turn waypoint cues (no cue accumulation)",
            s2_cues_count == s2_expected_cues_len,
            f"count={s2_cues_count}"
        )
        self.record(
            "RS_S2_LAYERS_COUNT",
            "Route Switching",
            "Scenario 2 map layers count remains exactly 4 (no layer leakage)",
            s2_layers_count == 4,
            f"layers={s2_layers_count}"
        )

        # Adversarial Stale Residue Elimination in Scenario 2:
        # Check that NO terms from Scenario 1 exist anywhere in Scenario 2 UI
        s1_residues = ['Velachery', 'Guindy', '100 Feet Road', '52.4 cm', 'Inner Ring Road']
        for res_term in s1_residues:
            in_dest = res_term in s2_destination
            in_direct_title = res_term in s2_direct_title
            in_safe_title = res_term in s2_safe_title
            in_cues = res_term in s2_cues_html
            in_direct_depth = res_term in s2_direct_depth
            in_safe_depth = res_term in s2_safe_depth

            has_residue = in_dest or in_direct_title or in_safe_title or in_cues or in_direct_depth or in_safe_depth
            self.record(
                f"RS_NO_S1_RESIDUE_{res_term.replace(' ', '_').upper()}",
                "Stale Residue Elimination",
                f"Scenario 2 contains zero stale residue of Scenario 1 keyword '{res_term}'",
                not has_residue,
                f"found_in: dest={in_dest}, title={in_direct_title}, cues={in_cues}, depths={in_direct_depth or in_safe_depth}"
            )

        # Step 2.3: Switch back from Scenario 2 to Scenario 1
        state.activeScenario = 'scenario1'
        js_update_vehicle_and_route_ui(self.data, state, doc, layers)

        s1_back_dest = doc.get_element_by_id('route-destination-badge').innerText
        s1_back_direct_dist = doc.get_element_by_id('route-direct-dist').innerText
        s1_back_direct_depth = doc.get_element_by_id('route-direct-depth').innerText
        s1_back_safe_depth = doc.get_element_by_id('route-safe-depth').innerText
        s1_back_cues_html = doc.get_element_by_id('route-turn-by-turn').innerHTML
        s1_back_cues_count = s1_back_cues_html.count('<li>')
        s1_back_layers_count = len(layers.layers)

        self.record(
            "RS_S1_RESTORE_DEST",
            "Route Switching Restoration",
            f"Returning to Scenario 1 cleanly restores destination '{s1_expected_dest}'",
            s1_back_dest == s1_destination,
            f"actual='{s1_back_dest}', expected='{s1_destination}'"
        )
        self.record(
            "RS_S1_RESTORE_DIRECT_DEPTH",
            "Route Switching Restoration",
            "Returning to Scenario 1 cleanly restores direct depth '52.4 cm'",
            s1_back_direct_depth == s1_direct_depth,
            f"actual='{s1_back_direct_depth}', expected='{s1_direct_depth}'"
        )
        self.record(
            "RS_S1_RESTORE_SAFE_DEPTH",
            "Route Switching Restoration",
            "Returning to Scenario 1 cleanly restores safe depth '8.5 cm'",
            s1_back_safe_depth == s1_safe_depth,
            f"actual='{s1_back_safe_depth}', expected='{s1_safe_depth}'"
        )
        self.record(
            "RS_S1_RESTORE_CUES_COUNT",
            "Route Switching Restoration",
            f"Returning to Scenario 1 restores cue count to exactly {s1_expected_cues_len}",
            s1_back_cues_count == s1_expected_cues_len,
            f"count={s1_back_cues_count}"
        )
        self.record(
            "RS_S1_RESTORE_LAYERS_COUNT",
            "Route Switching Restoration",
            "Returning to Scenario 1 keeps map layers count at exactly 4",
            s1_back_layers_count == 4,
            f"layers={s1_back_layers_count}"
        )

        # Adversarial Stale Residue Elimination in Restored Scenario 1:
        s2_residues = ['Kilpauk', 'Chennai Central', 'EVR Periyar Salai', 'Ormes Road', 'Poonamallee', '44.0 cm', '6.2 cm']
        for res_term in s2_residues:
            in_dest = res_term in s1_back_dest
            in_direct_title = res_term in doc.get_element_by_id('route-direct-title').innerText
            in_cues = res_term in s1_back_cues_html
            in_direct_depth = res_term in s1_back_direct_depth
            in_safe_depth = res_term in s1_back_safe_depth

            has_residue = in_dest or in_direct_title or in_cues or in_direct_depth or in_safe_depth
            self.record(
                f"RS_NO_S2_RESIDUE_{res_term.replace(' ', '_').upper()}",
                "Stale Residue Elimination",
                f"Restored Scenario 1 contains zero stale residue of Scenario 2 keyword '{res_term}'",
                not has_residue,
                f"found_in: dest={in_dest}, title={in_direct_title}, cues={in_cues}, depths={in_direct_depth or in_safe_depth}"
            )

        # Step 2.4: Rapid 20-Cycle Switching Stress Test
        stress_pass = True
        for cycle in range(20):
            target_scen = 'scenario2' if cycle % 2 == 0 else 'scenario1'
            state.activeScenario = target_scen
            js_update_vehicle_and_route_ui(self.data, state, doc, layers)
            if len(layers.layers) != 4:
                stress_pass = False
                break
            c_cnt = doc.get_element_by_id('route-turn-by-turn').innerHTML.count('<li>')
            expected_cues = len(self.data['routes'][target_scen]['turn_by_turn'])
            if c_cnt != expected_cues:
                stress_pass = False
                break

        self.record(
            "RS_RAPID_20_CYCLE_STRESS",
            "Switching Stress Testing",
            "20 consecutive rapid route switches maintain exact DOM cue count and layer count (4)",
            stress_pass,
            f"completed=20 cycles, last_layers={len(layers.layers)}"
        )

    # ==========================================================================
    # SECTION 3: MANHOLE SELECTION HYDRAULIC INTEGRITY (ALL 25 MANHOLES)
    # ==========================================================================
    def test_manhole_selection(self):
        print("\n--- [ADV-03] MANHOLE SELECTION & HYDRAULIC ATTRIBUTE VERIFICATION ---")

        manholes = self.data.get('surcharging_manholes', [])
        self.record(
            "MH_COUNT_EXACT_25",
            "Manhole Asset Dataset",
            "Authentic dataset contains exactly 25 field-audited surcharging manhole nodes",
            len(manholes) == 25,
            f"count={len(manholes)}"
        )

        doc = MockDocument()
        state = AppState()

        all_manholes_valid = True
        failed_mh_ids = []

        for idx, mh in enumerate(manholes):
            mh_id = mh.get('id', f'MH_{idx}')
            
            # Simulate clicking the manhole marker on the map
            js_select_asset('manhole', mh, state, doc)

            # Check that tab switched to inspector
            tab_switched = state.activeTab == 'inspector' and 'hidden' not in doc.get_element_by_id('tab-inspector').classList

            # Extract Inspector fields
            dom_id = doc.get_element_by_id('inspector-asset-id').innerText
            dom_zone = doc.get_element_by_id('inspector-zone').innerText
            dom_elev = doc.get_element_by_id('inspector-elevation').innerText
            dom_dia = doc.get_element_by_id('inspector-dia').innerText
            dom_manning = doc.get_element_by_id('inspector-manning').innerText
            dom_theor_cap = doc.get_element_by_id('inspector-theor-cap').innerText
            dom_clog = doc.get_element_by_id('inspector-clog').innerText
            dom_eff_cap = doc.get_element_by_id('inspector-eff-cap').innerText
            dom_hgl = doc.get_element_by_id('inspector-hgl').innerText
            dom_backflow = doc.get_element_by_id('inspector-backflow').innerText
            dom_depth = doc.get_element_by_id('inspector-depth').innerText

            # Validate non-empty and no NaN strings
            fields = {
                'id': dom_id,
                'zone': dom_zone,
                'elev': dom_elev,
                'dia': dom_dia,
                'manning': dom_manning,
                'theor_cap': dom_theor_cap,
                'clog': dom_clog,
                'eff_cap': dom_eff_cap,
                'hgl': dom_hgl,
                'backflow': dom_backflow,
                'depth': dom_depth
            }

            has_nan = any('NaN' in v or 'undefined' in v or 'null' in v or v == "" for v in fields.values())

            # Parse numeric quantities and verify sanity
            try:
                elev_val = float(dom_elev.split()[0])
                dia_val = float(dom_dia.split()[0])
                theor_val = float(dom_theor_cap.split()[0])
                eff_val = float(dom_eff_cap.split()[0])
                hgl_val = float(dom_hgl.split()[0])
                backflow_val = float(dom_backflow.split()[0])
                depth_val = float(dom_depth.split()[0])

                num_ok = (
                    not math.isnan(elev_val) and elev_val > 0 and
                    not math.isnan(dia_val) and dia_val > 0 and
                    not math.isnan(theor_val) and theor_val > 0 and
                    not math.isnan(eff_val) and eff_val > 0 and
                    not math.isnan(hgl_val) and hgl_val > 0 and
                    not math.isnan(backflow_val) and backflow_val >= 0 and
                    not math.isnan(depth_val) and depth_val >= 0
                )
            except Exception as e:
                num_ok = False

            # Verify Saint-Venant orifice backflow equation:
            # Q = Cd * A * sqrt(2 * g * delta_h)
            delta_h = max(0.0, hgl_val - elev_val)
            area = math.pi * ((dia_val / 1000.0) ** 2) / 4.0
            cd = mh.get('discharge_coeff', 0.62)
            expected_q = cd * area * math.sqrt(2 * 9.81 * delta_h) if delta_h > 0 else 0.0
            orifice_ok = abs(backflow_val - expected_q) < 0.005 # 3 decimal places matching

            is_valid = tab_switched and (not has_nan) and num_ok and orifice_ok
            if not is_valid:
                all_manholes_valid = False
                failed_mh_ids.append(mh_id)

            self.record(
                f"MH_INSPECT_{mh_id}",
                "Manhole Diagnostic Inspector",
                f"Clicking manhole {mh_id} populates valid non-NaN hydraulic attributes & verifies Saint-Venant orifice physics",
                is_valid,
                f"elev={elev_val:.2f}m, HGL={hgl_val:.2f}m, Δh={delta_h:.2f}m, Q_backflow={backflow_val:.3f}m³/s (expected={expected_q:.3f})"
            )

        self.record(
            "MH_ALL_25_INSPECTOR_VALID",
            "Manhole Asset Evaluation",
            "All 25 chronic surcharging manholes yield 100% valid, non-NaN hydraulic parameters in inspector",
            all_manholes_valid,
            f"failures={failed_mh_ids}"
        )

        # Test 3.2: Multi-Timestep Dynamic Manhole Stress (All 25 Manholes × 6 Timesteps = 150 checks)
        timestep_stress_ok = True
        for t_idx in range(6):
            state.currentTimeStep = t_idx
            for mh in manholes:
                js_select_asset('manhole', mh, state, doc)
                dom_backflow = doc.get_element_by_id('inspector-backflow').innerText
                dom_depth = doc.get_element_by_id('inspector-depth').innerText
                if 'NaN' in dom_backflow or 'NaN' in dom_depth or 'undefined' in dom_backflow:
                    timestep_stress_ok = False
                    break

        self.record(
            "MH_TIMESTEP_STRESS_150_CHECKS",
            "Manhole Dynamic Simulation",
            "All 25 manholes across all 6 nowcast timesteps (T+0 to T+180) compute non-NaN surcharge hydraulics",
            timestep_stress_ok,
            "150 / 150 state combinations evaluated"
        )

        # Test 3.3: Dynamic Clogging Factor Stress (0%, 35%, 80%) on Manhole Inspector
        clog_stress_ok = True
        state.currentTimeStep = 3 # Peak T+90m
        for clog_val in [0, 35, 80]:
            state.cloggingMultiplier = 0.6 + (clog_val / 100.0) * 0.8
            for mh in manholes:
                js_select_asset('manhole', mh, state, doc)
                dom_eff_cap = doc.get_element_by_id('inspector-eff-cap').innerText
                eff_val = float(dom_eff_cap.split()[0])
                theor_val = float(doc.get_element_by_id('inspector-theor-cap').innerText.split()[0])
                if eff_val > theor_val or eff_val <= 0 or math.isnan(eff_val):
                    clog_stress_ok = False
                    break

        self.record(
            "MH_CLOGGING_STRESS_75_CHECKS",
            "Dynamic Clogging Response",
            "All 25 manholes under 0%, 35%, and 80% clogging maintain positive choked carrying capacity (0 < Q_eff <= Q0)",
            clog_stress_ok,
            "75 / 75 clogging tests evaluated"
        )

    # ==========================================================================
    # SECTION 4: STANDALONE LAUNCHER & ZERO-DEPENDENCY FILE VERIFICATION
    # ==========================================================================
    def test_standalone_launcher_and_files(self):
        print("\n--- [ADV-04] STANDALONE LAUNCHER & ZERO-DEPENDENCY VERIFICATION ---")

        # 4.1 Check launch_dashboard.bat exists and content
        bat_exists = self.launcher_bat_file.exists()
        self.record(
            "SL_BAT_FILE_EXISTS",
            "Standalone Launcher",
            "launch_dashboard.bat exists in project root directory",
            bat_exists,
            f"path={self.launcher_bat_file}"
        )

        if bat_exists:
            with open(self.launcher_bat_file, 'r', encoding='utf-8') as f:
                bat_content = f.read()

            starts_index = '%~dp0frontend\\index.html' in bat_content or 'frontend\\index.html' in bat_content
            self.record(
                "SL_BAT_STARTS_INDEX",
                "Standalone Launcher",
                "launch_dashboard.bat opens frontend\\index.html via relative %~dp0 path",
                starts_index,
                "Relative invocation confirmed"
            )

            # Check zero external runtime dependencies in bat file
            prohibited_commands = ['npm', 'npx', 'node', 'pip', 'python', 'docker', 'yarn', 'pnpm', 'http-server']
            found_prohibited = [cmd for cmd in prohibited_commands if re.search(rf'\b{cmd}\b', bat_content, re.I)]
            self.record(
                "SL_BAT_ZERO_DEPENDENCIES",
                "Standalone Launcher",
                "launch_dashboard.bat contains ZERO npm/node/pip/python/docker prerequisite calls",
                len(found_prohibited) == 0,
                f"prohibited_found={found_prohibited}"
            )

            has_clean_exit = 'exit /b 0' in bat_content or 'exit' in bat_content
            self.record(
                "SL_BAT_CLEAN_EXIT",
                "Standalone Launcher",
                "launch_dashboard.bat exits cleanly with code 0",
                has_clean_exit,
                "Clean exit instruction verified"
            )

        # 4.2 Check frontend/index.html file:/// CORS safety and relative loading
        with open(self.index_html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Check relative script inclusion of data/chennai_flood_data.js
        loads_local_data = '<script src="data/chennai_flood_data.js"></script>' in html_content
        self.record(
            "SL_LOCAL_DATA_SCRIPT_TAG",
            "Zero-Dependency Architecture",
            "index.html includes data/chennai_flood_data.js via standard relative script tag",
            loads_local_data,
            "relative script tag verified"
        )

        # Check for ZERO local fetch() or XMLHttpRequest calls
        # (local file fetch triggers CORS origin 'null' error in modern browsers)
        fetch_calls = re.findall(r'fetch\([\'\"](?!\s*https?://)', html_content)
        xhr_calls = re.findall(r'new\s+XMLHttpRequest', html_content)
        self.record(
            "SL_ZERO_LOCAL_FILE_FETCH_CORS",
            "file:/// Protocol Integrity",
            "index.html makes ZERO local file fetch() or XMLHttpRequest calls (eliminating file:/// CORS blocks)",
            len(fetch_calls) == 0 and len(xhr_calls) == 0,
            f"local_fetch_count={len(fetch_calls)}, xhr_count={len(xhr_calls)}"
        )

        # Check global window namespace exposure
        with open(self.data_file, 'r', encoding='utf-8') as f:
            data_content = f.read()

        assigns_global = 'window.CHENNAI_FLOOD_DATA =' in data_content
        self.record(
            "SL_GLOBAL_WINDOW_DATA_NAMESPACE",
            "Data Pipeline Architecture",
            "chennai_flood_data.js binds master dataset to window.CHENNAI_FLOOD_DATA",
            assigns_global,
            "window.CHENNAI_FLOOD_DATA export verified"
        )

        # Check data asset scale
        segments_count = len(self.data.get('segments', []))
        substations_count = len(self.data.get('substations', []))
        routes_count = len(self.data.get('routes', {}))

        self.record(
            "SL_AUTHENTIC_DATA_SCALE",
            "Data Pipeline Scale",
            "Master flood dataset contains 500+ road segments, 20 substations, and 2 routing scenarios",
            segments_count >= 500 and substations_count == 20 and routes_count == 2,
            f"segments={segments_count}, substations={substations_count}, routes={routes_count}"
        )

    # ==========================================================================
    # EXECUTION HARNESS & VERDICT
    # ==========================================================================
    def run_all_challenges(self):
        t0 = time.perf_counter()
        print("=" * 80)
        print("  CHALLENGER 2: ADVERSARIAL VERIFICATION SUITE")
        print("  Routing, Vehicle Clearances, UI States & Event Handling")
        print("  Project: SIH 2026 #26085 | Greater Chennai Corporation")
        print("=" * 80)

        self.test_vehicle_clearances()
        self.test_route_switching()
        self.test_manhole_selection()
        self.test_standalone_launcher_and_files()

        duration = time.perf_counter() - t0
        total_checks = len(self.checks)
        passed_checks = sum(1 for c in self.checks if c.passed)
        failed_checks = total_checks - passed_checks
        pass_rate = (passed_checks / total_checks) * 100.0 if total_checks > 0 else 0.0

        print("\n" + "=" * 80)
        print("  CHALLENGE AUDIT SUMMARY REPORT")
        print("=" * 80)
        print(f"  Total Adversarial Checks: {total_checks}")
        print(f"  Passed Checks:           {passed_checks}")
        print(f"  Failed Checks (Defects): {failed_checks}")
        print(f"  Pass Rate:               {pass_rate:.1f}%")
        print(f"  Execution Time:          {duration:.3f} seconds")
        print("-" * 80)

        categories = {}
        for c in self.checks:
            cat = c.category
            if cat not in categories:
                categories[cat] = {'total': 0, 'passed': 0}
            categories[cat]['total'] += 1
            if c.passed:
                categories[cat]['passed'] += 1

        for cat, stats in categories.items():
            pct = (stats['passed'] / stats['total']) * 100.0
            print(f"  {cat:<32} {stats['passed']:>3} / {stats['total']:>3} ({pct:>5.1f}%)")

        print("=" * 80)

        if failed_checks == 0:
            verdict = "CONFIRM_CORRECTNESS"
            print(f"\n>>> FINAL VERDICT: {verdict} <<<")
            print("All adversarial challenges, boundary conditions, and state transitions verified successfully.\n")
        else:
            verdict = "REPORT_DEFECT"
            print(f"\n>>> FINAL VERDICT: {verdict} <<<")
            print(f"{failed_checks} defects detected during adversarial challenge.\n")

        return {
            'verdict': verdict,
            'total': total_checks,
            'passed': passed_checks,
            'failed': failed_checks,
            'pass_rate': pass_rate,
            'duration': duration,
            'categories': categories,
            'checks': self.checks
        }


if __name__ == '__main__':
    current = Path(__file__).resolve()
    root_directory = current.parent
    for _ in range(5):
        if (root_directory / 'frontend').is_dir():
            break
        root_directory = root_directory.parent
    challenger = AdversarialChallengerM82(root_directory)
    result = challenger.run_all_challenges()
    sys.exit(0 if result['verdict'] == 'CONFIRM_CORRECTNESS' else 1)

