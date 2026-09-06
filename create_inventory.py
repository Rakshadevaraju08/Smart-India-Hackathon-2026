import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def build_inventory_excel():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Dataset Inventory"
    ws.views.sheetView[0].showGridLines = True

    # Title block
    ws.merge_cells("A1:H1")
    title_cell = ws["A1"]
    title_cell.value = "Urban Flood Nowcasting System (SIH-26085) - Maintenance & Supporting Data Inventory"
    title_cell.font = Font(name="Calibri", size=15, bold=True, color="FFFFFF")
    title_cell.fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 40

    ws.merge_cells("A2:H2")
    sub_cell = ws["A2"]
    sub_cell.value = "Target Region: Greater Chennai Corporation (GCC) | Generated on: 2026-09-04 | Day 1 Deliverable"
    sub_cell.font = Font(name="Calibri", size=10, italic=True, color="475569")
    sub_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 20

    # Headers
    headers = [
        "Category",
        "Dataset / Artifact Name",
        "Primary Source",
        "Format",
        "Relative Path",
        "Status",
        "Key Fields / Attributes",
        "Operational Description & Hydro-Coupling Utility"
    ]
    
    ws.row_dimensions[3].height = 28
    header_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border

    # Data Rows
    data_records = [
        (
            "Solid Waste",
            "GCC Zonal Solid Waste Generation & Collection",
            "Greater Chennai Corporation (GCC) Solid Waste Dept",
            "CSV",
            "maintenance_data/solid_waste/chennai_gcc_solid_waste_zone_summary.csv",
            "Available (Official Structured)",
            "zone_no, zone_name, waste_generated_tpd, waste_collected_tpd, wet_waste_tpd, dry_waste_tpd, silt_debris_tpd, operator_agency",
            "Captures daily TPD generation across 15 zones (5,490 TPD total) used to parameterize inlet grate clogging probability."
        ),
        (
            "Swachh Survekshan",
            "Chennai Swachh Survekshan Assessment Scores",
            "Ministry of Housing & Urban Affairs (MoHUA)",
            "CSV",
            "maintenance_data/solid_waste/chennai_swachh_survekshan_scores.csv",
            "Available (MoHUA Data)",
            "indicator_category, indicator_name, max_marks, chennai_score, chennai_pct, assessment_level",
            "Detailed breakdown of drain cleanliness, segregated collection, and waste processing scores (Score: 4,313.79/9500)."
        ),
        (
            "Swachh Survekshan",
            "Zone-Wise Cleanliness & Drain Clogging Indicators",
            "GCC Swachh Bharat Cell / City Audits",
            "CSV",
            "maintenance_data/solid_waste/chennai_zone_cleanliness_indicators.csv",
            "Available (Derived)",
            "zone_no, cleanliness_score_100, source_segregation_pct, drain_garbage_dumping_risk, littering_vulnerability_index",
            "Identifies high-risk littering zones (Zones 4, 5, 6) where plastic and dry waste wash into curb inlets during flash storms."
        ),
        (
            "Solid Waste",
            "GCC Solid Waste System & Drainage Linkage Report",
            "GCC Annual Reports & Environmental Audits",
            "Markdown / Report",
            "maintenance_data/solid_waste/gcc_solid_waste_management_report.md",
            "Available (Analytical Report)",
            "Full operational report on Urbaser Sumeet, Ramky, Perungudi, Kodungaiyur dumpsites",
            "Synthesizes concessionaire contracts, waste composition, and mathematical coupling between uncollected litter and drain clogging."
        ),
        (
            "Drain Maintenance",
            "GCC Stormwater Drain Desilting Progress Records",
            "Greater Chennai Corporation SWD Department",
            "CSV",
            "maintenance_data/drain_maintenance/chennai_gcc_drain_maintenance_records.csv",
            "Available (Official Status)",
            "zone_no, swd_length_km, desilting_completed_km, silt_catch_pits_count, silt_removed_metric_tonnes, status",
            "Tracks 1,671.39 km of GCC micro-drains and 430 km Highway drains; 12,300+ MT silt removed for pre-monsoon readiness."
        ),
        (
            "Drain Maintenance",
            "Major Drainage Canals Desilting & Bottleneck Status",
            "Water Resources Department (WRD) / GCC",
            "CSV",
            "maintenance_data/drain_maintenance/chennai_canal_desilting_status.csv",
            "Available (Official Multi-Agency)",
            "canal_id, canal_name, length_km, basin_river, silt_hyacinth_cleared_tonnes, critical_bottleneck_points, flood_risk_level",
            "Monitors 44 major discharge canals (Buckingham Canal, Otteri Nullah, Mambalam Canal, Okkiyam Maduvu) and outfall tidal locks."
        ),
        (
            "Drain Maintenance",
            "GCC Stormwater Infrastructure & Hydraulics Report",
            "GCC, WRD & ADB Basin Project Documentation",
            "Markdown / Report",
            "maintenance_data/drain_maintenance/gcc_stormwater_drain_maintenance_report.md",
            "Available (Technical Report)",
            "Network scale, Kosasthalaiyar & Kovalam ADB/KfW projects, Manning's roughness, tidal backwater",
            "Provides physical network specifications, culvert siphon failure points, and Manning hydraulic roughness values."
        ),
        (
            "Blockage Complaints",
            "Historical Drain Blockage & Waterlogging Records",
            "GCC 1913 Portal, Namma Chennai App, CAG Chennai",
            "CSV",
            "maintenance_data/blockage_complaints/chennai_drain_blockage_complaints.csv",
            "Available (Verified Locations)",
            "latitude, longitude, date, location, type, source, confidence",
            "25 geo-located chronic choke points (Velachery, Pulianthope, T. Nagar, Vyasarpadi) for validation of graph backflow predictions."
        ),
        (
            "Traffic Data",
            "Chennai Arterial Corridors Volume & PCU Counts",
            "CMDA Comprehensive Mobility Plan / MoRTH",
            "CSV",
            "maintenance_data/traffic/chennai_traffic_volume_counts.csv",
            "Available (CMP / CTTP Studies)",
            "corridor_id, corridor_name, daily_pcu, peak_hour_morning_pcu, capacity_pcu_per_hr, vc_ratio, flood_vulnerability_rating",
            "Traffic volumes for 12 major corridors (Anna Salai, GST Rd, OMR, Poonamallee High Rd) to compute dynamic flood rerouting."
        ),
        (
            "Traffic Data",
            "Diurnal Hourly Traffic Profile & Evacuation Risk",
            "CMDA Traffic Monitoring Cell / CCTP",
            "CSV",
            "maintenance_data/traffic/chennai_hourly_traffic_profile.csv",
            "Available (Standardized Model)",
            "hour_interval, time_period, traffic_share_pct, avg_network_speed_kmh, emergency_corridor_clearance_risk",
            "24-hour temporal traffic distribution to model peak congestion vs cloudburst timing."
        ),
        (
            "Traffic Data",
            "Traffic Flow & Dynamic Flood Routing Methodology",
            "CMDA CMP 2019 / CCTP Traffic Guidelines",
            "Markdown / Report",
            "maintenance_data/traffic/chennai_traffic_and_transport_profile.md",
            "Available (Engineering Report)",
            "V/C ratios, underpass bottlenecks, A* dynamic water depth routing cost formulas",
            "Defines vehicle depth limits (15 cm for cars, 30 cm for ambulances) and cost function for the navigation API."
        ),
        (
            "Electrical Infra",
            "TANGEDCO Electrical Substations Spatial Dataset",
            "TANGEDCO Grid Directory / OpenStreetMap",
            "CSV",
            "maintenance_data/electrical/chennai_tangedco_substations.csv",
            "Available (Verified Coordinates)",
            "substation_id, name, voltage_kv, type, latitude, longitude, elevation_m, plinth_level_cm, flood_risk_level",
            "20 major transmission/distribution substations (400kV, 230kV, 110kV) with elevation, plinth height, and risk ratings."
        ),
        (
            "Electrical Infra",
            "TANGEDCO Substations GeoJSON FeatureCollection",
            "TANGEDCO / Spatial Extraction",
            "GeoJSON",
            "maintenance_data/electrical/chennai_electrical_substations.geojson",
            "Available (Spatial GeoJSON)",
            "FeatureCollection, Point geometry, properties (voltage, plinth, flood_risk, criticality)",
            "Ready-to-render GIS layer for web dashboard showing power assets at risk of flood immersion."
        ),
        (
            "Electrical Infra",
            "Electrical Infrastructure Flood Vulnerability Report",
            "TANGEDCO Operations & Disaster Protocols",
            "Markdown / Report",
            "maintenance_data/electrical/chennai_electrical_infrastructure_flood_risk.md",
            "Available (Operational Report)",
            "Transformer plinth heights, preemptive feeder tripping, SCADA nowcast integration",
            "Explains electrical hazard thresholds (25 cm pillar box flood trigger) and targeted micro-feeder isolation strategies."
        ),
        (
            "Economic Data",
            "Major Commercial Clusters & Business Value Exposure",
            "GCC Trade License Data / CMDA Land Use / OSM",
            "CSV",
            "maintenance_data/economic_data/chennai_commercial_clusters_economic_data.csv",
            "Available (Aggregated Analysis)",
            "cluster_id, cluster_name, primary_category, latitude, longitude, commercial_units_est, avg_daily_turnover_inr_cr",
            "Quantifies asset exposure across 12 commercial hubs (T. Nagar retail, OMR tech parks, George Town wholesale, Guindy MSMEs)."
        ),
        (
            "Economic Data",
            "Zonal Business Density & Flood Interruption Losses",
            "GCC Trade Licensing & Economic Census",
            "CSV",
            "maintenance_data/economic_data/chennai_business_density_by_zone.csv",
            "Available (Zonal Aggregation)",
            "zone_no, zone_name, total_commercial_units, business_density_per_sq_km, estimated_hourly_interruption_loss_lakhs",
            "147,190 commercial units across 15 zones with estimated hourly business interruption losses (₹15.9 Cr/hr citywide)."
        ),
        (
            "Economic Data",
            "Chennai Economic Flood Exposure & Damage Curves",
            "GCC / Disaster Management Authority / World Bank",
            "Markdown / Report",
            "maintenance_data/economic_data/chennai_economic_flood_exposure.md",
            "Available (Economic Framework)",
            "Depth-damage curves f(d), sector vulnerability, loss quantification models",
            "Provides empirical depth-damage curves for calculating direct rupee loss from predicted water depth."
        ),
        (
            "Environment",
            "Python Project Dependencies & Core Packages",
            "PyPI / Python 3.13 Environment",
            "TXT",
            "requirements.txt",
            "Available (Verified)",
            "xgboost, lightgbm, scikit-learn, networkx, fastapi, uvicorn, pandas, numpy, folium, redis, etc.",
            "Complete reproducible python environment for hydrologic-hydraulic modeling, ML, and API routing."
        )
    ]

    row_start = 4
    for idx, row_data in enumerate(data_records):
        row_num = row_start + idx
        ws.row_dimensions[row_num].height = 24
        fill_color = "F8FAFC" if idx % 2 == 0 else "FFFFFF"
        row_fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")

        for col_idx, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_num, column=col_idx, value=value)
            cell.font = Font(name="Calibri", size=10)
            cell.fill = row_fill
            cell.border = thin_border
            
            # Formatting alignments
            if col_idx in [1, 4, 6]:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif col_idx in [2, 3, 5]:
                cell.alignment = Alignment(horizontal="left", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

    # Column widths
    col_widths = [18, 36, 32, 12, 45, 24, 45, 55]
    for col_idx, width in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    # Save
    out_path = r"c:\Users\Gagan K S\Documents\SIH\maintenance_data\inventory.xlsx"
    wb.save(out_path)
    print(f"Successfully generated inventory spreadsheet at: {out_path}")

if __name__ == "__main__":
    build_inventory_excel()
