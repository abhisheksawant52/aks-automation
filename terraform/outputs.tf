# ---------------------------------------------------------------------------
# Resource group / networking
# ---------------------------------------------------------------------------

output "resource_group_name" {
  description = "The name of the resource group that contains the cluster."
  value       = azurerm_resource_group.aks.name
}

output "location" {
  description = "The Azure region where the cluster was deployed."
  value       = azurerm_resource_group.aks.location
}

output "vnet_id" {
  description = "Resource ID of the virtual network."
  value       = module.network.vnet_id
}

output "subnet_id" {
  description = "Resource ID of the node subnet."
  value       = module.network.subnet_id
}

# ---------------------------------------------------------------------------
# Cluster
# ---------------------------------------------------------------------------

output "cluster_id" {
  description = "The fully-qualified Azure resource ID of the AKS cluster."
  value       = module.aks.cluster_id
}

output "cluster_name" {
  description = "The name of the provisioned AKS cluster."
  value       = module.aks.cluster_name
}

output "fqdn" {
  description = "The FQDN of the AKS cluster API server."
  value       = module.aks.fqdn
}

output "kubernetes_version" {
  description = "The Kubernetes version running on the cluster."
  value       = module.aks.kubernetes_version
}

output "kubelet_identity_object_id" {
  description = "Object ID of the kubelet managed identity (useful for granting ACR pull access)."
  value       = module.aks.kubelet_identity_object_id
}

output "principal_id" {
  description = "Object ID of the cluster's system-assigned managed identity."
  value       = module.aks.principal_id
}

# ---------------------------------------------------------------------------
# Kubeconfig (sensitive)
# ---------------------------------------------------------------------------

output "kube_config" {
  description = "Raw kubeconfig file contents for the AKS cluster. Treat as a secret."
  value       = module.aks.kube_config
  sensitive   = true
}
