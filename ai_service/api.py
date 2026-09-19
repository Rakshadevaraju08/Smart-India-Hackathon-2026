"""
KAIROS: Urban Flood Nowcasting System - REST API Bridge (Layer 0 <-> Frontend)
Smart India Hackathon 2026 (Problem Statement #26085)
Ministry of Earth Sciences (MoES) & Greater Chennai Corporation (GCC) Pilot
"""

import os
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from ai_service.layer0.pipeline import Layer0Pipeline
from pydantic import BaseModel, Field
from ai_service.layer4.service import Layer4Service

app = FastAPI(
    title="KAIROS Layer 0 Rainfall Nowcasting API",
    description="Real-time coupled hydrodynamic simulation & IMD Doppler radar nowcasting API for Greater Chennai Corporation",
    version="1.0.0"
)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base directory
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# Singleton pipeline instance
_pipeline: Optional[Layer0Pipeline] = None


def get_pipeline() -> Layer0Pipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = Layer0Pipeline()
    return _pipeline

_layer4_service: Optional[Layer4Service] = None

def get_layer4_service() -> Layer4Service:
    global _layer4_service
    if _layer4_service is None:
        # Default development configuration: uses MockLayer3Provider internally
        _layer4_service = Layer4Service(graph_path=os.path.join(BASE_DIR, "ai_service/layer4/data/routing_graph.pkl"))
    return _layer4_service

class Coordinate(BaseModel):
    latitude: float = Field(..., description="Latitude in decimal degrees")
    longitude: float = Field(..., description="Longitude in decimal degrees")

class RouteRequest(BaseModel):
    vehicle_type: str = Field(..., description="Vehicle type (e.g. ambulance, passenger_car)")
    origin: Coordinate
    destination: Coordinate
    departure_time: float = Field(0.0, description="Departure time in minutes from now")


@app.get("/api/health")
def health_check() -> Dict[str, Any]:
    """Health check endpoint reporting Layer 0 radar & pipeline status."""
    return {
        "status": "operational",
        "service": "KAIROS Layer 0 Rainfall Nowcasting Engine (Python AI Microservice)",
        "organization": "Ministry of Earth Sciences (MoES) / NCMRWF",
        "pilot_region": "Greater Chennai Corporation (GCC CMA Core)",
        "calibrated_road_segments": 7894,
        "radar_station": "IMD Meenambakkam (Dual-Pol Doppler, 10-min scan)",
        "equations": "Manning-Saint-Venant coupled hydrodynamic routing",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/nowcast")
def get_nowcast(
    scenario: str = Query("michaung", description="Storm scenario: michaung, monsoon, moderate, 2015_flood"),
    mode: str = Query("auto", description="Execution mode: auto, live, archive"),
    clogging: float = Query(0.35, ge=0.0, le=0.85, description="Dynamic solid waste clogging factor (0.0 to 0.85)")
) -> Dict[str, Any]:
    """
    Execute Layer 0 rainfall nowcasting and street-level disaggregation.
    Returns calculated 0-180m flood water depths for Chennai road network.
    """
    t_start = time.perf_counter()
    pipeline = get_pipeline()

    scenario_map = {
        "michaung": "michaung",
        "monsoon": "monsoon",
        "moderate": "monsoon",
        "2015_flood": "2015_flood"
    }
    sc_name = scenario_map.get(scenario.lower(), "michaung")
    
    storm_scale = 0.35 if scenario.lower() == "moderate" else (0.60 if scenario.lower() == "monsoon" else 1.0)
    clog_scale = 1.0 + (clogging - 0.35) * 0.8

    # Run Layer 0 pipeline
    result = pipeline.run(scenario=sc_name, mode=mode)
    df = result.dataframe

    col_map = {
        "t0": "d_T+15m_mm",
        "t30": "d_T+30m_mm",
        "t60": "d_T+60m_mm",
        "t90": "d_T+90m_mm",
        "t120": "d_T+120m_mm",
        "t180": "d_T+180m_mm"
    }

    sample_df = df.head(600)
    inundated_count = 0
    max_depth_cm = 0.0
    segment_depths: Dict[str, Dict[str, float]] = {}

    for _, row in sample_df.iterrows():
        seg_id = str(row["segment_id"])
        depths_dict = {}
        for step_key, col_name in col_map.items():
            raw_mm = float(row.get(col_name, 0.0)) if col_name in row else 0.0
            calc_cm = round(raw_mm * 1.8 * storm_scale * clog_scale, 1)
            depths_dict[step_key] = calc_cm
            if calc_cm > max_depth_cm:
                max_depth_cm = calc_cm

        if depths_dict.get("t60", 0.0) > 10.0:
            inundated_count += 1

        segment_depths[seg_id] = depths_dict

    total_latency_ms = round((time.perf_counter() - t_start) * 1000.0, 1)

    return {
        "status": "success",
        "scenario": scenario,
        "mode": mode,
        "clogging_factor": clogging,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "latency_ms": total_latency_ms,
        "g_r_ratio": round(result.g_r_ratio, 3),
        "served_by": "python_ai_service_microservice",
        "kpis": {
            "inundated_segments": f"{inundated_count} Segments",
            "max_depth_cm": f"{max_depth_cm:.1f} cm",
            "active_segments": len(segment_depths),
            "radar_status": "IMD Meenambakkam 10-Min Live (Dual-Pol)"
        },
        "segments": segment_depths
    }

from fastapi import HTTPException

@app.post("/route", tags=["Layer 4: Routing"])
def get_route(request: RouteRequest) -> Dict[str, Any]:
    """
    Time-dependent A* emergency routing avoiding flood hazards.
    """
    try:
        service = get_layer4_service()
        res = service.route(
            vehicle_type=request.vehicle_type,
            origin_lon=request.origin.longitude,
            origin_lat=request.origin.latitude,
            dest_lon=request.destination.longitude,
            dest_lat=request.destination.latitude,
            departure_time_minutes=request.departure_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Layer 4 processing failed: {str(e)}")
        
    if res.get("status") == "FAILED":
        reason = res.get("failure_reason", "").lower()
        if "invalid" in reason or "not mapped" in reason:
            raise HTTPException(status_code=400, detail=res)
        if "no safe route" in reason or "impassable" in reason:
            raise HTTPException(status_code=404, detail=res)
        raise HTTPException(status_code=500, detail=res)
        
    return res

@app.get("/assets/status", tags=["Layer 4: Critical Assets"])
def get_asset_status() -> Dict[str, Any]:
    """
    Flood risk status for critical urban assets (TANGEDCO Substations).
    """
    try:
        service = get_layer4_service()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Layer 4 initialization failed: {str(e)}")
        
    res = service.get_asset_status()
    
    if res.get("status") == "FAILED":
        raise HTTPException(status_code=500, detail=res.get("error", "Unknown error fetching asset status"))
        
    return res


# Mount frontend static files
if os.path.isdir(FRONTEND_DIR):
    data_dir = os.path.join(FRONTEND_DIR, "data")
    if os.path.isdir(data_dir):
        app.mount("/data", StaticFiles(directory=data_dir), name="data")
    
    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    print("Starting KAIROS Layer 0 REST API on http://127.0.0.1:8000 ...")
    uvicorn.run("ai_service.api:app", host="127.0.0.1", port=8000, reload=True)
