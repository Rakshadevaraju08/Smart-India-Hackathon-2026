from ai_service.layer4.road_graph import SegmentLookup
from ai_service.layer4.road_graph import SegmentLookup, DuplicateSegmentIDError, SegmentNotFoundError
from ai_service.layer4.road_graph import SegmentLookup, SegmentNotFoundError, DuplicateSegmentIDError
from ai_service.layer4.road_graph import build_graph, validate_graph
from ai_service.layer4.road_graph import extract_routing_nodes
from ai_service.layer4.road_graph import load_graph
from ai_service.layer4.road_graph import parse_maxspeed, SPEED_FALLBACKS
from ai_service.layer4.road_graph import save_graph, load_graph
from shapely.geometry import LineString
import geopandas as gpd
import json
import networkx as nx
import os
import pickle
import pytest


def test_parse_maxspeed():
    # Valid numeric
    assert parse_maxspeed("40") == 40.0
    assert parse_maxspeed(30) == 30.0
    assert parse_maxspeed("50.5") == 50.5
    
    # Valid string with units
    assert parse_maxspeed("60 km/h") == 60.0
    assert parse_maxspeed("40 mph") == 40.0 * 1.60934
    
    # Lists
    assert parse_maxspeed(["40", "30"]) == 40.0
    
    # Invalid/Missing
    assert parse_maxspeed("none") is None
    assert parse_maxspeed(None) is None
    assert parse_maxspeed("") is None
    assert parse_maxspeed("signals") is None

def test_fallback_speeds_defined():
    # Ensure all basic road classes have a fallback
    assert 'primary' in SPEED_FALLBACKS
    assert 'residential' in SPEED_FALLBACKS
    assert SPEED_FALLBACKS['residential'] == 15
    assert SPEED_FALLBACKS['primary'] == 40

@pytest.fixture
def sample_geojson(tmp_path):
    # Mock data:
    # Segment 1: Connects node 100 to 200 (Ground level)
    # Segment 2: Connects node 200 to 300 (Ground level)
    # Segment 3: Connects node 400 to 500 (Bridge that visually crosses over seg 1 but does not intersect topologically)
    data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[0.0, 0.0], [0.5, 0.5], [1.0, 1.0]]
                },
                "properties": {
                    "segment_id": "seg_1",
                    "osm_u": 100,
                    "osm_v": 200
                }
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[1.0, 1.0], [2.0, 2.0]]
                },
                "properties": {
                    "segment_id": "seg_2",
                    "osm_u": 200,
                    "osm_v": 300
                }
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[0.0, 1.0], [0.5, 0.5], [1.0, 0.0]]
                },
                "properties": {
                    "segment_id": "seg_3",
                    "osm_u": 400,
                    "osm_v": 500
                }
            }
        ]
    }
    input_file = tmp_path / "input.geojson"
    with open(input_file, "w") as f:
        json.dump(data, f)
    return str(input_file)

def test_extract_routing_nodes(sample_geojson, tmp_path):
    output_file = tmp_path / "output.geojson"
    stats = extract_routing_nodes(sample_geojson, str(output_file))
    
    assert os.path.exists(output_file)
    with open(output_file, "r") as f:
        out_data = json.load(f)
        
    features = out_data["features"]
    
    # Expected Nodes: 100, 200, 300, 400, 500 -> 5 total nodes
    assert stats["total_nodes"] == 5
    # Node 200 is a junction (connected to seg_1 and seg_2)
    assert stats["junctions"] == 1
    # 100, 300, 400, 500 are endpoints
    assert stats["endpoints"] == 4
    
    # Check node 200 (True Intersection)
    node_200 = next(f for f in features if f["properties"]["osm_node_id"] == 200)
    assert node_200["properties"]["is_junction"] is True
    assert set(node_200["properties"]["connected_segments"]) == {"seg_1", "seg_2"}
    assert node_200["geometry"]["coordinates"] == [1.0, 1.0]
    
    # Check node 400 (bridge endpoint)
    node_400 = next(f for f in features if f["properties"]["osm_node_id"] == 400)
    assert node_400["properties"]["is_junction"] is False
    assert node_400["properties"]["connected_segments"] == ["seg_3"]
    
    # Note that seg_3 and seg_1 "cross" visually at [0.5, 0.5] in their LineStrings,
    # but because they don't share an osm node (they use 400->500 and 100->200),
    # no false junction is generated at [0.5, 0.5].
    
    # Verify deterministic naming
    # 100 -> CHN_NODE_00000
    # 200 -> CHN_NODE_00001
    assert node_200["properties"]["routing_node_id"] == "CHN_NODE_00001"

