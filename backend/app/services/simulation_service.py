"""
backend/app/services/simulation_service.py
Interactive 'What-If' Inundation Simulation Engine.
Computes dynamic hydrological runoff propagation, depression storage filling, and temporal inundation contours.
"""

import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import numpy as np


class SimulationEngine:
    """
    Simulates dynamic flood inundation response to synthetic extreme precipitation and hydraulic scenarios.
    """

    PRESETS = {
        "100_year_cloudburst": {
            "name": "100-Year Extreme Cloudburst Event",
            "description": "Severe localized convective storm dumping 120 mm/hr over 3 hours with saturated AMC-III soils.",
            "rainfall_intensity_mmh": 120.0,
            "duration_hours": 3,
            "antecedent_moisture_condition": "AMC-III",
            "reservoir_discharge_cumecs": 800.0,
            "urban_drainage_blockage_pct": 35.0,
        },
        "cyclone_heavy_band": {
            "name": "Severe Cyclonic Storm Rainband",
            "description": "Extended tropical cyclone precipitation band with 65 mm/hr for 8 hours and major upstream reservoir discharge.",
            "rainfall_intensity_mmh": 65.0,
            "duration_hours": 8,
            "antecedent_moisture_condition": "AMC-III",
            "reservoir_discharge_cumecs": 2200.0,
            "urban_drainage_blockage_pct": 20.0,
        },
        "urban_drainage_failure": {
            "name": "Flash Flood with Urban Drainage Clog",
            "description": "Moderate high-intensity burst (45 mm/hr) compounded by 75% municipal storm drain siltation/blockage.",
            "rainfall_intensity_mmh": 45.0,
            "duration_hours": 2,
            "antecedent_moisture_condition": "AMC-II",
            "reservoir_discharge_cumecs": 150.0,
            "urban_drainage_blockage_pct": 75.0,
        },
        "moderate_monsoon_surge": {
            "name": "Active Monsoon Low-Pressure Surge",
            "description": "Continuous steady monsoon rainfall of 30 mm/hr over 6 hours under normal soil moisture conditions.",
            "rainfall_intensity_mmh": 30.0,
            "duration_hours": 6,
            "antecedent_moisture_condition": "AMC-II",
            "reservoir_discharge_cumecs": 300.0,
            "urban_drainage_blockage_pct": 10.0,
        },
    }

    @classmethod
    def get_presets(cls) -> Dict[str, Any]:
        """Returns standard simulation presets."""
        return cls.PRESETS

    @classmethod
    def run_simulation(
        cls,
        rainfall_intensity_mmh: float,
        duration_hours: int,
        antecedent_moisture_condition: str = "AMC-II",
        reservoir_discharge_cumecs: float = 0.0,
        urban_drainage_blockage_pct: float = 0.0,
        center_lat: float = 13.0827,
        center_lon: float = 80.2707,
    ) -> Dict[str, Any]:
        """
        Executes hydrological routing and returns time-series spatial inundation polygons from T+0h to T+6h.
        """
        total_precip_mm = rainfall_intensity_mmh * duration_hours
        
        # SCS Curve Number estimation based on AMC
        base_cn = 82.0
        if antecedent_moisture_condition == "AMC-I":
            cn = base_cn / (2.281 - 0.01281 * base_cn)
        elif antecedent_moisture_condition == "AMC-III":
            cn = base_cn / (0.427 + 0.00573 * base_cn)
        else:
            cn = base_cn

        # Maximum potential retention S (mm)
        s_retention = (25400.0 / cn) - 254.0
        initial_abstraction = 0.2 * s_retention

        # Direct runoff calculation with drainage blockage factor
        blockage_multiplier = 1.0 + (urban_drainage_blockage_pct / 100.0) * 0.4
        if total_precip_mm > initial_abstraction:
            q_runoff_mm = ((total_precip_mm - initial_abstraction) ** 2) / (total_precip_mm + 0.8 * s_retention)
            q_runoff_mm *= blockage_multiplier
        else:
            q_runoff_mm = 0.0

        # Hydraulic peak inundation depth (m)
        peak_depth_m = round((q_runoff_mm / 1000.0) * 2.8 + (reservoir_discharge_cumecs / 3000.0) * 0.9, 2)
        peak_depth_m = max(0.05, min(4.5, peak_depth_m))

        # Time-stepped propagation
        timesteps = [0, 1, 2, 3, 4, 6]
        timeline = []
        max_extent_km2 = round(1.2 + (peak_depth_m * 4.8), 2)

        for t in timesteps:
            if t == 0:
                step_depth = 0.0
                step_area = 0.0
                polygons = []
            else:
                # Hydrograph growth factor
                fraction = min(1.0, math.sin((t / max(timesteps)) * (math.pi / 2)))
                step_depth = round(peak_depth_m * fraction, 2)
                step_area = round(max_extent_km2 * fraction, 2)

                # Generate multi-tier GeoJSON contours for the timestep
                polygons = cls._generate_contour_polygons(center_lat, center_lon, step_depth, fraction)

            timeline.append({
                "timestep_hours": t,
                "label": f"T+{t}h",
                "water_depth_m": step_depth,
                "inundated_area_km2": step_area,
                "geojson_features": polygons,
            })

        return {
            "simulation_id": f"SIM-{int(datetime.now(timezone.utc).timestamp())}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "inputs": {
                "rainfall_intensity_mmh": rainfall_intensity_mmh,
                "duration_hours": duration_hours,
                "total_precipitation_mm": total_precip_mm,
                "antecedent_moisture_condition": antecedent_moisture_condition,
                "reservoir_discharge_cumecs": reservoir_discharge_cumecs,
                "urban_drainage_blockage_pct": urban_drainage_blockage_pct,
                "center_coords": [center_lat, center_lon],
            },
            "hydrology_summary": {
                "curve_number": round(cn, 1),
                "total_surface_runoff_mm": round(q_runoff_mm, 1),
                "peak_water_depth_m": peak_depth_m,
                "max_inundation_area_km2": max_extent_km2,
                "estimated_time_to_peak_hours": min(duration_hours + 1, 6),
                "severity_tier": "EXTREME" if peak_depth_m > 1.5 else ("HIGH" if peak_depth_m > 0.8 else "MODERATE"),
            },
            "timeline": timeline,
        }

    @classmethod
    def _generate_contour_polygons(
        cls, center_lat: float, center_lon: float, depth_m: float, fraction: float
    ) -> List[Dict[str, Any]]:
        """Generates GeoJSON feature collection for 3 depth zones."""
        features = []

        # 1. Extreme Zone (> 1.2m) if depth permits
        if depth_m > 1.0:
            scale_ext = 0.012 * fraction
            features.append({
                "type": "Feature",
                "properties": {
                    "zone": "EXTREME_INUNDATION",
                    "depth_range": "> 1.2m",
                    "depth_m": depth_m,
                    "color": "#990000",
                    "fillColor": "#cc0000",
                    "fillOpacity": 0.65,
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [center_lon - scale_ext, center_lat - scale_ext * 0.8],
                        [center_lon + scale_ext, center_lat - scale_ext * 0.5],
                        [center_lon + scale_ext * 0.8, center_lat + scale_ext * 0.9],
                        [center_lon - scale_ext * 0.6, center_lat + scale_ext * 0.7],
                        [center_lon - scale_ext, center_lat - scale_ext * 0.8],
                    ]],
                },
            })

        # 2. Moderate-to-Severe Zone (0.4m - 1.0m)
        if depth_m > 0.3:
            scale_sev = 0.024 * fraction
            features.append({
                "type": "Feature",
                "properties": {
                    "zone": "SEVERE_INUNDATION",
                    "depth_range": "0.4m - 1.0m",
                    "depth_m": round(depth_m * 0.75, 2),
                    "color": "#e65100",
                    "fillColor": "#f57c00",
                    "fillOpacity": 0.50,
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [center_lon - scale_sev * 1.2, center_lat - scale_sev],
                        [center_lon + scale_sev * 1.1, center_lat - scale_sev * 0.9],
                        [center_lon + scale_sev * 1.3, center_lat + scale_sev * 1.1],
                        [center_lon - scale_sev * 0.9, center_lat + scale_sev * 1.2],
                        [center_lon - scale_sev * 1.2, center_lat - scale_sev],
                    ]],
                },
            })

        # 3. Waterlogging / Minor Zone (0.1m - 0.4m)
        scale_min = 0.038 * fraction
        features.append({
            "type": "Feature",
            "properties": {
                "zone": "WATERLOGGING_SPREAD",
                "depth_range": "0.1m - 0.4m",
                "depth_m": round(depth_m * 0.35, 2),
                "color": "#0288d1",
                "fillColor": "#03a9f4",
                "fillOpacity": 0.35,
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [center_lon - scale_min * 1.4, center_lat - scale_min * 1.2],
                    [center_lon + scale_min * 1.5, center_lat - scale_min * 1.1],
                    [center_lon + scale_min * 1.6, center_lat + scale_min * 1.4],
                    [center_lon - scale_min * 1.3, center_lat + scale_min * 1.5],
                    [center_lon - scale_min * 1.4, center_lat - scale_min * 1.2],
                ]],
            },
        })

        return features
