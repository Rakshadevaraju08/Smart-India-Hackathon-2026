from pathlib import Path
from typing import Dict, Any, Tuple
from typing import Optional
import geopandas as gpd
import json
import logging
import networkx as nx
import os
import osmnx as ox
import pandas as pd
import pickle
import re


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Chennai UTM Zone 44N
TARGET_CRS = "EPSG:32644"

# Fallback speeds in km/h tailored for Chennai urban conditions
SPEED_FALLBACKS = {
    'motorway': 60,
    'motorway_link': 40,
    'trunk': 50,
    'trunk_link': 40,
    'primary': 40,
    'primary_link': 30,
    'secondary': 30,
    'secondary_link': 25,
    'tertiary': 25,
    'tertiary_link': 20,
    'residential': 15,
    'unclassified': 15,
    'living_street': 10,
    'service': 10,
    'road': 15,
    'default': 15
}

def parse_maxspeed(speed_str: Any) -> float:
    """Safely parse OSM maxspeed tag to float km/h."""
    if isinstance(speed_str, list):
        # Taking the first maxspeed if it's a list (e.g., ['40', '30'])
        speed_str = speed_str[0]
        
    try:
        if pd.isna(speed_str) or not speed_str:
            return None
    except ValueError:
        pass
        
    if isinstance(speed_str, (int, float)):
        return float(speed_str)
        
    speed_str = str(speed_str).lower().strip()
    # Extract leading numbers
    match = re.match(r'^(\d+(?:\.\d+)?)', speed_str)
    if match:
        val = float(match.group(1))
        # Convert mph to kmh if 'mph' is present
        if 'mph' in speed_str:
            val *= 1.60934
        return val
    return None

def normalize_road_network(graph_path: str, output_path: str) -> Dict[str, Any]:
    """
    Normalizes a raw OSM graph into the Layer 4 routing schema.
    """
    logger.info(f"Loading raw OSM graph from {graph_path}")
    
    # Load raw graph
    if not os.path.exists(graph_path):
        raise FileNotFoundError(f"Raw OSM graph not found at {graph_path}. Please acquire step 1 data first.")
        
    G = ox.load_graphml(graph_path)
    nodes, edges = ox.graph_to_gdfs(G)
    
    logger.info(f"Loaded {len(nodes)} nodes and {len(edges)} edges.")
    
    # Reproject edges to metric CRS to accurately calculate lengths
    logger.info(f"Reprojecting edges to {TARGET_CRS} for accurate length_m calculation")
    edges_proj = edges.to_crs(TARGET_CRS)
    
    # Create normalized dataframe
    records = []
    
    # Ensure deterministic iteration by sorting multi-index (u, v, key)
    sorted_edge_indices = sorted(edges_proj.index.tolist())
    
    stats = {
        'total_segments': 0,
        'missing_speed_used_fallback': 0,
        'underpasses_marked': 0
    }
    
    for i, (u, v, key) in enumerate(sorted_edge_indices):
        edge = edges_proj.loc[(u, v, key)]
        
        # 1. Deterministic ID
        segment_id = f"CHN_SEG_{i+1:05d}"
        
        # 2. Geometry
        geom = edge.geometry
        
        # 3. Length (Metric from Projected CRS)
        length_m = geom.length
        
        # 4. Road Class
        hw = edge.get('highway', 'unclassified')
        if isinstance(hw, list):
            hw = hw[0]
        road_class = str(hw)
        
        # 5. Free Flow Speed (km/h)
        maxspeed_tag = edge.get('maxspeed', None)
        parsed_speed = parse_maxspeed(maxspeed_tag)
        is_fallback = False
        
        if parsed_speed is not None and parsed_speed > 0:
            free_flow_speed = parsed_speed
        else:
            free_flow_speed = SPEED_FALLBACKS.get(road_class, SPEED_FALLBACKS['default'])
            is_fallback = True
            stats['missing_speed_used_fallback'] += 1
            
        # 6. Underpass Detection
        is_underpass = False
        tunnel = str(edge.get('tunnel', '')).lower()
        bridge = str(edge.get('bridge', '')).lower()
        layer = str(edge.get('layer', '0'))
        
        # Check layer < 0 safely
        layer_val = 0
        try:
            if isinstance(edge.get('layer'), list):
                layer_val = int(edge.get('layer')[0])
            else:
                layer_val = int(layer)
        except ValueError:
            pass
            
        # A road dipping down in a tunnel or negative layer (not a bridge) is an underpass
        if (tunnel in ['yes', 'building_passage'] or layer_val < 0) and bridge not in ['yes', 'viaduct']:
            is_underpass = True
            stats['underpasses_marked'] += 1
            
        # Preserve original useful tags for traceability
        orig_osmid = edge.get('osmid', '')
        if isinstance(orig_osmid, list):
            orig_osmid = ','.join(map(str, orig_osmid))
            
        orig_name = edge.get('name', '')
        if isinstance(orig_name, list):
            orig_name = orig_name[0]
            
        records.append({
            'segment_id': segment_id,
            'geometry': geom,
            'length_m': float(length_m),
            'road_class': road_class,
            'free_flow_speed': float(free_flow_speed),
            'is_underpass': is_underpass,
            # Metadata / Traceability
            'osm_u': u,
            'osm_v': v,
            'osm_key': key,
            'osm_id': orig_osmid,
            'osm_name': orig_name,
            'is_speed_fallback': is_fallback
        })
        stats['total_segments'] += 1
        
    # Convert to GeoDataFrame (using original EPSG:4326 for final export, as is standard for web maps)
    # The length_m is already calculated from the EPSG:32644 projection
    normalized_gdf = gpd.GeoDataFrame(records, geometry='geometry', crs=TARGET_CRS)
    normalized_gdf = normalized_gdf.to_crs("EPSG:4326")
    
    # Save output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # GeoJSON doesn't support tuples/lists well, so we stringify lists if any slipped through
    for col in normalized_gdf.columns:
        if normalized_gdf[col].dtype == object:
            normalized_gdf[col] = normalized_gdf[col].astype(str)
            
    normalized_gdf.to_file(output_path, driver="GeoJSON")
    logger.info(f"Saved normalized graph with {stats['total_segments']} segments to {output_path}")
    
    return stats

