import pytest
import os
import networkx as nx
from unittest.mock import MagicMock

from ai_service.layer4.service import Layer4Service
from ai_service.layer4.layer3_mock import Layer3ProviderInterface, Layer3Result
from ai_service.layer4.routing_engine import RouteRequest

# Provide a small fake routing graph
@pytest.fixture
def small_graph():
    G = nx.MultiDiGraph()
    G.add_node(1, coordinates=[80.1, 13.1])
    G.add_node(2, coordinates=[80.2, 13.2])
    G.add_node(3, coordinates=[80.3, 13.3])
    G.add_node(4, coordinates=[80.4, 13.4])
    # 1 -> 2 -> 3
    G.add_edge(1, 2, segment_id="SEG_A", length_m=100.0, max_speed_kmh=50.0, is_underpass=False)
    G.add_edge(2, 3, segment_id="SEG_B", length_m=100.0, max_speed_kmh=50.0, is_underpass=False)
    # Disconnected node
    G.add_edge(4, 4, segment_id="SEG_C", length_m=10.0, max_speed_kmh=10.0, is_underpass=False)
    
    # KDTree mock
    from scipy.spatial import cKDTree
    coords = [[80.1, 13.1], [80.2, 13.2], [80.3, 13.3], [80.4, 13.4]]
    G.kdtree = cKDTree(coords)
    G.nodes_list = [1, 2, 3, 4]
    return G

# Implement the fake Layer3Result provider
class FakeLayer3Provider(Layer3ProviderInterface):
    def __init__(self, flood_level_cm: float = 0.0):
        self.flood_level_cm = flood_level_cm
        
    def get_predictions(self) -> Layer3Result:
        predictions = []
        for seg in ["SEG_A", "SEG_B", "SEG_C"]:
            pred = {
                "segment_id": seg,
                "depth_T+15m_cm": self.flood_level_cm,
                "depth_T+30m_cm": self.flood_level_cm,
                "depth_T+60m_cm": self.flood_level_cm,
                "depth_T+90m_cm": self.flood_level_cm,
                "depth_T+120m_cm": self.flood_level_cm,
                "depth_T+180m_cm": self.flood_level_cm,
                "is_impassable_T+15m": self.flood_level_cm > 20.0,
                "is_impassable_T+30m": self.flood_level_cm > 20.0,
                "is_impassable_T+60m": self.flood_level_cm > 20.0,
                "is_impassable_T+90m": self.flood_level_cm > 20.0,
                "is_impassable_T+120m": self.flood_level_cm > 20.0,
                "is_impassable_T+180m": self.flood_level_cm > 20.0,
            }
            predictions.append(pred)
        return Layer3Result(predictions)

def test_successful_route(small_graph):
    # 1. successful route
    # 11. preservation of route metrics
    provider = FakeLayer3Provider(flood_level_cm=0.0) # Safe
    service = Layer4Service(routing_graph=small_graph, layer3_provider=provider)
    
    # 1 -> 3
    res = service.route("ambulance", 80.1, 13.1, 80.3, 13.3)
    
    assert res["status"] == "SUCCESS"
    assert res["total_distance_m"] == 200.0
    assert "eta_min" in res
    assert res["maximum_effective_depth"] == 2.0
    assert res["maximum_hazard_ratio"] == 0.0667
    assert res["minimum_clearance"] == 28.0
    assert res["hazard_category"] == "GREEN"
    assert res["blocked_edges"] == 0
    assert res["underpasses_used"] == []
    assert res["underpasses_avoided"] == []
    assert res["ordered_node_ids"] == [1, 2, 3]

def test_blocked_route(small_graph):
    # 2. blocked route
    provider = FakeLayer3Provider(flood_level_cm=100.0) # Impassable
    service = Layer4Service(routing_graph=small_graph, layer3_provider=provider)
    
    res = service.route("ambulance", 80.1, 13.1, 80.3, 13.3)
    
    assert res["status"] == "FAILED"
    assert "no safe route found" in res["failure_reason"].lower()

def test_invalid_vehicle(small_graph):
    # 3. invalid vehicle
    service = Layer4Service(routing_graph=small_graph, layer3_provider=FakeLayer3Provider())
    # Submarine doesn't exist, will fallback or fail
    res = service.route("submarine", 80.1, 13.1, 80.3, 13.3)
    # The routing engine will just fail to find a route if costs are infinite or return standard error
    assert res["status"] == "FAILED"

def test_no_route(small_graph):
    # 6. no route
    # Try routing from 1 to 4 (disconnected)
    service = Layer4Service(routing_graph=small_graph, layer3_provider=FakeLayer3Provider())
    res = service.route("ambulance", 80.1, 13.1, 80.4, 13.4)
    assert res["status"] == "FAILED"
    assert "no safe route found" in res["failure_reason"].lower()

def test_layer3_provider_replacement(small_graph):
    # 7. Layer 3 provider replacement
    provider = FakeLayer3Provider(flood_level_cm=5.0)
    service = Layer4Service(routing_graph=small_graph, layer3_provider=provider)
    res = service.route("ambulance", 80.1, 13.1, 80.3, 13.3)
    assert res["status"] == "SUCCESS"

def test_successful_asset_status(small_graph):
    # 8. successful asset status
    # 12. preservation of substation-monitor results
    provider = FakeLayer3Provider(flood_level_cm=5.0)
    
    mock_monitor = MagicMock()
    mock_monitor.evaluate_substations.return_value = [
        MagicMock(
            substation_id="SS-1", name="Test", voltage_kv="110", latitude="13.0", longitude="80.0",
            flood_status="SAFE", maximum_effective_depth=5.0, road_segment_id="SEG_A", uncertainty_flag="", explanation="Safe"
        )
    ]
    
    service = Layer4Service(routing_graph=small_graph, layer3_provider=provider, asset_monitor=mock_monitor)
    res = service.get_asset_status()
    
    assert res["status"] == "SUCCESS"
    assert res["total_monitored"] == 1
    assert res["assets"][0]["status"] == "SAFE"
    assert res["assets"][0]["maximum_site_depth_cm"] == 5.0
    assert "SEG_A" in res["assets"][0]["supporting_road_segment_ids"]

def test_asset_data_unavailable(small_graph):
    # 9. asset data unavailable
    mock_provider = MagicMock()
    mock_provider.get_predictions.side_effect = Exception("Layer 3 API Offline")
    
    service = Layer4Service(routing_graph=small_graph, layer3_provider=mock_provider)
    res = service.get_asset_status()
    
    assert res["status"] == "FAILED"
    assert "Layer 3 API Offline" in res["error"]
