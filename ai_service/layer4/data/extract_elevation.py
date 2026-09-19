import csv
import os
import rasterio
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("extract_elevation")

CSV_PATH = 'ai_service/layer4/data/substations.csv'
DEM_PATH = 'ai_service/layer4/data/raw/chennai_dem_synthetic.tif'

def extract_elevation():
    if not os.path.exists(CSV_PATH) or not os.path.exists(DEM_PATH):
        logger.error("Required files missing.")
        return
        
    logger.info("Opening DEM raster...")
    with rasterio.open(DEM_PATH) as src:
        
        logger.info("Reading substation coordinates...")
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames)
            rows = list(reader)
            
        # Ensure new columns exist
        if "ground_elevation_m" not in fieldnames:
            fieldnames.extend(["ground_elevation_m", "ground_elevation_source"])
            
        success_count = 0
        missing_count = 0
            
        for row in rows:
            lat_str = row.get("latitude", "")
            lon_str = row.get("longitude", "")
            
            ground_elev = ""
            
            if lat_str and lon_str:
                try:
                    lat = float(lat_str)
                    lon = float(lon_str)
                    
                    # Sample raster using rasterio.sample
                    # sample() takes an iterable of (x, y) coordinates
                    gen = src.sample([(lon, lat)])
                    val = next(gen)[0]
                    
                    # Check if val is valid (not nodata)
                    if val != src.nodata:
                        ground_elev = round(float(val), 2)
                        success_count += 1
                    else:
                        missing_count += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to sample elevation for {lat_str}, {lon_str}: {e}")
                    missing_count += 1
            else:
                missing_count += 1
                
            row["ground_elevation_m"] = str(ground_elev) if ground_elev != "" else ""
            row["ground_elevation_source"] = "Synthetic_SRTM_30m" if ground_elev != "" else ""
            
            # The prompt explicitly requires NOT modifying plinth_height_m
            # It should remain unchanged (null)
            
        logger.info("Writing updated CSV...")
        with open(CSV_PATH, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            
    logger.info(f"Extraction complete. Added elevation to {success_count} substations. {missing_count} missing.")

if __name__ == "__main__":
    extract_elevation()
