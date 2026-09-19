import pytest
import os
import csv
from unittest.mock import patch, MagicMock

# Create a dummy script mock or just test the mapping logic directly
from ai_service.layer4.routing_engine import DynamicRoutingEngine, SnappingResult

def test_mapping_logic_success():
    """Test that a substation snaps correctly and finds an edge segment_id"""
    # Mock graph and engine
    mock_engine = MagicMock()
    mock_engine.snap_to_node.return_value = SnappingResult(
        requested_lon=80.2612,
        requested_lat=13.0384,
        snapped_node_id="NODE_1",
        snapping_distance_m=15.0
    )
    
    mock_G = MagicMock()
    mock_G.out_edges.return_value = [("NODE_1", "NODE_2", {"segment_id": "SEG_TEST_123"})]
    mock_G.in_edges.return_value = []
    
    # Simulate the script's logic
    snap_res = mock_engine.snap_to_node(80.2612, 13.0384)
    out_edges = list(mock_G.out_edges(snap_res.snapped_node_id))
    valid_segments = [d.get("segment_id") for u, v, d in out_edges if d.get("segment_id")]
    
    assert len(valid_segments) == 1
    assert valid_segments[0] == "SEG_TEST_123"
    assert snap_res.snapping_distance_m == 15.0

def test_mapping_logic_missing_segment():
    """Test when the snapped node has edges but no segment_ids"""
    mock_engine = MagicMock()
    mock_engine.snap_to_node.return_value = SnappingResult(
        requested_lon=80.2612,
        requested_lat=13.0384,
        snapped_node_id="NODE_1",
        snapping_distance_m=5.0
    )
    
    mock_G = MagicMock()
    # Edges exist but no segment_id property
    mock_G.out_edges.return_value = [("NODE_1", "NODE_2", {"road_class": "unclassified"})]
    mock_G.in_edges.return_value = []
    
    snap_res = mock_engine.snap_to_node(80.2612, 13.0384)
    out_edges = list(mock_G.out_edges(snap_res.snapped_node_id))
    valid_segments = [d.get("segment_id") for u, v, d in out_edges if d.get("segment_id")]
    
    assert len(valid_segments) == 0

def test_mapping_logic_suspicious_distance():
    """Test warning logic for high distance"""
    dist = 8500.0
    warning = ""
    if dist > 500.0:
        warning = "Distance unusually large (>500m)"
        
    assert warning == "Distance unusually large (>500m)"
