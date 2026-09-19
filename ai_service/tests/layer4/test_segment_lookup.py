import pytest
import networkx as nx
import pickle
import os
from ai_service.layer4.segment_lookup import SegmentLookup, DuplicateSegmentIDError, SegmentNotFoundError

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
