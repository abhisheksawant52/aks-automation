# Partial backend config for the dev environment.
# Usage: terraform init -backend-config=environments/dev/backend.hcl
resource_group_name  = "tfstate-rg"
storage_account_name = "aksautomationtfstate"
container_name       = "tfstate"
key                  = "dev/aks-automation.tfstate"
