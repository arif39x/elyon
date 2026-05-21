from __future__ import annotations

import logging
from typing import Any

try:
    import structlog
except ModuleNotFoundError:
    structlog = None

from orchestration.config import TelemetrySettings


def configure_logging(settings: TelemetrySettings) -> None:
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

    if structlog is None:
        return

    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]

    if settings.json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> Any:
    if structlog is None:
        return logging.getLogger(name)
    return structlog.get_logger(name)
