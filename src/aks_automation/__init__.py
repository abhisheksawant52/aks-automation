"""aks_automation — manage Azure Kubernetes Service (AKS) clusters.

A thin, typed wrapper around the Azure SDK for Python that provides
day-one and day-two operations for AKS: create, inspect, scale, upgrade,
and delete clusters, manage node pools, and fetch kubeconfig credentials.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__"]