@pytest.fixture
def sample_multidigraph():
    G = nx.MultiDiGraph()
    G.add_node("N1")
    G.add_node("N2")
    
    # Adding multiple edges between the same nodes
    G.add_edge("N1", "N2", key=0, segment_id="CHN_SEG_001", length_m=10.0, road_class="primary")
    G.add_edge("N1", "N2", key=1, segment_id="CHN_SEG_002", length_m=15.0, road_class="secondary")
    
    # Another node
    G.add_node("N3")
    G.add_edge("N2", "N3", key=0, segment_id="CHN_SEG_003", length_m=5.0)
    
    return G

def test_valid_lookup(sample_multidigraph):
    lookup = SegmentLookup(sample_multidigraph)
    
    data = lookup.get_segment("CHN_SEG_001")
    assert data["source_node"] == "N1"
    assert data["destination_node"] == "N2"
    assert data["edge_key"] == 0
    assert data["segment_id"] == "CHN_SEG_001"
    assert data["length_m"] == 10.0

def test_lookup_normalization(sample_multidigraph):
    lookup = SegmentLookup(sample_multidigraph)
    
    # Test lowercase and padding
    data = lookup.get_segment(" chn_seg_002 ")
    assert data["segment_id"] == "CHN_SEG_002"
    assert data["length_m"] == 15.0
    assert data["edge_key"] == 1

def test_invalid_lookup(sample_multidigraph):
    lookup = SegmentLookup(sample_multidigraph)
    
    with pytest.raises(SegmentNotFoundError, match="Segment ID not found"):
        lookup.get_segment("UNKNOWN_SEG_999")
        
def test_empty_lookup(sample_multidigraph):
    lookup = SegmentLookup(sample_multidigraph)
    
    with pytest.raises(ValueError, match="cannot be empty"):
        lookup.get_segment("")

def test_duplicate_segment_id_detection():
    G = nx.MultiDiGraph()
    G.add_node("A")
    G.add_node("B")
    G.add_node("C")
    
    G.add_edge("A", "B", key=0, segment_id="DUP_SEG")
    G.add_edge("B", "C", key=0, segment_id="dup_seg") # Case insensitive duplicate
    
    with pytest.raises(DuplicateSegmentIDError, match="Duplicate segment ID detected"):
        SegmentLookup(G)

def test_persistence_reload(sample_multidigraph, tmp_path):
    # Save to pickle
    filepath = tmp_path / "test_graph.pkl"
    with open(filepath, "wb") as f:
        pickle.dump(sample_multidigraph, f)
        
    # Reload and test lookup still functions perfectly
    with open(filepath, "rb") as f:
        loaded_G = pickle.load(f)
        
    lookup = SegmentLookup(loaded_G)
    data = lookup.get_segment("CHN_SEG_003")
    assert data["source_node"] == "N2"
    assert data["destination_node"] == "N3"
    assert data["length_m"] == 5.0

@pytest.fixture
def sample_data(tmp_path):
    nodes = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
                "properties": {"routing_node_id": "N1", "osm_node_id": 1, "is_junction": True}
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [1.0, 1.0]},
                "properties": {"routing_node_id": "N2", "osm_node_id": 2, "is_junction": True}
            }
        ]
    }
    
    edges = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]},
                "properties": {
                    "segment_id": "S1",
                    "osm_u": 1,
                    "osm_v": 2,
                    "length_m": 10.0,
                    "road_class": "primary",
                    "free_flow_speed": 40.0,
                    "is_underpass": False
                }
            }
        ]
    }
    
    nodes_file = tmp_path / "nodes.geojson"
    edges_file = tmp_path / "edges.geojson"
    out_file = tmp_path / "out.pkl"
    
    with open(nodes_file, "w") as f:
        json.dump(nodes, f)
    with open(edges_file, "w") as f:
        json.dump(edges, f)
        
    return str(nodes_file), str(edges_file), str(out_file)


