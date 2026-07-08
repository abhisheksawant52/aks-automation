"""Custom exceptions raised by aks_automation."""

from __future__ import annotations


class AKSAutomationError(Exception):
    """Base class for all aks_automation errors."""


class ConfigurationError(AKSAutomationError):
    """Raised when required configuration (e.g. subscription ID) is missing."""


class ClusterNotFoundError(AKSAutomationError):
    """Raised when a requested cluster does not exist in the resource group."""


class NodePoolNotFoundError(AKSAutomationError):
    """Raised when a requested node pool does not exist on the cluster."""
