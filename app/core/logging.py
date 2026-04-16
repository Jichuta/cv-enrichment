"""Logging configuration for the application."""

import logging
import sys

from app.core.config import settings


def configure_logging() -> None:
    """Set up root logging with a readable format."""
    log_level = logging.DEBUG if settings.APP_DEBUG else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Silence noisy libraries in non-debug mode
    if not settings.APP_DEBUG:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger. Prefer using module-level __name__ as the name."""
    return logging.getLogger(name)
