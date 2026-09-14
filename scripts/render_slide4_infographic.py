"""
Render Ultra High-Resolution 4K Infographic for Slide 4: FEASIBILITY AND VIABILITY
Replicates the 8-Point Circular Comparison Split Infographic.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Wedge
import numpy as np

def create_infographic():
    # 4K Canvas (16:9 ratio, 3840 x 2160 at 240 DPI)
    fig = plt.figure(figsize=(16, 9), dpi=240, facecolor='#FFFFFF')
    ax = fig.add_axes([0, 0, 1, 1], facecolor='#FFFFFF')
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis('off')

    # Top Header
    ax.text(8.0, 8.45, "FEASIBILITY, RISKS & MITIGATION MATRIX", 
            ha='center', va='center', fontsize=21, fontweight='bold', color='#0F172A', fontfamily='sans-serif')
    ax.text(8.0, 8.12, "Coupled Hydro-Meteorological Framework for 0–3 Hour Street-Level Nowcasting | Smart India Hackathon 2026 (PS: 26085)", 
            ha='center', va='center', fontsize=10.5, color='#475569', fontfamily='sans-serif', style='italic')

    # Center Hub Coordinates
    cx, cy = 8.0, 4.45
    r_outer = 2.45
    r_inner = 1.35
    r_center = 1.15

    # Sector Colors
    c_red = '#E11D48'      # Coral Red
    c_teal = '#0D9488'     # Teal
    c_amber = '#EA580C'    # Burnt Amber / Coral
    c_blue = '#4F46E5'     # Indigo Blue

    # Left Slices (Angles in degrees: 90 to 270)
    # 1: 135 to 180 (Top-Mid), 2: 90 to 135 (Top), 3: 180 to 225 (Bottom-Mid), 4: 225 to 270 (Bottom)
    left_sectors = [
        (135, 180, c_teal,  (cx - 2.8, cy + 0.9), "Drain Siltation & Clogging", 
         "Urban catch-pits choke with solid waste\nand silt, causing violent manhole surcharge\nnot accounted for in clean CAD blueprints.", 157.5),
        (90, 135, c_red,   (cx - 2.8, cy + 2.1), "2D Simulation Latency Bottleneck", 
         "Solving 2D Saint-Venant shallow water\nequations across 400 km² takes 3–5 hours,\nviolating the 0–3 hr nowcasting window.", 112.5),
        (180, 225, c_amber, (cx - 2.8, cy - 0.7), "Unmapped Underground Drains", 
         "Fragmented or legacy paper blueprints\nin municipal wards leave spatial blind spots\nin subsurface pipe network topology.", 202.5),
        (225, 270, c_blue,  (cx - 2.8, cy - 1.9), "Radar Attenuation & Data Gaps", 
         "Doppler radar suffers ground clutter and\nbeam attenuation; gauges only record rain\nafter it lands at isolated points.", 247.5)
    ]

    # Right Slices (Angles in degrees: 270 to 90 via 360/0)
    right_sectors = [
        (0, 45, c_teal,   (cx + 2.8, cy + 0.9), "Dynamic Clogging Factor (μ_clog)", 
         "Ingests municipal desilting logs, zonal MSW\ntonnage (TPD), and 1913 complaints to\ndynamically throttle pipe intake capacity.", 22.5),
        (45, 90, c_red,    (cx + 2.8, cy + 2.1), "Physics-Informed GNN (< 350 ms)", 
         "Pre-trained offline on 2D hydrodynamic runs;\nexecutes sub-second spatial inference during\nlive storms for true 0–3 hr lead time.", 67.5),
        (315, 360, c_amber, (cx + 2.8, cy - 0.7), "Topographic Flow Inversion", 
         "Combines OSM street centerlines with DEM\nflow-accumulation paths to synthesize directed\ndrainage graphs for unmapped wards.", 337.5),
        (270, 315, c_blue,  (cx + 2.8, cy - 1.9), "Multi-Source Sensor Fusion", 
         "Adaptive Kalman filtering fusing IMD Doppler\nradar (10-min scans) with NASA GPM DPR\nsatellite data & municipal AWS telemetry.", 292.5)
    ]

    # Draw Outer Ring Wedges
    for theta1, theta2, color, _, _, _, _ in left_sectors:
        w = Wedge((cx - 0.08, cy), r_outer, theta1, theta2, width=(r_outer - r_inner), 
                  facecolor=color, edgecolor='#FFFFFF', linewidth=2.5)
        ax.add_patch(w)

    for theta1, theta2, color, _, _, _, _ in right_sectors:
        w = Wedge((cx + 0.08, cy), r_outer, theta1, theta2, width=(r_outer - r_inner), 
                  facecolor=color, edgecolor='#FFFFFF', linewidth=2.5)
        ax.add_patch(w)

    # Center Hub - Left (Dark Navy)
    w_hub_l = Wedge((cx - 0.08, cy), r_center, 90, 270, facecolor='#0F172A', edgecolor='#FFFFFF', linewidth=2.0)
    ax.add_patch(w_hub_l)
    ax.text(cx - 0.65, cy + 0.25, "POTENTIAL\nCHALLENGES", ha='center', va='center', 
            fontsize=10.5, fontweight='bold', color='#FFFFFF', fontfamily='sans-serif')
    ax.text(cx - 0.65, cy - 0.28, "Physical & Compute\nBottlenecks", ha='center', va='center', 
            fontsize=7.5, color='#94A3B8', fontfamily='sans-serif')

    # Center Hub - Right (Clean Off-White)
    w_hub_r = Wedge((cx + 0.08, cy), r_center, 270, 90, facecolor='#F8FAFC', edgecolor='#CBD5E1', linewidth=2.0)
    ax.add_patch(w_hub_r)
    ax.text(cx + 0.65, cy + 0.25, "MITIGATION\nSTRATEGIES", ha='center', va='center', 
            fontsize=10.5, fontweight='bold', color='#0F172A', fontfamily='sans-serif')
    ax.text(cx + 0.65, cy - 0.28, "Engineering\nSolutions", ha='center', va='center', 
            fontsize=7.5, color='#64748B', fontfamily='sans-serif')

    # Add Connectors & Text - Left Side (Challenges)
    for theta1, theta2, color, (tx, ty), title, desc, mid_angle in left_sectors:
        # Radial point on arc
        rad = np.radians(mid_angle)
        px = (cx - 0.08) + ((r_outer + r_inner) / 2.0) * np.cos(rad)
        py = cy + ((r_outer + r_inner) / 2.0) * np.sin(rad)
        
        # Draw connector line
        ax.plot([px, tx + 0.3, tx], [py, ty, ty], color='#94A3B8', linewidth=1.4, linestyle='-')
        # Pin circle
        circle = plt.Circle((tx, ty), 0.07, facecolor=color, edgecolor='#0F172A', linewidth=1.5, zorder=5)
        ax.add_patch(circle)
        
        # Text Block
        ax.text(tx - 0.2, ty + 0.12, title, ha='right', va='bottom', 
                fontsize=9.8, fontweight='bold', color='#0F172A', fontfamily='sans-serif')
        ax.text(tx - 0.2, ty - 0.02, desc, ha='right', va='top', 
                fontsize=7.8, color='#334155', fontfamily='sans-serif', linespacing=1.25)

    # Add Connectors & Text - Right Side (Mitigations)
    for theta1, theta2, color, (tx, ty), title, desc, mid_angle in right_sectors:
        rad = np.radians(mid_angle)
        px = (cx + 0.08) + ((r_outer + r_inner) / 2.0) * np.cos(rad)
        py = cy + ((r_outer + r_inner) / 2.0) * np.sin(rad)
        
        ax.plot([px, tx - 0.3, tx], [py, ty, ty], color='#94A3B8', linewidth=1.4, linestyle='-')
        circle = plt.Circle((tx, ty), 0.07, facecolor=color, edgecolor='#0F172A', linewidth=1.5, zorder=5)
        ax.add_patch(circle)
        
        ax.text(tx + 0.2, ty + 0.12, title, ha='left', va='bottom', 
                fontsize=9.8, fontweight='bold', color=color, fontfamily='sans-serif')
        ax.text(tx + 0.2, ty - 0.02, desc, ha='left', va='top', 
                fontsize=7.8, color='#334155', fontfamily='sans-serif', linespacing=1.25)

    # Bottom Feasibility Pillars Banner (4 clean rounded pill cards)
    pillars = [
        ("1. TECHNICAL FEASIBILITY", "Zero Sensor Capex; Ingests IMD Doppler Radar & Cartosat DEM.", '#F1F5F9', '#0F172A'),
        ("2. OPERATIONAL VIABILITY", "0–3h Lead Time, cm Depth Resolution + Safe A* Navigation API.", '#F1F5F9', '#0F172A'),
        ("3. ECONOMIC VIABILITY", "Cloud-native microservice (NIC/AWS); Saves 100s Cr in losses.", '#F1F5F9', '#0F172A'),
        ("4. PAN-INDIA SCALABILITY", "Prototyped on Chennai; 100% portable to Mumbai, Delhi, Bengaluru.", '#F1F5F9', '#0F172A')
    ]
    
    box_w = 3.65
    box_h = 0.72
    start_x = 0.55
    y_pos = 0.38
    gap = 0.20

    for i, (title, sub, bg, txt_col) in enumerate(pillars):
        bx = start_x + i * (box_w + gap)
        # Draw rounded card
        rect = patches.FancyBboxPatch((bx, y_pos), box_w, box_h, boxstyle="round,pad=0.08,rounding_size=0.12",
                                      facecolor=bg, edgecolor='#CBD5E1', linewidth=1.2)
        ax.add_patch(rect)
        ax.text(bx + box_w/2.0, y_pos + 0.45, title, ha='center', va='center', 
                fontsize=7.5, fontweight='bold', color=txt_col, fontfamily='sans-serif')
        ax.text(bx + box_w/2.0, y_pos + 0.20, sub, ha='center', va='center', 
                fontsize=6.5, color='#475569', fontfamily='sans-serif')

    out_file = 'slide4_feasibility_matrix.png'
    plt.savefig(out_file, bbox_inches='tight', pad_inches=0.1, dpi=240)
    plt.close()
    print(f"Generated high-resolution graphic: {out_file}")

if __name__ == "__main__":
    create_infographic()
