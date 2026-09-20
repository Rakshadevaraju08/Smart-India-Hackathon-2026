import json
import csv
import os

RAW_PATH = 'ai_service/layer4/data/raw/osm_chennai_substations.json'
CSV_PATH = 'ai_service/layer4/data/substations.csv'

def build_csv():
    with open(RAW_PATH, 'r') as f:
        raw_data = json.load(f)
        
    elements = raw_data.get('elements', [])
    
    # We will map the OSM elements to the schema
    rows = []
    
    for i, el in enumerate(elements):
        tags = el.get('tags', {})
        voltage_v = tags.get('voltage', '')
        
        voltage_kv = None
        if voltage_v:
            try:
                voltage_kv = float(voltage_v) / 1000.0
            except ValueError:
                voltage_kv = None
                
        sub_id = f"SS-{i+1:03d}"
        
        row = {
            "substation_id": sub_id,
            "name": tags.get("name", "Unknown Substation"),
            "latitude": el.get("lat"),
            "longitude": el.get("lon"),
            "voltage_kv": voltage_kv if voltage_kv else "",
            "source_name": "TANTRANSCO/TNEB",
            "source_url": "https://tapps.tneb.in/geoserver/TNEB/wms",
            "coordinate_source": "OpenStreetMap",
            "plinth_height_m": "", # Explicitly null (empty string for CSV)
            "plinth_height_source": ""
        }
        rows.append(row)
        
    with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            "substation_id", "name", "latitude", "longitude", "voltage_kv",
            "source_name", "source_url", "coordinate_source", 
            "plinth_height_m", "plinth_height_source"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
            
    print(f"Successfully generated {CSV_PATH} with {len(rows)} records.")

if __name__ == "__main__":
    build_csv()
