variable "resource_group_name" {
  description = "Resource group that will contain the cluster."
  type        = string
}

variable "location" {
  description = "Azure region for the cluster."
  type        = string
}

variable "cluster_name" {
  description = "Name of the AKS managed cluster."
  type        = string
}

variable "dns_prefix" {
  description = "DNS prefix for the cluster FQDN."
  type        = string
}

variable "kubernetes_version" {
  description = "Kubernetes version. Null selects the latest stable version."
  type        = string
  default     = null
}

variable "node_count" {
  description = "Node count for the default (system) node pool."
  type        = number
  default     = 3
}

variable "vm_size" {
  description = "VM size for the default node pool."
  type        = string
  default     = "Standard_D2s_v3"
}

variable "os_disk_size_gb" {
  description = "OS disk size (GB) for default node pool nodes."
  type        = number
  default     = 128
}

variable "availability_zones" {
  description = "Availability zones for node placement."
  type        = list(string)
  default     = ["1", "2", "3"]
}

variable "enable_auto_scaling" {
  description = "Enable the cluster autoscaler on the default node pool."
  type        = bool
  default     = false
}

variable "min_node_count" {
  description = "Minimum nodes when autoscaling is enabled."
  type        = number
  default     = 1
}

variable "max_node_count" {
  description = "Maximum nodes when autoscaling is enabled."
  type        = number
  default     = 10
}

variable "network_plugin" {
  description = "Kubernetes network plugin: 'kubenet' or 'azure'."
  type        = string
  default     = "azure"
}

variable "vnet_subnet_id" {
  description = "Subnet ID for node placement (required for Azure CNI). Null for kubenet."
  type        = string
  default     = null
}

variable "user_node_pool_name" {
  description = "Name of the additional user node pool."
  type        = string
  default     = "workload"
}

variable "user_node_pool_count" {
  description = "Node count for the user node pool."
  type        = number
  default     = 2
}

variable "user_node_pool_vm_size" {
  description = "VM size for the user node pool."
  type        = string
  default     = "Standard_D2s_v3"
}

variable "log_analytics_workspace_id" {
  description = "Log Analytics workspace ID for Azure Monitor. Empty to disable."
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags applied to the cluster and node pools."
  type        = map(string)
  default     = {}
}
