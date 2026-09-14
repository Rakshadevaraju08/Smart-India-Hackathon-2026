import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def create_slide3_architecture_graphic():
    # 16:9 Aspect ratio (16 x 9 inches at 240 DPI = 3840 x 2160 pixels)
    fig, ax = plt.subplots(figsize=(16, 9), dpi=240)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis('off')

    # -------------------------------------------------------------
    # 1. Atmospheric Ambient Glare (Tiranga Lighting)
    # -------------------------------------------------------------
    bg = patches.Rectangle((0, 0), 16, 9, facecolor='#FFFFFF', zorder=0)
    ax.add_patch(bg)

    # Top Saffron Ambient Glow
    y_vals_top = np.linspace(7.2, 9.0, 50)
    for i in range(len(y_vals_top) - 1):
        y0 = y_vals_top[i]
        y1 = y_vals_top[i+1]
        progress = (y0 - 7.2) / (9.0 - 7.2)
        alpha = 0.015 + 0.12 * (progress ** 2.2)
        rect = patches.Rectangle((0, y0), 16, y1 - y0, facecolor='#FF9933', edgecolor='none', alpha=alpha, zorder=1)
        ax.add_patch(rect)

    # Bottom India Green Ambient Glow
    y_vals_bot = np.linspace(0.0, 1.8, 50)
    for i in range(len(y_vals_bot) - 1):
        y0 = y_vals_bot[i]
        y1 = y_vals_bot[i+1]
        progress = (1.8 - y1) / (1.8 - 0.0)
        alpha = 0.015 + 0.10 * (progress ** 2.2)
        rect = patches.Rectangle((0, y0), 16, y1 - y0, facecolor='#138808', edgecolor='none', alpha=alpha, zorder=1)
        ax.add_patch(rect)

    # -------------------------------------------------------------
    # 2. Slide Header & Subtitle
    # -------------------------------------------------------------
    ax.text(8.0, 8.54, "TECHNICAL APPROACH & SYSTEM ARCHITECTURE", 
            ha='center', va='center', fontsize=21, fontweight='bold', color='#0F172A', family='sans-serif', zorder=5)
    ax.text(8.0, 8.20, "Coupled Hydro-Meteorological Framework for 0-3 Hour Street-Level Nowcasting | Smart India Hackathon 2026 (PS: 26085)", 
            ha='center', va='center', fontsize=10.0, fontstyle='italic', color='#475569', family='sans-serif', zorder=5)

    # -------------------------------------------------------------
    # 3. Column Positions (Clean Margins & Spacing)
    # -------------------------------------------------------------
    y_top = 7.85
    col_h = 5.95
    y_bottom = y_top - col_h

    c1_x = 0.50
    c1_w = 3.50

    c2_x = 4.40
    c2_w = 7.30

    c3_x = 12.05
    c3_w = 3.45

    # -------------------------------------------------------------
    # COLUMN 1: DATA INGESTION LAYER
    # -------------------------------------------------------------
    c1_box = patches.FancyBboxPatch((c1_x, y_bottom), c1_w, col_h,
                                   boxstyle="Round,pad=0.06,rounding_size=0.16",
                                   facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(c1_box)
    
    h1 = patches.FancyBboxPatch((c1_x + 0.04, y_top - 0.60), c1_w - 0.08, 0.56,
                                boxstyle="Round,pad=0.03,rounding_size=0.10",
                                facecolor='#0F172A', edgecolor='none', zorder=3)
    ax.add_patch(h1)
    ax.text(c1_x + (c1_w / 2.0), y_top - 0.22, "1. DATA INGESTION LAYER", 
            ha='center', va='center', fontsize=10.0, fontweight='bold', color='#FFFFFF', zorder=4)
    ax.text(c1_x + (c1_w / 2.0), y_top - 0.44, "Real-Time Telemetry & Spatial Vault", 
            ha='center', va='center', fontsize=7.5, color='#94A3B8', zorder=4)

    in_items = [
        {
            "tag": "RADAR TELEMETRY",
            "title": "IMD Doppler Weather Radar",
            "source": "Chennai DWR (10-min S-Band Scans)",
            "line1": "Ingests polar reflectivity (dBZ) rasters.",
            "line2": "Dynamic AWS rain gauge bias calibration.",
            "color": "#EA580C",
            "bg": "#FFF7ED"
        },
        {
            "tag": "ELEVATION / DEM",
            "title": "ISRO Cartosat-1 10m DEM",
            "source": "NRSC Bhuvan Hydrological Raster",
            "line1": "Conditioned via Wang & Liu pit-filling",
            "line2": "for true urban flow accumulation paths.",
            "color": "#0284C7",
            "bg": "#F0F9FF"
        },
        {
            "tag": "SURFACE CORRIDORS",
            "title": "OpenStreetMap Road Network",
            "source": "OSMnx Vectorized Road Polylines",
            "line1": "Extracts 7,894 road corridors, curb elevations,",
            "line2": "and asphalt surface areas for runoff capture.",
            "color": "#0D9488",
            "bg": "#F0FDFA"
        },
        {
            "tag": "CIVIC TELEMETRY",
            "title": "GCC Civic Maintenance Data",
            "source": "Ward Solid Waste & Desilting Logs",
            "line1": "Ward waste tonnage (TPD) & 1913 complaints",
            "line2": "to quantify real-world pipe clogging.",
            "color": "#15803D",
            "bg": "#F0FDF4"
        }
    ]

    card_y_start = y_top - 0.72
    card_spacing = 1.28
    for idx, itm in enumerate(in_items):
        cy = card_y_start - (idx * card_spacing)
        
        ibox = patches.FancyBboxPatch((c1_x + 0.12, cy - 1.15), c1_w - 0.24, 1.15,
                                     boxstyle="Round,pad=0.03,rounding_size=0.08",
                                     facecolor=itm["bg"], edgecolor=itm["color"], linewidth=0.8, zorder=3)
        ax.add_patch(ibox)
        
        cbar = patches.Rectangle((c1_x + 0.12, cy - 1.15 + 0.08), 0.08, 0.99, facecolor=itm["color"], edgecolor='none', zorder=4)
        ax.add_patch(cbar)

        ax.text(c1_x + 0.26, cy - 0.18, itm["tag"], ha='left', va='center', fontsize=6.8, fontweight='bold', color=itm["color"], zorder=5)
        ax.text(c1_x + 0.26, cy - 0.40, itm["title"], ha='left', va='center', fontsize=8.6, fontweight='bold', color='#0F172A', zorder=5)
        ax.text(c1_x + 0.26, cy - 0.60, itm["source"], ha='left', va='center', fontsize=7.0, fontstyle='italic', color='#64748B', zorder=5)
        ax.text(c1_x + 0.26, cy - 0.80, itm["line1"], ha='left', va='center', fontsize=7.0, color='#334155', zorder=5)
        ax.text(c1_x + 0.26, cy - 0.98, itm["line2"], ha='left', va='center', fontsize=7.0, color='#334155', zorder=5)

    # -------------------------------------------------------------
    # COLUMN 2: COUPLED HYDRO-METEOROLOGICAL ENGINE (CENTER)
    # -------------------------------------------------------------
    c2_box = patches.FancyBboxPatch((c2_x, y_bottom), c2_w, col_h,
                                   boxstyle="Round,pad=0.06,rounding_size=0.16",
                                   facecolor='#FFFFFF', edgecolor='#94A3B8', linewidth=1.4, zorder=2)
    ax.add_patch(c2_box)

    h2 = patches.FancyBboxPatch((c2_x + 0.04, y_top - 0.60), c2_w - 0.08, 0.56,
                                boxstyle="Round,pad=0.03,rounding_size=0.10",
                                facecolor='#1E293B', edgecolor='none', zorder=3)
    ax.add_patch(h2)
    ax.text(c2_x + (c2_w / 2.0), y_top - 0.22, "2. COUPLED HYDRO-METEOROLOGICAL CORE (SUB-SECOND EXECUTION)", 
            ha='center', va='center', fontsize=10.5, fontweight='bold', color='#FFFFFF', zorder=4)
    ax.text(c2_x + (c2_w / 2.0), y_top - 0.44, "Physics Coupling: Radar Nowcasting + 2D Overland Runoff + 1D Subsurface Surcharge", 
            ha='center', va='center', fontsize=7.8, color='#38BDF8', zorder=4)

    # --- STAGE A: Atmospheric Nowcasting ---
    y_2a = y_top - 0.72
    h_2a = 1.50
    box_2a = patches.FancyBboxPatch((c2_x + 0.16, y_2a - h_2a), c2_w - 0.32, h_2a,
                                   boxstyle="Round,pad=0.03,rounding_size=0.08",
                                   facecolor='#FFF7ED', edgecolor='#EA580C', linewidth=1.1, zorder=3)
    ax.add_patch(box_2a)
    
    ax.text(c2_x + 0.28, y_2a - 0.22, "STAGE A: ATMOSPHERIC PRECIPITATION NOWCASTING (0-3 HOUR HORIZON)", 
            ha='left', va='center', fontsize=8.8, fontweight='bold', color='#EA580C', zorder=5)
    ax.text(c2_x + 0.28, y_2a - 0.50, "• Marshall-Palmer Z-R Transformation: R = (10^(Z/10) / 200)^(1/1.6) mm/hr (Coastal convective storm calibration)", 
            ha='left', va='center', fontsize=7.4, color='#0F172A', zorder=5)
    ax.text(c2_x + 0.28, y_2a - 0.76, "• Semi-Lagrangian Optical Flow: Farnebäck dense motion tracking (u, v) across radar frames in < 15 ms", 
            ha='left', va='center', fontsize=7.4, color='#0F172A', zorder=5)
    ax.text(c2_x + 0.28, y_2a - 1.04, "• Extrapolated Rain Fields: Spatio-temporal rainfall matrix R(x, y, t) at T+15m, T+30m, T+60m, T+120m, T+180m", 
            ha='left', va='center', fontsize=7.4, fontweight='bold', color='#C2410C', zorder=5)

    # Arrow 2A -> 2B
    arr_1 = patches.FancyArrowPatch((c2_x + (c2_w / 2.0), y_2a - h_2a), 
                                   (c2_x + (c2_w / 2.0), y_2a - h_2a - 0.30),
                                   arrowstyle='-|>', mutation_scale=13, facecolor='#EA580C', edgecolor='#EA580C', zorder=6)
    ax.add_patch(arr_1)
    ax.text(c2_x + (c2_w / 2.0) + 0.15, y_2a - h_2a - 0.15, "Rain Intensity R(t)", 
            ha='left', va='center', fontsize=7.2, fontstyle='italic', color='#EA580C', zorder=6)

    # --- STAGE B: 2D Surface Runoff ---
    y_2b = y_2a - h_2a - 0.32
    h_2b = 1.40
    box_2b = patches.FancyBboxPatch((c2_x + 0.16, y_2b - h_2b), c2_w - 0.32, h_2b,
                                   boxstyle="Round,pad=0.03,rounding_size=0.08",
                                   facecolor='#F0F9FF', edgecolor='#0284C7', linewidth=1.1, zorder=3)
    ax.add_patch(box_2b)

    ax.text(c2_x + 0.28, y_2b - 0.22, "STAGE B: 2D OVERLAND RUNOFF & CURB DROP-INLET CAPTURE", 
            ha='left', va='center', fontsize=8.8, fontweight='bold', color='#0284C7', zorder=5)
    ax.text(c2_x + 0.28, y_2b - 0.50, "• Modified Rational Method: Q_surface = C_impervious * R(t) * A_catchment (C = 0.92 for asphalt road corridors)", 
            ha='left', va='center', fontsize=7.4, color='#0F172A', zorder=5)
    ax.text(c2_x + 0.28, y_2b - 0.76, "• D-infinity Flow Accumulation: Routes surface surge along continuous road grade slopes into curb gutters", 
            ha='left', va='center', fontsize=7.4, color='#0F172A', zorder=5)
    ax.text(c2_x + 0.28, y_2b - 1.04, "• Drop-Inlet Hydraulics: Weir capture Q_weir = Cw*L*h^1.5 vs. Submerged orifice Q_orifice = Cd*A*sqrt(2gh)", 
            ha='left', va='center', fontsize=7.4, fontweight='bold', color='#0369A1', zorder=5)

    # Arrow 2B -> 2C
    arr_2 = patches.FancyArrowPatch((c2_x + (c2_w / 2.0), y_2b - h_2b), 
                                   (c2_x + (c2_w / 2.0), y_2b - h_2b - 0.30),
                                   arrowstyle='-|>', mutation_scale=13, facecolor='#0284C7', edgecolor='#0284C7', zorder=6)
    ax.add_patch(arr_2)
    ax.text(c2_x + (c2_w / 2.0) + 0.15, y_2b - h_2b - 0.15, "Inlet Discharge Q_inlet", 
            ha='left', va='center', fontsize=7.2, fontstyle='italic', color='#0284C7', zorder=6)

    # --- STAGE C: 1D Subsurface Graph & Surcharge ---
    y_2c = y_2b - h_2b - 0.32
    h_2c = 1.55
    box_2c = patches.FancyBboxPatch((c2_x + 0.16, y_2c - h_2c), c2_w - 0.32, h_2c,
                                   boxstyle="Round,pad=0.03,rounding_size=0.08",
                                   facecolor='#F0FDF4', edgecolor='#15803D', linewidth=1.1, zorder=3)
    ax.add_patch(box_2c)

    ax.text(c2_x + 0.28, y_2c - 0.22, "STAGE C: 1D SUBSURFACE DRAINAGE GRAPH & MANHOLE BACKFLOW ENGINE", 
            ha='left', va='center', fontsize=8.8, fontweight='bold', color='#15803D', zorder=5)
    ax.text(c2_x + 0.28, y_2c - 0.48, "• Directed Drainage Graph G=(V,E): Nodes = Manholes (Z_invert = Z_ground - 1.5m); Edges = Road RCC conduits", 
            ha='left', va='center', fontsize=7.4, color='#0F172A', zorder=5)
    ax.text(c2_x + 0.28, y_2c - 0.72, "• Dynamic Clogging Factor: A_eff = A0*(1 - mu_clog), n_eff = n0*(1 + 1.8*mu_clog) scaled by GCC waste TPD", 
            ha='left', va='center', fontsize=7.4, color='#0F172A', zorder=5)
    ax.text(c2_x + 0.28, y_2c - 0.98, "• Hydraulic Surcharge: When HGL > Z_ground, upward backflow erupts: Q_back = Cd*A_lid*sqrt(2g(HGL-Z))", 
            ha='left', va='center', fontsize=7.4, color='#0F172A', zorder=5)
    ax.text(c2_x + 0.28, y_2c - 1.25, "• Net Street Depth: d_street(t) = (V_runoff + V_backflow - V_drained) / A_road (< 350 ms across 7,894 segments)", 
            ha='left', va='center', fontsize=7.4, fontweight='bold', color='#15803D', zorder=5)

    # -------------------------------------------------------------
    # COLUMN 3: ACTIONABLE OUTPUTS & EMERGENCY DISPATCH (RIGHT)
    # -------------------------------------------------------------
    c3_box = patches.FancyBboxPatch((c3_x, y_bottom), c3_w, col_h,
                                   boxstyle="Round,pad=0.06,rounding_size=0.16",
                                   facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=2)
    ax.add_patch(c3_box)

    h3 = patches.FancyBboxPatch((c3_x + 0.04, y_top - 0.60), c3_w - 0.08, 0.56,
                                boxstyle="Round,pad=0.03,rounding_size=0.10",
                                facecolor='#0F172A', edgecolor='none', zorder=3)
    ax.add_patch(h3)
    ax.text(c3_x + (c3_w / 2.0), y_top - 0.22, "3. ACTIONABLE OUTPUTS", 
            ha='center', va='center', fontsize=10.0, fontweight='bold', color='#FFFFFF', zorder=4)
    ax.text(c3_x + (c3_w / 2.0), y_top - 0.44, "GIS Command Twin & Routing API", 
            ha='center', va='center', fontsize=7.5, color='#94A3B8', zorder=4)

    # Output Card 1: Web GIS Command Twin
    y_out1 = y_top - 0.72
    h_out1 = 2.45
    box_o1 = patches.FancyBboxPatch((c3_x + 0.12, y_out1 - h_out1), c3_w - 0.24, h_out1,
                                   boxstyle="Round,pad=0.03,rounding_size=0.08",
                                   facecolor='#F0F9FF', edgecolor='#0284C7', linewidth=0.9, zorder=3)
    ax.add_patch(box_o1)
    
    cbar_o1 = patches.Rectangle((c3_x + 0.12, y_out1 - h_out1 + 0.08), 0.08, h_out1 - 0.16, facecolor='#0284C7', edgecolor='none', zorder=4)
    ax.add_patch(cbar_o1)

    ax.text(c3_x + 0.26, y_out1 - 0.22, "DYNAMIC WEB GIS TWIN", ha='left', va='center', fontsize=8.6, fontweight='bold', color='#0284C7', zorder=5)
    ax.text(c3_x + 0.26, y_out1 - 0.44, "Municipal Command Center Interface", ha='left', va='center', fontsize=7.0, fontstyle='italic', color='#64748B', zorder=5)
    
    ax.text(c3_x + 0.26, y_out1 - 0.74, "• 0-3h Time-Slider Control:", ha='left', va='center', fontsize=7.4, fontweight='bold', color='#0F172A', zorder=5)
    ax.text(c3_x + 0.36, y_out1 - 0.96, "Inspect live & future inundation (0-180m)", ha='left', va='center', fontsize=6.8, color='#334155', zorder=5)
    ax.text(c3_x + 0.26, y_out1 - 1.24, "• Color-Coded Depth Tiers (cm):", ha='left', va='center', fontsize=7.4, fontweight='bold', color='#0F172A', zorder=5)
    ax.text(c3_x + 0.36, y_out1 - 1.46, "Green (<5cm), Yellow (5-15), Orange, Red (>30)", ha='left', va='center', fontsize=6.8, color='#334155', zorder=5)
    ax.text(c3_x + 0.26, y_out1 - 1.74, "• Pulsing Surcharge Pins:", ha='left', va='center', fontsize=7.4, fontweight='bold', color='#0F172A', zorder=5)
    ax.text(c3_x + 0.36, y_out1 - 1.96, "Warns pump operators 30m before backflow", ha='left', va='center', fontsize=6.8, color='#334155', zorder=5)

    # Output Card 2: Safe Routing API
    y_out2 = y_out1 - h_out1 - 0.22
    h_out2 = 2.45
    box_o2 = patches.FancyBboxPatch((c3_x + 0.12, y_out2 - h_out2), c3_w - 0.24, h_out2,
                                   boxstyle="Round,pad=0.03,rounding_size=0.08",
                                   facecolor='#F0FDF4', edgecolor='#15803D', linewidth=0.9, zorder=3)
    ax.add_patch(box_o2)

    cbar_o2 = patches.Rectangle((c3_x + 0.12, y_out2 - h_out2 + 0.08), 0.08, h_out2 - 0.16, facecolor='#15803D', edgecolor='none', zorder=4)
    ax.add_patch(cbar_o2)

    ax.text(c3_x + 0.26, y_out2 - 0.22, "A* FLOOD-SAFE ROUTING API", ha='left', va='center', fontsize=8.6, fontweight='bold', color='#15803D', zorder=5)
    ax.text(c3_x + 0.26, y_out2 - 0.44, "Emergency Vehicle Rerouting Service", ha='left', va='center', fontsize=7.0, fontstyle='italic', color='#64748B', zorder=5)

    ax.text(c3_x + 0.26, y_out2 - 0.74, "• Vehicle Clearance Limits:", ha='left', va='center', fontsize=7.4, fontweight='bold', color='#0F172A', zorder=5)
    ax.text(c3_x + 0.36, y_out2 - 0.96, "Ambulance (30cm), Bus (45), Sedan (18), Bike (10)", ha='left', va='center', fontsize=6.8, color='#334155', zorder=5)
    ax.text(c3_x + 0.26, y_out2 - 1.24, "• Dynamic Travel Cost Function:", ha='left', va='center', fontsize=7.4, fontweight='bold', color='#0F172A', zorder=5)
    ax.text(c3_x + 0.36, y_out2 - 1.46, "Cost = (L/V) * [1 + alpha*(depth / limit)^2]", ha='left', va='center', fontsize=6.8, fontstyle='italic', color='#334155', zorder=5)
    ax.text(c3_x + 0.26, y_out2 - 1.74, "• Automated Reroute Output:", ha='left', va='center', fontsize=7.4, fontweight='bold', color='#0F172A', zorder=5)
    ax.text(c3_x + 0.36, y_out2 - 1.96, "Returns safe GeoJSON navigation polyline in <15ms", ha='left', va='center', fontsize=6.8, color='#334155', zorder=5)

    # Inter-Column Horizontal Arrows
    arr_in_eng = patches.FancyArrowPatch((c1_x + c1_w, y_top - 2.4), 
                                        (c2_x, y_top - 2.4),
                                        arrowstyle='-|>', mutation_scale=14, facecolor='#0F172A', edgecolor='#0F172A', zorder=7)
    ax.add_patch(arr_in_eng)

    arr_eng_out = patches.FancyArrowPatch((c2_x + c2_w, y_top - 2.4), 
                                         (c3_x, y_top - 2.4),
                                         arrowstyle='-|>', mutation_scale=14, facecolor='#15803D', edgecolor='#15803D', zorder=7)
    ax.add_patch(arr_eng_out)
    ax.text(c2_x + c2_w + 0.18, y_top - 2.22, "Street Depth\nd(t) in cm", ha='center', va='bottom', fontsize=6.8, fontweight='bold', color='#15803D', zorder=8)

    # -------------------------------------------------------------
    # 4. Bottom Production Technology Stack (Matching Team UDAAN)
    # -------------------------------------------------------------
    y_stack = 0.65
    stack_h = 0.76
    
    stacks = [
        {"cat": "SCIENTIFIC & HYDROLOGY", "tech": "Python 3.13, PySWMM, NetworkX, OpenCV, GeoPandas, Rasterio", "color": "#EA580C"},
        {"cat": "BACKEND & API ENGINE", "tech": "FastAPI, Uvicorn, Pydantic, GeoJSON REST Endpoints", "color": "#0284C7"},
        {"cat": "DATA & STORAGE LAYER", "tech": "PostgreSQL / PostGIS, Redis, Master CSV (7,894 Segments)", "color": "#0D9488"},
        {"cat": "FRONTEND DIGITAL TWIN", "tech": "Leaflet.js, MapLibre GL, Tailwind CSS, HTML5 Dynamic Canvas", "color": "#15803D"}
    ]

    sw = (16.0 - 1.00 - (3 * 0.20)) / 4.0
    for idx, stk in enumerate(stacks):
        sx = 0.50 + idx * (sw + 0.20)
        
        sbox = patches.FancyBboxPatch((sx, y_stack - (stack_h / 2.0)), sw, stack_h,
                                     boxstyle="Round,pad=0.03,rounding_size=0.08",
                                     facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=0.9, zorder=3)
        ax.add_patch(sbox)
        
        sbar = patches.Rectangle((sx + 0.03, y_stack - (stack_h / 2.0) + 0.05), 0.07, stack_h - 0.10,
                                facecolor=stk["color"], edgecolor='none', zorder=4)
        ax.add_patch(sbar)

        ax.text(sx + 0.18, y_stack + 0.13, stk["cat"], ha='left', va='center', fontsize=7.6, fontweight='bold', color=stk["color"], zorder=5)
        ax.text(sx + 0.18, y_stack - 0.13, stk["tech"], ha='left', va='center', fontsize=6.8, color='#334155', zorder=5)

    plt.tight_layout()
    out_file = 'slide3_technical_architecture_tiranga_glare.png'
    plt.savefig(out_file, format='png', dpi=240, bbox_inches='tight', pad_inches=0.05)
    plt.close()
    print(f"[+] Successfully re-generated with perfect text bounds: {out_file}")

if __name__ == '__main__':
    create_slide3_architecture_graphic()
