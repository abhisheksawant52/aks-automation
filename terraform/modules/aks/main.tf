resource "azurerm_kubernetes_cluster" "this" {
  name                = var.cluster_name
  location            = var.location
  resource_group_name = var.resource_group_name
  dns_prefix          = var.dns_prefix
  kubernetes_version  = var.kubernetes_version

  # System-assigned managed identity — no service principal credentials to rotate.
  identity {
    type = "SystemAssigned"
  }

  default_node_pool {
    name                         = "system"
    node_count                   = var.enable_auto_scaling ? null : var.node_count
    vm_size                      = var.vm_size
    os_disk_size_gb              = var.os_disk_size_gb
    type                         = "VirtualMachineScaleSets"
    vnet_subnet_id               = var.vnet_subnet_id
    enable_auto_scaling          = var.enable_auto_scaling
    min_count                    = var.enable_auto_scaling ? var.min_node_count : null
    max_count                    = var.enable_auto_scaling ? var.max_node_count : null
    zones                        = var.availability_zones
    only_critical_addons_enabled = true
  }

  network_profile {
    network_plugin    = var.network_plugin
    load_balancer_sku = "standard"
    outbound_type     = "loadBalancer"
  }

  # Azure Monitor / Log Analytics integration (enabled only when a workspace is set).
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
      # Prevent drift when the autoscaler changes node count out of band.
      default_node_pool[0].node_count,
    ]
  }
}

resource "azurerm_kubernetes_cluster_node_pool" "user" {
  name                  = var.user_node_pool_name
  kubernetes_cluster_id = azurerm_kubernetes_cluster.this.id
  vm_size               = var.user_node_pool_vm_size
  node_count            = var.user_node_pool_count
  mode                  = "User"
  os_type               = "Linux"
  vnet_subnet_id        = var.vnet_subnet_id
  zones                 = var.availability_zones

  tags = var.tags
}
