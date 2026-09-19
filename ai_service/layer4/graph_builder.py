import json
import os
import networkx as nx
import pickle

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
        from ai_service.layer4.graph_persistence import save_graph
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
