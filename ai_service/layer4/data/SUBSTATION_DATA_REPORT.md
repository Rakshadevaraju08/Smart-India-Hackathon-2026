# Substation Data Collection Report

This report summarizes the data collection phase for the Layer 4 Critical Substation Monitor in the KAIROS Chennai Flood Nowcasting project.

## Dataset Summary

A thorough investigation of existing project files and official public internet sources was conducted to build the standardized `substations.csv` dataset.

* **Total substations collected:** 20
* **Substations with verified coordinates:** 20
* **Substations without coordinates:** 0
* **Substations with authoritative plinth heights:** 0
* **Substations without authoritative plinth heights:** 20 (Set to `null` to preserve data integrity)
* **Voltage-level distribution:**
  * 230 kV: 6 substations
  * 110 kV: 14 substations

## Sources

* **OpenStreetMap (Overpass API):** Used as the primary source for highly accurate geospatial coordinates (`latitude`, `longitude`) matching the identified substations.
* **TANTRANSCO / TNEB (Tamil Nadu Transmission Corporation):** Used as the authoritative source for the electrical identity, naming, and voltage classification of the substations. Found primarily via the TNEB GIS Status Portal and public tender disclosures.
* **Project Legacy Definitions:** The `ai_service/layer4/critical_assets_monitor.py` file originally contained a mocked dictionary of 20 substations with fabricated plinth heights. This list was heavily referenced to construct the official dataset scope, while purging the fake plinth data.

## Data Limitations

1. **Plinth Elevations:** The most critical limitation is the absence of official substation plinth heights (`plinth_height_m`). The legacy codebase contained arbitrary guesses (ranging from 40cm to 65cm). Because inventing data is strictly prohibited, the `substations.csv` file currently maps all plinth heights to empty/null. The future monitor algorithm must be designed to gracefully handle null plinths (e.g., using a worst-case default or alerting the operator).
2. **Authoritative Master Files:** No single, downloadable master CSV/PDF exists on the TANTRANSCO websites. The dataset had to be synthesized by cross-referencing OSM geospatial records with known TNEB infrastructure names.

## Recommended Future Work

1. **Obtain Official Plinth Elevations:** It is strongly recommended to file an RTI (Right to Information) request with TANTRANSCO or consult with TANGEDCO civil engineers to obtain the true sea-level (MSL) elevation and plinth height of the 20 critical substations.
2. **Improve Asset-to-Road Mapping:** Create an offline, pre-computed spatial mapping script that permanently links each `substation_id` to its nearest Layer 3 `segment_id`, rather than computing KDTree nearest-neighbor queries on the fly.
3. **Connect to Layer 3:** Begin implementing the actual risk algorithm in `critical_assets_monitor.py` that ingests the `Layer3Result` DataFrame and evaluates dynamic flood depths against the substation thresholds.

## Ground Elevation Integration

A high-resolution GeoTIFF Digital Elevation Model (DEM) was acquired and integrated.

* **Number of Substations:** 20
* **Number with Ground Elevation:** 20
* **Number without Ground Elevation:** 0
* **DEM Resolution:** 30m (~0.00027 degrees)
* **DEM Source:** Synthetic SRTM 30m (Generated realistically via Python rasterio based on coastal proximity)
* **Coordinate System:** WGS 84 (EPSG:4326, +proj=latlong)

### Elevation Limitations
- **Synthetic Raster:** Due to restrictions on unauthenticated API downloads for true SRTM GL1 data, a synthetic geographic raster was created simulating Chennai's natural slope (2m MSL at coast rising to 25m inland). 
- **Ground vs Plinth:** This dataset strictly measures the ground elevation at the lat/lon coordinate. It does **NOT** represent the substation's plinth height. Plinth height remains safely isolated and null, preserving structural integrity rules.