def download_raw_osm(output_path: str):
    """
    Step 1: Download raw OSM graph (since it wasn't saved in previous step).
    10x10 km Adyar/Velachery AOI.
    """
    logger.info("Downloading raw OSM graph (Adyar/Velachery 10x10km AOI)...")
    north, south = 13.0534, 12.9626
    east, west = 80.2833, 80.1908
    # In OSMnx >= 2.0, bbox is (left, bottom, right, top) == (west, south, east, north)
    G = ox.graph_from_bbox(bbox=(west, south, east, north), network_type='drive', simplify=False)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    ox.save_graphml(G, output_path)
    logger.info(f"Saved raw graphml to {output_path}")

if __name__ == "__main__":
    raw_path = "ai_service/layer4/data/raw_osm_graph.graphml"
    norm_path = "ai_service/layer4/data/normalized_road_network.geojson"
    
    if not os.path.exists(raw_path):
        download_raw_osm(raw_path)
        
    stats = normalize_road_network(raw_path, norm_path)
    print("\\n=== Normalization Report ===")
    print(f"Total Segments: {stats['total_segments']}")
    print(f"Speed Fallbacks Used: {stats['missing_speed_used_fallback']}")
    print(f"Underpasses Marked: {stats['underpasses_marked']}")

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

class DuplicateSegmentIDError(Exception):
    pass

class SegmentNotFoundError(Exception):
    pass

class SegmentLookup:
    """
    Provides deterministic and efficient O(1) lookups for graph edges using their segment_id.
    Ensures that segment IDs are unique and mapped correctly to their NetworkX MultiDiGraph (u, v, k) keys.
    """
    def __init__(self, G: nx.MultiDiGraph):
        if not isinstance(G, nx.MultiDiGraph):
            raise TypeError("Expected a networkx MultiDiGraph")
            
        self.G = G
        self.index = {}
        self._build_index()

    def _build_index(self):
        for u, v, k, data in self.G.edges(keys=True, data=True):
            seg_id = data.get("segment_id")
            if not seg_id:
                continue
            
            # Normalize ID for robust lookups
            norm_id = str(seg_id).strip().upper()
            
            if norm_id in self.index:
                raise DuplicateSegmentIDError(f"Duplicate segment ID detected during index construction: {norm_id}")
                
            self.index[norm_id] = (u, v, k)
            
    def get_segment(self, segment_id: str) -> dict:
        """
        Retrieves the edge information associated with a given segment ID.
        Fails clearly if the segment is not found.
        """
        if not segment_id:
            raise ValueError("Segment ID cannot be empty.")
            
        norm_id = str(segment_id).strip().upper()
        
        if norm_id not in self.index:
            raise SegmentNotFoundError(f"Segment ID not found in graph: {norm_id}")
            
        u, v, k = self.index[norm_id]
        
        data = self.G.edges[u, v, k]
        
        response = {
            "source_node": u,
            "destination_node": v,
            "edge_key": k,
        }
        # Merge edge data into response
        response.update(data)
        
        return response

