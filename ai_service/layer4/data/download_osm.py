import urllib.request
import json
import os

os.makedirs('ai_service/layer4/data/raw', exist_ok=True)

# Overpass API query for substations in Chennai bounding box
query = """
[out:json][timeout:25];
(
  node["power"="substation"](12.85, 80.10, 13.25, 80.35);
  way["power"="substation"](12.85, 80.10, 13.25, 80.35);
  relation["power"="substation"](12.85, 80.10, 13.25, 80.35);
);
out center;
"""

url = 'https://overpass-api.de/api/interpreter'
data = query.encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
print("Downloading OSM data...")
try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        with open('ai_service/layer4/data/raw/osm_chennai_substations.json', 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Successfully downloaded {len(result.get('elements', []))} substations from OSM.")
except Exception as e:
    print('Failed to download OSM data:', e)
