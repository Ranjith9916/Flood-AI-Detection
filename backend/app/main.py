"""
backend/app/main.py
FastAPI application entry point.
Registers all API routers, middleware, and startup/shutdown hooks.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.core.database import engine
from backend.app.core.logging_config import setup_logging
from backend.app.core.security import get_cors_kwargs

# Initialize logging before anything else
setup_logging(
    log_level=settings.log_level,
    environment=settings.environment,
)
logger = logging.getLogger(__name__)

# ============================================
# IMPORT ALL ROUTERS
# ============================================

from backend.app.api import weather
from backend.app.api import rainfall
from backend.app.api import satellite
from backend.app.api import radar
from backend.app.api import nwp
from backend.app.api import alerts
from backend.app.api import predictions
from backend.app.api import system
from backend.app.api import websocket_router
from backend.app.api import simulation
from backend.app.api import historical


# ============================================
# LIFESPAN
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info(
        "Starting %s v%s [%s]",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )

    # Verify database connection at startup
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection verified")
    except Exception as exc:
        logger.error("Database connection failed at startup: %s", exc)

    yield

    logger.info("Application shutting down")


# ============================================
# APPLICATION
# ============================================

app = FastAPI(
    title=settings.app_name,
    description=(
        "AI/ML-based integrated heavy rainfall early warning "
        "and inundation prediction system. "
        "Combines weather observations, satellite precipitation, "
        "NWP forecasts, and ML models to produce real-time flood risk "
        "assessments and early warnings."
    ),
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ============================================
# MIDDLEWARE
# ============================================

app.add_middleware(
    CORSMiddleware,
    **get_cors_kwargs(),
)


# ============================================
# API ROUTERS
# ============================================

app.include_router(system.router)
app.include_router(weather.router)
app.include_router(rainfall.router)
app.include_router(satellite.router)
app.include_router(radar.router)
app.include_router(nwp.router)
app.include_router(alerts.router)
app.include_router(predictions.router)
app.include_router(simulation.router)
app.include_router(historical.router)
app.include_router(websocket_router.router)



# ============================================
# ROOT
# ============================================

@app.get("/", tags=["System"])
def root():
    return {
        "system": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "status": "online",
        "docs": "/docs",
        "health": "/health",
        "system_status": "/system/status",
    }


# ============================================
# DATABASE TEST (development convenience)
# ============================================

@app.get("/database-test", tags=["System"])
def database_test():
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT current_database(), version();")
            )
            row = result.fetchone()
            return {
                "database": row[0],
                "postgresql": row[1],
                "status": "connected",
            }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
