"""
data_pipeline/validators/satellite_validator.py
Validates satellite precipitation metadata records before DB insertion.
"""

from datetime import datetime, timezone
from typing import Any

from data_pipeline.validators.base_validator import BaseValidator, ValidationResult


class SatelliteValidator(BaseValidator):
    """
    Validates SatelliteData records.
    Ensures spatial bounding boxes, precipitation ranges, and coverage percentages are valid.
    """

    def validate(self, record: dict[str, Any]) -> ValidationResult:
        result = ValidationResult(is_valid=True, record=dict(record))

        # Required fields
        for f in ["observation_time", "satellite_name", "product_name"]:
            if not record.get(f):
                result.add_error(f, f"Required field '{f}' is missing or null")

        if not result.is_valid:
            return result

        # Timestamp checks
        obs_time = record.get("observation_time")
        if isinstance(obs_time, datetime):
            if obs_time.tzinfo is None:
                result.add_warning(
                    "observation_time",
                    "Timestamp has no timezone info — assuming UTC",
                )
                result.record["observation_time"] = obs_time.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            if obs_time > now:
                result.add_warning(
                    "observation_time",
                    f"Observation timestamp is in the future: {obs_time}",
                )

        # Coordinate bounding box checks
        min_lat = record.get("min_lat")
        max_lat = record.get("max_lat")
        min_lon = record.get("min_lon")
        max_lon = record.get("max_lon")

        if min_lat is not None and not (-90.0 <= min_lat <= 90.0):
            result.add_error("min_lat", f"Invalid min_lat {min_lat}")
        if max_lat is not None and not (-90.0 <= max_lat <= 90.0):
            result.add_error("max_lat", f"Invalid max_lat {max_lat}")
        if min_lat is not None and max_lat is not None and min_lat > max_lat:
            result.add_error("min_lat", f"min_lat ({min_lat}) > max_lat ({max_lat})")

        if min_lon is not None and not (-180.0 <= min_lon <= 180.0):
            result.add_error("min_lon", f"Invalid min_lon {min_lon}")
        if max_lon is not None and not (-180.0 <= max_lon <= 180.0):
            result.add_error("max_lon", f"Invalid max_lon {max_lon}")
        if min_lon is not None and max_lon is not None and min_lon > max_lon:
            result.add_error("min_lon", f"min_lon ({min_lon}) > max_lon ({max_lon})")

        # Precipitation statistics checks
        mean_p = record.get("mean_precipitation_mm")
        max_p = record.get("max_precipitation_mm")

        if mean_p is not None:
            if mean_p < 0:
                result.add_error("mean_precipitation_mm", f"Negative mean precipitation: {mean_p}")
            elif mean_p > 500:
                result.add_warning("mean_precipitation_mm", f"Unusually high mean precipitation: {mean_p} mm")

        if max_p is not None:
            if max_p < 0:
                result.add_error("max_precipitation_mm", f"Negative max precipitation: {max_p}")
            elif max_p > 1000:
                result.add_warning("max_precipitation_mm", f"Extreme max precipitation: {max_p} mm")

        if mean_p is not None and max_p is not None and mean_p > max_p:
            result.add_error(
                "mean_precipitation_mm",
                f"mean_precipitation ({mean_p}) cannot exceed max_precipitation ({max_p})",
            )

        # Coverage pct checks
        coverage = record.get("data_coverage_pct")
        if coverage is not None:
            if not (0.0 <= coverage <= 100.0):
                result.add_error("data_coverage_pct", f"data_coverage_pct must be between 0 and 100, got {coverage}")

        return result
