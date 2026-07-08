"""Command-line interface for aks_automation.

Exposes an ``aks`` command group backed by :class:`~aks_automation.manager.AKSManager`.
Run ``aks --help`` or ``aks <command> --help`` for usage.
"""

from __future__ import annotations

import json
from pathlib import Path

import click

from . import __version__
from .config import get_settings
from .exceptions import AKSAutomationError
from .logging_config import configure_logging
from .manager import AKSManager


def _manager(ctx: click.Context) -> AKSManager:
    """Return the shared :class:`AKSManager` from the click context."""
    return ctx.obj["manager"]


@click.group()
@click.version_option(__version__, prog_name="aks")
@click.option(
    "--log-level",
    default=None,
    help="Override the log level (DEBUG, INFO, WARNING, ERROR).",
)
@click.pass_context
def cli(ctx: click.Context, log_level: str | None) -> None:
    """Manage Azure Kubernetes Service (AKS) clusters from the command line."""
    settings = get_settings()
    configure_logging(log_level or settings.log_level)
    ctx.ensure_object(dict)
    ctx.obj["settings"] = settings
    ctx.obj["manager"] = AKSManager(settings=settings)


# Shared options ------------------------------------------------------------
_rg_option = click.option(
    "--resource-group",
    "-g",
    required=True,
    envvar="AKS_RESOURCE_GROUP",
    help="Azure resource group.",
)
_name_option = click.option(
    "--cluster-name",
    "-n",
    required=True,
    envvar="AKS_CLUSTER_NAME",
    help="Name of the AKS cluster.",
)


@cli.command()
@_rg_option
@_name_option
@click.option("--location", "-l", default="eastus", show_default=True, help="Azure region.")
@click.option(
    "--node-count", default=3, show_default=True, type=click.IntRange(1, 100), help="Node count."
)
@click.option(
    "--vm-size", default="Standard_D2s_v3", show_default=True, help="VM SKU for the node pool."
)
@click.option("--kubernetes-version", default=None, help="Kubernetes version (default: latest).")
@click.option("--dns-prefix", default=None, help="DNS prefix (default: cluster name).")
@click.pass_context
def create(
    ctx: click.Context,
    resource_group: str,
    cluster_name: str,
    location: str,
    node_count: int,
    vm_size: str,
    kubernetes_version: str | None,
    dns_prefix: str | None,
) -> None:
    """Create a new AKS cluster."""
    try:
        cluster = _manager(ctx).create_cluster(
            resource_group=resource_group,
            cluster_name=cluster_name,
            location=location,
            node_count=node_count,
            vm_size=vm_size,
            kubernetes_version=kubernetes_version,
            dns_prefix=dns_prefix,
        )
    except AKSAutomationError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(
        click.style(
            f"Cluster '{cluster.name}' created ({cluster.provisioning_state}).",
            fg="green",
        )
    )


@cli.command()
@_rg_option
@_name_option
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt.")
@click.pass_context
def delete(ctx: click.Context, resource_group: str, cluster_name: str, yes: bool) -> None:
    """Delete an existing AKS cluster."""
    if not yes:
        click.confirm(
            f"Delete cluster '{cluster_name}' in resource group '{resource_group}'?",
            abort=True,
        )
    try:
        _manager(ctx).delete_cluster(resource_group, cluster_name)
    except AKSAutomationError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(click.style(f"Cluster '{cluster_name}' deleted.", fg="green"))


