import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def build_grand_master_inventory():
    wb = openpyxl.Workbook()
    
    # -------------------------------------------------------------
    # SHEET 1: Master Inventory with Google Drive & GitHub Mappings
    # -------------------------------------------------------------
    ws1 = wb.active
    ws1.title = "Unified Master Inventory"
    ws1.views.sheetView[0].showGridLines = True

    # Title Block
    ws1.merge_cells("A1:J1")
    title_cell = ws1["A1"]
    title_cell.value = "Smart India Hackathon 2026 | PS ID: 26085 - Urban Flood Nowcasting System"
    title_cell.font = Font(name="Calibri", size=15, bold=True, color="FFFFFF")
    title_cell.fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[1].height = 36

    ws1.merge_cells("A2:J2")
    sub_cell = ws1["A2"]
    sub_cell.value = "Grand Master Catalog (Yashwanth, Vijay, Rithesh, Raksha, Vaishnavi, Gagan) | Storage: GitHub + Google Drive Vault"
    sub_cell.font = Font(name="Calibri", size=10.5, italic=True, color="FFFFFF")
    sub_cell.fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    sub_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[2].height = 24

    headers1 = [
        "Module / Domain",
        "Team Lead / Member",
        "Dataset / Artifact Name",
        "Primary Source",
        "Format",
        "Local Project Path (ML-Ready)",
        "Google Drive Cloud Vault Path",
        "Storage & Git Status",
        "Key Physical / ML Attributes",
        "Role in Flood Nowcasting & ML Pipeline"
    ]

    ws1.row_dimensions[3].height = 28
    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    header_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    for col_idx, header in enumerate(headers1, 1):
        cell = ws1.cell(row=3, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border

    # Records: 10 columns each
    records1 = [
        # --- UNIFIED MASTER ML DATASET (Grand Integration) ---
        (
            "Unified ML Training Matrix",
            "Full Team Integration",
            "Chennai Master Unified Flood Dataset",
            "Multi-Source Fusion (Yashwanth, Vijay, Rithesh, Raksha, Vaishnavi, Gagan)",
            "CSV (1.62 MB)",
            "Datasets/chennai_unified_flood_master_dataset.csv",
            "Google_Drive_Datasets/ & GitHub Repository",
            "Tracked in Git & Google Drive",
            "7,894 segments, 27 physical/meteorological/hydraulic/blockage features",
            "Core ML Training Ground Truth: Single unified table combining rainfall, elevation, slope, SWD pipe diameter, desilting %, and flood depth."
        ),
        # --- RAINFALL (Yashwanth) ---
        (
            "Rainfall & Meteorology",
            "Yashwanth",
            "GPM IMERG 2015 Satellite Precipitation (4,416 Rasters)",
            "NASA Earthdata GES DISC / GPM V07B",
            "NetCDF (.nc4) / 30-min",
            "Datasets/rainfall/satellite/GPM_IMERG_2015/gpm_data/",
            "Google_Drive_Datasets/01_Rainfall_Yashwanth/rainfall_data.zip",
            "Google Drive (Raw Rasters) & Git (Scripts)",
            "precipitationCal, precipitationUncal, randomError, lat, lon, time",
            "Dynamic Rainfall Forcing: 30-minute precipitation time-series driving the 2D surface runoff overland grid."
        ),
        (
            "Rainfall & Meteorology",
            "Yashwanth",
            "ECMWF ERA5 Reanalysis Weather Grid",
            "ECMWF Copernicus Climate Data Store",
            "NetCDF (.nc)",
            "Datasets/rainfall/era5/era5_chennai_oct_dec_2015.nc",
            "Google_Drive_Datasets/01_Rainfall_Yashwanth/rainfall_data.zip",
            "Google Drive Vault",
            "u10, v10, total_precipitation, convective_available_potential_energy",
            "Synoptic Atmosphere Influx: Hourly convective winds and pressure tracking storm pulses across the Bay of Bengal."
        ),
        (
            "Rainfall & Meteorology",
            "Yashwanth",
            "IMD Chennai Station Daily Rainfall (Oct-Dec 2015)",
            "India Meteorological Department (IMD)",
            "CSV (1.7 KB)",
            "Datasets/rainfall/imd/chennai_rainfall_oct_dec_2015.csv",
            "Google_Drive_Datasets/01_Rainfall_Yashwanth/rainfall_data.zip",
            "Tracked in Git & Google Drive",
            "date, rainfall_mm (Highlights 299mm Nov 16 & 329mm Dec 2)",
            "Ground-Truth Benchmark: Ground gauge records to calibrate satellite radar bias and validate rainfall totals."
        ),
        # --- TERRAIN & SOIL (Vijay) ---
        (
            "Terrain & Topography",
            "Vijay",
            "Cartosat-1 30m Digital Elevation Model (DEM)",
            "ISRO Bhuvan / Cartosat-1",
            "GeoTIFF (.tif, 99MB)",
            "Datasets/terrain/terrain data/dem/cartostat/...",
            "Google_Drive_Datasets/03_Terrain_and_DEM_Vijay/terrain data(Vijay).zip",
            "Google Drive Vault (>25MB Excluded from Git)",
            "elevation_meters, spatial_resolution_30m, crs_epsg4326",
            "Topographical Overland Routing: Defines gravity flow accumulation, terrain slope S_0, and natural depression sinks."
        ),
        (
            "Terrain & Topography",
            "Vijay",
            "SRTM 30m Global Elevation Tiles",
            "NASA / USGS EarthExplorer",
            "HGT (.hgt, 49MB)",
            "Datasets/terrain/terrain data/dem/srtm/...",
            "Google_Drive_Datasets/03_Terrain_and_DEM_Vijay/terrain data(Vijay).zip",
            "Google Drive Vault (>25MB Excluded from Git)",
            "elevation_grid, void_filled_topography",
            "Elevation Cross-Validation: Eliminates digital noise in coastal flat terrain and marshland zones."
        ),
        (
            "Terrain & Topography",
            "Vijay",
            "High-Resolution Soil Classification Maps",
            "NBSSLUP (ICAR) & State Agriculture Dept",
            "PNG (184MB) & Docs",
            "Datasets/terrain/terrain data/soil/...",
            "Google_Drive_Datasets/03_Terrain_and_DEM_Vijay/terrain data(Vijay).zip",
            "Google Drive Vault (184MB Excluded from Git)",
            "soil_texture_class, infiltration_capacity_fc, hydrologic_soil_group_A_D",
            "Infiltration & Runoff: Horton infiltration parameters determining how much rainwater enters soil vs runs off."
        ),
        (
            "Terrain & Topography",
            "Vijay",
            "Chennai Coastal Subsidence Rates",
            "InSAR Satellite Geodesy Studies",
            "CSV (3 KB)",
            "Datasets/terrain/terrain data/subsidence/subsidence_rates.csv",
            "Google_Drive_Datasets/03_Terrain_and_DEM_Vijay/terrain data(Vijay).zip",
            "Tracked in Git & Google Drive",
            "station_name, subsidence_rate_mm_per_year, lat, lon",
            "Micro-Elevation Correction: Corrects coastal elevation loss in delta areas experiencing groundwater extraction."
        ),
        (
            "Terrain & Topography",
            "Vijay",
            "Long-Term Groundwater Table Monitoring (1994-2025)",
            "Central Ground Water Board (CGWB)",
            "Excel (.xlsx, 160 KB)",
            "Datasets/terrain/terrain data/groundwater/...",
            "Google_Drive_Datasets/03_Terrain_and_DEM_Vijay/terrain data(Vijay).zip",
            "Tracked in Git & Google Drive",
            "pre_monsoon_wl, post_monsoon_wl, seasonal_fluctuation_m",
            "Soil Saturation Limit: Pre-monsoon water table depth determining time-to-saturation for surface flooding."
        ),
        # --- DRAINAGE NETWORK (Rithesh) ---
        (
            "Drainage Infrastructure",
            "Rithesh",
            "CMWSSB Stormwater Drainage Pipe Attributes",
            "Chennai Metro Water & Sewerage Board (CMWSSB)",
            "Excel (.xlsx, 27 KB)",
            "Datasets/drainage_network/drainage_data/cmwssb/pipe_attributes.xlsx",
            "Google_Drive_Datasets/02_Drainage_Rithesh/drainage_data(Rithesh).zip",
            "Tracked in Git & Google Drive",
            "pipe_id, diameter_mm, material_rcc, invert_level, slope, length_m",
            "1D Hydraulic Graph: Manning's conduit conveyance capacity Q_cap and conduit geometry for 1D pipe network."
        ),
        (
            "Drainage Infrastructure",
            "Rithesh",
            "GCC Stormwater Drainage Vector Network",
            "Greater Chennai Corporation / OpenStreetMap",
            "GeoJSON (53 KB)",
            "Datasets/drainage_network/drainage_data/oms_network/drainage network.geojson",
            "Google_Drive_Datasets/02_Drainage_Rithesh/drainage_data(Rithesh).zip",
            "Tracked in Git & Google Drive",
            "line_geometry, drain_type, flow_direction, connectivity",
            "Network Topology: Directed graph connecting micro-catchment inlets to outfalls."
        ),
        (
            "Drainage Infrastructure",
            "Rithesh",
            "Heavy OSM Building Footprints & Road Network",
            "OpenStreetMap Geospatial Export",
            "GeoJSON (332 MB total)",
            "Datasets/drainage_network/drainage_data/oms_network/...",
            "Google_Drive_Datasets/02_Drainage_Rithesh/drainage_data(Rithesh).zip",
            "Google Drive Vault (>50MB Excluded from Git)",
            "building_polygons, road_centerlines, surface_type",
            "Surface Obstacle Modeling: 2D flow barrier rasterization and building blockage factors."
        ),
        (
            "Drainage Infrastructure",
            "Rithesh",
            "CMWSSB Package Engineering DPR Reports",
            "CMWSSB Engineering Wing (Ambattur, Avadi, Mugalivakkam)",
            "PDF Reports (25 files, 91MB)",
            "Datasets/drainage_network/drainage_data/cmwssb/reports/...",
            "Google_Drive_Datasets/02_Drainage_Rithesh/drainage_data(Rithesh).zip",
            "Google Drive Vault (Excluded from Git)",
            "pumping_capacities, outfall_invert_levels, sluice_gate_specs",
            "Engineering Validation: Invert levels, pump sump volumes, and gravity main dimensions."
        ),
        # --- HISTORICAL FLOOD OBSERVATIONS (Raksha) ---
        (
            "Historical Flood Validation",
            "Raksha",
            "Master Flooded Street Segments Database (2015)",
            "GCC, Citizen Audits & OpenCity Chennai",
            "CSV (7,895 records)",
            "Datasets/historical_floods/Chennai_Historical_Flood_Data/Chennai_Flood_Data/00_master_flooded_street_segments.csv",
            "Google_Drive_Datasets/04_Historical_Floods_Raksha/Chennai_Historical_Flood_Data(Raksha).zip",
            "Tracked in Git & Google Drive",
            "osm_id, latitude, longitude, road_class, is_flooded, flood_depth",
            "ML Ground-Truth Target (y): 7,895 street segments to train and evaluate ML classification/nowcasting."
        ),
        (
            "Historical Flood Validation",
            "Raksha",
            "Quantitative Measured Flood Water Depths",
            "NRSC / NDMA Field Damage Surveys",
            "CSV (156 records)",
            "Datasets/historical_floods/Chennai_Historical_Flood_Data/Chennai_Flood_Data/00_master_flood_depth.csv",
            "Google_Drive_Datasets/04_Historical_Floods_Raksha/Chennai_Historical_Flood_Data(Raksha).zip",
            "Tracked in Git & Google Drive",
            "location_name, latitude, longitude, depth_cm, date, time",
            "Regression Ground Truth: Continuous centimeter flood depths to train depth regression models."
        ),
        (
            "Historical Flood Validation",
            "Raksha",
            "GCC Chronic Flood Hotspots & Vulnerability Locations",
            "GCC Disaster Management Cell",
            "CSV (327 hotspots)",
            "Datasets/historical_floods/Chennai_Historical_Flood_Data/Chennai_Flood_Data/00_master_gcc_flood_vulnerability_hotspots.csv",
            "Google_Drive_Datasets/04_Historical_Floods_Raksha/Chennai_Historical_Flood_Data(Raksha).zip",
            "Tracked in Git & Google Drive",
            "hotspot_name, ward, zone, vulnerability_rating, latitude, longitude",
            "Spatial Prioritization: Identifies chronic recurring bottlenecks (Velachery, Pulianthope, Vyasarpadi)."
        ),
        (
            "Historical Flood Validation",
            "Raksha",
            "HEC-RAS 2D Hydrodynamic Benchmark Results",
            "Academic Flood Modeling Literature (Adyar Basin)",
            "CSV",
            "Datasets/historical_floods/Chennai_Historical_Flood_Data/Chennai_Flood_Data/00_master_simulated_hec_ras_model_results.csv",
            "Google_Drive_Datasets/04_Historical_Floods_Raksha/Chennai_Historical_Flood_Data(Raksha).zip",
            "Tracked in Git & Google Drive",
            "cross_section_id, simulated_peak_discharge, simulated_hgl_m",
            "Physics Benchmark: Hydraulic validation standard to benchmark the sub-second Graph Neural Network (GNN)."
        ),
        (
            "Historical Flood Validation",
            "Raksha",
            "GCC Ward Population & Vulnerability Demographics",
            "Census of India (MDDS 2011)",
            "CSV & Excel (8,800 records)",
            "Datasets/historical_floods/Chennai_Historical_Flood_Data/Chennai_Flood_Data/population/...",
            "Google_Drive_Datasets/04_Historical_Floods_Raksha/Chennai_Historical_Flood_Data(Raksha).zip",
            "Tracked in Git & Google Drive",
            "ward_no, total_population, male, female, sc_st_pop, households",
            "Human Vulnerability: Population density and demographic vulnerability index for evacuation prioritisation."
        ),
        # --- SATELLITE EO (Vaishnavi) ---
        (
            "Earth Observation & SAR",
            "Vaishnavi",
            "Sentinel-1 SAR Flood Extent & Preprocessing Pipeline",
            "Copernicus Open Access Hub / ESA",
            "Python / Specs",
            "Datasets/satellite/satellite_data/sentinel1/...",
            "Google_Drive_Datasets/05_Satellite_Vaishnavi/Chennai_Satellite_Data_FINAL(vaishnavi).zip",
            "Tracked in Git & Google Drive",
            "backscatter_sigma0_db, water_mask_threshold, acquisition_date",
            "Radar Flood Extents: Synthetic Aperture Radar (SAR) all-weather cloud-penetrating water mask for validation."
        ),
        (
            "Earth Observation & SAR",
            "Vaishnavi",
            "Chennai Area of Interest (AOI) Bounding Boundary",
            "Greater Chennai Corporation Boundary",
            "GeoJSON (61 KB)",
            "Datasets/satellite/satellite_data/aoi/Chennai_AOI.geojson",
            "Google_Drive_Datasets/05_Satellite_Vaishnavi/Chennai_Satellite_Data_FINAL(vaishnavi).zip",
            "Tracked in Git & Google Drive",
            "polygon_geometry, bounding_box, crs_epsg4326",
            "Spatial Clip Boundary: Enforces consistent spatial bounds across all team GIS rasters and vectors."
        ),
        # --- CIVIC MAINTENANCE & INFRASTRUCTURE (Gagan) ---
        (
            "Civic Maintenance & Blockage",
            "Gagan",
            "GCC Zonal Solid Waste & Silt Generation Summary",
            "GCC Solid Waste Department & Urbaser Sumeet",
            "CSV (17 KB)",
            "maintenance_data/solid_waste/chennai_gcc_solid_waste_zone_summary.csv",
            "Google_Drive_Datasets/06_Civic_Maintenance_Gagan/SIH_Day1_Deliverables_Maintenance_and_Research.zip",
            "Tracked in Git & Google Drive",
            "zone_no, waste_generated_tpd, wet_dry_split, silt_debris_tpd",
            "Inlet Blockage Factor: Scales catch-pit inlet efficiency based on daily street litter and silt accumulation."
        ),
        (
            "Civic Maintenance & Blockage",
            "Gagan",
            "GCC Stormwater Drain Pre-Monsoon Desilting Progress",
            "GCC SWD Department & State Highways Dept",
            "CSV (19 KB)",
            "maintenance_data/drain_maintenance/chennai_gcc_drain_maintenance_records.csv",
            "Google_Drive_Datasets/06_Civic_Maintenance_Gagan/SIH_Day1_Deliverables_Maintenance_and_Research.zip",
            "Tracked in Git & Google Drive",
            "zone_no, swd_length_km, desilting_completed_km, silt_removed_tonnes",
            "Effective Hydraulic Capacity: Dynamically updates conduit roughness n_eff and active cross-section A_eff."
        ),
        (
            "Civic Maintenance & Blockage",
            "Gagan",
            "Major Outfall Canals Desilting & Bottleneck Status",
            "Water Resources Department (WRD) / GCC",
            "CSV (13 KB)",
            "maintenance_data/drain_maintenance/chennai_canal_desilting_status.csv",
            "Google_Drive_Datasets/06_Civic_Maintenance_Gagan/SIH_Day1_Deliverables_Maintenance_and_Research.zip",
            "Tracked in Git & Google Drive",
            "canal_id, length_km, silt_hyacinth_cleared_tonnes, bottleneck_points",
            "Boundary Condition: Models tidal lock and outfall backwater rise in Buckingham Canal and Otteri Nullah."
        ),
        (
            "Civic Maintenance & Blockage",
            "Gagan",
            "Chronic Drain Blockage & Waterlogging Hotspot Complaints",
            "GCC 1913 Portal, Namma Chennai App, Civic Audit",
            "CSV (26 records)",
            "maintenance_data/blockage_complaints/chennai_drain_blockage_complaints.csv",
            "Google_Drive_Datasets/06_Civic_Maintenance_Gagan/SIH_Day1_Deliverables_Maintenance_and_Research.zip",
            "Tracked in Git & Google Drive",
            "latitude, longitude, date, location, type, source, confidence",
            "Validation Coordinates: 25 verified geo-coordinates to benchmark manhole surcharge backflow simulation."
        ),
        (
            "Traffic & Evacuation",
            "Gagan",
            "Chennai Arterial Corridors Traffic Volume & Hourly Profiles",
            "CMDA Comprehensive Mobility Plan / MoRTH",
            "CSV (39 KB)",
            "maintenance_data/traffic/chennai_traffic_volume_counts.csv",
            "Google_Drive_Datasets/06_Civic_Maintenance_Gagan/SIH_Day1_Deliverables_Maintenance_and_Research.zip",
            "Tracked in Git & Google Drive",
            "corridor_id, daily_pcu, peak_hour_pcu, vc_ratio, hourly_flow_pct",
            "Safe Navigation API: Dynamic routing cost calculation; closes roads where predicted water depth > clearance."
        ),
        (
            "Electrical Infrastructure",
            "Gagan",
            "TANGEDCO Electrical Substations Spatial Grid",
            "TANGEDCO Grid Directory / OpenStreetMap",
            "GeoJSON & CSV",
            "maintenance_data/electrical/chennai_electrical_substations.geojson",
            "Google_Drive_Datasets/06_Civic_Maintenance_Gagan/SIH_Day1_Deliverables_Maintenance_and_Research.zip",
            "Tracked in Git & Google Drive",
            "substation_id, name, voltage_kv, type, plinth_level_cm, flood_risk",
            "Power Grid Resilience: Predicts transformer submersion to guide targeted feeder shutdowns instead of blackouts."
        ),
        (
            "Economic Vulnerability",
            "Gagan",
            "Commercial Clusters & Depth-Damage Rupee Functions",
            "GCC Trade Licensing & Economic Census",
            "CSV & Markdown",
            "maintenance_data/economic_data/chennai_commercial_clusters_economic_data.csv",
            "Google_Drive_Datasets/06_Civic_Maintenance_Gagan/SIH_Day1_Deliverables_Maintenance_and_Research.zip",
            "Tracked in Git & Google Drive",
            "cluster_name, commercial_units, daily_turnover_cr, depth_damage_curves",
            "Disaster Loss Quantification: Computes projected rupee stock loss as flood water rises from 5cm to 60cm."
        ),
        # --- RESEARCH & SYSTEM BLUEPRINT (Gagan) ---
        (
            "Technical Architecture",
            "Gagan",
            "Urban Flood Nowcasting Research Report (5 Pages)",
            "MoES / NCMRWF Mathematical Formulation",
            "PDF (Publication-Grade)",
            "Urban_Flood_Nowcasting_Comprehensive_Research_Report.pdf",
            "Google_Drive_Datasets/06_Civic_Maintenance_Gagan/Urban_Flood_Nowcasting_Comprehensive_Research_Report.pdf",
            "Tracked in Git & Google Drive",
            "Z-R nowcast, 2D overland, 1D graph hydraulics, GNN surrogate",
            "Scientific Blueprint: Mathematical derivation of manhole surcharge backflow and navigation API cost equations."
        )
    ]

    row_start = 4
    for idx, r in enumerate(records1):
        row_num = row_start + idx
        ws1.row_dimensions[row_num].height = 24
        fill_color = "F8FAFC" if idx % 2 == 0 else "FFFFFF"
        row_fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")

        for col_idx, val in enumerate(r, 1):
            cell = ws1.cell(row=row_num, column=col_idx, value=val)
            cell.font = Font(name="Calibri", size=9.5)
            cell.fill = row_fill
            cell.border = thin_border

            # Column alignments
            if col_idx in [1, 2, 5, 8]:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif col_idx in [3, 4, 6, 7]:
                cell.alignment = Alignment(horizontal="left", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

    col_widths1 = [22, 16, 36, 28, 16, 38, 42, 26, 45, 60]
    for col_idx, width in enumerate(col_widths1, 1):
        ws1.column_dimensions[get_column_letter(col_idx)].width = width

    # -------------------------------------------------------------
    # SHEET 2: Google Drive Vault Directory Mapping & Instructions
    # -------------------------------------------------------------
    ws2 = wb.create_sheet(title="Google Drive Vault Map")
    ws2.views.sheetView[0].showGridLines = True

    ws2.merge_cells("A1:F1")
    t2 = ws2["A1"]
    t2.value = "Google Drive Cloud Vault Structure (SIH_2026_Data_Vault)"
    t2.font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    t2.fill = PatternFill(start_color="065F46", end_color="065F46", fill_type="solid")
    t2.alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[1].height = 34

    headers2 = [
        "Folder Number & Name",
        "Lead Contributor",
        "Zip Archive / Primary File",
        "Raw Archive Size",
        "Unpacked Contents Description",
        "Download & Usage Command"
    ]
    ws2.row_dimensions[2].height = 26
    h2_fill = PatternFill(start_color="047857", end_color="047857", fill_type="solid")
    for col_idx, h in enumerate(headers2, 1):
        cell = ws2.cell(row=2, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = h2_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border

    drive_folders = [
        (
            "01_Rainfall_Yashwanth",
            "Yashwanth N",
            "rainfall_data.zip",
            "14.3 MB",
            "4,416 NASA GPM IMERG 30-min NetCDF (.nc4) rasters, ECMWF ERA5 hourly weather .nc, IMD 2015 daily CSV",
            "python scripts/download_drive_data.py --module rainfall"
        ),
        (
            "02_Drainage_Rithesh",
            "Rithesh",
            "drainage_data(Rithesh).zip",
            "196.0 MB",
            "CMWSSB pipe attributes, GCC stormwater drain network GeoJSON, heavy OSM building polygons (332MB), 25 DPR PDFs",
            "python scripts/download_drive_data.py --module drainage"
        ),
        (
            "03_Terrain_and_DEM_Vijay",
            "Vijay",
            "terrain data(Vijay).zip",
            "222.1 MB",
            "ISRO Cartosat-1 30m DEM GeoTIFF, SRTM 30m .hgt tiles, 184MB NBSSLUP soil raster, subsidence CSV, groundwater Excel",
            "python scripts/download_drive_data.py --module terrain"
        ),
        (
            "04_Historical_Floods_Raksha",
            "Raksha",
            "Chennai_Historical_Flood_Data(Raksha).zip",
            "48.3 MB",
            "7,895 flooded street segments CSV, 327 GCC hotspots, 156 measured depth points, HEC-RAS model, NDMA reports",
            "python scripts/download_drive_data.py --module historical"
        ),
        (
            "05_Satellite_Vaishnavi",
            "Vaishnavi",
            "Chennai_Satellite_Data_FINAL(vaishnavi).zip",
            "22 KB",
            "Sentinel-1 SAR flood extent processing scripts, ESA WorldCover 10m LULC instructions, Chennai AOI GeoJSON",
            "python scripts/download_drive_data.py --module satellite"
        ),
        (
            "06_Civic_Maintenance_Gagan",
            "Gagan K S",
            "SIH_Day1_Deliverables_Maintenance_and_Research.zip",
            "54 KB + 17 KB PDF",
            "All 6 GCC maintenance CSVs (solid waste, desilting, complaints, traffic, electrical, economic) + 5-page Research PDF",
            "python scripts/download_drive_data.py --module maintenance"
        )
    ]

    for idx, d in enumerate(drive_folders):
        row_num = 3 + idx
        ws2.row_dimensions[row_num].height = 24
        fill_color = "F0FDF4" if idx % 2 == 0 else "FFFFFF"
        row_fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")

        for col_idx, val in enumerate(d, 1):
            cell = ws2.cell(row=row_num, column=col_idx, value=val)
            cell.font = Font(name="Calibri", size=9.5)
            cell.fill = row_fill
            cell.border = thin_border

            if col_idx in [1, 2, 4]:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

    col_widths2 = [28, 18, 30, 16, 55, 45]
    for col_idx, width in enumerate(col_widths2, 1):
        ws2.column_dimensions[get_column_letter(col_idx)].width = width

    # Save to all required destinations
    out_root = r"c:\Users\Gagan K S\Documents\SIH\inventory.xlsx"
    out_maint = r"c:\Users\Gagan K S\Documents\SIH\maintenance_data\inventory.xlsx"
    out_drive = r"c:\Users\Gagan K S\Documents\SIH\Google_Drive_Datasets\inventory.xlsx"

    wb.save(out_root)
    wb.save(out_maint)
    wb.save(out_drive)
    print(f"Grand Master Inventory successfully updated and saved across all 3 locations!")

if __name__ == "__main__":
    build_grand_master_inventory()
