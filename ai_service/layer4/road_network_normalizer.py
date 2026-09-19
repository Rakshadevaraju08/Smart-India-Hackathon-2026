import logging
import os
import re
from pathlib import Path
from typing import Dict, Any, Tuple

import geopandas as gpd
import networkx as nx
import osmnx as ox
import pandas as pd

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
