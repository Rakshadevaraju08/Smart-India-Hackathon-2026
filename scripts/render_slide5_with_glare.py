"""
Render Ultra High-Resolution 4K Slide 5 Infographic with Indian Flag Ambient Glare
Clean typography, zero overlapping text, crisp layout matching SIH Winner Team UDAAN.
Top Section: Prototype Showcase Cards (Officer Command Twin, A* Evacuation Twin, Hydro Inspector)
Bottom Left: Measurable Social, Economic & Operational Impact (4 Cleanly Spaced Metric Cards)
Bottom Right: Future Scalability & Improvement Roadmap (5-Stage Chevron Flow + Extensibility Card)
Footer: Live Prototype, GitHub Repo, and Demo Video Links
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Polygon
import numpy as np
import textwrap

def render_slide5_with_glare():
    fig = plt.figure(figsize=(16, 9), dpi=240, facecolor='#FFFFFF')
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis('off')

    # 1. Indian Flag Ambient Glare Background
    nx, ny = 1200, 675
    gx = np.linspace(0, 16, nx)
    gy = np.linspace(0, 9, ny)
    X, Y = np.meshgrid(gx, gy)

    orange_glare = np.exp(-(((X - 8.0) / 7.5)**2 + ((Y - 9.2) / 2.8)**2))
    green_glare = np.exp(-(((X - 8.0) / 7.5)**2 + ((Y - -0.2) / 2.6)**2))

    bg_rgba = np.ones((ny, nx, 4))
    for c, val in enumerate([1.0, 0.52, 0.10]):
        bg_rgba[:, :, c] = bg_rgba[:, :, c] * (1.0 - orange_glare * 0.20) + val * (orange_glare * 0.20)
    for c, val in enumerate([0.08, 0.58, 0.18]):
        bg_rgba[:, :, c] = bg_rgba[:, :, c] * (1.0 - green_glare * 0.16) + val * (green_glare * 0.16)

    ax.imshow(bg_rgba, origin='lower', extent=[0, 16, 0, 9], aspect='auto', zorder=0)

    # 2. Main Title Banner
    banner = FancyBboxPatch((4.0, 8.2), 8.0, 0.62, boxstyle="round,pad=0.08,rounding_size=0.3",
                            facecolor='#EFF6FF', edgecolor='#3B82F6', linewidth=1.5, zorder=3)
    ax.add_patch(banner)
    ax.text(8.0, 8.51, "IMPACT, BENEFITS & PROTOTYPE SHOWCASE", ha='center', va='center',
            fontsize=15, fontweight='bold', color='#1E3A8A', zorder=4)

    # -------------------------------------------------------------
    # TOP SECTION: 3 PROTOTYPE SHOWCASE MOCKUP CARDS
    # -------------------------------------------------------------
    
    # Left: Hydro-Asset Inspector Mockup
    card_l = FancyBboxPatch((0.8, 4.5), 4.2, 3.4, boxstyle="round,pad=0.06,rounding_size=0.2",
                            facecolor='#0F172A', edgecolor='#334155', linewidth=1.5, zorder=3)
    ax.add_patch(card_l)
    
    ax.text(1.1, 7.6, "Asset Hydro-Inspector", fontsize=10, fontweight='bold', color='#38BDF8', zorder=4)
    ax.text(4.7, 7.6, "CHN_SEG_00412", fontsize=8, fontfamily='monospace', color='#94A3B8', ha='right', zorder=4)
    
    fields_l = [
        ("Zone / Location:", "Perungudi / Velachery Lake"),
        ("Surface Elevation:", "4.15 m MSL (Low Basin)"),
        ("SWD Conduit Dia:", "600 mm RCC Hume Pipe"),
        ("Rated Capacity Q₀:", "0.317 m³/s"),
        ("Dynamic Clog μ:", "0.38 (38% Silt/Debris)"),
        ("Effective Cap Q_eff:", "0.196 m³/s (-38%)"),
        ("Hydraulic Grade Line:", "4.82 m (Surcharge: +0.67m)"),
        ("Backflow Fountain:", "0.42 m³/s (Fountain Active)")
    ]
    for idx, (lbl, val) in enumerate(fields_l):
        yy = 7.15 - idx * 0.31
        ax.text(1.1, yy, lbl, fontsize=7.5, color='#94A3B8', zorder=4)
        col = '#F43F5E' if 'Surcharge' in val or 'Fountain' in val else '#F1F5F9'
        ax.text(4.7, yy, val, fontsize=7.5, fontfamily='monospace', fontweight='bold', color=col, ha='right', zorder=4)
        ax.plot([1.1, 4.7], [yy - 0.08, yy - 0.08], color='#1E293B', lw=0.8, zorder=3)

    # Center: Officer Command Twin GIS Dashboard Mockup
    card_c = FancyBboxPatch((5.3, 4.5), 5.4, 3.4, boxstyle="round,pad=0.06,rounding_size=0.2",
                            facecolor='#0B0F19', edgecolor='#0EA5E9', linewidth=1.8, zorder=3)
    ax.add_patch(card_c)

    ax.text(5.55, 7.6, "Kairos Command Twin • Web GIS View", fontsize=10.5, fontweight='bold', color='#FFFFFF', zorder=4)
    ax.text(10.45, 7.6, "IMD Radar: ACTIVE", fontsize=8, fontfamily='monospace', color='#10B981', ha='right', zorder=4)

    # Mock Map Canvas Box
    map_box = FancyBboxPatch((5.55, 5.15), 4.9, 2.2, boxstyle="round,pad=0.04,rounding_size=0.1",
                             facecolor='#020617', edgecolor='#1E293B', linewidth=1.0, zorder=4)
    ax.add_patch(map_box)

    # Mock Map Vector Lines (Roads)
    ax.plot([5.8, 6.6, 7.5, 8.4], [6.8, 6.7, 6.9, 6.6], color='#10B981', lw=3.0, zorder=5)
    ax.plot([7.5, 8.2, 9.2, 10.1], [6.9, 6.2, 6.5, 6.7], color='#10B981', lw=3.0, zorder=5)
    ax.plot([6.2, 7.0, 7.8], [5.6, 5.8, 5.7], color='#F59E0B', lw=3.5, zorder=5)
    ax.plot([7.0, 7.6, 8.5, 9.3], [5.8, 5.4, 5.5, 5.3], color='#EF4444', lw=4.5, zorder=5)
    ax.plot([7.6, 7.8, 8.2], [5.4, 5.9, 6.2], color='#EF4444', lw=4.0, zorder=5)
    
    # Pulsing manhole markers
    ax.scatter([7.6, 8.5, 7.8], [5.4, 5.5, 5.9], color='#EF4444', s=65, edgecolors='white', linewidths=1.5, zorder=6)

    # Map Labels
    ax.text(6.0, 6.9, "Poonamallee High (Safe: 4cm)", fontsize=6.5, color='#A7F3D0', zorder=6)
    ax.text(7.7, 5.25, "Velachery Subway (FLOODED: 52cm)", fontsize=6.5, fontweight='bold', color='#FCA5A5', zorder=6)

    # Bottom Dock Mockup
    ax.text(5.55, 4.95, "Nowcast: T + 60m (19:40 IST)", fontsize=8, fontfamily='monospace', color='#38BDF8', zorder=4)
    ax.text(10.45, 4.95, "Peak Rain: 84 mm/h", fontsize=8, fontfamily='monospace', color='#F59E0B', ha='right', zorder=4)
    ax.plot([5.55, 10.45], [4.72, 4.72], color='#334155', lw=4.0, zorder=4)
    ax.plot([5.55, 7.8], [4.72, 4.72], color='#0EA5E9', lw=4.0, zorder=5)
    ax.scatter([7.8], [4.72], color='#FFFFFF', s=45, zorder=6)

    # Right: First Responder Navigation Mockup
    card_r = FancyBboxPatch((11.0, 4.5), 4.2, 3.4, boxstyle="round,pad=0.06,rounding_size=0.2",
                            facecolor='#0F172A', edgecolor='#334155', linewidth=1.5, zorder=3)
    ax.add_patch(card_r)

    ax.text(11.25, 7.6, "108 Ambulance A* Routing", fontsize=10, fontweight='bold', color='#10B981', zorder=4)
    ax.text(14.95, 7.6, "Clearance: 30cm", fontsize=8, fontfamily='monospace', color='#FCD34D', ha='right', zorder=4)

    # Route 1: Direct Trapped Box
    trap_box = FancyBboxPatch((11.25, 6.25), 3.7, 1.1, boxstyle="round,pad=0.04,rounding_size=0.1",
                              facecolor='#450A0A', edgecolor='#DC2626', linewidth=1.2, zorder=4)
    ax.add_patch(trap_box)
    ax.text(11.4, 7.1, "Standard Route (Submerged)", fontsize=8, fontweight='bold', color='#F87171', zorder=5)
    ax.text(11.4, 6.75, "Bottleneck: Velachery Underpass (52.4 cm)", fontsize=7.2, color='#FECACA', zorder=5)
    ax.text(11.4, 6.45, "STATUS: IMPASSABLE (Engine Hydrolock)", fontsize=7.2, fontfamily='monospace', fontweight='bold', color='#EF4444', zorder=5)

    # Route 2: Safe Calculated Bypass Box
    safe_box = FancyBboxPatch((11.25, 4.9), 3.7, 1.1, boxstyle="round,pad=0.04,rounding_size=0.1",
                             facecolor='#064E3B', edgecolor='#059669', linewidth=1.2, zorder=4)
    ax.add_patch(safe_box)
    ax.text(11.4, 5.75, "Kairos A* Safe Bypass (Active)", fontsize=8, fontweight='bold', color='#34D399', zorder=5)
    ax.text(11.4, 5.4, "Bypass Ridge Route: Max Depth 8.5 cm", fontsize=7.2, color='#A7F3D0', zorder=5)
    ax.text(11.4, 5.1, "STATUS: 100% CLEAR (+3.2 min detour)", fontsize=7.2, fontfamily='monospace', fontweight='bold', color='#10B981', zorder=5)

    # -------------------------------------------------------------
    # BOTTOM LEFT: QUANTITATIVE IMPACT & BENEFITS (4 Cleanly Spaced Cards)
    # -------------------------------------------------------------
    impact_title = FancyBboxPatch((0.8, 3.82), 6.4, 0.42, boxstyle="round,pad=0.05,rounding_size=0.15",
                                  facecolor='#FEF3C7', edgecolor='#F59E0B', linewidth=1.2, zorder=3)
    ax.add_patch(impact_title)
    ax.text(4.0, 4.03, "Measurable Social, Economic & Operational Impact", ha='center', va='center',
            fontsize=10.5, fontweight='bold', color='#92400E', zorder=4)

    impacts = [
        ("₹1,200+ Cr Direct Loss Avoidance", "Cyclone Michaung inflicted ₹4,000+ Cr damage. 2h nowcasting enables proactive basement barricades & asset relocation.", "#DC2626"),
        ("65% Reduction in Ambulance Stalls", "Eliminates ambulance hydrolock traps in flooded subways via dynamic vehicle-clearance A* detour recalculation.", "#059669"),
        ("Targeted GCC Pump Pre-Deployment", "Shifts municipal response from reactive pumping to pre-positioning high-capacity diesel de-watering sets 90m ahead of peak runoff.", "#2563EB"),
        ("1.8M Ward Residents Safeguarded", "Hyper-local SMS/WhatsApp alerts warn low-elevation basin residents before storm drains begin surcharging onto roads.", "#7C3AED")
    ]

    for idx, (title, desc, col) in enumerate(impacts):
        iy = 3.32 - idx * 0.72
        ibox = FancyBboxPatch((0.8, iy - 0.28), 6.4, 0.62, boxstyle="round,pad=0.04,rounding_size=0.1",
                              facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.0, zorder=2)
        ax.add_patch(ibox)
        
        # Color accent stripe
        cbar = FancyBboxPatch((0.8, iy - 0.28), 0.18, 0.62, boxstyle="round,pad=0.0,rounding_size=0.05",
                              facecolor=col, edgecolor='none', zorder=3)
        ax.add_patch(cbar)
        
        # Title (anchored to bottom of top half)
        ax.text(1.15, iy + 0.06, title, fontsize=8.2, fontweight='bold', color='#0F172A', va='bottom', zorder=4)
        # Description (anchored to top of bottom half)
        wrapped_desc = textwrap.fill(desc, width=64)
        ax.text(1.15, iy + 0.02, wrapped_desc, fontsize=6.8, color='#475569', va='top', zorder=4, linespacing=1.2)

    # -------------------------------------------------------------
    # BOTTOM RIGHT: SCALABILITY & FUTURE IMPROVEMENTS CHEVRON FLOW
    # -------------------------------------------------------------
    road_title = FancyBboxPatch((7.6, 3.82), 7.6, 0.42, boxstyle="round,pad=0.05,rounding_size=0.15",
                                facecolor='#EFF6FF', edgecolor='#3B82F6', linewidth=1.2, zorder=3)
    ax.add_patch(road_title)
    ax.text(11.4, 4.03, "Future Scalability & Improvement Roadmap", ha='center', va='center',
            fontsize=10.5, fontweight='bold', color='#1E40AF', zorder=4)

    chevrons = [
        ("Phase 1: Pilot", "GCC 15 Zones\n7,894 Segments", "#2563EB"),
        ("Phase 2: Data", "OSM + Dual-Pol\nRadar Stream", "#0891B2"),
        ("Phase 3: Cities", "Mumbai BMC &\nBengaluru BBMP", "#059669"),
        ("Phase 4: NDMA", "National Disaster\nAPI Integration", "#D97706"),
        ("Phase 5: SCADA", "Automated Sluice\n& Pump Gates", "#7C3AED")
    ]

    ch_w = 1.42
    ch_h = 0.95
    ch_start_x = 7.6
    ch_y = 2.45

    for idx, (title, sub, col) in enumerate(chevrons):
        cx = ch_start_x + idx * 1.52
        pts = np.array([
            [cx, ch_y - ch_h/2],
            [cx + ch_w - 0.22, ch_y - ch_h/2],
            [cx + ch_w, ch_y],
            [cx + ch_w - 0.22, ch_y + ch_h/2],
            [cx, ch_y + ch_h/2],
            [cx + 0.22, ch_y]
        ])
        poly = Polygon(pts, closed=True, facecolor=col, edgecolor='#FFFFFF', linewidth=1.5, zorder=3)
        ax.add_patch(poly)
        
        ax.text(cx + ch_w/2, ch_y + 0.16, title, ha='center', va='center', fontsize=7.8, fontweight='bold', color='#FFFFFF', zorder=4)
        ax.text(cx + ch_w/2, ch_y - 0.20, sub, ha='center', va='center', fontsize=6.5, color='#F8FAFC', zorder=4, linespacing=1.15)

    # Bottom Right Extensibility Card
    desc_road = FancyBboxPatch((7.6, 0.98), 7.6, 0.65, boxstyle="round,pad=0.04,rounding_size=0.1",
                               facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.0, zorder=2)
    ax.add_patch(desc_road)
    ax.text(7.85, 1.42, "Architectural Extensibility:", fontsize=8.0, fontweight='bold', color='#0F172A', zorder=3)
    ax.text(7.85, 1.16, "Built on standard OpenStreetMap graph topology and OGC SensorThings API, allowing rapid porting to any coastal or riverine Indian metropolis in under 72 hours without rewriting solver kernels.",
            fontsize=7.2, color='#475569', wrap=True, zorder=3)

    # -------------------------------------------------------------
    # FOOTER: PROTOTYPE LINKS (Clean Text, No missing glyphs)
    # -------------------------------------------------------------
    ax.plot([0.8, 15.2], [0.60, 0.60], color='#CBD5E1', lw=1.0, zorder=2)

    ax.text(2.2, 0.32, "[Demo Video] Prototype Video Link: Click Here", fontsize=8.8, fontweight='bold', color='#2563EB', zorder=3)
    ax.text(7.5, 0.32, "[GitHub] Project Repo Link: Click Here", fontsize=8.8, fontweight='bold', color='#059669', zorder=3)
    ax.text(12.8, 0.32, "[Web GIS] Live Command Twin: Click Here", fontsize=8.8, fontweight='bold', color='#7C3AED', zorder=3)

    output_path = 'slide5_impact_benefits_tiranga_glare.png'
    plt.savefig(output_path, dpi=240, bbox_inches='tight', pad_inches=0.02)
    plt.close()
    print(f"Slide 5 re-rendered cleanly to {output_path}")

if __name__ == '__main__':
    render_slide5_with_glare()
