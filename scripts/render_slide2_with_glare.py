"""
Render Ultra High-Resolution 4K Slide 2 Infographic with Indian Flag Ambient Glare
Pixel-perfect typography, cleanly wrapped text boxes, zero overlapping.
Matches winning Team UDAAN style:
Left: "Root Problems in Urban Flooding" (Hexagonal hub with 6 neatly formatted challenge cards)
Right: "Kairos Solution & Architectural Uniqueness" (7 alternating pill-card pairs)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import numpy as np
import textwrap

def render_slide2_with_glare():
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

    # 2. Main Title Banners
    # Left Header Banner: "Problems"
    prob_banner = FancyBboxPatch((0.8, 8.1), 5.8, 0.65, boxstyle="round,pad=0.08,rounding_size=0.3",
                                 facecolor='#FEF3C7', edgecolor='#F59E0B', linewidth=1.5, zorder=3)
    ax.add_patch(prob_banner)
    ax.text(3.7, 8.42, "Root Problems in Urban Drainage", ha='center', va='center',
            fontsize=14.5, fontweight='bold', color='#78350F', zorder=4)

    # Right Header Banner: "Solution and Problem Uniqueness"
    sol_banner = FancyBboxPatch((7.8, 8.1), 7.4, 0.65, boxstyle="round,pad=0.08,rounding_size=0.3",
                                facecolor='#EFF6FF', edgecolor='#3B82F6', linewidth=1.5, zorder=3)
    ax.add_patch(sol_banner)
    ax.text(11.5, 8.42, "Kairos Solution & Architectural Uniqueness", ha='center', va='center',
            fontsize=14.5, fontweight='bold', color='#1E3A8A', zorder=4)

    # -------------------------------------------------------------
    # LEFT SECTION: PROBLEMS (Central Hub with 6 Challenge Cards)
    # -------------------------------------------------------------
    cx, cy = 3.7, 4.45
    
    # Draw central circle hub
    center_hub = plt.Circle((cx, cy), 0.72, facecolor='#FFFFFF', edgecolor='#0F172A', linewidth=2.5, zorder=5)
    ax.add_patch(center_hub)
    ax.text(cx, cy + 0.15, "URBAN", ha='center', va='center', fontsize=10, fontweight='bold', color='#0F172A', zorder=6)
    ax.text(cx, cy - 0.12, "DRAINAGE", ha='center', va='center', fontsize=9, fontweight='bold', color='#EF4444', zorder=6)

    # 6 Root Problem Cards with exact dimensions and wrapped text
    problems = [
        {
            "x": 3.7, "y": 7.15, "w": 2.9, "h": 1.15,
            "title": "Static Gauges Miss Cloudbursts",
            "desc": "Tipping-bucket gauges log rain post-event. Convective microbursts (>80mm/h) flood streets before ground gauges record totals.",
            "color": "#FEE2E2", "edge": "#EF4444", "title_c": "#991B1B",
            "target": (cx, cy + 0.72)
        },
        {
            "x": 5.75, "y": 5.4, "w": 2.6, "h": 1.15,
            "title": "Blindness to Storm Drains",
            "desc": "Standard 2D models model surface runoff only, ignoring subsurface SWD pipe backwater, tidal lock, and outfall sluice gates.",
            "color": "#FFEDD5", "edge": "#F97316", "title_c": "#9A3412",
            "target": (cx + 0.62, cy + 0.36)
        },
        {
            "x": 5.75, "y": 2.85, "w": 2.6, "h": 1.15,
            "title": "Solid Waste & Silt Choking",
            "desc": "Plastic debris and desilting deficit reduce conduit capacity by 30-60%, making theoretical pipe design capacity invalid.",
            "color": "#FEF3C7", "edge": "#F59E0B", "title_c": "#92400E",
            "target": (cx + 0.62, cy - 0.36)
        },
        {
            "x": 3.7, "y": 1.35, "w": 2.9, "h": 1.15,
            "title": "Zero Street Granularity",
            "desc": "Broad city-wide alerts ('Heavy rain in Chennai') offer zero actionable intelligence for specific road underpasses or junctions.",
            "color": "#ECFDF5", "edge": "#10B981", "title_c": "#065F46",
            "target": (cx, cy - 0.72)
        },
        {
            "x": 1.65, "y": 2.85, "w": 2.6, "h": 1.15,
            "title": "Ambulance Hydrolock Stalls",
            "desc": "Standard civilian GPS navigates ambulances into 60cm submerged subways, causing engine seizure and ICU patient loss.",
            "color": "#CFFAFE", "edge": "#06B6D4", "title_c": "#155E75",
            "target": (cx - 0.62, cy - 0.36)
        },
        {
            "x": 1.65, "y": 5.4, "w": 2.6, "h": 1.15,
            "title": "Post-Disaster Reactive Response",
            "desc": "De-watering pumps and rescue boats are dispatched after streets are flooded, rather than pre-positioned 2 hours prior.",
            "color": "#EDE9FE", "edge": "#8B5CF6", "title_c": "#5B21B6",
            "target": (cx - 0.62, cy + 0.36)
        }
    ]

    for p in problems:
        bx, by = p["x"], p["y"]
        bw, bh = p["w"], p["h"]
        card = FancyBboxPatch((bx - bw/2, by - bh/2), bw, bh, boxstyle="round,pad=0.06,rounding_size=0.18",
                              facecolor=p["color"], edgecolor=p["edge"], linewidth=1.4, zorder=3)
        ax.add_patch(card)
        
        # Title
        ax.text(bx, by + bh*0.28, p["title"], ha='center', va='center',
                fontsize=8.5, fontweight='bold', color=p["title_c"], zorder=4)
        
        # Wrapped description text
        wrapped_desc = textwrap.fill(p["desc"], width=28)
        ax.text(bx, by - bh*0.14, wrapped_desc, ha='center', va='center',
                fontsize=7.2, color='#1E293B', zorder=4, linespacing=1.2)
        
        # Arrow pointing toward center hub
        tx, ty = p["target"]
        ax.annotate('', xy=(tx, ty), xytext=(bx, by),
                    arrowprops=dict(arrowstyle='->', color=p["edge"], lw=1.6, shrinkA=bh*0.5, shrinkB=0), zorder=2)

    # -------------------------------------------------------------
    # RIGHT SECTION: SOLUTION & UNIQUENESS (7 Alternating Pill Rows)
    # -------------------------------------------------------------
    solutions = [
        {
            "title": "1D/2D Coupled Hydro Engine",
            "desc": "Couples 1D SWMM Saint-Venant pipe flow with 2D overland shallow water equations for accurate subsurface-surface interchange.",
            "pill_color": "#D97706", "side": "left"
        },
        {
            "title": "IMD Doppler Radar Nowcasting",
            "desc": "Direct ingestion of Meenambakkam Dual-Pol Radar for 0-3h extrapolated precipitation at 1 km / 10-min resolution.",
            "pill_color": "#2563EB", "side": "right"
        },
        {
            "title": "Dynamic Solid Waste Clogging (μ)",
            "desc": "Empirically calibrates effective drainage cross-section A_eff = A_0(1 - μ) using GCC ward desilting and solid waste logs.",
            "pill_color": "#059669", "side": "left"
        },
        {
            "title": "7,894-Segment Street Twin",
            "desc": "Hyper-local depth prediction across all 15 GCC zones, categorizing roads into 4 NDMA vehicle safety passage levels.",
            "pill_color": "#7C3AED", "side": "right"
        },
        {
            "title": "A* Flood-Safe Emergency Routing",
            "desc": "Turn-by-turn navigation constrained by vehicle clearance (Ambulance 30cm, Bus 45cm, Car 18cm) with safe bypass guidance.",
            "pill_color": "#DB2777", "side": "left"
        },
        {
            "title": "Surcharge Backflow Early Warning",
            "desc": "Detects manhole hydraulic surcharge (HGL > ground elevation) up to 90 minutes before water surfaces on roads.",
            "pill_color": "#0891B2", "side": "right"
        },
        {
            "title": "100% Zero-Hardware Edge Ready",
            "desc": "Operates entirely on existing government radar, DEM, and municipal GIS assets—zero new hardware sensors required.",
            "pill_color": "#0D9488", "side": "right"
        }
    ]

    start_y = 7.42
    spacing_y = 0.90
    
    for i, s in enumerate(solutions):
        sy = start_y - i * spacing_y
        
        if s["side"] == "left":
            # Pill on left, text on right
            pill_x, pill_w = 7.6, 2.75
            text_x, text_w = 10.55, 4.7
            
            # Pill
            pill = FancyBboxPatch((pill_x, sy - 0.28), pill_w, 0.56, boxstyle="round,pad=0.05,rounding_size=0.28",
                                  facecolor=s["pill_color"], edgecolor='none', zorder=3)
            ax.add_patch(pill)
            ax.text(pill_x + pill_w/2, sy, s["title"], ha='center', va='center',
                    fontsize=8.0, fontweight='bold', color='#FFFFFF', zorder=4)
            
            # Desc card
            desc_box = FancyBboxPatch((text_x, sy - 0.32), text_w, 0.64, boxstyle="round,pad=0.05,rounding_size=0.12",
                                      facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.1, zorder=2)
            ax.add_patch(desc_box)
            wrapped_desc = textwrap.fill(s["desc"], width=46)
            ax.text(text_x + 0.18, sy, wrapped_desc, ha='left', va='center',
                    fontsize=7.4, color='#334155', zorder=3, linespacing=1.2)
            
        else:
            # Text on left, pill on right
            text_x, text_w = 7.6, 4.7
            pill_x, pill_w = 12.5, 2.75
            
            # Desc card
            desc_box = FancyBboxPatch((text_x, sy - 0.32), text_w, 0.64, boxstyle="round,pad=0.05,rounding_size=0.12",
                                      facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.1, zorder=2)
            ax.add_patch(desc_box)
            wrapped_desc = textwrap.fill(s["desc"], width=46)
            ax.text(text_x + 0.18, sy, wrapped_desc, ha='left', va='center',
                    fontsize=7.4, color='#334155', zorder=3, linespacing=1.2)

            # Pill
            pill = FancyBboxPatch((pill_x, sy - 0.28), pill_w, 0.56, boxstyle="round,pad=0.05,rounding_size=0.28",
                                  facecolor=s["pill_color"], edgecolor='none', zorder=3)
            ax.add_patch(pill)
            ax.text(pill_x + pill_w/2, sy, s["title"], ha='center', va='center',
                    fontsize=8.0, fontweight='bold', color='#FFFFFF', zorder=4)

    # Bottom Footer
    ax.plot([0.8, 15.2], [0.55, 0.55], color='#CBD5E1', lw=1.0, zorder=2)
    ax.text(0.8, 0.32, "Team Kairos | SIH 2026 Problem ID: 26085", fontsize=8.5, fontweight='bold', color='#0F172A', zorder=3)
    ax.text(15.2, 0.32, "Ministry of Earth Sciences (MoES) / NCMRWF • Greater Chennai Corporation Pilot",
            fontsize=8.5, ha='right', color='#475569', zorder=3)

    output_path = 'slide2_problem_solution_tiranga_glare.png'
    plt.savefig(output_path, dpi=240, bbox_inches='tight', pad_inches=0.02)
    plt.close()
    print(f"Slide 2 re-rendered cleanly to {output_path}")

if __name__ == '__main__':
    render_slide2_with_glare()