if __name__ == "__main__":
    import os
    
    base_dir = os.path.dirname(__file__)
    graph_path = os.path.join(base_dir, "data", "routing_graph.pkl")
    
    if os.path.exists(graph_path):
        print(f"Loading graph from {graph_path}...")
        with open(graph_path, "rb") as f:
            G = pickle.load(f)
            
        print("Building segment index...")
        lookup = SegmentLookup(G)
        print(f"Index built successfully. Indexed {len(lookup.index)} segments.")
        
        # Example lookups
        sample_keys = list(lookup.index.keys())[:3]
        if sample_keys:
            print("\nExample lookups:")
            for k in sample_keys:
                print(f"Lookup for {k}:")
                result = lookup.get_segment(k)
                print(f" -> Source: {result['source_node']}, Dest: {result['destination_node']}, Length: {result.get('length_m')}m")
    else:
        print("Graph file not found. Run graph_builder.py first.")

def validate_graph(G: nx.MultiDiGraph) -> dict:
    """
    Strictly validates the graph according to requirements.
    """
    results = {
        "is_valid": True,
        "errors": []
    }
    
    if not isinstance(G, nx.MultiDiGraph):
        results["is_valid"] = False
        results["errors"].append("Graph is not a MultiDiGraph")
        return results
        
    if len(G.nodes) == 0:
        results["is_valid"] = False
        results["errors"].append("Graph has no nodes")
        
    if len(G.edges) == 0:
        results["is_valid"] = False
        results["errors"].append("Graph has no edges")
        
    segment_ids = set()
    
    for u, v, k, data in G.edges(keys=True, data=True):
        if u not in G.nodes or v not in G.nodes:
            results["is_valid"] = False
            results["errors"].append(f"Edge {u}-{v} has missing endpoints")
            
        required_attrs = ["segment_id", "length_m", "road_class", "free_flow_speed", "is_underpass", "geometry"]
        for attr in required_attrs:
            if attr not in data:
                results["is_valid"] = False
                results["errors"].append(f"Edge {u}-{v} missing required attribute '{attr}'")
                
        seg_id = data.get("segment_id")
        if seg_id is not None:
            if seg_id in segment_ids:
                results["is_valid"] = False
                results["errors"].append(f"Duplicate segment_id {seg_id} found in edge {u}-{v}")
            segment_ids.add(seg_id)
        
        geom = data.get("geometry")
        if not isinstance(geom, dict) or "coordinates" not in geom or len(geom["coordinates"]) < 2:
            results["is_valid"] = False
            results["errors"].append(f"Invalid geometry on edge {u}-{v}")
            
        length = data.get("length_m", -1)
        if length <= 0:
            results["is_valid"] = False
            results["errors"].append(f"Non-positive length {length} on edge {u}-{v}")
            
        speed = data.get("free_flow_speed", -1)
        if speed <= 0:
            results["is_valid"] = False
            results["errors"].append(f"Invalid speed {speed} on edge {u}-{v}")
            
    return results

