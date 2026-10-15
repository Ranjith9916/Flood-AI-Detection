"""
data_pipeline/validators/radar_validator.py
Validates weather radar metadata records before DB insertion.
"""

from datetime import datetime, timezone
from typing import Any

from data_pipeline.validators.base_validator import BaseValidator, ValidationResult


class RadarValidator(BaseValidator):
    """
    Validates RadarData records.
    Ensures reflectivity ranges, rain rate ranges, and timestamps are within physical bounds.
    """

    def validate(self, record: dict[str, Any]) -> ValidationResult:
        result = ValidationResult(is_valid=True, record=dict(record))

        # Required fields
        for f in ["observation_time", "radar_name", "product_name"]:
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

        # Coordinates
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

        # Reflectivity checks (dBZ: typical atmospheric range -20 dBZ to 80 dBZ)
        mean_dbz = record.get("mean_reflectivity_dbz")
        max_dbz = record.get("max_reflectivity_dbz")

        if mean_dbz is not None:
            if not (-30.0 <= mean_dbz <= 85.0):
                result.add_error("mean_reflectivity_dbz", f"Reflectivity {mean_dbz} dBZ out of range [-30, 85]")

        if max_dbz is not None:
            if not (-30.0 <= max_dbz <= 85.0):
                result.add_error("max_reflectivity_dbz", f"Max reflectivity {max_dbz} dBZ out of range [-30, 85]")

        if mean_dbz is not None and max_dbz is not None and mean_dbz > max_dbz:
            result.add_error(
                "mean_reflectivity_dbz",
                f"mean_reflectivity ({mean_dbz}) cannot exceed max_reflectivity ({max_dbz})",
            )

        # Rainfall rate check (mm/h)
        rain_rate = record.get("mean_rainfall_rate_mmh")
        if rain_rate is not None:
            if rain_rate < 0:
                result.add_error("mean_rainfall_rate_mmh", f"Negative rainfall rate: {rain_rate} mm/h")
            elif rain_rate > 300:
                result.add_warning("mean_rainfall_rate_mmh", f"Extreme rainfall rate: {rain_rate} mm/h")

        return result
