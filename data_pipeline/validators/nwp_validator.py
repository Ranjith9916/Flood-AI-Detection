"""
data_pipeline/validators/nwp_validator.py
Validates Numerical Weather Prediction (NWP) forecast records before DB insertion.
"""

from datetime import datetime, timezone
from typing import Any

from data_pipeline.validators.base_validator import BaseValidator, ValidationResult


class NwpValidator(BaseValidator):
    """
    Validates NwpForecast records.
    Ensures forecast lead times, timestamps, and meteorological variables are valid.
    """

    def validate(self, record: dict[str, Any]) -> ValidationResult:
        result = ValidationResult(is_valid=True, record=dict(record))

        # Required fields
        for f in ["model_name", "forecast_time", "valid_time"]:
            if not record.get(f):
                result.add_error(f, f"Required field '{f}' is missing or null")

        if not result.is_valid:
            return result

        # Timestamp checks
        fc_time = record.get("forecast_time")
        vl_time = record.get("valid_time")

        if isinstance(fc_time, datetime) and fc_time.tzinfo is None:
            result.record["forecast_time"] = fc_time.replace(tzinfo=timezone.utc)
            fc_time = result.record["forecast_time"]

        if isinstance(vl_time, datetime) and vl_time.tzinfo is None:
            result.record["valid_time"] = vl_time.replace(tzinfo=timezone.utc)
            vl_time = result.record["valid_time"]

        if isinstance(fc_time, datetime) and isinstance(vl_time, datetime):
            if vl_time < fc_time:
                result.add_error("valid_time", f"valid_time ({vl_time}) cannot be earlier than forecast_time ({fc_time})")
            else:
                # Calculate or verify lead_time_hours
                calc_lead = int((vl_time - fc_time).total_seconds() // 3600)
                if record.get("lead_time_hours") is None:
                    result.record["lead_time_hours"] = calc_lead
                elif record.get("lead_time_hours") != calc_lead:
                    result.add_warning(
                        "lead_time_hours",
                        f"lead_time_hours {record.get('lead_time_hours')} differs from calculated {calc_lead}h",
                    )

        # Coordinate checks
        lat = record.get("latitude")
        lon = record.get("longitude")
        if lat is not None and not (-90.0 <= lat <= 90.0):
            result.add_error("latitude", f"Invalid latitude {lat}")
        if lon is not None and not (-180.0 <= lon <= 180.0):
            result.add_error("longitude", f"Invalid longitude {lon}")

        # Meteorological variables
        rain = record.get("rainfall_mm")
        if rain is not None:
            if rain < 0:
                result.add_error("rainfall_mm", f"Negative forecast rainfall: {rain} mm")
            elif rain > 800:
                result.add_warning("rainfall_mm", f"Extreme forecast rainfall: {rain} mm")

        temp = record.get("temperature_c")
        if temp is not None and not (-90.0 <= temp <= 65.0):
            result.add_error("temperature_c", f"Temperature {temp} C out of range [-90, 65]")

        hum = record.get("humidity_percent")
        if hum is not None and not (0.0 <= hum <= 100.0):
            result.add_error("humidity_percent", f"Humidity {hum}% out of range [0, 100]")

        wind = record.get("wind_speed_ms")
        if wind is not None and not (0.0 <= wind <= 120.0):
            result.add_error("wind_speed_ms", f"Wind speed {wind} m/s out of range [0, 120]")

        wind_dir = record.get("wind_direction_deg")
        if wind_dir is not None and not (0.0 <= wind_dir <= 360.0):
            result.add_error("wind_direction_deg", f"Wind direction {wind_dir} deg out of range [0, 360]")

        pressure = record.get("pressure_hpa")
        if pressure is not None and not (800.0 <= pressure <= 1100.0):
            result.add_warning("pressure_hpa", f"Pressure {pressure} hPa outside normal range [800, 1100]")

        return result
