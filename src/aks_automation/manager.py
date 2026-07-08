"""High-level manager for Azure Kubernetes Service (AKS) clusters.

This module wraps the Azure SDK for Python (``azure-identity``,
``azure-mgmt-containerservice`` and ``azure-mgmt-resource``) behind a small,
typed API. Every method returns SDK model objects (or primitives) and raises
the package-specific exceptions declared in :mod:`aks_automation.exceptions`
for the common not-found / misconfiguration cases.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from azure.core.exceptions import AzureError, ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.mgmt.containerservice import ContainerServiceClient
from azure.mgmt.containerservice.models import (
    ManagedCluster,
    ManagedClusterAgentPoolProfile,
    ManagedClusterIdentity,
)
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import ResourceGroup

from .config import Settings, get_settings
from .exceptions import (
    ClusterNotFoundError,
    ConfigurationError,
    NodePoolNotFoundError,
)
from .logging_config import get_logger

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Iterator

    from azure.core.credentials import TokenCredential
    from azure.mgmt.containerservice.models import AgentPool

logger = get_logger("manager")

_DEFAULT_NODE_POOL = "nodepool1"


class AKSManager:
    """Manage the lifecycle of AKS clusters and their node pools.

    The manager lazily constructs the underlying SDK clients so that it can be
    instantiated cheaply (e.g. in tests) without triggering authentication.

    Args:
        settings: Optional pre-built :class:`~aks_automation.config.Settings`.
            When omitted, settings are loaded from the environment.
        credential: Optional Azure credential. Defaults to
            :class:`~azure.identity.DefaultAzureCredential`.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        credential: TokenCredential | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._credential = credential
        self._container_client: ContainerServiceClient | None = None
        self._resource_client: ResourceManagementClient | None = None

    # ------------------------------------------------------------------
    # Lazy client / credential accessors
    # ------------------------------------------------------------------
    @property
    def subscription_id(self) -> str:
        """Return the configured subscription ID or raise if unset."""
        if not self.settings.subscription_id:
            raise ConfigurationError(
                "Azure subscription ID is not set. Export AZURE_SUBSCRIPTION_ID "
                "or add it to your .env file."
            )
        return self.settings.subscription_id

    @property
    def credential(self) -> TokenCredential:
        """Return the Azure credential, creating a default one on first use."""
        if self._credential is None:
            self._credential = DefaultAzureCredential()
        return self._credential

    @property
    def container_client(self) -> ContainerServiceClient:
        """Return a memoised :class:`ContainerServiceClient`."""
        if self._container_client is None:
            self._container_client = ContainerServiceClient(
                self.credential, self.subscription_id
            )
        return self._container_client

    @property
    def resource_client(self) -> ResourceManagementClient:
        """Return a memoised :class:`ResourceManagementClient`."""
        if self._resource_client is None:
            self._resource_client = ResourceManagementClient(
                self.credential, self.subscription_id
            )
        return self._resource_client

    # ------------------------------------------------------------------
    # Resource group helpers
    # ------------------------------------------------------------------
    def ensure_resource_group(self, resource_group: str, location: str) -> None:
        """Create the resource group if it does not already exist.

        Args:
            resource_group: Name of the resource group.
            location: Azure region used when the group must be created.
        """
        exists = self.resource_client.resource_groups.check_existence(resource_group)
        if exists:
            logger.info("Resource group '%s' already exists.", resource_group)
            return
        logger.info("Creating resource group '%s' in '%s'.", resource_group, location)
        self.resource_client.resource_groups.create_or_update(
            resource_group, ResourceGroup(location=location)
        )

    # ------------------------------------------------------------------
    # Cluster lifecycle
    # ------------------------------------------------------------------
    def create_cluster(
        self,
        resource_group: str,
        cluster_name: str,
        location: str,
        node_count: int = 3,
        vm_size: str = "Standard_D2s_v3",
        kubernetes_version: str | None = None,
        dns_prefix: str | None = None,
        *,
        wait: bool = True,
    ) -> ManagedCluster:
        """Create (or update) an AKS cluster with a system node pool.

        Args:
            resource_group: Target resource group (created if missing).
            cluster_name: Name of the cluster to create.
            location: Azure region for the cluster.
            node_count: Number of nodes in the default node pool.
            vm_size: VM SKU for the default node pool.
            kubernetes_version: Kubernetes version, or ``None`` for latest.
            dns_prefix: DNS prefix; defaults to ``cluster_name``.
            wait: When ``True``, block until provisioning completes.

        Returns:
            The provisioned (or in-progress) :class:`ManagedCluster`.

        Raises:
            AzureError: If the underlying create/update call fails.
        """
        self.ensure_resource_group(resource_group, location)

        parameters = ManagedCluster(
            location=location,
            dns_prefix=dns_prefix or cluster_name,
            kubernetes_version=kubernetes_version,
            identity=ManagedClusterIdentity(type="SystemAssigned"),
            enable_rbac=True,
            agent_pool_profiles=[
                ManagedClusterAgentPoolProfile(
                    name=_DEFAULT_NODE_POOL,
                    count=node_count,
                    vm_size=vm_size,
                    mode="System",
                    os_type="Linux",
                    type="VirtualMachineScaleSets",
                )
            ],
        )

        logger.info(
            "Creating cluster '%s' (rg=%s, location=%s, nodes=%d, vm=%s).",
            cluster_name,
            resource_group,
            location,
            node_count,
            vm_size,
        )
        poller = self.container_client.managed_clusters.begin_create_or_update(
            resource_group, cluster_name, parameters
        )
        return poller.result() if wait else poller.result(timeout=0)

    def get_cluster(self, resource_group: str, cluster_name: str) -> ManagedCluster:
        """Return a single cluster.

        Args:
            resource_group: Resource group that owns the cluster.
            cluster_name: Name of the cluster.

        Returns:
            The requested :class:`ManagedCluster`.

        Raises:
            ClusterNotFoundError: If the cluster does not exist.
        """
        try:
            return self.container_client.managed_clusters.get(
                resource_group, cluster_name
            )
        except ResourceNotFoundError as exc:
            raise ClusterNotFoundError(
                f"Cluster '{cluster_name}' not found in resource group "
                f"'{resource_group}'."
            ) from exc

    def list_clusters(
        self, resource_group: str | None = None
    ) -> list[ManagedCluster]:
        """List clusters in a resource group or across the subscription.

        Args:
            resource_group: When provided, restrict the listing to this group.

        Returns:
            A list of :class:`ManagedCluster` objects.
        """
        if resource_group:
            iterator: Iterator[ManagedCluster] = (
                self.container_client.managed_clusters.list_by_resource_group(
                    resource_group
                )
            )
        else:
            iterator = self.container_client.managed_clusters.list()
        return list(iterator)

    def delete_cluster(
        self, resource_group: str, cluster_name: str, *, wait: bool = True
    ) -> None:
        """Delete an AKS cluster.

        Args:
            resource_group: Resource group that owns the cluster.
            cluster_name: Name of the cluster to delete.
            wait: When ``True``, block until deletion completes.

        Raises:
            ClusterNotFoundError: If the cluster does not exist.
        """
        logger.info("Deleting cluster '%s' (rg=%s).", cluster_name, resource_group)
        try:
            poller = self.container_client.managed_clusters.begin_delete(
                resource_group, cluster_name
            )
        except ResourceNotFoundError as exc:
            raise ClusterNotFoundError(
                f"Cluster '{cluster_name}' not found in resource group "
                f"'{resource_group}'."
            ) from exc
        if wait:
            poller.result()

    def upgrade_cluster(
        self,
        resource_group: str,
        cluster_name: str,
        kubernetes_version: str,
        *,
        wait: bool = True,
    ) -> ManagedCluster:
        """Upgrade the cluster control plane to a new Kubernetes version.

        Args:
            resource_group: Resource group that owns the cluster.
            cluster_name: Name of the cluster.
            kubernetes_version: Target Kubernetes version (e.g. ``1.30.0``).
            wait: When ``True``, block until the upgrade completes.

        Returns:
            The updated :class:`ManagedCluster`.
        """
        cluster = self.get_cluster(resource_group, cluster_name)
        cluster.kubernetes_version = kubernetes_version
        logger.info(
            "Upgrading cluster '%s' to Kubernetes %s.",
            cluster_name,
            kubernetes_version,
        )
        poller = self.container_client.managed_clusters.begin_create_or_update(
            resource_group, cluster_name, cluster
        )
        return poller.result() if wait else poller.result(timeout=0)

    # ------------------------------------------------------------------
    # Node pools
    # ------------------------------------------------------------------
    def add_node_pool(
        self,
        resource_group: str,
        cluster_name: str,
        node_pool_name: str,
        node_count: int = 1,
        vm_size: str = "Standard_D2s_v3",
        mode: str = "User",
        *,
        wait: bool = True,
    ) -> AgentPool:
        """Add a new node pool to an existing cluster.

        Args:
            resource_group: Resource group that owns the cluster.
            cluster_name: Name of the cluster.
            node_pool_name: Name of the new node pool.
            node_count: Initial node count.
            vm_size: VM SKU for the pool.
            mode: ``System`` or ``User`` node pool mode.
            wait: When ``True``, block until provisioning completes.

        Returns:
            The created :class:`AgentPool`.
        """
        from azure.mgmt.containerservice.models import AgentPool

        parameters = AgentPool(
            count=node_count,
            vm_size=vm_size,
            mode=mode,
            os_type="Linux",
            type="VirtualMachineScaleSets",
        )
        logger.info(
            "Adding node pool '%s' to cluster '%s' (%d nodes, %s).",
            node_pool_name,
            cluster_name,
            node_count,
            vm_size,
        )
        poller = self.container_client.agent_pools.begin_create_or_update(
            resource_group, cluster_name, node_pool_name, parameters
        )
        return poller.result() if wait else poller.result(timeout=0)

    def scale_node_pool(
        self,
        resource_group: str,
        cluster_name: str,
        node_pool_name: str,
        node_count: int,
        *,
        wait: bool = True,
    ) -> AgentPool:
        """Scale an existing node pool to a target node count.

        Args:
            resource_group: Resource group that owns the cluster.
            cluster_name: Name of the cluster.
            node_pool_name: Name of the node pool to scale.
            node_count: Desired number of nodes.
            wait: When ``True``, block until the operation completes.

        Returns:
            The updated :class:`AgentPool`.

        Raises:
            NodePoolNotFoundError: If the node pool does not exist.
        """
        try:
            pool = self.container_client.agent_pools.get(
                resource_group, cluster_name, node_pool_name
            )
        except ResourceNotFoundError as exc:
            raise NodePoolNotFoundError(
                f"Node pool '{node_pool_name}' not found on cluster "
                f"'{cluster_name}'."
            ) from exc

        pool.count = node_count
        logger.info(
            "Scaling node pool '%s' on cluster '%s' to %d nodes.",
            node_pool_name,
            cluster_name,
            node_count,
        )
        poller = self.container_client.agent_pools.begin_create_or_update(
            resource_group, cluster_name, node_pool_name, pool
        )
        return poller.result() if wait else poller.result(timeout=0)

    # ------------------------------------------------------------------
    # Credentials
    # ------------------------------------------------------------------
    def get_credentials(
        self, resource_group: str, cluster_name: str, *, admin: bool = False
    ) -> bytes:
        """Return the raw kubeconfig bytes for a cluster.

        Args:
            resource_group: Resource group that owns the cluster.
            cluster_name: Name of the cluster.
            admin: When ``True``, fetch cluster-admin credentials.

        Returns:
            The raw kubeconfig content as ``bytes``.

        Raises:
            ClusterNotFoundError: If the cluster does not exist.
            AzureError: If no kubeconfig is returned by the API.
        """
        try:
            if admin:
                result = self.container_client.managed_clusters.list_cluster_admin_credentials(
                    resource_group, cluster_name
                )
            else:
                result = self.container_client.managed_clusters.list_cluster_user_credentials(
                    resource_group, cluster_name
                )
        except ResourceNotFoundError as exc:
            raise ClusterNotFoundError(
                f"Cluster '{cluster_name}' not found in resource group "
                f"'{resource_group}'."
            ) from exc

        if not result.kubeconfigs:
            raise AzureError("No kubeconfig was returned by the AKS API.")
        return result.kubeconfigs[0].value
