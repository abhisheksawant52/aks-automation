terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.80"
    }
  }

  # Remote state in Azure Blob Storage. Provide the concrete values through a
  # partial backend config, e.g.:
  #   terraform init -backend-config=environments/dev/backend.hcl
  #
  # backend "azurerm" {
  #   resource_group_name  = "tfstate-rg"
  #   storage_account_name = "tfstatesa"
  #   container_name       = "tfstate"
  #   key                  = "aks-automation.tfstate"
  # }
}
