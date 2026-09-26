"""Logging setup for ContextForge."""

import logging
import sys

from contextforge.config import get_config


def setup_logging() -> None:
    """Configure application logging."""
    config = get_config()

    level = getattr(logging, config.log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if config.log_format == "json":
        try:
            import json_logging  # type: ignore[import-not-found]
            json_logging.init_non_web()
            formatter = json_logging.JSONLogFormatter()
        except ImportError:
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]

    # Reduce noise from dependencies
    logging.getLogger("sqlite_utils").setLevel(logging.WARNING)
    logging.getLogger("pydantic").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