def test_build_and_validate(sample_data):
    nodes_file, edges_file, out_file = sample_data
    
    G, stats = build_graph(nodes_file, edges_file, out_file)
    
    assert stats["validation_passed"] is True
    assert stats["nodes"] == 2
    assert stats["edges"] == 1
    assert stats["unique_segments"] == 1
    
    assert os.path.exists(out_file)
    
def test_validate_graph_failures():
    G = nx.MultiDiGraph()
    G.add_node("N1")
    G.add_node("N2")
    # Add an edge with missing required attributes (like length_m, geometry)
    G.add_edge("N1", "N2", segment_id="S1") 
    
    val = validate_graph(G)
    assert val["is_valid"] is False
    assert any("missing required attribute" in e for e in val["errors"])

def test_validate_duplicate_segments():
    G = nx.MultiDiGraph()
    G.add_node("N1")
    G.add_node("N2")
    
    valid_attrs = {
        "segment_id": "S1",
        "length_m": 10.0,
        "road_class": "primary",
        "free_flow_speed": 40.0,
        "is_underpass": False,
        "geometry": {"type": "LineString", "coordinates": [[0,0], [1,1]]}
    }
    
    G.add_edge("N1", "N2", **valid_attrs)
    # Add the exact same segment_id again
    G.add_edge("N2", "N1", **valid_attrs)
    
    val = validate_graph(G)
    assert val["is_valid"] is False
    assert any("Duplicate segment_id" in e for e in val["errors"])

@pytest.fixture
def mock_graph():
    G = nx.MultiDiGraph()
    G.add_node("N1", attr1="foo")
    G.add_node("N2", attr1="bar")
    
    # Adding a fully populated edge
    G.add_edge("N1", "N2", key=0, segment_id="CHN_SEG_123", length_m=10.5, road_class="primary", free_flow_speed=40.0, is_underpass=False, geometry={"type": "LineString", "coordinates": [[0,0], [1,1]]})
    
    # Second edge for multidigraph testing
    G.add_edge("N1", "N2", key=1, segment_id="CHN_SEG_124", length_m=12.0)
    
    return G
    
def test_graph_persistence(mock_graph, tmp_path):
    filepath = tmp_path / "test_graph.pkl"
    
    # 1. Graph saves successfully
    save_graph(mock_graph, str(filepath))
    assert os.path.exists(filepath)
    
    # 2. Graph loads successfully
    loaded_G = load_graph(str(filepath))
    
    # 3. Node count remains the same
    assert len(loaded_G.nodes) == len(mock_graph.nodes) == 2
    
    # 4. Edge count remains the same
    assert len(loaded_G.edges) == len(mock_graph.edges) == 2
    
    # 5. Segment IDs and Edge attributes remain the same
    edge_data_0 = loaded_G.edges["N1", "N2", 0]
    assert edge_data_0["segment_id"] == "CHN_SEG_123"
    assert edge_data_0["length_m"] == 10.5
    assert edge_data_0["road_class"] == "primary"
    
    edge_data_1 = loaded_G.edges["N1", "N2", 1]
    assert edge_data_1["segment_id"] == "CHN_SEG_124"
    assert edge_data_1["length_m"] == 12.0
    
    # 6. Segment lookup still works after reload
    lookup = SegmentLookup(loaded_G)
    seg_lookup = lookup.get_segment("CHN_SEG_123")
    assert seg_lookup["source_node"] == "N1"
    assert seg_lookup["edge_key"] == 0
    assert seg_lookup["length_m"] == 10.5

def test_load_graph_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_graph(str(tmp_path / "does_not_exist.pkl"))
        
def test_save_graph_invalid_type(tmp_path):
    # Pass a standard DiGraph instead of MultiDiGraph
    G = nx.DiGraph()
    with pytest.raises(TypeError):
        save_graph(G, str(tmp_path / "invalid.pkl"))

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
    from ai_service.layer4.road_graph import save_graph, load_graph
    
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

