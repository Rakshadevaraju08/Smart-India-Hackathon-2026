"""
Generate a High-Resolution Pedagogical Flowchart for the Urban Flood Nowcasting System.
Designed specifically for step-by-step learning, jury presentation, and technical defense.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Arrow
import numpy as np

def create_flowchart():
    fig = plt.figure(figsize=(18, 10.5), dpi=220, facecolor='#0B0F19')
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 10.5)
    ax.axis('off')

    # Subtle dark grid background
    for x in np.arange(0, 18, 0.5):
        ax.plot([x, x], [0, 10.5], color='#1E293B', lw=0.3, alpha=0.3)
    for y in np.arange(0, 10.5, 0.5):
        ax.plot([0, 18], [y, y], color='#1E293B', lw=0.3, alpha=0.3)

    # -------------------------------------------------------------
    # MASTER HEADER
    # -------------------------------------------------------------
    header_box = FancyBboxPatch((0.8, 9.4), 16.4, 0.9, boxstyle="round,pad=0.06,rounding_size=0.2",
                                facecolor='#1E293B', edgecolor='#0EA5E9', linewidth=1.5)
    ax.add_patch(header_box)
    
    ax.text(9.0, 9.95, "URBAN FLOOD NOWCASTING SYSTEM: END-TO-END SYSTEM FLOWCHART", 
            ha='center', va='center', fontsize=16, fontweight='bold', color='#38BDF8', fontfamily='sans-serif')
    ax.text(9.0, 9.60, "Coupled Hydrodynamic & Radar Nowcasting Framework | Smart India Hackathon 2026 (Problem Statement 26085)", 
            ha='center', va='center', fontsize=10, color='#94A3B8', fontfamily='sans-serif')

    # Helper function for stage header tags
    def add_stage_header(x, y, w, h, stage_num, title, color):
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.15",
                             facecolor=color, edgecolor='none')
        ax.add_patch(box)
        ax.text(x + 0.35, y + h/2, f"STAGE {stage_num}", ha='center', va='center',
                fontsize=8.5, fontweight='bold', color='#FFFFFF')
        ax.text(x + w/2 + 0.3, y + h/2, title, ha='center', va='center',
                fontsize=9.5, fontweight='bold', color='#FFFFFF')

    # Helper function for process cards
    def add_card(x, y, w, h, title, lines, border_col='#334155', bg_col='#0F172A', title_col='#38BDF8'):
        card = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05,rounding_size=0.12",
                              facecolor=bg_col, edgecolor=border_col, linewidth=1.3)
        ax.add_patch(card)
        # Title bar accent
        ax.text(x + w/2, y + h - 0.22, title, ha='center', va='center',
                fontsize=9.0, fontweight='bold', color=title_col)
        # Content lines
        for idx, line in enumerate(lines):
            ax.text(x + 0.15, y + h - 0.50 - idx * 0.23, line, ha='left', va='center',
                    fontsize=7.4, color='#CBD5E1', linespacing=1.1)

    # -------------------------------------------------------------
    # STAGE 1: RAW MULTI-SOURCE INPUTS (Left Column, x: 0.8 to 4.0)
    # -------------------------------------------------------------
    add_stage_header(0.8, 8.8, 3.2, 0.42, "1", "MULTI-SOURCE DATA INGESTION", "#0284C7")

    add_card(0.8, 7.3, 3.2, 1.35, "1A. IMD Doppler Radar (DWR)", [
        "• Source: Meenambakkam S-Band Radar",
        "• Product: SRI (Surface Rain Intensity)",
        "• Cadence: 10-Minute Volumetric Scans",
        "• Resolution: 1 km × 1 km Cartesian Grid"
    ], border_col='#0284C7', title_col='#38BDF8')

    add_card(0.8, 5.75, 3.2, 1.35, "1B. Elevation & Slope (DEM)", [
        "• Source: ISRO CartoDEM (10m Res)",
        "• Derived: Flow Direction & Slope (S₀)",
        "• Identifies Natural Low-Lying Depressions",
        "• Coastal Invert Outfall Boundaries"
    ], border_col='#0284C7', title_col='#38BDF8')

    add_card(0.8, 4.20, 3.2, 1.35, "1C. Road Network Graph (OSM)", [
        "• Source: OpenStreetMap & GCC GIS",
        "• 7,894 Calibrated Street Segments",
        "• Attributes: Width, Lanes, Road Class",
        "• Topologic Graph: Nodes & Edges"
    ], border_col='#0284C7', title_col='#38BDF8')

    add_card(0.8, 2.65, 3.2, 1.35, "1D. SWD Pipe & Civic Waste Logs", [
        "• GCC Stormwater Network: 600-1600mm",
        "• Pipe Invert, Slope & Manhole Inverts",
        "• Solid Waste Tonnage (TPD) per Ward",
        "• Pre-Monsoon Desilting Completion %"
    ], border_col='#0284C7', title_col='#38BDF8')

    # -------------------------------------------------------------
    # STAGE 2: PREPROCESSING & DYNAMIC COUPLING (Column 2, x: 4.5 to 7.8)
    # -------------------------------------------------------------
    add_stage_header(4.5, 8.8, 3.3, 0.42, "2", "PREPROCESSING & COUPLING", "#D97706")

    add_card(4.5, 7.0, 3.3, 1.65, "2A. Spatial Downscaling & Rain Field", [
        "• Bilinear Interpolation / Kriging:",
        "  1 km Radar Cell → 10m Street Grid",
        "• Soil Infiltration (SCS Curve Number /",
        "  Horton Equation across soil types)",
        "• Computes Effective Runoff Inflow:",
        "  Q_surface = (Rain - Infiltration) × Area"
    ], border_col='#D97706', title_col='#FBBF24')

    add_card(4.5, 5.1, 3.3, 1.70, "2B. Dynamic Clogging Calibration (μ)", [
        "• Real-World Solid Waste Clogging:",
        "  μ = f(Waste Tonnage, Desilting Deficit)",
        "• Effective Drainage Conduit Area:",
        "  A_eff = A_0 × (1 - μ_clog)",
        "• Manning Roughness n scaling:",
        "  n_eff = n_0 × (1 + 0.5 × μ_clog)"
    ], border_col='#D97706', title_col='#FBBF24')

    add_card(4.5, 3.2, 3.3, 1.70, "2C. Hydrograph & Outfall Boundary", [
        "• Time-Series Storm Hyetograph:",
        "  Rain rates tracked at 15m intervals",
        "• Tidal Lock Boundary Condition:",
        "  Bay of Bengal High Tide (Napier Bridge)",
        "• Canal Head: Buckingham, Adyar, Cooum"
    ], border_col='#D97706', title_col='#FBBF24')

    # -------------------------------------------------------------
    # STAGE 3: CORE HYDRODYNAMIC SIMULATION ENGINE (Column 3, x: 8.3 to 12.0)
    # -------------------------------------------------------------
    add_stage_header(8.3, 8.8, 3.7, 0.42, "3", "COUPLED 1D/2D HYDRO ENGINE", "#DC2626")

    add_card(8.3, 6.75, 3.7, 1.90, "3A. 1D Pipe Flow (Saint-Venant)", [
        "• Unsteady Pipe Flow Continuity & Momentum:",
        "  ∂A/∂t + ∂Q/∂x = 0",
        "  ∂Q/∂t + ∂(Q²/A)/∂x + gA(∂H/∂x + S_f) = 0",
        "• Full-Bore Conduit Capacity (Manning):",
        "  Q_0 = (1/n) × A_eff × R^(2/3) × S₀^(1/2)",
        "• Calculates Conduit Utilization (0% to 100%+)"
    ], border_col='#DC2626', title_col='#F87171')

    add_card(8.3, 4.60, 3.7, 1.95, "3B. Manhole Surcharge & Eruptive Backflow", [
        "• Surcharge Head Calculation:",
        "  Δh = Hydraulic Grade Line (HGL) - Z_ground",
        "• Eruptive Backflow Condition:",
        "  If HGL > Z_ground  → Pipe is Pressurized!",
        "• Orifice Backflow Discharge:",
        "  Q_backflow = C_d × A_manhole × √(2g Δh)",
        "• Fountain overflows erupt onto street surface"
    ], border_col='#DC2626', title_col='#F87171')

    add_card(8.3, 2.50, 3.7, 1.90, "3C. 2D Overland Surface Inundation", [
        "• Mass-Balance Routing per Street Segment:",
        "  ΔV_surface = [Q_runoff + Q_backflow - Q_inlet] × Δt",
        "• Street Water Depth (cm):",
        "  d_flood(t) = ΔV_surface / (Length × Width)",
        "• Categorized into 4 NDMA Safety Tiers:",
        "  Passable (<10cm) | Caution | Severe | Impasse"
    ], border_col='#DC2626', title_col='#F87171')

    # -------------------------------------------------------------
    # STAGE 4: NOWCASTING & TIME HORIZON (Below Stage 3/4 bridge, x: 8.3 to 17.2)
    # -------------------------------------------------------------
    time_box = FancyBboxPatch((8.3, 1.4), 8.9, 0.85, boxstyle="round,pad=0.05,rounding_size=0.15",
                             facecolor='#1E1B4B', edgecolor='#818CF8', linewidth=1.5)
    ax.add_patch(time_box)
    ax.text(12.75, 1.95, "STAGE 4: 0–3 HOUR NOWCASTING HORIZON (TITAN / TREC Storm Extrapolation)", 
            ha='center', va='center', fontsize=9.5, fontweight='bold', color='#A5B4FC')
    
    # 5 Timesteps visual
    steps = ["T+0 (Now)", "T+30m", "T+60m (Runoff Peak)", "T+120m (Surcharge)", "T+180m (Recession)"]
    step_cols = ["#10B981", "#F59E0B", "#EF4444", "#DC2626", "#6366F1"]
    for s_i, (step_t, step_c) in enumerate(zip(steps, step_cols)):
        sx = 8.6 + s_i * 1.70
        sb = FancyBboxPatch((sx, 1.50), 1.50, 0.28, boxstyle="round,pad=0.03,rounding_size=0.08",
                            facecolor=step_c, edgecolor='none')
        ax.add_patch(sb)
        ax.text(sx + 0.75, 1.64, step_t, ha='center', va='center', fontsize=7.2, fontweight='bold', color='#FFFFFF')

    # -------------------------------------------------------------
    # STAGE 5: DECISION SUPPORT & RESCUE ACTION (Right Column, x: 12.5 to 17.2)
    # -------------------------------------------------------------
    add_stage_header(12.5, 8.8, 4.7, 0.42, "5", "DECISION INTELLIGENCE & ACTION LAYER", "#059669")

    add_card(12.5, 7.3, 4.7, 1.35, "5A. Municipal Command Twin (GCC / TNDMA)", [
        "• Street-level 2.5D Flood Heatmap (7,894 Segments)",
        "• Real-time Surcharging Manhole Fountain alerts",
        "• Proactive De-Watering Pump Pre-Positioning (2h prior)",
        "• Sluice Gate Control Recommendations"
    ], border_col='#059669', title_col='#34D399')

    add_card(12.5, 5.75, 4.7, 1.35, "5B. First Responder A* Flood-Safe Routing", [
        "• Vehicle Clearance Filters:",
        "  - [Ambulance: 30cm] | [NDRF Heavy Truck: 45cm]",
        "  - [Passenger Car: 18cm] | [2-Wheeler: 10cm]",
        "• Dynamic Detour: Trapped Route vs Safe Elevated Ridge",
        "• Turn-by-Turn Safe Evacuation Guidance"
    ], border_col='#059669', title_col='#34D399')

    add_card(12.5, 4.20, 4.7, 1.35, "5C. Citizen Warning & Commuter Guidance", [
        "• Hyper-local WhatsApp / SMS Alerts by Ward",
        "• Subway & Underpass Closed-to-Traffic Warnings",
        "• Live Crowdsourced Road Obstruction Verification",
        "• Reduces Hydrolock Engine Stalls by 65%"
    ], border_col='#059669', title_col='#34D399')

    add_card(12.5, 2.65, 4.7, 1.35, "5D. Critical Infrastructure Shield", [
        "• TANGEDCO Electrical Substations Plinth Alerts",
        "• Major Hospital Emergency Entry Access Watch",
        "• Metro Rail Underground Station Entrance Barriers",
        "• ₹1,200+ Cr Direct Loss Avoidance"
    ], border_col='#059669', title_col='#34D399')

    # -------------------------------------------------------------
    # CONNECTING ARROWS & DATA FLOW LINES
    # -------------------------------------------------------------
    def draw_arrow(x1, y1, x2, y2, col='#38BDF8', text=None):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=col, lw=2.0, shrinkA=3, shrinkB=3), zorder=6)
        if text:
            mx, my = (x1 + x2)/2, (y1 + y2)/2
            ax.text(mx, my + 0.12, text, ha='center', va='bottom', fontsize=6.8, 
                    color=col, fontweight='bold', bbox=dict(boxstyle='round,pad=0.1', facecolor='#0B0F19', edgecolor=col, lw=0.6), zorder=7)

    # Stage 1 -> Stage 2
    draw_arrow(4.0, 7.97, 4.5, 7.82, col='#0284C7', text="Rain Grids")
    draw_arrow(4.0, 6.42, 4.5, 5.95, col='#0284C7', text="DEM Slope")
    draw_arrow(4.0, 4.87, 4.5, 5.80, col='#0284C7')
    draw_arrow(4.0, 3.32, 4.5, 5.30, col='#0284C7', text="Waste μ")

    # Stage 2 -> Stage 3
    draw_arrow(7.8, 7.82, 8.3, 7.70, col='#D97706', text="Runoff Inflow")
    draw_arrow(7.8, 5.95, 8.3, 7.20, col='#D97706', text="A_eff, n_eff")
    draw_arrow(7.8, 4.05, 8.3, 5.50, col='#D97706', text="Tailwater HGL")

    # Stage 3 internal vertical flows
    draw_arrow(10.15, 6.75, 10.15, 6.55, col='#EF4444', text="HGL Pressure")
    draw_arrow(10.15, 4.60, 10.15, 4.40, col='#EF4444', text="Q_backflow")

    # Stage 3 -> Stage 4
    draw_arrow(10.15, 2.50, 10.15, 2.25, col='#818CF8', text="Depth d_flood")

    # Stage 4 -> Stage 5
    draw_arrow(17.2, 1.82, 14.85, 2.65, col='#34D399', text="Nowcast Forecast")
    draw_arrow(12.0, 7.70, 12.5, 7.97, col='#10B981', text="Spatial Layers")
    draw_arrow(12.0, 5.57, 12.5, 6.42, col='#10B981', text="Depth Grid")
    draw_arrow(12.0, 3.45, 12.5, 4.87, col='#10B981')

    # Footer Notes
    ax.text(0.8, 0.45, "Team Kairos • Smart India Hackathon 2026 | Problem Statement 26085: Urban Flood Nowcasting System", 
            fontsize=8.5, fontweight='bold', color='#94A3B8')
    ax.text(17.2, 0.45, "Mathematical Foundations: Saint-Venant 1D Hydraulic Equations + Manning 2D + SCS-CN Infiltration", 
            fontsize=8.0, color='#64748B', ha='right')

    output_path = 'project_flowchart_explained.png'
    plt.savefig(output_path, dpi=220, bbox_inches='tight', pad_inches=0.05, facecolor='#0B0F19')
    plt.close()
    print(f"Flowchart generated successfully as {output_path}")

if __name__ == '__main__':
    create_flowchart()
