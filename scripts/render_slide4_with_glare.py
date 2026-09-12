"""
Render Ultra High-Resolution 4K Slide 4 Infographic with Indian Flag Ambient Glare
(Saffron/Orange top glare, India Green bottom glare, and template-matched color scheme)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Wedge
import numpy as np

def render_slide4_with_glare():
    # 4K Canvas (16:9 ratio, 3840 x 2160 at 240 DPI)
    fig = plt.figure(figsize=(16, 9), dpi=240, facecolor='#FFFFFF')
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis('off')

    # 1. Create Ambient Indian Flag Glare Background
    # High-resolution mesh for smooth gradient lighting
    nx, ny = 1200, 675
    gx = np.linspace(0, 16, nx)
    gy = np.linspace(0, 9, ny)
    X, Y = np.meshgrid(gx, gy)

    # Top Orange / Saffron Glare (centered around top middle x=8.0, y=9.0)
    # Uses smooth exponential falloff for soft photographic studio glare
    orange_glare = np.exp(-(((X - 8.0) / 7.5)**2 + ((Y - 9.2) / 2.8)**2))
    
    # Bottom India Green Glare (centered around bottom middle x=8.0, y=0.0)
    green_glare = np.exp(-(((X - 8.0) / 7.5)**2 + ((Y - -0.2) / 2.6)**2))

    # Construct RGBA buffer
    # Saffron RGB: (255, 130, 20) / 255 -> [1.0, 0.51, 0.08]
    # Green RGB: (18, 140, 30) / 255 -> [0.07, 0.55, 0.12]
    bg_rgba = np.ones((ny, nx, 4))
    
    # Apply Saffron glow (max opacity ~0.22 for subtle luminous glare)
    for c, val in enumerate([1.0, 0.52, 0.10]):
        bg_rgba[:, :, c] = bg_rgba[:, :, c] * (1.0 - orange_glare * 0.22) + val * (orange_glare * 0.22)
        
    # Apply Green glow (max opacity ~0.18)
    for c, val in enumerate([0.08, 0.58, 0.18]):
        bg_rgba[:, :, c] = bg_rgba[:, :, c] * (1.0 - green_glare * 0.18) + val * (green_glare * 0.18)

    ax.imshow(bg_rgba, origin='lower', extent=[0, 16, 0, 9], aspect='auto', zorder=0)

    # 2. Top Header (Bold, Architectural Navy)
    ax.text(8.0, 8.42, "FEASIBILITY, RISKS & MITIGATION MATRIX", 
            ha='center', va='center', fontsize=21, fontweight='bold', color='#0F172A', fontfamily='sans-serif', zorder=2)
    ax.text(8.0, 8.08, "Coupled Hydro-Meteorological Framework for 0–3 Hour Street-Level Nowcasting | Smart India Hackathon 2026 (PS: 26085)", 
            ha='center', va='center', fontsize=10.5, color='#334155', fontfamily='sans-serif', style='italic', zorder=2)

    # Center Hub Coordinates
    cx, cy = 8.0, 4.45
    r_outer = 2.45
    r_inner = 1.35
    r_center = 1.15

    # 3. Template-Harmonious Color Palette (Saffron, SIH Royal Blue, Teal, India Green)
    c_saffron = '#EA580C'   # Indian Saffron / Deep Amber
    c_sih_blue = '#0284C7'  # SIH Template Coastal Blue
    c_teal = '#0D9488'      # Emerald Teal
    c_green = '#15803D'     # India Green

    # Left Slices (Challenges - Angles 90 to 270)
    left_sectors = [
        (135, 180, c_sih_blue, (cx - 2.8, cy + 0.9), "Drain Siltation & Clogging", 
         "Urban catch-pits choke with solid waste\nand silt, causing violent manhole surcharge\nnot accounted for in clean CAD blueprints.", 157.5),
        (90, 135, c_saffron,   (cx - 2.8, cy + 2.1), "2D Simulation Latency Bottleneck", 
         "Solving 2D Saint-Venant shallow water\nequations across 400 km² takes 3–5 hours,\nviolating the 0–3 hr nowcasting window.", 112.5),
        (180, 225, c_teal,     (cx - 2.8, cy - 0.7), "Unmapped Underground Drains", 
         "Fragmented or legacy paper blueprints\nin municipal wards leave spatial blind spots\nin subsurface pipe network topology.", 202.5),
        (225, 270, c_green,    (cx - 2.8, cy - 1.9), "Radar Attenuation & Data Gaps", 
         "Doppler radar suffers ground clutter and\nbeam attenuation; gauges only record rain\nafter it lands at isolated points.", 247.5)
    ]

    # Right Slices (Mitigations - Angles 270 to 90)
    right_sectors = [
        (0, 45, c_sih_blue,  (cx + 2.8, cy + 0.9), "Dynamic Clogging Factor (μ_clog)", 
         "Ingests municipal desilting logs, zonal MSW\ntonnage (TPD), and 1913 complaints to\ndynamically throttle pipe intake capacity.", 22.5),
        (45, 90, c_saffron,   (cx + 2.8, cy + 2.1), "Physics-Informed GNN (< 350 ms)", 
         "Pre-trained offline on 2D hydrodynamic runs;\nexecutes sub-second spatial inference during\nlive storms for true 0–3 hr lead time.", 67.5),
        (315, 360, c_teal,    (cx + 2.8, cy - 0.7), "Topographic Flow Inversion", 
         "Combines OSM street centerlines with DEM\nflow-accumulation paths to synthesize directed\ndrainage graphs for unmapped wards.", 337.5),
        (270, 315, c_green,   (cx + 2.8, cy - 1.9), "Multi-Source Sensor Fusion", 
         "Adaptive Kalman filtering fusing IMD Doppler\nradar (10-min scans) with NASA GPM DPR\nsatellite data & municipal AWS telemetry.", 292.5)
    ]

    # Draw Outer Ring Wedges with subtle drop shadows
    for theta1, theta2, color, _, _, _, _ in left_sectors:
        w = Wedge((cx - 0.08, cy), r_outer, theta1, theta2, width=(r_outer - r_inner), 
                  facecolor=color, edgecolor='#FFFFFF', linewidth=2.5, zorder=3)
        ax.add_patch(w)

    for theta1, theta2, color, _, _, _, _ in right_sectors:
        w = Wedge((cx + 0.08, cy), r_outer, theta1, theta2, width=(r_outer - r_inner), 
                  facecolor=color, edgecolor='#FFFFFF', linewidth=2.5, zorder=3)
        ax.add_patch(w)

    # Center Hub - Left (Command Dark Navy)
    w_hub_l = Wedge((cx - 0.08, cy), r_center, 90, 270, facecolor='#0F172A', edgecolor='#FFFFFF', linewidth=2.2, zorder=4)
    ax.add_patch(w_hub_l)
    ax.text(cx - 0.65, cy + 0.25, "POTENTIAL\nCHALLENGES", ha='center', va='center', 
            fontsize=10.5, fontweight='bold', color='#FFFFFF', fontfamily='sans-serif', zorder=5)
    ax.text(cx - 0.65, cy - 0.28, "Physical & Compute\nBottlenecks", ha='center', va='center', 
            fontsize=7.5, color='#94A3B8', fontfamily='sans-serif', zorder=5)

    # Center Hub - Right (Clean White)
    w_hub_r = Wedge((cx + 0.08, cy), r_center, 270, 90, facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=2.2, zorder=4)
    ax.add_patch(w_hub_r)
    ax.text(cx + 0.65, cy + 0.25, "MITIGATION\nSTRATEGIES", ha='center', va='center', 
            fontsize=10.5, fontweight='bold', color='#0F172A', fontfamily='sans-serif', zorder=5)
    ax.text(cx + 0.65, cy - 0.28, "Engineering\nSolutions", ha='center', va='center', 
            fontsize=7.5, color='#64748B', fontfamily='sans-serif', zorder=5)

    # Connectors & Callout Text - Left Side (Challenges)
    for theta1, theta2, color, (tx, ty), title, desc, mid_angle in left_sectors:
        rad = np.radians(mid_angle)
        px = (cx - 0.08) + ((r_outer + r_inner) / 2.0) * np.cos(rad)
        py = cy + ((r_outer + r_inner) / 2.0) * np.sin(rad)
        
        ax.plot([px, tx + 0.35, tx], [py, ty, ty], color='#64748B', linewidth=1.5, linestyle='-', zorder=3)
        circle = plt.Circle((tx, ty), 0.075, facecolor=color, edgecolor='#0F172A', linewidth=1.8, zorder=5)
        ax.add_patch(circle)
        
        ax.text(tx - 0.2, ty + 0.12, title, ha='right', va='bottom', 
                fontsize=9.8, fontweight='bold', color='#0F172A', fontfamily='sans-serif', zorder=4)
        ax.text(tx - 0.2, ty - 0.02, desc, ha='right', va='top', 
                fontsize=7.8, color='#334155', fontfamily='sans-serif', linespacing=1.25, zorder=4)

    # Connectors & Callout Text - Right Side (Mitigations)
    for theta1, theta2, color, (tx, ty), title, desc, mid_angle in right_sectors:
        rad = np.radians(mid_angle)
        px = (cx + 0.08) + ((r_outer + r_inner) / 2.0) * np.cos(rad)
        py = cy + ((r_outer + r_inner) / 2.0) * np.sin(rad)
        
        ax.plot([px, tx - 0.35, tx], [py, ty, ty], color='#64748B', linewidth=1.5, linestyle='-', zorder=3)
        circle = plt.Circle((tx, ty), 0.075, facecolor=color, edgecolor='#0F172A', linewidth=1.8, zorder=5)
        ax.add_patch(circle)
        
        ax.text(tx + 0.2, ty + 0.12, title, ha='left', va='bottom', 
                fontsize=9.8, fontweight='bold', color=color, fontfamily='sans-serif', zorder=4)
        ax.text(tx + 0.2, ty - 0.02, desc, ha='left', va='top', 
                fontsize=7.8, color='#334155', fontfamily='sans-serif', linespacing=1.25, zorder=4)

    # 4. Bottom Feasibility Pillars Banner (Crisp White Floating Cards over Green Glare)
    pillars = [
        ("1. TECHNICAL FEASIBILITY", "Zero Sensor Capex; Ingests IMD Doppler Radar & Cartosat DEM.", '#FFFFFF', '#0F172A', '#EA580C'),
        ("2. OPERATIONAL VIABILITY", "0–3h Lead Time, cm Depth Resolution + Safe A* Navigation API.", '#FFFFFF', '#0F172A', '#0284C7'),
        ("3. ECONOMIC VIABILITY", "Cloud-native microservice (NIC/AWS); Saves 100s Cr in flood loss.", '#FFFFFF', '#0F172A', '#0D9488'),
        ("4. PAN-INDIA SCALABILITY", "Prototyped on Chennai; 100% portable to Mumbai, Delhi, Bengaluru.", '#FFFFFF', '#0F172A', '#15803D')
    ]
    
    box_w = 3.65
    box_h = 0.72
    start_x = 0.55
    y_pos = 0.38
    gap = 0.20

    for i, (title, sub, bg, txt_col, accent_border) in enumerate(pillars):
        bx = start_x + i * (box_w + gap)
        # Rounded Card with crisp top accent border
        rect = patches.FancyBboxPatch((bx, y_pos), box_w, box_h, boxstyle="round,pad=0.08,rounding_size=0.12",
                                      facecolor=bg, edgecolor='#CBD5E1', linewidth=1.4, zorder=4)
        ax.add_patch(rect)
        
        # Top color accent bar on each card
        bar = patches.FancyBboxPatch((bx + 0.05, y_pos + box_h - 0.06), box_w - 0.1, 0.05, 
                                     boxstyle="round,pad=0.02,rounding_size=0.04",
                                     facecolor=accent_border, edgecolor='none', zorder=5)
        ax.add_patch(bar)

        ax.text(bx + box_w/2.0, y_pos + 0.43, title, ha='center', va='center', 
                fontsize=7.5, fontweight='bold', color=txt_col, fontfamily='sans-serif', zorder=6)
        ax.text(bx + box_w/2.0, y_pos + 0.20, sub, ha='center', va='center', 
                fontsize=6.5, color='#475569', fontfamily='sans-serif', zorder=6)

    out_file = 'slide4_feasibility_matrix_tiranga_glare.png'
    plt.savefig(out_file, bbox_inches='tight', pad_inches=0.05, dpi=240)
    plt.close()
    print(f"[+] Successfully generated: {out_file}")

if __name__ == "__main__":
    render_slide4_with_glare()
