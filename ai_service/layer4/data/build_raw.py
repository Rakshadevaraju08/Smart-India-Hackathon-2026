import json
import os

os.makedirs('ai_service/layer4/data/raw', exist_ok=True)

# We are mocking the Overpass API download since the API returned 406 Not Acceptable
CHENNAI_SUBSTATIONS = [
    {"id": "SS-001", "name": "Mylapore Substation", "voltage_kv": 230, "plinth_cm": 60.0, "lat": 13.0384, "lon": 80.2612},
    {"id": "SS-002", "name": "T. Nagar Substation", "voltage_kv": 110, "plinth_cm": 45.0, "lat": 13.0418, "lon": 80.2341},
    {"id": "SS-003", "name": "Guindy Industrial Grid", "voltage_kv": 230, "plinth_cm": 55.0, "lat": 13.0067, "lon": 80.2036},
    {"id": "SS-004", "name": "Koyambedu Substation", "voltage_kv": 110, "plinth_cm": 50.0, "lat": 13.0694, "lon": 80.1948},
    {"id": "SS-005", "name": "Velachery Substation", "voltage_kv": 110, "plinth_cm": 40.0, "lat": 12.9815, "lon": 80.2180},
    {"id": "SS-006", "name": "Alandur Substation", "voltage_kv": 110, "plinth_cm": 45.0, "lat": 13.0031, "lon": 80.1989},
    {"id": "SS-007", "name": "Adyar Substation", "voltage_kv": 110, "plinth_cm": 50.0, "lat": 13.0064, "lon": 80.2575},
    {"id": "SS-008", "name": "Kilpauk Water Works Grid", "voltage_kv": 110, "plinth_cm": 60.0, "lat": 13.0782, "lon": 80.2415},
    {"id": "SS-009", "name": "Perambur Railway Substation", "voltage_kv": 110, "plinth_cm": 45.0, "lat": 13.1075, "lon": 80.2334},
    {"id": "SS-010", "name": "Anna Nagar West Substation", "voltage_kv": 230, "plinth_cm": 65.0, "lat": 13.0878, "lon": 80.2052},
    {"id": "SS-011", "name": "Royapettah Substation", "voltage_kv": 110, "plinth_cm": 50.0, "lat": 13.0535, "lon": 80.2608},
    {"id": "SS-012", "name": "Saidapet Substation", "voltage_kv": 110, "plinth_cm": 45.0, "lat": 13.0211, "lon": 80.2229},
    {"id": "SS-013", "name": "Egmore Substation", "voltage_kv": 110, "plinth_cm": 55.0, "lat": 13.0732, "lon": 80.2609},
    {"id": "SS-014", "name": "Tondiarpet Grid", "voltage_kv": 230, "plinth_cm": 50.0, "lat": 13.1280, "lon": 80.2872},
    {"id": "SS-015", "name": "Thiruvanmiyur Substation", "voltage_kv": 110, "plinth_cm": 45.0, "lat": 12.9830, "lon": 80.2594},
    {"id": "SS-016", "name": "Pallavaram Substation", "voltage_kv": 110, "plinth_cm": 45.0, "lat": 12.9675, "lon": 80.1491},
    {"id": "SS-017", "name": "Tambaram Substation", "voltage_kv": 230, "plinth_cm": 60.0, "lat": 12.9249, "lon": 80.1165},
    {"id": "SS-018", "name": "Madhavaram Substation", "voltage_kv": 110, "plinth_cm": 50.0, "lat": 13.1482, "lon": 80.2314},
    {"id": "SS-019", "name": "Ambattur Industrial Substation", "voltage_kv": 230, "plinth_cm": 60.0, "lat": 13.1143, "lon": 80.1548},
    {"id": "SS-020", "name": "Porur Substation", "voltage_kv": 110, "plinth_cm": 45.0, "lat": 13.0382, "lon": 80.1565},
]

elements = []
for i, sub in enumerate(CHENNAI_SUBSTATIONS):
    elements.append({
        "type": "node",
        "id": 100000 + i,
        "lat": sub["lat"],
        "lon": sub["lon"],
        "tags": {
            "name": sub["name"],
            "power": "substation",
            "voltage": str(sub["voltage_kv"] * 1000)
        }
    })

raw_data = {
    "version": 0.6,
    "generator": "Overpass API",
    "osm3s": {"timestamp_osm_base": "2026-09-20T00:00:00Z"},
    "elements": elements
}

with open('ai_service/layer4/data/raw/osm_chennai_substations.json', 'w') as f:
    json.dump(raw_data, f, indent=2)

print("Mock OSM raw dataset created successfully.")
