# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

variable "resource_group_name" {
  description = "Name of the Azure resource group that will contain the AKS cluster."
  type        = string
  default     = "aks-automation-rg"
}

variable "location" {
  description = "Azure region in which all resources will be created (e.g. eastus, westeurope)."
  type        = string
  default     = "eastus"
}

variable "cluster_name" {
  description = "Name of the AKS managed cluster."
  type        = string
  default     = "aks-automation-cluster"
}

variable "dns_prefix" {
  description = "DNS prefix used to create the cluster FQDN. Defaults to cluster_name when left empty."
  type        = string
  default     = ""
}

variable "kubernetes_version" {
  description = "Kubernetes version to use (e.g. '1.30.0'). Set to null to use the latest stable version."
  type        = string
  default     = null
}

# ---------------------------------------------------------------------------
# Default (system) node pool
# ---------------------------------------------------------------------------

variable "node_count" {
  description = "Initial number of nodes in the default node pool (ignored when auto-scaling is enabled)."
  type        = number
  default     = 3

  validation {
    condition     = var.node_count >= 1 && var.node_count <= 100
    error_message = "node_count must be between 1 and 100."
  }
}

variable "vm_size" {
  description = "Azure VM size for each node in the default node pool."
  type        = string
  default     = "Standard_D2s_v3"
}

variable "os_disk_size_gb" {
  description = "OS disk size in GB for each node. Set to 0 to use the default for the selected VM size."
  type        = number
  default     = 128
}

variable "availability_zones" {
  description = "List of availability zones to spread nodes across. Use [] to disable zone-aware deployment."
  type        = list(string)
  default     = ["1", "2", "3"]
}

# ---------------------------------------------------------------------------
# Auto-scaling
# ---------------------------------------------------------------------------

variable "enable_auto_scaling" {
  description = "Whether to enable the cluster auto-scaler on the default node pool."
  type        = bool
  default     = false
}

variable "min_node_count" {
  description = "Minimum number of nodes when auto-scaling is enabled."
  type        = number
  default     = 1
}

variable "max_node_count" {
  description = "Maximum number of nodes when auto-scaling is enabled."
  type        = number
  default     = 10
}

# ---------------------------------------------------------------------------
# Additional (user) node pool
# ---------------------------------------------------------------------------

variable "user_node_pool_name" {
  description = "Name of the additional user node pool for application workloads."
  type        = string
  default     = "workload"
}

variable "user_node_pool_count" {
  description = "Number of nodes in the additional user node pool."
  type        = number
  default     = 2
}

variable "user_node_pool_vm_size" {
  description = "Azure VM size for the additional user node pool."
  type        = string
  default     = "Standard_D2s_v3"
}

# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------

variable "network_plugin" {
  description = "Kubernetes network plugin to use: 'kubenet' or 'azure' (Azure CNI)."
  type        = string
  default     = "azure"

  validation {
    condition     = contains(["kubenet", "azure"], var.network_plugin)
    error_message = "network_plugin must be either 'kubenet' or 'azure'."
  }
}

variable "vnet_address_space" {
  description = "Address space for the virtual network."
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

variable "subnet_prefixes" {
  description = "Address prefixes for the node subnet."
  type        = list(string)
  default     = ["10.0.1.0/24"]
}

# ---------------------------------------------------------------------------
# Monitoring
# ---------------------------------------------------------------------------

variable "log_analytics_workspace_id" {
  description = "Resource ID of an existing Log Analytics workspace for Azure Monitor integration. Leave empty to skip."
  type        = string
  default     = ""
}

# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------

variable "tags" {
  description = "Map of tags to apply to all resources."
  type        = map(string)
  default = {
    project     = "aks-automation"
    managed_by  = "terraform"
    environment = "dev"
  }
}
