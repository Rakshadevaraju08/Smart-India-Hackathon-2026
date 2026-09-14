import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def create_slide6_graphic():
    # 16:9 Aspect ratio (16 x 9 inches at 240 DPI = 3840 x 2160 pixels)
    fig, ax = plt.subplots(figsize=(16, 9), dpi=240)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis('off')

    # -------------------------------------------------------------
    # 1. Atmospheric Ambient Glare (Tiranga Lighting)
    # -------------------------------------------------------------
    # Base pure white
    bg = patches.Rectangle((0, 0), 16, 9, facecolor='#FFFFFF', zorder=0)
    ax.add_patch(bg)

    # Top Saffron Ambient Glow (Soft Gaussian-decay gradient)
    y_vals_top = np.linspace(6.8, 9.0, 60)
    for i in range(len(y_vals_top) - 1):
        y0 = y_vals_top[i]
        y1 = y_vals_top[i+1]
        progress = (y0 - 6.8) / (9.0 - 6.8)
        alpha = 0.015 + 0.13 * (progress ** 2.2)
        rect = patches.Rectangle((0, y0), 16, y1 - y0, facecolor='#FF9933', edgecolor='none', alpha=alpha, zorder=1)
        ax.add_patch(rect)

    # Bottom India Green Ambient Glow
    y_vals_bot = np.linspace(0.0, 2.2, 60)
    for i in range(len(y_vals_bot) - 1):
        y0 = y_vals_bot[i]
        y1 = y_vals_bot[i+1]
        progress = (2.2 - y1) / (2.2 - 0.0)
        alpha = 0.015 + 0.11 * (progress ** 2.2)
        rect = patches.Rectangle((0, y0), 16, y1 - y0, facecolor='#138808', edgecolor='none', alpha=alpha, zorder=1)
        ax.add_patch(rect)

    # -------------------------------------------------------------
    # 2. Slide Header & Subtitle
    # -------------------------------------------------------------
    ax.text(8.0, 8.44, "RESEARCH, REFERENCES & VALIDATION BENCHMARKS", 
            ha='center', va='center', fontsize=21, fontweight='bold', color='#0F172A', family='sans-serif', zorder=5)
    ax.text(8.0, 8.10, "Scientific Literature, Government Standards & Ground-Truth Datasets | Smart India Hackathon 2026 (PS: 26085)", 
            ha='center', va='center', fontsize=10.5, fontstyle='italic', color='#475569', family='sans-serif', zorder=5)

    # -------------------------------------------------------------
    # 3. Three Thematic Content Pillars (Cards)
    # -------------------------------------------------------------
    card_w = 4.80
    card_h = 5.75
    y_top = 7.78
    y_bottom = y_top - card_h

    # Card 1: Government & Regulatory Standards (Saffron Accent)
    x1 = 0.65
    # Card 2: Scientific Foundations & Peer-Reviewed Papers (Blue Accent)
    x2 = 5.60
    # Card 3: Empirical Datasets & Disaster Benchmarks (India Green Accent)
    x3 = 10.55

    cards_config = [
        {
            "x": x1,
            "title": "GOVERNMENT MANUALS & CODES",
            "subtitle": "National Guidelines & Urban Engineering Standards",
            "accent_color": "#EA580C",
            "border_color": "#FDBA74",
            "header_bg": "#FFF7ED",
            "items": [
                {
                    "title": "CPHEEO Stormwater Drainage Manual (2019)",
                    "author": "Ministry of Housing and Urban Affairs (MoHUA), Govt. of India",
                    "desc": "Official urban runoff coefficients (C >= 0.90 for roads) and Manning's roughness (n = 0.015) for RCC pipe networks.",
                    "tag": "DESIGN STANDARD"
                },
                {
                    "title": "National Urban Flood Guidelines (2010)",
                    "author": "National Disaster Management Authority (NDMA)",
                    "desc": "Standard operating procedures for 0-3h localized flood nowcasting, pump de-watering, and evacuation routing.",
                    "tag": "DISASTER SOP"
                },
                {
                    "title": "Smart Cities Climate Action Plan (2021)",
                    "author": "Ministry of Housing and Urban Affairs (MoHUA)",
                    "desc": "Mandates digital twin GIS platforms, sensor integration, and real-time municipal grievance response for drainage.",
                    "tag": "POLICY MANDATE"
                }
            ]
        },
        {
            "x": x2,
            "title": "PEER-REVIEWED SCIENTIFIC PAPERS",
            "subtitle": "Hydrological, Radar & Mathematical Foundations",
            "accent_color": "#0284C7",
            "border_color": "#93C5FD",
            "header_bg": "#F0F9FF",
            "items": [
                {
                    "title": "Marshall & Palmer (1948) - Precipitation",
                    "author": "Journal of Meteorology | 4,200+ Citations",
                    "desc": "Establishes empirical radar reflectivity Z = a * R^b (a=200, b=1.6 calibrated for tropical coastal convective storms).",
                    "tag": "RADAR PHYSICS"
                },
                {
                    "title": "Rossman, L. A. (2015) - EPA SWMM 5.2",
                    "author": "United States Environmental Protection Agency",
                    "desc": "Formulates 1D dynamic wave routing, pipe surcharge head (HGL), pressurized flow, and manhole backflow hydraulics.",
                    "tag": "1D HYDRAULICS"
                },
                {
                    "title": "Wang & Liu (2006) - DEM Pit-Filling",
                    "author": "Int. Journal of Geographical Information Science",
                    "desc": "Priority-queue depression filling on high-resolution DEMs to route overland flow without spurious digital sinks.",
                    "tag": "TERRAIN ROUTING"
                }
            ]
        },
        {
            "x": x3,
            "title": "EMPIRICAL GROUND-TRUTH BENCHMARKS",
            "subtitle": "Real City Master Data & Disaster Calibration",
            "accent_color": "#15803D",
            "border_color": "#86EFAC",
            "header_bg": "#F0FDF4",
            "items": [
                {
                    "title": "GCC 1913 Waterlogging Grievance Logs",
                    "author": "Greater Chennai Corporation Smart City Portal",
                    "desc": "Empirical database of 7,894 road segments, ward solid waste (TPD), desilting schedules, and chronic waterlogging hotspots.",
                    "tag": "CIVIC DATASET"
                },
                {
                    "title": "Cyclone Michaung Calibration (Dec 2023)",
                    "author": "Sentinel-1 SAR Satellite + Traffic Police Logs",
                    "desc": "Real-world validation event (450 mm rain / 24h) used to benchmark model flood depths, surcharges, and road passability.",
                    "tag": "GROUND TRUTH"
                },
                {
                    "title": "ISRO Cartosat-1 DEM & IMD Radar Scans",
                    "author": "NRSC Bhuvan & India Meteorological Department",
                    "desc": "Ingests 10m high-resolution elevation rasters and S-band Doppler Weather Radar polar reflectivity feeds for nowcasting.",
                    "tag": "EARTH OBSERVATION"
                }
            ]
        }
    ]

    for col in cards_config:
        bx = col["x"]
        
        # Outer Card Container
        card_box = patches.FancyBboxPatch((bx, y_bottom), card_w, card_h,
                                         boxstyle="Round,pad=0.08,rounding_size=0.18",
                                         facecolor='#FFFFFF', edgecolor=col["border_color"],
                                         linewidth=1.3, zorder=2)
        ax.add_patch(card_box)

        # Top Accent Header Strip
        header_rect = patches.FancyBboxPatch((bx + 0.04, y_top - 0.70), card_w - 0.08, 0.66,
                                           boxstyle="Round,pad=0.04,rounding_size=0.12",
                                           facecolor=col["header_bg"], edgecolor='none', zorder=3)
        ax.add_patch(header_rect)
        
        # Thin top highlight line
        line_top = patches.Rectangle((bx + 0.35, y_top - 0.04), card_w - 0.70, 0.05,
                                     facecolor=col["accent_color"], edgecolor='none', zorder=4)
        ax.add_patch(line_top)

        # Header Titles
        ax.text(bx + (card_w / 2.0), y_top - 0.28, col["title"],
                ha='center', va='center', fontsize=11.5, fontweight='bold', color=col["accent_color"], family='sans-serif', zorder=5)
        ax.text(bx + (card_w / 2.0), y_top - 0.52, col["subtitle"],
                ha='center', va='center', fontsize=8.2, color='#64748B', family='sans-serif', zorder=5)

        # Render 3 Items inside each card
        item_y_start = y_top - 0.86
        item_spacing = 1.62
        
        for idx, itm in enumerate(col["items"]):
            curr_y = item_y_start - (idx * item_spacing)
            
            # Subtle item box
            item_box = patches.FancyBboxPatch((bx + 0.16, curr_y - 1.42), card_w - 0.32, 1.42,
                                             boxstyle="Round,pad=0.04,rounding_size=0.10",
                                             facecolor='#F8FAFC', edgecolor='#E2E8F0',
                                             linewidth=0.8, zorder=3)
            ax.add_patch(item_box)

            # Row 1: Tag Badge on the left, Author on the right
            badge_w = 1.42
            badge_h = 0.24
            badge_box = patches.FancyBboxPatch((bx + 0.26, curr_y - 0.30), badge_w, badge_h,
                                               boxstyle="Round,pad=0.02,rounding_size=0.06",
                                               facecolor=col["accent_color"], edgecolor='none', alpha=0.14, zorder=4)
            ax.add_patch(badge_box)
            ax.text(bx + 0.26 + (badge_w / 2.0), curr_y - 0.18, itm["tag"],
                    ha='center', va='center', fontsize=7.0, fontweight='bold', color=col["accent_color"], zorder=5)

            # Author/Organization on the right
            ax.text(bx + card_w - 0.26, curr_y - 0.18, itm["author"][:36],
                    ha='right', va='center', fontsize=7.5, fontstyle='italic', color='#64748B', family='sans-serif', zorder=5)

            # Row 2: Title (Full width, bold, never overlaps)
            ax.text(bx + 0.26, curr_y - 0.52, f"{idx+1}. {itm['title']}",
                    ha='left', va='center', fontsize=9.2, fontweight='bold', color='#0F172A', family='sans-serif', zorder=5)

            # Row 3 & 4: Description (Clean wrapping)
            words = itm["desc"].split(' ')
            lines = []
            cur_line = []
            for w in words:
                cur_line.append(w)
                if len(' '.join(cur_line)) > 50:
                    lines.append(' '.join(cur_line))
                    cur_line = []
            if cur_line:
                lines.append(' '.join(cur_line))

            desc_y = curr_y - 0.80
            for l_idx, line_text in enumerate(lines[:3]):
                ax.text(bx + 0.26, desc_y - (l_idx * 0.23), line_text,
                        ha='left', va='center', fontsize=8.0, color='#334155', family='sans-serif', zorder=5)

    # -------------------------------------------------------------
    # 4. Bottom Verification Resource Badges (Like Team UDAAN's Links)
    # -------------------------------------------------------------
    y_footer_card = 0.68
    footer_h = 0.84

    resources = [
        {"title": "PROJECT REPOSITORY", "detail": "github.com/team-kairos/urban-flood-nowcast", "icon": "[CODE]", "color": "#EA580C"},
        {"title": "LIVE WEB GIS TWIN", "detail": "Interactive 0-3h Inundation Map Dashboard", "icon": "[DEMO]", "color": "#0284C7"},
        {"title": "A* ROUTING API DOCS", "detail": "FastAPI REST: Dynamic Vehicle Clearance", "icon": "[API]", "color": "#0D9488"},
        {"title": "TECHNICAL PDF SPEC", "detail": "5-Page Formal Hydrological Architecture", "icon": "[DOCS]", "color": "#15803D"},
    ]

    card_spacing = (16.0 - 1.30 - (4 * 3.45)) / 3.0
    for idx, res in enumerate(resources):
        rx = 0.65 + idx * (3.45 + card_spacing)
        
        # Pill card
        res_box = patches.FancyBboxPatch((rx, y_footer_card - (footer_h / 2.0)), 3.45, footer_h,
                                        boxstyle="Round,pad=0.06,rounding_size=0.12",
                                        facecolor='#FFFFFF', edgecolor='#CBD5E1',
                                        linewidth=1.0, zorder=3)
        ax.add_patch(res_box)
        
        # Left color bar
        cbar = patches.FancyBboxPatch((rx + 0.05, y_footer_card - (footer_h / 2.0) + 0.08), 0.12, footer_h - 0.16,
                                     boxstyle="Round,pad=0.02,rounding_size=0.04",
                                     facecolor=res["color"], edgecolor='none', zorder=4)
        ax.add_patch(cbar)

        # Icon / Badge Text
        ax.text(rx + 0.32, y_footer_card + 0.16, res["icon"],
                ha='left', va='center', fontsize=8.5, fontweight='bold', color=res["color"], zorder=5)
        ax.text(rx + 1.10, y_footer_card + 0.16, res["title"],
                ha='left', va='center', fontsize=8.8, fontweight='bold', color='#0F172A', zorder=5)
        ax.text(rx + 0.32, y_footer_card - 0.18, res["detail"],
                ha='left', va='center', fontsize=7.6, color='#475569', zorder=5)

    plt.tight_layout()
    output_png = 'slide6_research_references_tiranga_glare.png'
    plt.savefig(output_png, format='png', dpi=240, bbox_inches='tight', pad_inches=0.05)
    plt.close()
    print(f"[+] Successfully generated: {output_png}")

if __name__ == '__main__':
    create_slide6_graphic()
