resource_group_name = "aks-automation-dev-rg"
location            = "eastus"
cluster_name        = "aks-automation-dev"
kubernetes_version  = "1.30.0"

node_count = 2
vm_size    = "Standard_D2s_v3"

enable_auto_scaling = true
min_node_count      = 1
max_node_count      = 5

user_node_pool_name    = "workload"
user_node_pool_count   = 1
user_node_pool_vm_size = "Standard_D2s_v3"

network_plugin     = "azure"
vnet_address_space = ["10.10.0.0/16"]
subnet_prefixes    = ["10.10.1.0/24"]

tags = {
  project     = "aks-automation"
  managed_by  = "terraform"
  environment = "dev"
}
