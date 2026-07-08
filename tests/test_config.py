"""Tests for configuration loading and pure helpers."""

from aks_automation import __version__
from aks_automation.config import Settings, get_settings


def test_version_is_semver():
    assert __version__.count(".") == 2


def test_defaults_are_applied(monkeypatch):
    monkeypatch.delenv("AZURE_SUBSCRIPTION_ID", raising=False)
    settings = get_settings()
    assert settings.location == "eastus"
    assert settings.node_count == 3
    assert settings.vm_size == "Standard_D2s_v3"


def test_effective_dns_prefix_falls_back_to_cluster_name():
    settings = Settings(cluster_name="demo-cluster", dns_prefix=None)
    assert settings.effective_dns_prefix == "demo-cluster"


def test_explicit_dns_prefix_is_preferred():
    settings = Settings(cluster_name="demo-cluster", dns_prefix="custom")
    assert settings.effective_dns_prefix == "custom"


def test_overrides_take_precedence():
    settings = get_settings(location="westeurope", node_count=5)
    assert settings.location == "westeurope"
    assert settings.node_count == 5
