import csv
import pickle
import os
import math
import logging
import networkx as nx

from ai_service.layer4.routing_engine import DynamicRoutingEngine, haversine_m

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("build_mapping")

CSV_PATH = 'ai_service/layer4/data/substations.csv'
GRAPH_PATH = 'ai_service/layer4/data/routing_graph.pkl'
MAPPING_REPORT_PATH = 'ai_service/layer4/data/substation_mapping.md'

def build_mapping():
    if not os.path.exists(CSV_PATH):
        logger.error(f"CSV not found at {CSV_PATH}")
        return
        
    if not os.path.exists(GRAPH_PATH):
        logger.error(f"Graph not found at {GRAPH_PATH}")
        return
        
    logger.info("Loading routing graph...")
    with open(GRAPH_PATH, 'rb') as f:
        G = pickle.load(f)
        
    engine = DynamicRoutingEngine(G)
    
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)
        
    # Ensure new columns exist
    if "road_segment_id" not in fieldnames:
        fieldnames.extend(["road_segment_id", "nearest_road_distance_m"])
        
    report_lines = [
        "# Static Substation to Layer 3 Segment Mapping Report\n",
        "| Substation ID | Name | Voltage (kV) | Lat, Lon | Mapped Segment ID | Distance (m) | Status | Warning |",
        "|---|---|---|---|---|---|---|---|"
    ]
    
    mapped_count = 0
    warnings_count = 0
    missing_segment = 0
    max_distance = 0.0
    
    for row in rows:
        sub_id = row.get("substation_id", "")
        name = row.get("name", "")
        voltage = row.get("voltage_kv", "")
        lat_str = row.get("latitude", "")
        lon_str = row.get("longitude", "")
        
        road_segment_id = ""
        distance_m = ""
        status = "Mapped"
        warning = ""
        
        try:
            lat = float(lat_str)
            lon = float(lon_str)
            
            # Snap to nearest node
            snap_res = engine.snap_to_node(lon, lat)
            node_id = snap_res.snapped_node_id
            dist = snap_res.snapping_distance_m
            
            # Find a valid segment_id from connected edges
            out_edges = list(G.out_edges(node_id, data=True))
            in_edges = list(G.in_edges(node_id, data=True))
            all_edges = out_edges + in_edges
            
            valid_segments = [d.get("segment_id") for u, v, d in all_edges if d.get("segment_id")]
            
            if valid_segments:
                road_segment_id = valid_segments[0]
                distance_m = round(dist, 2)
                max_distance = max(max_distance, dist)
                
                # Check for suspicious distance
                if dist > 500.0:
                    status = "Warning"
                    warning = f"Distance unusually large (>500m)"
                    warnings_count += 1
                else:
                    mapped_count += 1
            else:
                status = "Failed"
                warning = "Nearest node has no valid segment_id"
                missing_segment += 1
                warnings_count += 1
                
        except Exception as e:
            status = "Error"
            warning = str(e)
            missing_segment += 1
            warnings_count += 1
            
        row["road_segment_id"] = road_segment_id
        row["nearest_road_distance_m"] = str(distance_m) if distance_m != "" else ""
        
        report_lines.append(f"| {sub_id} | {name} | {voltage} | {lat_str}, {lon_str} | `{road_segment_id}` | {distance_m} | {status} | {warning} |")
        
    # Write back to CSV
    with open(CSV_PATH, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        
    # Write report
    with open(MAPPING_REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines))
        f.write("\n\n## Summary\n")
        f.write(f"- Total Substations: {len(rows)}\n")
        f.write(f"- Successfully Mapped: {mapped_count}\n")
        f.write(f"- Warnings: {warnings_count}\n")
        f.write(f"- Missing Segment ID: {missing_segment}\n")
        f.write(f"- Maximum Snapping Distance: {round(max_distance, 2)}m\n")

    logger.info("Mapping complete.")
    logger.info(f"Total: {len(rows)}, Mapped: {mapped_count}, Warnings: {warnings_count}, Missing: {missing_segment}, Max Dist: {round(max_distance, 2)}m")
    
if __name__ == "__main__":
    build_mapping()
