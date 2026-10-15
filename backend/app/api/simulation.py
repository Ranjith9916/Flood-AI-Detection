"""
backend/app/api/simulation.py
FastAPI router for Interactive 'What-If' Inundation Simulation.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.services.simulation_service import SimulationEngine

router = APIRouter(prefix="/simulations", tags=["Simulation"])


class SimulationRequest(BaseModel):
    rainfall_intensity_mmh: float = Field(..., ge=0.0, le=500.0, description="Rainfall intensity in mm/hour")
    duration_hours: int = Field(..., ge=1, le=48, description="Rainfall duration in hours")
    antecedent_moisture_condition: str = Field(default="AMC-II", description="Soil moisture state: AMC-I, AMC-II, AMC-III")
    reservoir_discharge_cumecs: float = Field(default=0.0, ge=0.0, le=50000.0, description="Upstream reservoir outflow in m3/s")
    urban_drainage_blockage_pct: float = Field(default=0.0, ge=0.0, le=100.0, description="Percentage of urban drainage network clogged")
    center_lat: float = Field(default=13.0827, description="Latitude for simulation origin")
    center_lon: float = Field(default=80.2707, description="Longitude for simulation origin")


@router.get("/presets", status_code=status.HTTP_200_OK)
def get_simulation_presets() -> Dict[str, Any]:
    """
    Returns curated extreme weather simulation presets (Cloudburst, Cyclone, Urban Failure).
    """
    presets = SimulationEngine.get_presets()
    return {
        "status": "success",
        "count": len(presets),
        "data": presets,
    }


@router.post("/run", status_code=status.HTTP_200_OK)
def execute_simulation(req: SimulationRequest) -> Dict[str, Any]:
    """
    Executes on-demand hydrological routing and emits multi-timestep inundation extent GeoJSON contours.
    """
    try:
        result = SimulationEngine.run_simulation(
            rainfall_intensity_mmh=req.rainfall_intensity_mmh,
            duration_hours=req.duration_hours,
            antecedent_moisture_condition=req.antecedent_moisture_condition,
            reservoir_discharge_cumecs=req.reservoir_discharge_cumecs,
            urban_drainage_blockage_pct=req.urban_drainage_blockage_pct,
            center_lat=req.center_lat,
            center_lon=req.center_lon,
        )
        return {
            "status": "success",
            "data": result,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation calculation failed: {str(exc)}",
        )
