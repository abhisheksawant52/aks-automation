"""Tests for AKSManager behaviour that does not require Azure access."""

import pytest

from aks_automation.config import Settings
from aks_automation.exceptions import ConfigurationError
from aks_automation.manager import AKSManager


def test_manager_can_be_instantiated_without_credentials():
    manager = AKSManager(settings=Settings(subscription_id="sub-123"))
    assert manager.subscription_id == "sub-123"


def test_missing_subscription_id_raises_configuration_error():
    manager = AKSManager(settings=Settings(subscription_id=""))
    with pytest.raises(ConfigurationError):
        _ = manager.subscription_id


def test_clients_are_not_built_eagerly():
    manager = AKSManager(settings=Settings(subscription_id="sub-123"))
    assert manager._container_client is None
    assert manager._resource_client is None
