# ---------------------------------------------------------------------------
# Cluster identifiers
# ---------------------------------------------------------------------------

output "cluster_id" {
  description = "The fully-qualified Azure resource ID of the AKS cluster."
  value       = azurerm_kubernetes_cluster.aks.id
}

output "cluster_name" {
  description = "The name of the provisioned AKS cluster."
  value       = azurerm_kubernetes_cluster.aks.name
}

output "resource_group_name" {
  description = "The name of the resource group that contains the cluster."
  value       = azurerm_resource_group.aks.name
}

output "location" {
  description = "The Azure region where the cluster was deployed."
  value       = azurerm_kubernetes_cluster.aks.location
}

output "fqdn" {
  description = "The FQDN of the AKS cluster API server."
  value       = azurerm_kubernetes_cluster.aks.fqdn
}

output "kubernetes_version" {
  description = "The Kubernetes version running on the cluster."
  value       = azurerm_kubernetes_cluster.aks.kubernetes_version
}

# ---------------------------------------------------------------------------
# Kubeconfig / TLS (sensitive)
# ---------------------------------------------------------------------------

output "kube_config" {
  description = "Raw kubeconfig file contents for the AKS cluster. Treat as a secret."
  value       = azurerm_kubernetes_cluster.aks.kube_config_raw
  sensitive   = true
}

output "host" {
  description = "The Kubernetes API server endpoint."
  value       = azurerm_kubernetes_cluster.aks.kube_config[0].host
  sensitive   = true
}

output "client_certificate" {
  description = "PEM-encoded client certificate used to authenticate to the cluster."
  value       = azurerm_kubernetes_cluster.aks.kube_config[0].client_certificate
  sensitive   = true
}

output "client_key" {
  description = "PEM-encoded client key used to authenticate to the cluster."
  value       = azurerm_kubernetes_cluster.aks.kube_config[0].client_key
  sensitive   = true
}

output "cluster_ca_certificate" {
  description = "PEM-encoded CA certificate for the cluster's certificate authority."
  value       = azurerm_kubernetes_cluster.aks.kube_config[0].cluster_ca_certificate
  sensitive   = true
}

# ---------------------------------------------------------------------------
# Managed identity
# ---------------------------------------------------------------------------

output "kubelet_identity_object_id" {
  description = "Object ID of the kubelet managed identity (useful for granting ACR pull access)."
  value       = azurerm_kubernetes_cluster.aks.kubelet_identity[0].object_id
}

output "principal_id" {
  description = "Object ID of the cluster's system-assigned managed identity."
  value       = azurerm_kubernetes_cluster.aks.identity[0].principal_id
}
