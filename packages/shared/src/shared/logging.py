"""Logging configuration for Stranger Beers services."""

import logging
import sys
from typing import Literal

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def configure_logging(
    level: LogLevel = "INFO",
    service_name: str | None = None,
    json_format: bool = False,
) -> logging.Logger:
    """
    Configure logging for a Stranger Beers service.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        service_name: Name of the service for log identification
        json_format: If True, output logs in JSON format (useful for production)

    Returns:
        Configured logger instance

    Example:
        >>> logger = configure_logging("INFO", "ingestion-api")
        >>> logger.info("Service started")
    """
    logger = logging.getLogger(service_name or "stranger-beers")
    logger.setLevel(getattr(logging, level))

    # Clear existing handlers
    logger.handlers.clear()

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level))

    # Create formatter
    if json_format:
        # Simple JSON-like format for structured logging
        format_str = (
            '{"time": "%(asctime)s", "level": "%(levelname)s", '
            '"service": "%(name)s", "message": "%(message)s"}'
        )
    else:
        format_str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    formatter = logging.Formatter(format_str, datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a child logger with the given name."""
    return logging.getLogger(f"stranger-beers.{name}")
