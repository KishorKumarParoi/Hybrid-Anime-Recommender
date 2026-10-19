output "cluster_name" {
  description = "AKS cluster name"
  value       = azurerm_kubernetes_cluster.this.name
}

output "resource_group" {
  description = "Resource group holding all project resources"
  value       = azurerm_resource_group.this.name
}

output "configure_kubectl" {
  description = "Run this to point kubectl at the cluster"
  value       = "az aks get-credentials --resource-group ${azurerm_resource_group.this.name} --name ${azurerm_kubernetes_cluster.this.name}"
}