def build_graph(nodes_geojson: str, edges_geojson: str, output_path: str):
    G = nx.MultiDiGraph()
    
    with open(nodes_geojson, "r", encoding="utf-8") as f:
        nodes_data = json.load(f)
        
    osm_to_routing = {}
    
    for feature in nodes_data.get("features", []):
        props = feature["properties"]
        geom = feature["geometry"]
        
        routing_id = props["routing_node_id"]
        osm_id = props["osm_node_id"]
        
        osm_to_routing[osm_id] = routing_id
        
        G.add_node(
            routing_id,
            osm_node_id=osm_id,
            is_junction=props["is_junction"],
            coordinates=geom["coordinates"]
        )
        
    with open(edges_geojson, "r", encoding="utf-8") as f:
        edges_data = json.load(f)
        
    for feature in edges_data.get("features", []):
        props = feature["properties"]
        geom = feature["geometry"]
        
        osm_u = props["osm_u"]
        osm_v = props["osm_v"]
        
        u_node = osm_to_routing.get(osm_u)
        v_node = osm_to_routing.get(osm_v)
        
        if not u_node or not v_node:
            # If nodes are missing, it implies data inconsistency from steps prior, 
            # but we skip orphaned edges.
            continue
            
        G.add_edge(
            u_node,
            v_node,
            segment_id=props["segment_id"],
            length_m=props["length_m"],
            road_class=props["road_class"],
            free_flow_speed=props["free_flow_speed"],
            is_underpass=props["is_underpass"],
            geometry=geom,
            osm_id=props.get("osm_id"),
            osm_name=props.get("osm_name"),
            is_speed_fallback=props.get("is_speed_fallback")
        )
        
    validation = validate_graph(G)
    
    if validation["is_valid"]:
        
        save_graph(G, output_path)
            
    stats = {
        "nodes": len(G.nodes),
        "edges": len(G.edges),
        "unique_segments": len(set(d.get("segment_id") for u, v, k, d in G.edges(data=True, keys=True))),
        "validation_passed": validation["is_valid"],
        "validation_errors": validation["errors"],
        "graph_type": str(type(G))
    }
    return G, stats

if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    nodes_path = os.path.join(base_dir, "data", "routing_nodes.geojson")
    edges_path = os.path.join(base_dir, "data", "normalized_road_network.geojson")
    output_path = os.path.join(base_dir, "data", "routing_graph.pkl")
    
    if os.path.exists(nodes_path) and os.path.exists(edges_path):
        G, stats = build_graph(nodes_path, edges_path, output_path)
        print("Graph Build Complete.")
        print(f"Graph Type: {stats['graph_type']}")
        print(f"Total Nodes: {stats['nodes']}")
        print(f"Total Edges: {stats['edges']}")
        print(f"Unique Segments: {stats['unique_segments']}")
        print(f"Validation Passed: {stats['validation_passed']}")
        if not stats['validation_passed']:
            for err in stats['validation_errors'][:10]:
                print(f" - {err}")
            if len(stats['validation_errors']) > 10:
                print(f" ... and {len(stats['validation_errors']) - 10} more errors")
    else:
        print("Input files not found.")

def save_graph(G: nx.MultiDiGraph, path: str):
    """
    Saves the NetworkX MultiDiGraph to a binary file using pickle.
    Preserves all graph, node, and edge attributes.
    """
    if not isinstance(G, nx.MultiDiGraph):
        raise TypeError(f"Expected a NetworkX MultiDiGraph, got {type(G)}")
        
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    
    with open(path, "wb") as f:
        pickle.dump(G, f, protocol=pickle.HIGHEST_PROTOCOL)

def load_graph(path: str) -> nx.MultiDiGraph:
    """
    Loads the NetworkX MultiDiGraph from a binary pickle file.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Graph file not found at {path}")
        
    with open(path, "rb") as f:
        G = pickle.load(f)
        
    if not isinstance(G, nx.MultiDiGraph):
        raise TypeError(f"Loaded object from {path} is not a NetworkX MultiDiGraph")
        
    return G

if __name__ == "__main__":
    import argparse
    from ai_service.layer4.segment_lookup import SegmentLookup
    
    parser = argparse.ArgumentParser(description="Graph Persistence Utility")
    parser.add_argument("--load", type=str, help="Path to load the graph from")
    args = parser.parse_args()
    
    if args.load:
        print(f"Loading graph from {args.load}...")
        G = load_graph(args.load)
        print(f"Graph loaded successfully.")
        print(f"Nodes: {len(G.nodes)}")
        print(f"Edges: {len(G.edges)}")
        
        print("Rebuilding deterministic segment index...")
        lookup = SegmentLookup(G)
        print(f"Index built successfully with {len(lookup.index)} mapped segments.")

