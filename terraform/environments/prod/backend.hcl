# Partial backend config for the prod environment.
# Usage: terraform init -backend-config=environments/prod/backend.hcl
resource_group_name  = "tfstate-rg"
storage_account_name = "aksautomationtfstate"
container_name       = "tfstate"
key                  = "prod/aks-automation.tfstate"
