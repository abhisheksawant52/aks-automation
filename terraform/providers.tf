provider "azurerm" {
  features {
    resource_group {
      # Prevent accidentally destroying non-empty resource groups.
      prevent_deletion_if_contains_resources = false
    }
  }
}
