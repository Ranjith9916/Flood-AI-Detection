"""
backend/app/core/config.py
Central application configuration using Pydantic BaseSettings.
All values are read from environment variables with sensible development defaults.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    See .env.example for all available configuration keys.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ============================================
    # APPLICATION
    # ============================================

    app_name: str = "Flood AI Early Warning System"
    app_version: str = "0.1.0"
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")
    debug: bool = Field(default=False)

    # ============================================
    # DATABASE
    # ============================================

    database_url: str = Field(
        default=(
            "postgresql+psycopg://"
            "flood_admin:flood_password@"
            "localhost:5432/flood_ai"
        )
    )
    db_pool_size: int = Field(default=5)
    db_max_overflow: int = Field(default=10)
    db_pool_pre_ping: bool = Field(default=True)

    # ============================================
    # REDIS
    # ============================================

    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_ttl_weather: int = Field(default=300)
    redis_ttl_rainfall: int = Field(default=300)
    redis_ttl_predictions: int = Field(default=600)
    redis_ttl_alerts: int = Field(default=60)

    # ============================================
    # SECURITY / CORS
    # ============================================

    cors_origins: str = Field(default="http://localhost:3000")
    api_key: Optional[str] = Field(default=None)
    api_key_header: str = Field(default="X-API-Key")

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    # ============================================
    # STUDY AREA (lon_min,lat_min,lon_max,lat_max)
    # Default: Bangalore metropolitan region
    # ============================================

    study_area_bbox: str = Field(default="77.35,12.75,77.85,13.20")

    @property
    def study_area_bbox_tuple(self):
        parts = [float(x) for x in self.study_area_bbox.split(",")]
        return {
            "lon_min": parts[0],
            "lat_min": parts[1],
            "lon_max": parts[2],
            "lat_max": parts[3],
        }

    # ============================================
    # EXTERNAL DATA SOURCES
    # ============================================

    open_meteo_base_url: str = Field(
        default="https://api.open-meteo.com/v1"
    )
    open_meteo_timeout_s: int = Field(default=30)

    nasa_earthdata_username: Optional[str] = Field(default=None)
    nasa_earthdata_password: Optional[str] = Field(default=None)

    gfs_base_url: str = Field(
        default="https://nomads.ncep.noaa.gov/dods"
    )

    radar_base_url: Optional[str] = Field(default=None)
    radar_api_key: Optional[str] = Field(default=None)

    # ============================================
    # RAINFALL THRESHOLDS (IMD classification, mm/day)
    # ============================================

    rainfall_light_threshold_mm: float = Field(default=2.5)
    rainfall_moderate_threshold_mm: float = Field(default=15.6)
    rainfall_heavy_threshold_mm: float = Field(default=64.5)
    rainfall_very_heavy_threshold_mm: float = Field(default=115.5)
    rainfall_extremely_heavy_threshold_mm: float = Field(default=204.5)

    # ============================================
    # FLOOD / RISK THRESHOLDS
    # ============================================

    flood_prob_moderate_threshold: float = Field(default=0.35)
    flood_prob_high_threshold: float = Field(default=0.55)
    flood_prob_very_high_threshold: float = Field(default=0.70)
    flood_prob_extreme_threshold: float = Field(default=0.85)

    # ============================================
    # PIPELINE SCHEDULES (cron expressions)
    # ============================================

    pipeline_weather_cron: str = Field(default="0 * * * *")
    pipeline_rainfall_cron: str = Field(default="0 * * * *")
    pipeline_satellite_cron: str = Field(default="0 */3 * * *")
    pipeline_nwp_cron: str = Field(default="0 */6 * * *")
    pipeline_predictions_cron: str = Field(default="15 * * * *")

    # ============================================
    # ML / MLFLOW
    # ============================================

    mlflow_tracking_uri: str = Field(default="http://localhost:5000")
    ml_models_dir: str = Field(default="ml/models")
    ml_data_dir: str = Field(default="ml/data")
    ml_features_dir: str = Field(default="ml/data/features")

    forecast_horizons_h: str = Field(default="1,3,6,12,24")

    @property
    def forecast_horizons_list(self) -> List[int]:
        return [int(h) for h in self.forecast_horizons_h.split(",")]

    # ============================================
    # DATA DIRECTORIES
    # ============================================

    data_raw_dir: str = Field(default="ml/data/raw")
    data_processed_dir: str = Field(default="ml/data/processed")
    geospatial_dir: str = Field(default="geospatial")
    outputs_dir: str = Field(default="outputs")

    # ============================================
    # VALIDATORS
    # ============================================

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v.upper()

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()


# Module-level singleton for convenience imports
settings = get_settings()
