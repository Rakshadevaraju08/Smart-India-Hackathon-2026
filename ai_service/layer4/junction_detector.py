import json
import os

def extract_routing_nodes(input_geojson: str, output_geojson: str, tolerance: float = 1e-6):
    """
    Reads normalized road network, extracts physical junctions based on osm_u/osm_v nodes,
    and maps connected segments to these routing nodes.
    Outputs a GeoJSON FeatureCollection of Point geometries representing the nodes.
    """
    with open(input_geojson, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Group segments by their osm_node
    # node_id -> { "coordinates": (lon, lat), "segments": set(segment_ids) }
    nodes = {}

    for feature in data.get("features", []):
        props = feature["properties"]
        geom = feature["geometry"]
        segment_id = props["segment_id"]
        osm_u = props["osm_u"]
        osm_v = props["osm_v"]
        
        # Validate geometry
        if geom["type"] != "LineString" or len(geom["coordinates"]) < 2:
            continue
            
        start_coord = tuple(geom["coordinates"][0])
        end_coord = tuple(geom["coordinates"][-1])
        
        # Process u node
        if osm_u not in nodes:
            nodes[osm_u] = {"coordinates": start_coord, "segments": set()}
        else:
            # Tolerance sanity check (optional, to verify data consistency)
            existing_coord = nodes[osm_u]["coordinates"]
            if abs(existing_coord[0] - start_coord[0]) > tolerance or abs(existing_coord[1] - start_coord[1]) > tolerance:
                # Usually coordinates from OSM are exact, but floats can drift slightly.
                pass 

        nodes[osm_u]["segments"].add(segment_id)
        
        # Process v node
        if osm_v not in nodes:
            nodes[osm_v] = {"coordinates": end_coord, "segments": set()}
        else:
            existing_coord = nodes[osm_v]["coordinates"]
            if abs(existing_coord[0] - end_coord[0]) > tolerance or abs(existing_coord[1] - end_coord[1]) > tolerance:
                pass

        nodes[osm_v]["segments"].add(segment_id)

    # Sort nodes to generate deterministic IDs based on osm_node
    sorted_node_ids = sorted(list(nodes.keys()))
    
    out_features = []
    
    for idx, osm_node in enumerate(sorted_node_ids):
        # Generate deterministic CHN_NODE_XXXXX
        routing_node_id = f"CHN_NODE_{idx:05d}"
        
        node_data = nodes[osm_node]
        
        # Check if junction (>= 2 connected segments) or isolated endpoint (1 segment)
        is_junction = len(node_data["segments"]) > 1
        
        out_feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": list(node_data["coordinates"])
            },
            "properties": {
                "routing_node_id": routing_node_id,
                "osm_node_id": osm_node,
                "is_junction": is_junction,
                "connected_segments": sorted(list(node_data["segments"]))
            }
        }
        out_features.append(out_feature)

    out_geojson = {
        "type": "FeatureCollection",
        "features": out_features
    }

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_geojson), exist_ok=True)
    
    with open(output_geojson, "w", encoding="utf-8") as f:
        json.dump(out_geojson, f, separators=(',', ':'))

    total_nodes = len(out_features)
    junctions = sum(1 for f in out_features if f["properties"]["is_junction"])
    endpoints = total_nodes - junctions
    
    return {
        "total_nodes": total_nodes,
        "junctions": junctions,
        "endpoints": endpoints
    }

if __name__ == "__main__":
    input_path = os.path.join(os.path.dirname(__file__), "data", "normalized_road_network.geojson")
    output_path = os.path.join(os.path.dirname(__file__), "data", "routing_nodes.geojson")
    
    if os.path.exists(input_path):
        stats = extract_routing_nodes(input_path, output_path)
        print("Junction Detection Complete.")
        print(f"Total Routing Nodes: {stats['total_nodes']}")
        print(f"Physical Junctions: {stats['junctions']}")
        print(f"Isolated Endpoints: {stats['endpoints']}")
    else:
        print(f"Input file not found: {input_path}")
