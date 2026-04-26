"""Logging configuration for the FinAI Risk Platform.

Call ``configure_logging()`` once at application startup.
Every module then obtains its own logger via ``logging.getLogger(__name__)``.
"""

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """Configure root logger with a consistent format.

    Args:
        level: Log level string (e.g. ``"DEBUG"``, ``"INFO"``, ``"WARNING"``).
               Controlled via the ``LOG_LEVEL`` environment variable.
    """
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stdout,
        force=True,
    )

    # Keep third-party libraries from flooding the logs.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("yfinance").setLevel(logging.WARNING)
