import os
import json
import pytest
import networkx as nx
from ai_service.layer4.graph_builder import build_graph, validate_graph

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
