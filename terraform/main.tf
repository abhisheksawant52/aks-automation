terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }

  # Optional: store state in Azure Blob Storage.
  # Uncomment and fill in your values to enable remote state.
  # backend "azurerm" {
  #   resource_group_name  = "tfstate-rg"
  #   storage_account_name = "tfstatesa"
  #   container_name       = "tfstate"
  #   key                  = "aks-automation.tfstate"
  # }
}

provider "azurerm" {
  features {
    resource_group {
      # Prevent accidentally destroying non-empty resource groups.
      prevent_deletion_if_contains_resources = false
    }
  }
}

# ---------------------------------------------------------------------------
# Resource Group
# ---------------------------------------------------------------------------

resource "azurerm_resource_group" "aks" {
  name     = var.resource_group_name
  location = var.location

  tags = var.tags
}

# ---------------------------------------------------------------------------
# AKS Cluster
# ---------------------------------------------------------------------------

resource "azurerm_kubernetes_cluster" "aks" {
  name                = var.cluster_name
  location            = azurerm_resource_group.aks.location
  resource_group_name = azurerm_resource_group.aks.name
  dns_prefix          = var.dns_prefix != "" ? var.dns_prefix : var.cluster_name
  kubernetes_version  = var.kubernetes_version

  # System-assigned managed identity — no service principal credentials to rotate.
  identity {
    type = "SystemAssigned"
  }

  default_node_pool {
    name                = "nodepool1"
    node_count          = var.node_count
    vm_size             = var.node_size
    os_disk_size_gb     = var.os_disk_size_gb
    type                = "VirtualMachineScaleSets"
    enable_auto_scaling = var.enable_auto_scaling
    min_count           = var.enable_auto_scaling ? var.min_node_count : null
    max_count           = var.enable_auto_scaling ? var.max_node_count : null

    # Spread nodes across availability zones when the region supports it.
    zones = var.availability_zones
  }

  network_profile {
    network_plugin    = var.network_plugin
    load_balancer_sku = "standard"
    outbound_type     = "loadBalancer"
  }

  # Enable the Kubernetes Dashboard add-on (disabled by default — RBAC preferred).
  # addon_profile {
  #   kube_dashboard {
  #     enabled = false
  #   }
  # }

  # Azure Monitor / Log Analytics integration.
  dynamic "oms_agent" {
    for_each = var.log_analytics_workspace_id != "" ? [1] : []
    content {
      log_analytics_workspace_id = var.log_analytics_workspace_id
    }
  }

  role_based_access_control_enabled = true

  tags = var.tags

  lifecycle {
    ignore_changes = [
      # Prevent drift when node count is changed outside Terraform (e.g., autoscaler).
      default_node_pool[0].node_count,
      kubernetes_version,
    ]
  }
}
