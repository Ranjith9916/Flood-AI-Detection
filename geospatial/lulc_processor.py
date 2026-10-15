"""
geospatial/lulc_processor.py
Land Use / Land Cover (LULC) and Soil Hydrology Processor.
Implements:
- LULC classification mapping
- Hydrologic Soil Group (HSG) association
- USDA NRCS SCS-CN (Runoff Curve Number) computation
- Antecedent Moisture Condition (AMC-I, AMC-II, AMC-III) adjustments
- Potential maximum retention S and Direct Runoff Q calculation
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Standard USDA SCS Curve Numbers (AMC-II) for Soil Groups [A, B, C, D]
CN_TABLE = {
    "URBAN_HIGH_DENSITY": {"A": 89, "B": 92, "C": 94, "D": 95, "impervious_pct": 85.0},
    "URBAN_RESIDENTIAL":  {"A": 61, "B": 75, "C": 83, "D": 87, "impervious_pct": 45.0},
    "AGRICULTURE":        {"A": 64, "B": 75, "C": 82, "D": 85, "impervious_pct": 10.0},
    "FOREST_VEGETATION":  {"A": 36, "B": 60, "C": 73, "D": 79, "impervious_pct": 5.0},
    "WATER_WETLAND":      {"A": 100, "B": 100, "C": 100, "D": 100, "impervious_pct": 100.0},
    "BARREN_OPEN":        {"A": 68, "B": 79, "C": 86, "D": 89, "impervious_pct": 15.0},
}


class LULCProcessor:
    """
    Manages land cover classification and hydrologic runoff parameters for the catchment.
    """

    def __init__(
        self,
        study_area_bbox: Optional[dict] = None,
        output_dir: Optional[str] = None,
    ):
        self.bbox = study_area_bbox or {
            "min_lon": 77.35,
            "max_lon": 77.85,
            "min_lat": 12.75,
            "max_lat": 13.20,
        }
        self.output_dir = Path(output_dir or "ml/data/geospatial")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_lulc_grid(self, grid_shape: Tuple[int, int] = (100, 100)) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generates realistic spatial distribution of LULC classes and soil groups across urban/peri-urban basin.
        """
        ny, nx = grid_shape
        y = np.linspace(self.bbox["min_lat"], self.bbox["max_lat"], ny)
        x = np.linspace(self.bbox["min_lon"], self.bbox["max_lon"], nx)
        X, Y = np.meshgrid(x, y)

        # Distance from city center
        center_lon, center_lat = 77.5946, 12.9716
        dist = np.sqrt((X - center_lon)**2 + (Y - center_lat)**2)

        lulc_grid = np.empty((ny, nx), dtype=object)
        hsg_grid = np.empty((ny, nx), dtype=object)

        # Assign classes based on urban core vs peripheral agriculture/forest
        for i in range(ny):
            for j in range(nx):
                d = dist[i, j]
                # Water body channels
                if (abs(X[i, j] - 77.65) < 0.01 and Y[i, j] < 13.0) or (abs(Y[i, j] - 12.92) < 0.01):
                    lulc_grid[i, j] = "WATER_WETLAND"
                    hsg_grid[i, j] = "D"
                elif d < 0.08:
                    lulc_grid[i, j] = "URBAN_HIGH_DENSITY"
                    hsg_grid[i, j] = "C"
                elif d < 0.16:
                    lulc_grid[i, j] = "URBAN_RESIDENTIAL"
                    hsg_grid[i, j] = "C"
                elif d < 0.25:
                    lulc_grid[i, j] = "AGRICULTURE"
                    hsg_grid[i, j] = "B"
                else:
                    lulc_grid[i, j] = "FOREST_VEGETATION" if (i + j) % 2 == 0 else "BARREN_OPEN"
                    hsg_grid[i, j] = "B" if lulc_grid[i, j] == "FOREST_VEGETATION" else "C"

        return lulc_grid, hsg_grid

    def compute_curve_number_grid(
        self,
        lulc_grid: np.ndarray,
        hsg_grid: np.ndarray,
        amc: str = "II",
    ) -> np.ndarray:
        """
        Calculates Curve Number (CN) grid with Antecedent Moisture Condition (AMC) conversion:
        AMC-I (Dry):   CN_I   = CN_II / (2.281 - 0.01281 * CN_II)
        AMC-III (Wet): CN_III = CN_II / (0.427 + 0.00573 * CN_II)
        """
        ny, nx = lulc_grid.shape
        cn_grid = np.zeros((ny, nx), dtype=float)

        for i in range(ny):
            for j in range(nx):
                l_type = lulc_grid[i, j]
                h_group = hsg_grid[i, j]
                cn_base = float(CN_TABLE.get(l_type, {}).get(h_group, 75))

                if amc == "I":
                    cn_adj = cn_base / (2.281 - 0.01281 * cn_base)
                elif amc == "III":
                    cn_adj = cn_base / (0.427 + 0.00573 * cn_base)
                else:
                    cn_adj = cn_base

                cn_grid[i, j] = np.clip(round(cn_adj, 1), 30.0, 100.0)

        return cn_grid

    @staticmethod
    def calculate_runoff(precipitation_mm: float, curve_number: float) -> float:
        """
        Calculates direct runoff depth Q (mm) via SCS-CN equation:
        S = (25400 / CN) - 254
        Initial abstraction Ia = 0.2 * S
        If P > Ia: Q = (P - 0.2S)^2 / (P + 0.8S)
        Else:      Q = 0
        """
        if curve_number >= 99.5:
            return precipitation_mm
        if precipitation_mm <= 0:
            return 0.0

        s = (25400.0 / curve_number) - 254.0
        ia = 0.2 * s
        if precipitation_mm <= ia:
            return 0.0

        q = ((precipitation_mm - ia) ** 2) / (precipitation_mm + 0.8 * s)
        return round(float(q), 2)

    def sample_point(self, lat: float, lon: float) -> dict[str, Any]:
        """
        Samples LULC class, Hydrologic Soil Group, CN, and impervious fraction at a coordinate.
        """
        # Distance from city center
        center_lon, center_lat = 77.5946, 12.9716
        dist = np.sqrt((lon - center_lon)**2 + (lat - center_lat)**2)

        if dist < 0.08:
            lulc = "URBAN_HIGH_DENSITY"
            hsg = "C"
        elif dist < 0.16:
            lulc = "URBAN_RESIDENTIAL"
            hsg = "C"
        elif dist < 0.25:
            lulc = "AGRICULTURE"
            hsg = "B"
        else:
            lulc = "FOREST_VEGETATION"
            hsg = "B"

        cn = float(CN_TABLE[lulc][hsg])
        impervious = float(CN_TABLE[lulc]["impervious_pct"])

        return {
            "lulc_class": lulc,
            "soil_group": hsg,
            "curve_number_amc2": cn,
            "impervious_pct": impervious,
        }
