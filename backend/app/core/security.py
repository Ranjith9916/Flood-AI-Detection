"""
backend/app/core/security.py
Security utilities: CORS configuration, optional API key authentication.
Designed to allow plugging in JWT or OAuth2 in production without rewriting
the downstream code.
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================
# API KEY AUTHENTICATION (optional)
# ============================================

_api_key_scheme = APIKeyHeader(
    name=settings.api_key_header,
    auto_error=False,
)


async def verify_api_key(
    api_key: Optional[str] = Security(_api_key_scheme),
) -> Optional[str]:
    """
    FastAPI dependency for optional API key authentication.

    Behaviour:
    - If API_KEY is not configured in settings -> authentication is disabled,
      all requests are allowed (development mode).
    - If API_KEY is configured -> the request must supply the correct key
      in the X-API-Key header, otherwise 401 is returned.

    Usage:
        @router.get("/protected")
        def protected_endpoint(
            _key: str = Depends(verify_api_key)
        ):
            ...
    """
    configured_key = settings.api_key

    # No key configured -> open access (dev mode)
    if not configured_key:
        return None

    if api_key != configured_key:
        logger.warning("Invalid or missing API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key


def get_cors_kwargs() -> dict:
    """
    Return kwargs for FastAPI CORSMiddleware.
    Read from settings so CORS can be tuned per environment.
    """
    return {
        "allow_origins": settings.cors_origins_list,
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": [
            "Authorization",
            "Content-Type",
            "X-API-Key",
            "X-Request-ID",
        ],
        "expose_headers": [
            "X-Total-Count",
            "X-Request-ID",
        ],
    }
