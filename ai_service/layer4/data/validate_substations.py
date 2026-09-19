import csv
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("validate_substations")

CSV_PATH = 'ai_service/layer4/data/substations.csv'
CHENNAI_BBOX = {
    "min_lat": 12.8, "max_lat": 13.3,
    "min_lon": 80.0, "max_lon": 80.4
}

def validate():
    success = True
    ids = set()
    coords = set()
    
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    logger.info(f"Loaded {len(rows)} records from {CSV_PATH}")
    
    for i, row in enumerate(rows):
        row_num = i + 2
        sub_id = row.get("substation_id", "")
        name = row.get("name", "")
        lat_str = row.get("latitude", "")
        lon_str = row.get("longitude", "")
        voltage_str = row.get("voltage_kv", "")
        source_name = row.get("source_name", "")
        source_url = row.get("source_url", "")
        plinth_str = row.get("plinth_height_m", "")
        
        # 1. Unique ID
        if not sub_id:
            logger.error(f"Row {row_num}: Missing substation_id")
            success = False
        elif sub_id in ids:
            logger.error(f"Row {row_num}: Duplicate substation_id {sub_id}")
            success = False
        ids.add(sub_id)
            
        # 2. Non-empty name
        if not name:
            logger.error(f"Row {row_num}: Missing name")
            success = False
            
        # 3. Source Metadata
        if not source_name or not source_url:
            logger.error(f"Row {row_num}: Missing source metadata")
            success = False
            
        # 4. Latitude/Longitude
        if not lat_str or not lon_str:
            logger.error(f"Row {row_num}: Missing coordinates")
            success = False
        else:
            try:
                lat = float(lat_str)
                lon = float(lon_str)
                
                # Bounds check
                if not (-90.0 <= lat <= 90.0):
                    logger.error(f"Row {row_num}: Invalid latitude {lat}")
                    success = False
                if not (-180.0 <= lon <= 180.0):
                    logger.error(f"Row {row_num}: Invalid longitude {lon}")
                    success = False
                    
                # Chennai BBox check
                if not (CHENNAI_BBOX["min_lat"] <= lat <= CHENNAI_BBOX["max_lat"] and
                        CHENNAI_BBOX["min_lon"] <= lon <= CHENNAI_BBOX["max_lon"]):
                    logger.warning(f"Row {row_num}: Suspicious coordinates {lat}, {lon} outside Chennai")
                
                # Duplicate coordinates
                coord_key = (lat, lon)
                if coord_key in coords:
                    logger.error(f"Row {row_num}: Duplicate coordinates {lat}, {lon}")
                    success = False
                coords.add(coord_key)
                
            except ValueError:
                logger.error(f"Row {row_num}: Malformed coordinates '{lat_str}', '{lon_str}'")
                success = False
                
        # 5. Voltage
        if voltage_str:
            try:
                volt = float(voltage_str)
                if volt <= 0:
                    logger.error(f"Row {row_num}: Invalid voltage {volt}")
                    success = False
            except ValueError:
                logger.error(f"Row {row_num}: Malformed voltage '{voltage_str}'")
                success = False
                
        # 6. Plinth Height (must NOT fail if empty)
        if not plinth_str:
            logger.info(f"Row {row_num}: Plinth height missing (Expected condition)")
        else:
            try:
                pl = float(plinth_str)
                if pl < 0:
                    logger.error(f"Row {row_num}: Invalid negative plinth {pl}")
                    success = False
            except ValueError:
                logger.error(f"Row {row_num}: Malformed plinth '{plinth_str}'")
                success = False

    if success:
        logger.info("Validation passed.")
    else:
        logger.error("Validation failed.")
        
    return success

if __name__ == "__main__":
    import sys
    if not validate():
        sys.exit(1)
