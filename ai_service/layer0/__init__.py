"""Layer 0: Flat Plane Rainfall Ingestion & Nowcasting Engine (GCC / NCMRWF 26085).

Authoritative public API for weather ingestion, real-time gauge calibration,
deterministic 0-180 minute storm motion nowcasting, and mass-conservative
street-level spatial disaggregation.
"""

from .calibrator import GaugeRadarCalibrator
from .disaggregator import (
    DEFAULT_ROAD_AREA,
    ROAD_CLASS_AREAS,
    StreetDisaggregator,
)
from .ingestion import (
    CHENNAI_AWS_STATIONS,
    DEFAULT_CHENNAI_BOUNDS,
    DEFAULT_DLAT,
    DEFAULT_DLON,
    DEFAULT_GRID_SHAPE,
    MAXZ_PALETTE_BINS,
    SRI_PALETTE_BINS,
    HistoricalArchiveLoader,
    IMDAWSIngestion,
    IMDRadarIngestion,
    RadarSweep,
    dbz_to_rain_rate,
    load_radar_sweep,
    rain_rate_to_dbz,
)
from .nowcaster import DEFAULT_HORIZONS, StormMotionNowcaster
from .pipeline import Layer0Pipeline, Layer0Result

__all__ = [
    'RadarSweep',
    'IMDRadarIngestion',
    'IMDAWSIngestion',
    'HistoricalArchiveLoader',
    'load_radar_sweep',
    'dbz_to_rain_rate',
    'rain_rate_to_dbz',
    'GaugeRadarCalibrator',
    'StormMotionNowcaster',
    'StreetDisaggregator',
    'Layer0Pipeline',
    'Layer0Result',
    'DEFAULT_CHENNAI_BOUNDS',
    'DEFAULT_GRID_SHAPE',
    'DEFAULT_HORIZONS',
    'CHENNAI_AWS_STATIONS',
    'ROAD_CLASS_AREAS',
    'DEFAULT_ROAD_AREA',
    'SRI_PALETTE_BINS',
    'MAXZ_PALETTE_BINS',
]

__version__ = '1.0.0'
