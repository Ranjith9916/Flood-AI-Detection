"""
backend/app/api/system.py
System health and status endpoints.
GET /health  - lightweight liveness probe
GET /system/status - full component health check
"""
import logging
import time
from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.core.database import engine, SessionLocal
from backend.app.models.pipeline import PipelineRun, ModelRegistry
from backend.app.schemas.system import ComponentHealth, HealthResponse, SystemStatus

logger = logging.getLogger(__name__)
router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse)
def health():
    """Lightweight liveness probe. Returns 200 if server is up."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/system/status", response_model=SystemStatus)
def system_status():
    """
    Full system health check.
    Tests connectivity to database, Redis, data sources, and ML model registry.
    """
    components: list[ComponentHealth] = []
    data_sources: list[ComponentHealth] = []
    ml_models: list[ComponentHealth] = []

    # ---- Database ----
    t0 = time.perf_counter()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_latency = (time.perf_counter() - t0) * 1000
        components.append(ComponentHealth(
            name="postgresql",
            status="healthy",
            latency_ms=round(db_latency, 1),
        ))
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)
        components.append(ComponentHealth(
            name="postgresql",
            status="unavailable",
            message=str(exc),
        ))

    # ---- Redis ----
    try:
        import redis as redis_lib
        t0 = time.perf_counter()
        r = redis_lib.from_url(settings.redis_url, socket_connect_timeout=2)
        r.ping()
        redis_latency = (time.perf_counter() - t0) * 1000
        components.append(ComponentHealth(
            name="redis",
            status="healthy",
            latency_ms=round(redis_latency, 1),
        ))
    except ImportError:
        components.append(ComponentHealth(
            name="redis",
            status="unknown",
            message="redis package not installed",
        ))
    except Exception as exc:
        components.append(ComponentHealth(
            name="redis",
            status="unavailable",
            message=str(exc),
        ))

    # ---- Data Sources (from latest PipelineRuns) ----
    session = SessionLocal()
    try:
        pipeline_names = [
            ("weather_ingestion", "Open-Meteo Weather"),
            ("satellite_ingestion", "NASA GPM Satellite"),
            ("radar_ingestion", "Doppler Radar DWR"),
            ("nwp_ingestion", "ECMWF/GFS NWP"),
        ]
        for p_name, label in pipeline_names:
            last_run = (
                session.query(PipelineRun)
                .filter(PipelineRun.pipeline_name == p_name)
                .order_by(PipelineRun.started_at.desc())
                .first()
            )
            if last_run:
                status_val = "healthy" if last_run.status == "SUCCESS" else "degraded"
                dur = round(last_run.duration_seconds * 1000, 1) if last_run.duration_seconds else None
                data_sources.append(ComponentHealth(
                    name=label,
                    status=status_val,
                    message=f"Last run: {last_run.records_inserted} inserted ({last_run.status})",
                    latency_ms=dur,
                ))
            else:
                data_sources.append(ComponentHealth(
                    name=label,
                    status="unknown",
                    message="No pipeline runs recorded yet",
                ))

        # ---- Active ML Models ----
        active_models = (
            session.query(ModelRegistry)
            .filter(ModelRegistry.is_active.is_(True))
            .all()
        )
        for m in active_models:
            ml_models.append(ComponentHealth(
                name=m.model_name,
                status="healthy",
                message=f"v{m.model_version} ({m.model_type})",
            ))
    except Exception as e:
        logger.error("Error checking pipeline / model registry status: %s", e)
    finally:
        session.close()

    # ---- Overall status ----
    statuses = [c.status for c in components]
    if all(s == "healthy" for s in statuses):
        overall = "healthy"
    elif any(s == "unavailable" for s in statuses):
        overall = "degraded"
    else:
        overall = "degraded"

    return SystemStatus(
        status=overall,
        environment=settings.environment,
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc),
        components=components,
        data_sources=data_sources,
        ml_models=ml_models,
    )
