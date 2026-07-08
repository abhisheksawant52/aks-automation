"""Runtime configuration for aks_automation.

Settings are loaded, in order of precedence, from explicit keyword
arguments, environment variables (optionally prefixed with ``AKS_``), and
a local ``.env`` file. See ``.env.example`` for the full list of variables.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings.

    Attributes:
        subscription_id: Azure subscription ID that owns the resources.
        resource_group: Resource group that contains (or will contain) the cluster.
        location: Azure region for the cluster, e.g. ``eastus``.
        cluster_name: Name of the managed AKS cluster.
        kubernetes_version: Optional Kubernetes version (``None`` = latest stable).
        node_count: Initial node count for the default (system) node pool.
        vm_size: Azure VM SKU used for the default node pool nodes.
        dns_prefix: DNS prefix for the cluster FQDN (defaults to ``cluster_name``).
        log_level: Root log level for the CLI and library.
    """

    model_config = SettingsConfigDict(
        env_prefix="AKS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    subscription_id: str = Field(
        default="",
        validation_alias="AZURE_SUBSCRIPTION_ID",
        description="Azure subscription ID.",
    )
    resource_group: str = Field(default="aks-automation-rg")
    location: str = Field(default="eastus")
    cluster_name: str = Field(default="aks-automation-cluster")
    kubernetes_version: str | None = Field(default=None)
    node_count: int = Field(default=3, ge=1, le=100)
    vm_size: str = Field(default="Standard_D2s_v3")
    dns_prefix: str | None = Field(default=None)
    log_level: str = Field(default="INFO")

    @property
    def effective_dns_prefix(self) -> str:
        """Return the DNS prefix, falling back to the cluster name."""
        return self.dns_prefix or self.cluster_name


def get_settings(**overrides: object) -> Settings:
    """Build a :class:`Settings` instance, applying any keyword overrides.

    Args:
        **overrides: Field values that take precedence over environment
            variables and the ``.env`` file.

    Returns:
        A populated :class:`Settings` instance.
    """
    return Settings(**overrides)  # type: ignore[arg-type]
