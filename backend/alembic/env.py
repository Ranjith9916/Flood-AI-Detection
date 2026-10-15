"""
backend/alembic/env.py
Alembic migration environment.
Reads DATABASE_URL from app settings so migrations use the same
database configuration as the application.
"""

import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Ensure the project root is on the path so we can import backend.*
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# Import app settings (reads .env / environment variables)
from backend.app.core.config import settings

# Import all models so Alembic sees the full metadata
import backend.app.models  # noqa: F401 - registers all models with Base
from backend.app.core.database import Base

# ---- Alembic Config ----
config = context.config

# Override sqlalchemy.url with app settings
config.set_main_option("sqlalchemy.url", settings.database_url)

# Set up file-based logging if alembic.ini defines it
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use the application's metadata for autogenerate
target_metadata = Base.metadata


# Tables that belong to PostGIS / PostgreSQL extensions.
# Autogenerate must never try to drop or modify these.
_EXCLUDED_TABLES = {
    # PostGIS Tiger Geocoder
    "zip_lookup_base", "zip_lookup", "zip_state", "zip_state_loc",
    "county", "county_lookup", "countysub_lookup", "cousub",
    "edges", "faces", "featnames", "place", "place_lookup",
    "secondary_unit_lookup", "state", "state_lookup", "street_type_lookup",
    "tabblock", "tabblock20", "tract", "addr", "addrfeat", "bg",
    # PostGIS Topology
    "topology", "layer",
    # PostGIS Raster
    "raster_columns", "raster_overviews",
    # PostGIS general
    "spatial_ref_sys", "geography_columns", "geometry_columns",
}


def include_object(object, name, type_, reflected, compare_to):
    """
    Filter function for autogenerate.
    Only include objects that are:
    1. Not PostGIS/system extension tables
    2. Registered in our application metadata (when reflected)
    """
    if type_ == "table":
        if name in _EXCLUDED_TABLES:
            return False
        # Only include reflected tables that our models define
        if reflected and name not in target_metadata.tables:
            return False
    return True


def run_migrations_offline() -> None:
    """Run migrations in offline mode (no live DB connection required)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations with a live database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
