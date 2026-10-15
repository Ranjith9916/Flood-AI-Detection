"""
backend/app/core/logging_config.py
Structured logging configuration for the Flood AI backend.
Produces JSON-formatted logs in production and readable logs in development.
"""

import logging
import sys
import json
from datetime import datetime, timezone
from typing import Any


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for production structured logging.
    Each log record is emitted as a single JSON line.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_entry["exception"] = self.formatException(
                record.exc_info
            )

        # Include extra fields added via logging.info("msg", extra={...})
        for key, value in record.__dict__.items():
            if key not in (
                "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text",
                "stack_info", "lineno", "funcName", "created",
                "msecs", "relativeCreated", "thread", "threadName",
                "processName", "process", "name", "message",
                "taskName",
            ):
                log_entry[key] = value

        return json.dumps(log_entry, default=str)


class DevelopmentFormatter(logging.Formatter):
    """
    Human-readable formatter for development.
    """

    LEVEL_COLORS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[35m", # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.LEVEL_COLORS.get(record.levelname, "")
        reset = self.RESET
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        return (
            f"{color}[{timestamp}] "
            f"{record.levelname:<8} "
            f"{record.name}: "
            f"{record.getMessage()}"
            f"{reset}"
        )


def setup_logging(log_level: str = "INFO", environment: str = "development") -> None:
    """
    Configure application-wide structured logging.
    Call this once at application startup.
    """

    level = getattr(logging, log_level.upper(), logging.INFO)

    # Remove existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if environment == "development":
        handler.setFormatter(DevelopmentFormatter())
    else:
        handler.setFormatter(StructuredFormatter())

    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger. Use module __name__ as the name."""
    return logging.getLogger(name)
