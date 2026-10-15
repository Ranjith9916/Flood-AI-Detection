"""
data_pipeline/validators/weather_validator.py
Validates weather observation records before DB insertion.
Enforces physical plausibility and required-field constraints.
"""

from datetime import datetime, timezone
from typing import Any

from data_pipeline.validators.base_validator import BaseValidator, ValidationResult

# Physical plausibility ranges (WMO-informed)
_RANGES = {
    "temperature_c":       (-89.0,  60.0),   # WMO absolute extremes
    "humidity_percent":    (  0.0, 100.0),
    "pressure_hpa":        (870.0, 1085.0),  # Sea-level range
    "wind_speed_ms":       (  0.0,  90.0),   # Category 5 hurricane ~70 m/s
    "wind_direction_deg":  (  0.0, 360.0),
    "rainfall_mm":         (  0.0, 500.0),   # 500 mm/hour is extreme record
}

_REQUIRED_FIELDS = ["station_code", "observation_time"]


class WeatherValidator(BaseValidator):

    def validate(self, record: dict[str, Any]) -> ValidationResult:
        result = ValidationResult(is_valid=True, record=dict(record))

        # ---- Required fields ----
        for f in _REQUIRED_FIELDS:
            if not record.get(f):
                result.add_error(f, f"Required field '{f}' is missing or null")

        if not result.is_valid:
            return result

        # ---- Timestamp must be UTC and not future ----
        obs_time = record.get("observation_time")
        if isinstance(obs_time, datetime):
            if obs_time.tzinfo is None:
                result.add_warning(
                    "observation_time",
                    "Timestamp has no timezone info — assuming UTC",
                )
                result.record["observation_time"] = obs_time.replace(
                    tzinfo=timezone.utc
                )
            now = datetime.now(timezone.utc)
            if obs_time > now:
                result.add_warning(
                    "observation_time",
                    f"Timestamp is {(obs_time - now).total_seconds()/3600:.1f}h in the future",
                )

        # ---- Physical range checks ----
        for field_name, (lo, hi) in _RANGES.items():
            val = record.get(field_name)
            if val is None:
                continue                    # Missing is allowed (nullable)
            if not (lo <= val <= hi):
                result.add_error(
                    field_name,
                    f"Value {val} out of physical range [{lo}, {hi}]",
                    value=val,
                )

        # ---- Wind: if speed=0, direction is irrelevant ----
        ws = record.get("wind_speed_ms")
        wd = record.get("wind_direction_deg")
        if ws is not None and ws == 0.0 and wd is not None:
            result.add_warning(
                "wind_direction_deg",
                "Wind direction irrelevant when wind speed is 0",
            )

        return result
