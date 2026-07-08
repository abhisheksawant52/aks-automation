resource_group_name = "aks-automation-prod-rg"
location            = "westeurope"
cluster_name        = "aks-automation-prod"
kubernetes_version  = "1.30.0"

node_count = 3
vm_size    = "Standard_D4s_v3"

enable_auto_scaling = true
min_node_count      = 3
max_node_count      = 20

user_node_pool_name    = "workload"
user_node_pool_count   = 3
user_node_pool_vm_size = "Standard_D8s_v3"

network_plugin     = "azure"
vnet_address_space = ["10.20.0.0/16"]
subnet_prefixes    = ["10.20.1.0/24"]

tags = {
  project     = "aks-automation"
  managed_by  = "terraform"
  environment = "production"
  owner       = "platform-team"
}
