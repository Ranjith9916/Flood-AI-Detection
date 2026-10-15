"""
geospatial/drainage_network.py
Catchment river, drainage network, and stream proximity analyzer.
Computes:
- Distance to nearest river / primary storm drainage channel (meters)
- Catchment basin identification
- Local drainage density (km / km^2)
"""

import math
from typing import Any, Optional

import numpy as np


# Primary drainage networks (Bangalore Valley System)
# 1. Koramangala-Challaghatta (K&C) Valley (Central to South-East)
# 2. Hebbal Valley (North to North-East)
# 3. Vrishabhavathi Valley (West to South-West)
PRIMARY_DRAINAGE_REACHES = [
    {
        "name": "Koramangala_Challaghatta_Reach",
        "valley": "K_AND_C_VALLEY",
        "points": [(12.980, 77.580), (12.950, 77.620), (12.920, 77.660), (12.890, 77.710)],
    },
    {
        "name": "Hebbal_Valley_Reach",
        "valley": "HEBBAL_VALLEY",
        "points": [(13.040, 77.570), (13.030, 77.600), (13.010, 77.650), (13.000, 77.720)],
    },
    {
        "name": "Vrishabhavathi_Valley_Reach",
        "valley": "VRISHABHAVATHI_VALLEY",
        "points": [(12.990, 77.540), (12.950, 77.520), (12.900, 77.490), (12.830, 77.450)],
    },
]


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance between two points on earth in meters."""
    r_earth = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r_earth * c


def point_to_segment_distance_m(
    plat: float, plon: float,
    lat1: float, lon1: float,
    lat2: float, lon2: float,
) -> float:
    """Computes minimum distance from a point to a line segment in meters."""
    # Approximate planar projection for local segments
    d_total = haversine_distance_m(lat1, lon1, lat2, lon2)
    if d_total < 1.0:
        return haversine_distance_m(plat, plon, lat1, lon1)

    d1 = haversine_distance_m(plat, plon, lat1, lon1)
    d2 = haversine_distance_m(plat, plon, lat2, lon2)

    # Cosine rule projection factor t in [0, 1]
    t = max(0.0, min(1.0, (d1**2 - d2**2 + d_total**2) / (2.0 * d_total**2)))
    
    interp_lat = lat1 + t * (lat2 - lat1)
    interp_lon = lon1 + t * (lon2 - lon1)
    return haversine_distance_m(plat, plon, interp_lat, interp_lon)


class DrainageNetworkAnalyzer:
    """
    Evaluates drainage proximity and catchment parameters for points across the domain.
    """

    def __init__(self, reaches: Optional[list[dict]] = None):
        self.reaches = reaches or PRIMARY_DRAINAGE_REACHES

    def compute_distance_to_stream(self, lat: float, lon: float) -> dict[str, Any]:
        """
        Calculates distance in meters to the nearest drainage axis and identifies the catchment valley.
        """
        min_dist_m = float("inf")
        nearest_reach_name = "UNKNOWN"
        nearest_valley = "UNKNOWN"

        for reach in self.reaches:
            pts = reach["points"]
            for i in range(len(pts) - 1):
                lat1, lon1 = pts[i]
                lat2, lon2 = pts[i + 1]
                dist = point_to_segment_distance_m(lat, lon, lat1, lon1, lat2, lon2)
                if dist < min_dist_m:
                    min_dist_m = dist
                    nearest_reach_name = reach["name"]
                    nearest_valley = reach["valley"]

        # Drainage density proxy (km of channel per km^2)
        # Urban valleys with dense storm drains have ~3.5 km/km^2
        drainage_density = round(3.5 / (1.0 + (min_dist_m / 2000.0)), 2)

        return {
            "dist_to_stream_m": round(min_dist_m, 1),
            "nearest_reach": nearest_reach_name,
            "catchment_valley": nearest_valley,
            "drainage_density_km_km2": drainage_density,
        }
