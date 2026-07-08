# ---------------------------------------------------------------------------
# Resource Group
# ---------------------------------------------------------------------------

resource "azurerm_resource_group" "aks" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

# ---------------------------------------------------------------------------
# Networking (VNet + subnet for the cluster nodes)
# ---------------------------------------------------------------------------

module "network" {
  source = "./modules/network"

  resource_group_name = azurerm_resource_group.aks.name
  location            = azurerm_resource_group.aks.location
  vnet_name           = "${var.cluster_name}-vnet"
  vnet_address_space  = var.vnet_address_space
  subnet_name         = "${var.cluster_name}-nodes"
  subnet_prefixes     = var.subnet_prefixes
  tags                = var.tags
}

# ---------------------------------------------------------------------------
# AKS cluster + additional (user) node pool
# ---------------------------------------------------------------------------

module "aks" {
  source = "./modules/aks"

  resource_group_name = azurerm_resource_group.aks.name
  location            = azurerm_resource_group.aks.location
  cluster_name        = var.cluster_name
  dns_prefix          = var.dns_prefix != "" ? var.dns_prefix : var.cluster_name
  kubernetes_version  = var.kubernetes_version

  node_count          = var.node_count
  vm_size             = var.vm_size
  os_disk_size_gb     = var.os_disk_size_gb
  availability_zones  = var.availability_zones
  enable_auto_scaling = var.enable_auto_scaling
  min_node_count      = var.min_node_count
  max_node_count      = var.max_node_count

  network_plugin = var.network_plugin
  # Azure CNI requires an explicit subnet; kubenet manages its own network.
  vnet_subnet_id = var.network_plugin == "azure" ? module.network.subnet_id : null

  user_node_pool_name    = var.user_node_pool_name
  user_node_pool_count   = var.user_node_pool_count
  user_node_pool_vm_size = var.user_node_pool_vm_size

  log_analytics_workspace_id = var.log_analytics_workspace_id
  tags                       = var.tags
}
