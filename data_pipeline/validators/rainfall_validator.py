"""
data_pipeline/validators/rainfall_validator.py
Validates rainfall observation records.
"""

from datetime import datetime, timezone
from typing import Any

from data_pipeline.validators.base_validator import BaseValidator, ValidationResult

_VALID_SOURCES = {
    "STATION", "GPM_IMERG", "RADAR", "NWP", "OPEN_METEO",
    "MANUAL", "OTHER",
}
_VALID_DURATIONS = {1, 5, 10, 15, 30, 60, 180, 360, 720, 1440, 2880, 4320}


class RainfallValidator(BaseValidator):

    def validate(self, record: dict[str, Any]) -> ValidationResult:
        result = ValidationResult(is_valid=True, record=dict(record))

        # ---- Required fields ----
        for f in ["observation_time", "source", "rainfall_mm"]:
            if record.get(f) is None:
                result.add_error(f, f"Required field '{f}' is missing")

        if not result.is_valid:
            return result

        # ---- Negative rainfall ----
        rain = record.get("rainfall_mm", 0)
        if rain < 0:
            result.add_error(
                "rainfall_mm",
                f"Negative rainfall ({rain} mm) is physically impossible",
                value=rain,
            )
        elif rain > 500:
            result.add_warning(
                "rainfall_mm",
                f"Extreme rainfall value ({rain} mm) — check instrument",
                value=rain,
            )

        # ---- Source code ----
        src = str(record.get("source", "")).upper()
        if src not in _VALID_SOURCES:
            result.add_warning(
                "source",
                f"Unknown source '{src}'. Expected one of {_VALID_SOURCES}",
            )

        # ---- Coordinates ----
        lat = record.get("latitude")
        lon = record.get("longitude")
        if lat is not None and not (-90 <= lat <= 90):
            result.add_error("latitude", f"Invalid latitude {lat}")
        if lon is not None and not (-180 <= lon <= 180):
            result.add_error("longitude", f"Invalid longitude {lon}")

        # ---- Duration ----
        dur = record.get("duration_minutes")
        if dur is not None:
            if dur <= 0:
                result.add_error(
                    "duration_minutes", f"Duration must be positive (got {dur})"
                )
            elif dur not in _VALID_DURATIONS:
                result.add_warning(
                    "duration_minutes",
                    f"Non-standard duration {dur} min. Expected one of {sorted(_VALID_DURATIONS)}",
                )

        return result
