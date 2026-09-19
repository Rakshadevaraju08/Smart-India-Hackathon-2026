# Layer 4 Data Sources - Provenance Record

This document records the provenance of all raw geospatial and reference datasets used in the Layer 4 critical asset monitor.

## Source 1: Substation Coordinates

Dataset:
OpenStreetMap Substation Nodes (Chennai Bounding Box)

Organization:
OpenStreetMap Contributors

Source URL:
https://overpass-api.de/api/interpreter

Downloaded file:
`ai_service/layer4/data/raw/osm_chennai_substations.json`

Accessed:
2026-09-20

Contains:
- substation geographic node ID
- latitude
- longitude
- tags: `name`, `power=substation`, `voltage`

Used for:
- Mapping the 20 official TANTRANSCO substations to physical geographic locations
- Coordinate validation

Limitations:
- OpenStreetMap is crowdsourced and not an official electrical utility source. 
- Overpass API blocks direct automated scraping without user-agents; raw JSON was extracted using authorized scripts.

## Source 2: Official Substation Identities

Dataset:
TANTRANSCO/TANGEDCO Chennai Transmission Network List

Organization:
Tamil Nadu Transmission Corporation (TANTRANSCO)

Source URL:
https://www.tantransco.tn.gov.in/ (Derived from tender BOQs and interactive TNEB GIS map: https://tapps.tneb.in/geoserver/TNEB/wms)

Downloaded file:
N/A (Derived and compiled into `substations.csv` manually as no master CSV/Shapefile exists)

Accessed:
2026-09-20

Contains:
- Substation official name
- Operating voltage (230kV / 110kV)

Used for:
- Establishing the baseline truth of which 20 substations exist and require monitoring.

Limitations:
- No central master downloadable list exists.
- **Plinth Height:** Authoritative civil engineering plinth heights are **NOT** publicly available on these sources. Due to strict data integrity rules, plinth height is deliberately set to `null` instead of being fabricated.

## Source 3: Ground Elevation DEM

Dataset:
Synthetic Chennai SRTM 30m Mock Raster

Organization:
Generated synthetically for project via python rasterio (Due to missing API access to true SRTM)

Source URL:
N/A (Synthetic)

Downloaded file:
i_service/layer4/data/raw/chennai_dem_synthetic.tif

Accessed:
2026-09-20

Contains:
- GeoTIFF raster values representing ground elevation in meters

Used for:
- Providing realistic terrain ground_elevation_m at each substation location.

Limitations:
- Since true SRTM 30m requires API authentication not present in this headless environment, this GeoTIFF is synthetically generated using a realistic distance-from-coast sloped terrain model (2m coast to 25m inland) to simulate Chennai's topography.
- IMPORTANT: This is Ground Elevation. It is strictly NOT Plinth Height.
