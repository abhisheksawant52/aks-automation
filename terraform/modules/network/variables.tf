variable "resource_group_name" {
  description = "Resource group in which to create the network resources."
  type        = string
}

variable "location" {
  description = "Azure region for the network resources."
  type        = string
}

variable "vnet_name" {
  description = "Name of the virtual network."
  type        = string
}

variable "vnet_address_space" {
  description = "Address space for the virtual network."
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

variable "subnet_name" {
  description = "Name of the node subnet."
  type        = string
}

variable "subnet_prefixes" {
  description = "Address prefixes for the node subnet."
  type        = list(string)
  default     = ["10.0.1.0/24"]
}

variable "tags" {
  description = "Tags applied to network resources."
  type        = map(string)
  default     = {}
}
