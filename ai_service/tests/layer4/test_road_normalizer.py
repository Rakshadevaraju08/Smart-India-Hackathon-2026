import pytest
import geopandas as gpd
from shapely.geometry import LineString
from ai_service.layer4.road_network_normalizer import parse_maxspeed, SPEED_FALLBACKS

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
