"""
AKS Manager - A CLI tool for managing Azure Kubernetes Service clusters.

Usage:
    python aks_manager.py [COMMAND] [OPTIONS]

Authentication:
    Uses DefaultAzureCredential from azure-identity. Ensure one of the
    following is configured: Azure CLI login, environment variables, or
    managed identity.
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

import click
from azure.core.exceptions import AzureError, ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.mgmt.containerservice import ContainerServiceClient
from azure.mgmt.containerservice.models import (
    ManagedCluster,
    ManagedClusterAgentPoolProfile,
    ManagedClusterServicePrincipalProfile,
    ManagedClusterIdentity,
)
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import ResourceGroup
from dotenv import load_dotenv
from tabulate import tabulate

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("aks-manager")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_subscription_id() -> str:
    """Return the Azure subscription ID from environment or raise."""
    sub_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
    if not sub_id:
        raise click.ClickException(
            "AZURE_SUBSCRIPTION_ID environment variable is not set. "
            "Export it or add it to a .env file."
        )
    return sub_id


def _get_credential() -> DefaultAzureCredential:
    """Return a DefaultAzureCredential instance."""
    try:
        return DefaultAzureCredential()
    except Exception as exc:  # pragma: no cover
        raise click.ClickException(
            f"Failed to acquire Azure credentials: {exc}. "
            "Run 'az login' or set the required environment variables."
        ) from exc


def _container_client(credential: DefaultAzureCredential, subscription_id: str) -> ContainerServiceClient:
    return ContainerServiceClient(credential, subscription_id)


def _resource_client(credential: DefaultAzureCredential, subscription_id: str) -> ResourceManagementClient:
    return ResourceManagementClient(credential, subscription_id)


def _ensure_resource_group(
    resource_client: ResourceManagementClient,
    resource_group: str,
    location: str,
) -> None:
    """Create the resource group if it does not already exist."""
    groups = [rg.name for rg in resource_client.resource_groups.list()]
    if resource_group not in groups:
        logger.info("Resource group '%s' not found — creating it in '%s'.", resource_group, location)
        resource_client.resource_groups.create_or_update(
            resource_group,
            ResourceGroup(location=location),
        )
        logger.info("Resource group '%s' created.", resource_group)
    else:
        logger.info("Resource group '%s' already exists.", resource_group)


# ---------------------------------------------------------------------------
# CLI definition
# ---------------------------------------------------------------------------


@click.group()
@click.version_option("1.0.0", prog_name="aks-manager")
def cli() -> None:
    """AKS Manager — manage Azure Kubernetes Service clusters from the command line."""


# ---------------------------------------------------------------------------
# create-cluster
# ---------------------------------------------------------------------------


@cli.command("create-cluster")
@click.option(
    "--resource-group", "-g",
    required=True,
    envvar="AKS_RESOURCE_GROUP",
    help="Name of the Azure resource group.",
)
@click.option(
    "--cluster-name", "-n",
    required=True,
    envvar="AKS_CLUSTER_NAME",
    help="Name of the AKS cluster to create.",
)
@click.option(
    "--location", "-l",
    default="eastus",
    show_default=True,
    envvar="AKS_LOCATION",
    help="Azure region where the cluster will be created.",
)
@click.option(
    "--node-count",
    default=3,
    show_default=True,
    type=click.IntRange(1, 100),
    help="Number of nodes in the default node pool.",
)
@click.option(
    "--node-size",
    default="Standard_D2s_v3",
    show_default=True,
    help="VM size for the default node pool.",
)
@click.option(
    "--kubernetes-version",
    default=None,
    help="Kubernetes version (e.g. 1.29.0). Defaults to the latest stable.",
)
@click.option(
    "--dns-prefix",
    default=None,
    help="DNS prefix for the cluster FQDN. Defaults to <cluster-name>.",
)
def create_cluster(
    resource_group: str,
    cluster_name: str,
    location: str,
    node_count: int,
    node_size: str,
    kubernetes_version: str | None,
    dns_prefix: str | None,
) -> None:
    """Create a new AKS cluster.

    \b
    Example:
        python aks_manager.py create-cluster \\
            --resource-group my-rg \\
            --cluster-name my-cluster \\
            --location eastus \\
            --node-count 3 \\
            --node-size Standard_D2s_v3
    """
    subscription_id = _get_subscription_id()
    credential = _get_credential()
    resource_client = _resource_client(credential, subscription_id)
    aks_client = _container_client(credential, subscription_id)

    _ensure_resource_group(resource_client, resource_group, location)

    dns = dns_prefix or cluster_name

    cluster_params = ManagedCluster(
        location=location,
        dns_prefix=dns,
        kubernetes_version=kubernetes_version,
        identity=ManagedClusterIdentity(type="SystemAssigned"),
        agent_pool_profiles=[
            ManagedClusterAgentPoolProfile(
                name="nodepool1",
                count=node_count,
                vm_size=node_size,
                mode="System",
                os_type="Linux",
                type="VirtualMachineScaleSets",
            )
        ],
    )

    logger.info(
        "Creating AKS cluster '%s' in resource group '%s' (location: %s, nodes: %d, vm: %s)...",
        cluster_name,
        resource_group,
        location,
        node_count,
        node_size,
    )

    try:
        poller = aks_client.managed_clusters.begin_create_or_update(
            resource_group, cluster_name, cluster_params
        )
        result = poller.result()
        click.echo(
            click.style(
                f"✓ Cluster '{result.name}' created successfully. "
                f"State: {result.provisioning_state}",
                fg="green",
            )
        )
        logger.info("Cluster FQDN: %s", result.fqdn)
    except AzureError as exc:
        raise click.ClickException(f"Failed to create cluster: {exc}") from exc


# ---------------------------------------------------------------------------
# delete-cluster
# ---------------------------------------------------------------------------


@cli.command("delete-cluster")
@click.option("--resource-group", "-g", required=True, envvar="AKS_RESOURCE_GROUP", help="Azure resource group.")
@click.option("--cluster-name", "-n", required=True, envvar="AKS_CLUSTER_NAME", help="Name of the AKS cluster.")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt.")
def delete_cluster(resource_group: str, cluster_name: str, yes: bool) -> None:
    """Delete an existing AKS cluster.

    \b
    Example:
        python aks_manager.py delete-cluster \\
            --resource-group my-rg \\
            --cluster-name my-cluster --yes
    """
    if not yes:
        click.confirm(
            f"Are you sure you want to delete cluster '{cluster_name}' "
            f"in resource group '{resource_group}'?",
            abort=True,
        )

    subscription_id = _get_subscription_id()
    credential = _get_credential()
    aks_client = _container_client(credential, subscription_id)

    logger.info("Deleting AKS cluster '%s' from resource group '%s'...", cluster_name, resource_group)

    try:
        poller = aks_client.managed_clusters.begin_delete(resource_group, cluster_name)
        poller.result()
        click.echo(click.style(f"✓ Cluster '{cluster_name}' deleted successfully.", fg="green"))
    except ResourceNotFoundError:
        raise click.ClickException(
            f"Cluster '{cluster_name}' not found in resource group '{resource_group}'."
        )
    except AzureError as exc:
        raise click.ClickException(f"Failed to delete cluster: {exc}") from exc


# ---------------------------------------------------------------------------
# get-credentials
# ---------------------------------------------------------------------------


@cli.command("get-credentials")
@click.option("--resource-group", "-g", required=True, envvar="AKS_RESOURCE_GROUP", help="Azure resource group.")
@click.option("--cluster-name", "-n", required=True, envvar="AKS_CLUSTER_NAME", help="Name of the AKS cluster.")
@click.option(
    "--output-file",
    default=None,
    help="Path to write the kubeconfig. Defaults to ~/.kube/config (merged).",
)
@click.option("--admin", is_flag=True, help="Retrieve admin credentials (clusterAdmin role required).")
def get_credentials(resource_group: str, cluster_name: str, output_file: str | None, admin: bool) -> None:
    """Fetch kubeconfig for an AKS cluster and merge it into ~/.kube/config.

    \b
    Example:
        python aks_manager.py get-credentials \\
            --resource-group my-rg \\
            --cluster-name my-cluster
    """
    subscription_id = _get_subscription_id()
    credential = _get_credential()
    aks_client = _container_client(credential, subscription_id)

    logger.info(
        "Fetching %s credentials for cluster '%s'...",
        "admin" if admin else "user",
        cluster_name,
    )

    try:
        if admin:
            result = aks_client.managed_clusters.list_cluster_admin_credentials(
                resource_group, cluster_name
            )
        else:
            result = aks_client.managed_clusters.list_cluster_user_credentials(
                resource_group, cluster_name
            )
    except ResourceNotFoundError:
        raise click.ClickException(
            f"Cluster '{cluster_name}' not found in resource group '{resource_group}'."
        )
    except AzureError as exc:
        raise click.ClickException(f"Failed to fetch credentials: {exc}") from exc

    if not result.kubeconfigs:
        raise click.ClickException("No kubeconfig returned from the API.")

    raw_kubeconfig = result.kubeconfigs[0].value  # bytes

    if output_file:
        dest = Path(output_file).expanduser()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw_kubeconfig)
        click.echo(click.style(f"✓ Kubeconfig written to '{dest}'.", fg="green"))
    else:
        # Merge into ~/.kube/config using kubectl
        kube_dir = Path.home() / ".kube"
        kube_dir.mkdir(parents=True, exist_ok=True)
        tmp_file = kube_dir / f"{cluster_name}_tmp.yaml"
        merged_file = kube_dir / "config"

        try:
            tmp_file.write_bytes(raw_kubeconfig)

            env = os.environ.copy()
            if merged_file.exists():
                env["KUBECONFIG"] = f"{tmp_file}{os.pathsep}{merged_file}"
            else:
                env["KUBECONFIG"] = str(tmp_file)

            flat = subprocess.check_output(
                ["kubectl", "config", "view", "--flatten"],
                env=env,
                stderr=subprocess.STDOUT,
            )
            merged_file.write_bytes(flat)
            click.echo(
                click.style(
                    f"✓ Kubeconfig for '{cluster_name}' merged into '{merged_file}'.",
                    fg="green",
                )
            )
        except subprocess.CalledProcessError as exc:
            raise click.ClickException(
                f"kubectl failed while merging kubeconfig: {exc.output.decode()}"
            ) from exc
        except FileNotFoundError:
            # kubectl not on PATH — just write raw file
            merged_file.write_bytes(raw_kubeconfig)
            click.echo(
                click.style(
                    f"✓ kubectl not found; kubeconfig written directly to '{merged_file}'.",
                    fg="yellow",
                )
            )
        finally:
            if tmp_file.exists():
                tmp_file.unlink()


# ---------------------------------------------------------------------------
# list-clusters
# ---------------------------------------------------------------------------


@cli.command("list-clusters")
@click.option(
    "--resource-group", "-g",
    default=None,
    envvar="AKS_RESOURCE_GROUP",
    help="Filter by resource group. If omitted, lists all clusters in the subscription.",
)
@click.option(
    "--output", "-o",
    type=click.Choice(["table", "json"], case_sensitive=False),
    default="table",
    show_default=True,
    help="Output format.",
)
def list_clusters(resource_group: str | None, output: str) -> None:
    """List AKS clusters in the subscription (or a specific resource group).

    \b
    Example:
        python aks_manager.py list-clusters
        python aks_manager.py list-clusters --resource-group my-rg --output json
    """
    import json as _json

    subscription_id = _get_subscription_id()
    credential = _get_credential()
    aks_client = _container_client(credential, subscription_id)

    try:
        if resource_group:
            clusters = list(aks_client.managed_clusters.list_by_resource_group(resource_group))
        else:
            clusters = list(aks_client.managed_clusters.list())
    except AzureError as exc:
        raise click.ClickException(f"Failed to list clusters: {exc}") from exc

    if not clusters:
        click.echo("No AKS clusters found.")
        return

    rows = []
    for c in clusters:
        node_count = sum(
            (p.count or 0) for p in (c.agent_pool_profiles or [])
        )
        rows.append(
            {
                "Name": c.name,
                "Resource Group": c.id.split("/")[4] if c.id else "—",
                "Location": c.location,
                "Kubernetes Version": c.kubernetes_version or "—",
                "Node Count": node_count,
                "State": c.provisioning_state or "—",
                "FQDN": c.fqdn or "—",
            }
        )

    if output == "json":
        click.echo(_json.dumps(rows, indent=2))
    else:
        click.echo(tabulate(rows, headers="keys", tablefmt="rounded_outline"))


# ---------------------------------------------------------------------------
# scale-nodepool
# ---------------------------------------------------------------------------


@cli.command("scale-nodepool")
@click.option("--resource-group", "-g", required=True, envvar="AKS_RESOURCE_GROUP", help="Azure resource group.")
@click.option("--cluster-name", "-n", required=True, envvar="AKS_CLUSTER_NAME", help="Name of the AKS cluster.")
@click.option(
    "--nodepool-name",
    default="nodepool1",
    show_default=True,
    help="Name of the agent pool to scale.",
)
@click.option(
    "--node-count",
    required=True,
    type=click.IntRange(0, 1000),
    help="Desired number of nodes.",
)
def scale_nodepool(resource_group: str, cluster_name: str, nodepool_name: str, node_count: int) -> None:
    """Scale a node pool to the specified node count.

    \b
    Example:
        python aks_manager.py scale-nodepool \\
            --resource-group my-rg \\
            --cluster-name my-cluster \\
            --nodepool-name nodepool1 \\
            --node-count 5
    """
    subscription_id = _get_subscription_id()
    credential = _get_credential()
    aks_client = _container_client(credential, subscription_id)

    logger.info(
        "Scaling node pool '%s' in cluster '%s' to %d nodes...",
        nodepool_name,
        cluster_name,
        node_count,
    )

    try:
        pool = aks_client.agent_pools.get(resource_group, cluster_name, nodepool_name)
    except ResourceNotFoundError:
        raise click.ClickException(
            f"Node pool '{nodepool_name}' not found in cluster '{cluster_name}'."
        )
    except AzureError as exc:
        raise click.ClickException(f"Failed to retrieve node pool: {exc}") from exc

    pool.count = node_count

    try:
        poller = aks_client.agent_pools.begin_create_or_update(
            resource_group, cluster_name, nodepool_name, pool
        )
        result = poller.result()
        click.echo(
            click.style(
                f"✓ Node pool '{nodepool_name}' scaled to {result.count} node(s). "
                f"State: {result.provisioning_state}",
                fg="green",
            )
        )
    except AzureError as exc:
        raise click.ClickException(f"Failed to scale node pool: {exc}") from exc


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cli()
