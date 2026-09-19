import pytest
import os
import json
import networkx as nx
from ai_service.layer4.graph_persistence import load_graph
from ai_service.layer4.segment_lookup import SegmentLookup, SegmentNotFoundError, DuplicateSegmentIDError

@pytest.fixture(scope="module")
def paths():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return {
        "graph": os.path.join(base_dir, "layer4", "data", "routing_graph.pkl"),
        "normalized": os.path.join(base_dir, "layer4", "data", "normalized_road_network.geojson"),
        "nodes": os.path.join(base_dir, "layer4", "data", "routing_nodes.geojson")
    }

@pytest.fixture(scope="module")
def graph_data(paths):
    if not os.path.exists(paths["graph"]):
        pytest.skip("Live graph data not found. Run Part 1 generation first.")
    return load_graph(paths["graph"])

@pytest.fixture(scope="module")
def normalized_data(paths):
    if not os.path.exists(paths["normalized"]):
        pytest.skip("Normalized GeoJSON not found.")
    with open(paths["normalized"], "r", encoding="utf-8") as f:
        return json.load(f)

# --- Data Acquisition & Persistence ---

def test_data_acquisition_and_persistence(graph_data):
    # graph can be loaded
    assert graph_data is not None
    assert isinstance(graph_data, nx.MultiDiGraph)

def test_persistence_logic(graph_data, tmp_path):
    from ai_service.layer4.graph_persistence import save_graph, load_graph
    
    path = tmp_path / "test_persist.pkl"
    save_graph(graph_data, str(path))
    reloaded = load_graph(str(path))
    
    assert len(reloaded.nodes) == len(graph_data.nodes)
    assert len(reloaded.edges) == len(graph_data.edges)

# --- Road Segments Validation ---

def test_road_segments(normalized_data):
    features = normalized_data.get("features", [])
    assert len(features) > 0
    
    segment_ids = set()
    for feature in features:
        props = feature["properties"]
        geom = feature["geometry"]
        
        # segment IDs exist and are unique
        seg_id = props.get("segment_id")
        assert seg_id is not None
        assert seg_id not in segment_ids
        segment_ids.add(seg_id)
        
        # geometry exists and valid
        assert geom is not None
        assert geom.get("type") == "LineString"
        assert len(geom.get("coordinates", [])) >= 2
        
        # length_m exists and positive
        assert props.get("length_m", -1) > 0
        
        # road_class exists
        assert "road_class" in props
        
        # free_flow_speed exists and valid
        assert props.get("free_flow_speed", -1) > 0
        
        # is_underpass exists
        assert "is_underpass" in props

# --- Graph and Junction Topology Validation ---

def test_junction_topology_and_graph(graph_data):
    # graph contains nodes and edges
    assert len(graph_data.nodes) > 0
    assert len(graph_data.edges) > 0
    
    # edge endpoints exist
    for u, v, k, data in graph_data.edges(keys=True, data=True):
        assert u in graph_data.nodes
        assert v in graph_data.nodes
        
        # every edge has required attributes
        for attr in ["segment_id", "geometry", "length_m", "road_class", "free_flow_speed", "is_underpass"]:
            assert attr in data
            
        assert isinstance(k, int)
        
# --- Segment Lookup Validation ---

def test_segment_lookup(graph_data):
    lookup = SegmentLookup(graph_data)
    
    # Grab first segment ID to test
    first_edge = list(graph_data.edges(data=True, keys=True))[0]
    seg_id = first_edge[3]["segment_id"]
    
    # known segment ID resolves
    result = lookup.get_segment(seg_id)
    assert result["segment_id"] == seg_id
    assert result["source_node"] == first_edge[0]
    assert result["destination_node"] == first_edge[1]
    
    # unknown segment ID fails correctly
    with pytest.raises(SegmentNotFoundError):
        lookup.get_segment("INVALID_SEGMENT_ID_123")

def test_connectivity_diagnostics(graph_data):
    # Diagnostics - we just run the functions to ensure they don't crash
    # and print to stdout for report gathering.
    components = list(nx.weakly_connected_components(graph_data))
    num_components = len(components)
    
    sizes = [len(c) for c in components]
    largest_size = max(sizes) if sizes else 0
    
    small_components = [s for s in sizes if s < 10]
    
    print("\n[DIAGNOSTICS]")
    print(f"Total Nodes: {len(graph_data.nodes)}")
    print(f"Total Edges: {len(graph_data.edges)}")
    print(f"Weakly Connected Components: {num_components}")
    print(f"Largest Component Size: {largest_size}")
    print(f"Isolated/Small Components (<10 nodes): {len(small_components)}")
    print("[/DIAGNOSTICS]")