@cli.command(name="list")
@click.option(
    "--resource-group",
    "-g",
    default=None,
    envvar="AKS_RESOURCE_GROUP",
    help="Filter by resource group (default: whole subscription).",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["table", "json"], case_sensitive=False),
    default="table",
    show_default=True,
    help="Output format.",
)
@click.pass_context
def list_clusters(ctx: click.Context, resource_group: str | None, output: str) -> None:
    """List AKS clusters in a resource group or the whole subscription."""
    try:
        clusters = _manager(ctx).list_clusters(resource_group)
    except AKSAutomationError as exc:
        raise click.ClickException(str(exc)) from exc

    if not clusters:
        click.echo("No AKS clusters found.")
        return

    rows = [
        {
            "name": c.name,
            "location": c.location,
            "version": c.kubernetes_version or "-",
            "state": c.provisioning_state or "-",
            "fqdn": c.fqdn or "-",
        }
        for c in clusters
    ]

    if output.lower() == "json":
        click.echo(json.dumps(rows, indent=2))
        return

    headers = ["NAME", "LOCATION", "VERSION", "STATE", "FQDN"]
    click.echo("  ".join(headers))
    for row in rows:
        click.echo("  ".join(str(row[k]) for k in ("name", "location", "version", "state", "fqdn")))


@cli.command()
@_rg_option
@_name_option
@click.pass_context
def show(ctx: click.Context, resource_group: str, cluster_name: str) -> None:
    """Show details for a single AKS cluster."""
    try:
        cluster = _manager(ctx).get_cluster(resource_group, cluster_name)
    except AKSAutomationError as exc:
        raise click.ClickException(str(exc)) from exc
    details = {
        "name": cluster.name,
        "location": cluster.location,
        "kubernetes_version": cluster.kubernetes_version,
        "provisioning_state": cluster.provisioning_state,
        "fqdn": cluster.fqdn,
        "node_pools": [p.name for p in (cluster.agent_pool_profiles or [])],
    }
    click.echo(json.dumps(details, indent=2))


@cli.command()
@_rg_option
@_name_option
@click.option("--node-pool", default="nodepool1", show_default=True, help="Node pool to scale.")
@click.option(
    "--node-count", required=True, type=click.IntRange(0, 1000), help="Desired node count."
)
@click.pass_context
def scale(
    ctx: click.Context,
    resource_group: str,
    cluster_name: str,
    node_pool: str,
    node_count: int,
) -> None:
    """Scale a node pool to a target node count."""
    try:
        pool = _manager(ctx).scale_node_pool(
            resource_group, cluster_name, node_pool, node_count
        )
    except AKSAutomationError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(
        click.style(f"Node pool '{node_pool}' scaled to {pool.count} node(s).", fg="green")
    )


@cli.command()
@_rg_option
@_name_option
@click.option("--kubernetes-version", required=True, help="Target Kubernetes version.")
@click.pass_context
def upgrade(
    ctx: click.Context,
    resource_group: str,
    cluster_name: str,
    kubernetes_version: str,
) -> None:
    """Upgrade a cluster's control plane to a new Kubernetes version."""
    try:
        cluster = _manager(ctx).upgrade_cluster(
            resource_group, cluster_name, kubernetes_version
        )
    except AKSAutomationError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(
        click.style(
            f"Cluster '{cluster.name}' upgraded to {cluster.kubernetes_version}.",
            fg="green",
        )
    )


@cli.command()
@_rg_option
@_name_option
@click.option("--admin", is_flag=True, help="Fetch cluster-admin credentials.")
@click.option(
    "--output-file",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Write kubeconfig here (default: stdout).",
)
@click.pass_context
def credentials(
    ctx: click.Context,
    resource_group: str,
    cluster_name: str,
    admin: bool,
    output_file: Path | None,
) -> None:
    """Fetch kubeconfig credentials for a cluster."""
    try:
        kubeconfig = _manager(ctx).get_credentials(
            resource_group, cluster_name, admin=admin
        )
    except AKSAutomationError as exc:
        raise click.ClickException(str(exc)) from exc

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_bytes(kubeconfig)
        click.echo(click.style(f"Kubeconfig written to '{output_file}'.", fg="green"))
    else:
        click.echo(kubeconfig.decode("utf-8"))


def main() -> None:
    """Console-script entry point."""
    cli()


if __name__ == "__main__":  # pragma: no cover
    main()
