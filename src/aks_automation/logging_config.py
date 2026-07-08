"""Centralised logging configuration for aks_automation."""

from __future__ import annotations

import logging

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

_configured = False


def configure_logging(level: str = "INFO") -> logging.Logger:
    """Configure root logging once and return the package logger.

    Args:
        level: Log level name (e.g. ``DEBUG``, ``INFO``, ``WARNING``).

    Returns:
        The ``aks_automation`` package logger.
    """
    global _configured
    if not _configured:
        logging.basicConfig(
            level=level.upper(),
            format=_LOG_FORMAT,
            datefmt=_DATE_FORMAT,
        )
        _configured = True
    else:
        logging.getLogger().setLevel(level.upper())
    return logging.getLogger("aks_automation")


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a child logger under the ``aks_automation`` namespace.

    Args:
        name: Optional child logger name.

    Returns:
        A :class:`logging.Logger` instance.
    """
    if name:
        return logging.getLogger(f"aks_automation.{name}")
    return logging.getLogger("aks_automation")
