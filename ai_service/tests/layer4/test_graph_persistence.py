import pytest
import os
import networkx as nx
from ai_service.layer4.graph_persistence import save_graph, load_graph
from ai_service.layer4.segment_lookup import SegmentLookup

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
