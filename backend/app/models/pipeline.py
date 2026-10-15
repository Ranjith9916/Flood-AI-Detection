"""
backend/app/models/pipeline.py
SQLAlchemy models for pipeline monitoring, data quality reporting,
ML model registry, and model metrics.
"""

import uuid

from sqlalchemy import (
    Boolean, Column, Float, ForeignKey, Integer,
    String, DateTime, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.core.database import Base


class PipelineRun(Base):
    """
    One execution run of a data ingestion pipeline.
    Records timing, record counts, and outcome for monitoring.
    """

    __tablename__ = "pipeline_runs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    pipeline_name = Column(
        String(100),
        nullable=False,
        index=True,
    )                                       # e.g. "weather", "rainfall", "satellite"

    started_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )

    completed_at = Column(DateTime(timezone=True))

    status = Column(
        String(30),
        nullable=False,
        default="RUNNING",
    )
    # RUNNING / SUCCESS / FAILED / PARTIAL

    records_received = Column(Integer, default=0)
    records_valid = Column(Integer, default=0)
    records_rejected = Column(Integer, default=0)
    records_inserted = Column(Integer, default=0)
    records_duplicate = Column(Integer, default=0)

    duration_seconds = Column(Float)

    error_message = Column(Text)

    # Relationship
    quality_reports = relationship(
        "DataQualityReport",
        back_populates="pipeline_run",
    )


class DataQualityReport(Base):
    """
    Data quality summary for one pipeline run and data source.
    One pipeline run may produce multiple quality reports
    (e.g. one per data source type).
    """

    __tablename__ = "data_quality_reports"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    pipeline_run_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pipeline_runs.id"),
        nullable=True,
        index=True,
    )

    source = Column(String(100), nullable=False)    # e.g. "weather", "rainfall"
    report_time = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    records_received = Column(Integer, default=0)
    records_valid = Column(Integer, default=0)
    records_rejected = Column(Integer, default=0)
    missing_values = Column(Integer, default=0)
    duplicates = Column(Integer, default=0)
    out_of_range = Column(Integer, default=0)
    invalid_timestamps = Column(Integer, default=0)

    details_json = Column(Text)                     # JSON with per-field details

    # Relationship
    pipeline_run = relationship(
        "PipelineRun",
        back_populates="quality_reports",
    )


class ModelRegistry(Base):
    """
    Registry of trained ML models.
    Every model version is tracked here for full reproducibility.
    Never overwrite — always create a new version record.
    """

    __tablename__ = "model_registry"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    model_name = Column(
        String(100),
        nullable=False,
        index=True,
    )
    # e.g. "heavy_rain_classifier", "flood_probability", "rainfall_forecast_xgb"

    model_version = Column(
        String(50),
        nullable=False,
    )                                               # e.g. "1.0.0", "20260908"

    model_type = Column(String(100))                # e.g. "XGBClassifier", "LightGBM"

    training_dataset_version = Column(String(100))  # Dataset identifier
    feature_version = Column(String(50))            # Feature pipeline version
    target_variable = Column(String(100))

    training_date = Column(DateTime(timezone=True))
    training_duration_s = Column(Float)

    file_path = Column(Text)                        # Path to serialized model
    mlflow_run_id = Column(String(100))             # MLflow run ID for full traceability

    is_active = Column(Boolean, default=False)      # Current production model
    is_development = Column(Boolean, default=True)  # Dev/prod flag

    metadata_json = Column(Text)                    # JSON with hyperparams etc.
    notes = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # Relationship
    metrics = relationship(
        "ModelMetric",
        back_populates="model",
    )


class ModelMetric(Base):
    """
    Evaluation metric for a specific model version.
    All metrics are from actual evaluation on real or validated datasets.
    Never populate with fabricated values.
    """

    __tablename__ = "model_metrics"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    model_id = Column(
        UUID(as_uuid=True),
        ForeignKey("model_registry.id"),
        nullable=False,
        index=True,
    )

    metric_name = Column(
        String(100),
        nullable=False,
    )
    # e.g. "roc_auc", "f1_score", "mae", "rmse", "brier_score"

    metric_value = Column(Float, nullable=False)

    dataset_split = Column(String(50))              # "train", "validation", "test"
    evaluation_date = Column(DateTime(timezone=True))
    notes = Column(Text)

    # Relationship
    model = relationship(
        "ModelRegistry",
        back_populates="metrics",
    )
