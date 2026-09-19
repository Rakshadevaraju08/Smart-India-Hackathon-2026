import os
import json
import pytest
from ai_service.layer4.junction_detector import extract_routing_nodes

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
