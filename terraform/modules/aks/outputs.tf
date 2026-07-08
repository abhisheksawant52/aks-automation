output "cluster_id" {
  description = "Resource ID of the AKS cluster."
  value       = azurerm_kubernetes_cluster.this.id
}

output "cluster_name" {
  description = "Name of the AKS cluster."
  value       = azurerm_kubernetes_cluster.this.name
}

output "fqdn" {
  description = "FQDN of the cluster API server."
  value       = azurerm_kubernetes_cluster.this.fqdn
}

output "kubernetes_version" {
  description = "Kubernetes version running on the cluster."
  value       = azurerm_kubernetes_cluster.this.kubernetes_version
}

output "kube_config" {
  description = "Raw kubeconfig for the cluster. Treat as a secret."
  value       = azurerm_kubernetes_cluster.this.kube_config_raw
  sensitive   = true
}

output "kubelet_identity_object_id" {
  description = "Object ID of the kubelet managed identity."
  value       = azurerm_kubernetes_cluster.this.kubelet_identity[0].object_id
}

output "principal_id" {
  description = "Object ID of the cluster system-assigned managed identity."
  value       = azurerm_kubernetes_cluster.this.identity[0].principal_id
}
